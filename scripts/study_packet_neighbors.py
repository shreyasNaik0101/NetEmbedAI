"""Run a fixed ordered-packet diagnostic. Never capture, tune policy or deploy."""

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from netembed.bundle import sha256, write_json
from netembed.contract import BUDGETS, Flow
from netembed.packet_neighbors import VERSION, VARIANTS, PacketNeighbors
from netembed.packet_study import audit_guard, cohorts, summarize


def benchmark(predict, raw, warmup, calls):
    for _ in range(warmup):
        predict(raw)
    times = []
    for _ in range(calls):
        start = time.perf_counter()
        predict(raw)
        times.append((time.perf_counter() - start) * 1000)
    return {
        "calls": calls,
        "warmup": warmup,
        "p50_ms": float(np.percentile(times, 50)),
        "p95_ms": float(np.percentile(times, 95)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/packet-neighbor-study.json")
    parser.add_argument("--data", default="data/processed/v2")
    parser.add_argument("--collection", default="artifacts/local/browser-development")
    parser.add_argument("--reference-root", default="experiments/browser-adaptation")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sys.addaudithook(audit_guard)
    cfg = json.loads(Path(args.config).read_text())
    if cfg["representation_version"] != VERSION or cfg["variants_in_order"] != list(VARIANTS):
        raise ValueError("study differs from implemented representation")
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(out)
    torch.set_num_threads(cfg["threads"])
    with threadpool_limits(limits=cfg["threads"]):
        run(args, cfg, out)


def run(args, cfg, out):
    cohort = cohorts(args.data, args.collection, args.reference_root)
    labels = cohort["labels"]
    provenance = {
        **cohort["provenance"],
        "fixture": False,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "study": cfg,
        "config_sha256": sha256(args.config),
        "source_sha256": {
            p: sha256(p)
            for p in (__file__, "src/netembed/packet_neighbors.py", "src/netembed/packet_study.py")
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
        },
    }
    out.mkdir(parents=True)
    write_json(out / "protocol.json", provenance)
    print(
        json.dumps(
            {
                "stage": "cohorts_verified",
                "train": len(cohort["train"]),
                "local_selection": len(cohort["local"]),
            }
        ),
        flush=True,
    )
    started = time.perf_counter()
    original = PacketNeighbors(cohort["train"], cohort["train_y"], cohort["train_ids"], labels, provenance)
    original.save(out / "neighbors")
    model = PacketNeighbors.load(out / "neighbors")
    preparation_seconds = time.perf_counter() - started
    # These frozen baseline reports use the exact cohorts checked above.
    run_path = Path(args.reference_root) / "forward-mass25-seed17"
    references = {
        name: json.loads((run_path / path / "development.json").read_text())
        for name, path in (("tcn", "tcn-epoch-5"), ("forest", "forest"))
    }
    report = {
        "provenance": provenance,
        "preparation_seconds": preparation_seconds,
        "baseline_reports": references,
        "variants": {},
        "new_capture": False,
        "default_promoted": False,
        "policy_fitted": False,
        "final_evaluation": False,
    }
    for variant in cfg["variants_in_order"]:
        report["variants"][variant] = {}
        for name in ("local", "control"):
            records = []
            for budget in BUDGETS:
                for raw, truth, ident in zip(cohort[name], cohort[name + "_y"], cohort[name + "_ids"]):
                    if name == "local" and len(raw) < budget:
                        continue
                    x = raw[:budget]
                    reply = model.predict(x, variant)
                    records.append(
                        {
                            "id": ident,
                            "reference": labels[int(truth)],
                            "requested_cap": budget,
                            "actual_packets": len(x),
                            "prediction": reply,
                        }
                    )
            write_json(out / f"{variant}-{name}-predictions.json", records)
            result = summarize(records, labels)
            result["nearest_source_counts"] = {
                source: sum(
                    r["prediction"].get("reference_id", "").startswith("browser:") == local
                    for r in records
                    if r["prediction"]["label"] is not None
                )
                for source, local in (("local_training", True), ("public_training", False))
            }
            report["variants"][variant][name] = result
            print(
                json.dumps(
                    {
                        "stage": variant,
                        "cohort": name,
                        "correct": result["correct"],
                        "ranked": result["ranked"],
                        "available": result["available"],
                        "f1": result["mean_budget_macro_f1"],
                    }
                ),
                flush=True,
            )
    # Numerical save/load parity and a repeat do not use selection to fit anything.
    probes = [x[:b] for x in cohort["local"] for b in BUDGETS if len(x) >= b]
    if any(original.predict(x, v) != model.predict(x, v) for v in VARIANTS for x in probes):
        raise ValueError("neighbor save/load prediction mismatch")
    report["save_load_parity"] = {"local_probes_per_variant": len(probes), "exact": True}
    base = references["forest"]
    candidate = report["variants"]["ordered"]
    gate = cfg["gates"]
    recall_pass = all(
        np.mean([b["recall_on_ranked"][label] for b in candidate["local"]["budgets"].values()]) >= value
        for label, value in base["local_recall"].items()
    )
    report["ordered_further_validation_gate"] = {
        "local_comparable": candidate["local"]["mean_budget_macro_f1"]
        >= base["local_macro_f1"] - gate["local_f1_comparability_margin"],
        "public_retained": candidate["control"]["mean_budget_macro_f1"]
        >= base["public_clean_macro_f1"] - gate["public_f1_loss_limit"],
        "class_recall_nonregression": bool(recall_pass),
        "note": "Exploratory screen only. Feature ablations are diagnostics, not extra promotion candidates.",
    }
    raw = Flow(**json.loads(Path(cfg["benchmark_input"]).read_text())).array()
    report["cpu"] = {
        "hardware": platform.platform() + " / " + platform.processor(),
        "input_sha256": sha256(cfg["benchmark_input"]),
        "actual_packets": len(raw),
        "threads": cfg["threads"],
        "ordered": benchmark(model.predict, raw, cfg["benchmark_warmup"], cfg["benchmark_calls"]),
    }
    report["checksums"] = {p.name: sha256(p) for p in out.glob("*-predictions.json")}
    report["artifact_metadata_sha256"] = sha256(out / "neighbors/metadata.json")
    report["limits"] = (
        "Reused development data, fourteen correlated connections/two visits, not new independent accuracy. "
        "1-NN uses one reference per original flow, not forest domain mass weights; no causal learner claim. "
        "After8 has no budget5 evidence; its incomplete-cohort mean is null. No calibrated probabilities, "
        "threshold fitting or promotion. CPU excludes HTTP/capture/UI. Fixed no-sweep protocol."
    )
    write_json(out / "report.json", report)
    print(
        json.dumps(
            {"stage": "complete", "cpu": report["cpu"], "gate": report["ordered_further_validation_gate"]}
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
