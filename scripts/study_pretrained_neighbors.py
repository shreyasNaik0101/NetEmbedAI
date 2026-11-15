"""Fixed official encoder transfer screen. No capture, policy fitting or deployment."""

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
from netembed.packet_study import audit_guard, cohorts, summarize
from netembed.pretrained_neighbors import FrozenEncoder, FrozenNeighbors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pretrained-neighbor-study.json")
    parser.add_argument("--data", default="data/processed/v2")
    parser.add_argument("--collection", default="artifacts/local/browser-development")
    parser.add_argument("--reference-root", default="experiments/browser-adaptation")
    parser.add_argument("--upstream", default="artifacts/local/upstream-models")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sys.addaudithook(audit_guard)
    cfg = json.loads(Path(args.config).read_text())
    upstream = Path(args.upstream)
    wheel = upstream / "cesnet_models-0.4.1-py3-none-any.whl"
    weights = upstream / "30pktTCNET_256_CESNET_QUIC22_Week46_Domains.pth"
    if sha256(wheel) != cfg["wheel_sha256"] or sha256(weights) != cfg["weight_sha256"]:
        raise ValueError("upstream wheel/weights differ from frozen study")
    # Optional research dependency is isolated; the app's environment is unchanged.
    sys.path.insert(0, str((upstream / "python").resolve()))
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(out)
    torch.set_num_threads(cfg["threads"])
    with threadpool_limits(limits=cfg["threads"]):
        run(args, cfg, out, wheel, weights)


def run(args, cfg, out, wheel, weights):
    cohort = cohorts(args.data, args.collection, args.reference_root)
    labels = cohort["labels"]
    encoder = FrozenEncoder(weights, cfg["weight_sha256"])
    # Actual pretrained outputs, including incomplete prefixes, must be finite/unit length.
    encoder.encode([cohort["train"][0][:b] for b in BUDGETS])
    out.mkdir(parents=True)
    provenance = {
        **cohort["provenance"],
        "fixture": False,
        "study": cfg,
        "config_sha256": sha256(args.config),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {
            p: sha256(p)
            for p in (__file__, "src/netembed/pretrained_neighbors.py", "src/netembed/packet_study.py")
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "cesnet_models": cfg["package_version"],
        },
        "weight_sha256": cfg["weight_sha256"],
        "wheel_sha256": cfg["wheel_sha256"],
        "encoder_parameters": sum(p.numel() for p in encoder.model.parameters()),
        "pretraining_overlap": cfg["pretraining"],
    }
    write_json(out / "protocol.json", provenance)
    banks, fit_times = {}, {}
    for budget in BUDGETS:
        started = time.perf_counter()

        def progress(done, total):
            if done % 4096 == 0 or done == total:
                print(
                    json.dumps({"stage": "encode_training", "budget": budget, "done": done, "total": total}),
                    flush=True,
                )

        banks[budget] = encoder.encode([x[:budget] for x in cohort["train"]], cfg["batch_size"], progress)
        fit_times[str(budget)] = time.perf_counter() - started
    fitted = FrozenNeighbors(encoder, banks, cohort["train_y"], cohort["train_ids"], labels, provenance)
    fitted.save(out / "bundle", wheel)
    model = FrozenNeighbors.load(out / "bundle")
    report = {
        "provenance": provenance,
        "reference_embedding_seconds": fit_times,
        "cohorts": {},
        "policy_fitted": False,
        "default_promoted": False,
        "new_capture": False,
        "final_evaluation": False,
    }
    for name in ("local", "control"):
        records = []
        for budget in BUDGETS:
            for raw, truth, ident in zip(cohort[name], cohort[name + "_y"], cohort[name + "_ids"]):
                if name == "local" and len(raw) < budget:
                    continue
                x = raw[:budget]
                reply = model.predict(x)
                records.append(
                    {
                        "id": ident,
                        "reference": labels[int(truth)],
                        "requested_cap": budget,
                        "actual_packets": len(x),
                        "prediction": reply,
                    }
                )
            print(json.dumps({"stage": "score", "cohort": name, "budget": budget}), flush=True)
        write_json(out / f"{name}-predictions.json", records)
        report["cohorts"][name] = summarize(records, labels)
        print(
            json.dumps(
                {
                    "stage": name,
                    "correct": report["cohorts"][name]["correct"],
                    "f1": report["cohorts"][name]["mean_budget_macro_f1"],
                }
            ),
            flush=True,
        )
    probes = [x[:b] for x in cohort["local"] for b in BUDGETS if len(x) >= b]
    max_delta = 0
    for raw in probes:
        left, right = fitted.predict(raw), model.predict(raw)
        if left["label"] != right["label"] or left["reference_id"] != right["reference_id"]:
            raise ValueError("loaded pretrained retrieval label changed")
        max_delta = max(
            max_delta,
            max(
                abs(a["cosine_similarity"] - b["cosine_similarity"])
                for a, b in zip(left["alternatives"], right["alternatives"])
            ),
        )
    if max_delta > 1e-7:
        raise ValueError("loaded pretrained similarities changed")
    report["save_load_parity"] = {"probes": len(probes), "maximum_similarity_difference": max_delta}
    baseline_path = Path(args.reference_root) / "forward-mass25-seed17/forest/development.json"
    baseline = json.loads(baseline_path.read_text())
    local = report["cohorts"]["local"]
    recall_pass = all(
        np.mean([b["recall_on_ranked"][label] for b in local["budgets"].values()]) >= value
        for label, value in baseline["local_recall"].items()
    )
    report["further_validation_gate"] = {
        "local_comparable": local["mean_budget_macro_f1"]
        >= baseline["local_macro_f1"] - cfg["gates"]["local_f1_comparability_margin"],
        "class_recall_nonregression": bool(recall_pass),
        "public_control": "retrospective/non-independent of pretraining chronology; diagnostic only",
    }
    raw = Flow(**json.loads(Path(cfg["benchmark_input"]).read_text())).array()
    for _ in range(cfg["benchmark_warmup"]):
        model.predict(raw)
    times = []
    for _ in range(cfg["benchmark_calls"]):
        start = time.perf_counter()
        model.predict(raw)
        times.append((time.perf_counter() - start) * 1000)
    report["cpu"] = {
        "calls": len(times),
        "warmup": cfg["benchmark_warmup"],
        "threads": cfg["threads"],
        "input_sha256": sha256(cfg["benchmark_input"]),
        "actual_packets": len(raw),
        "p50_ms": float(np.percentile(times, 50)),
        "p95_ms": float(np.percentile(times, 95)),
    }
    report["checksums"] = {p.name: sha256(p) for p in out.glob("*-predictions.json")}
    report["artifact_metadata_sha256"] = sha256(out / "bundle/metadata.json")
    report["limits"] = (
        "Exploratory reused development only. Prefixes share14 connections/two visits. "
        "Pretrained week46 overlaps original public final; no evaluation there. Historical control predates "
        "pretraining and cannot establish forward retention. Similarities are not probabilities. "
        "No policy fit or live promotion. CPU includes encoder/retrieval, excludes capture/HTTP/UI."
    )
    write_json(out / "report.json", report)
    print(
        json.dumps({"stage": "complete", "gate": report["further_validation_gate"], "cpu": report["cpu"]}),
        flush=True,
    )


if __name__ == "__main__":
    main()
