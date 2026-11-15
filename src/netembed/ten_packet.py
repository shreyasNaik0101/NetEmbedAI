"""Explicit ten-packet inference contract and a fit-free, development-only comparison."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from .bundle import Predictor, sha256, write_json
from .contract import Flow
from .ipv6_pilot import clean_assessment, read_config as read_recipe
from .paired_study import read_plan
from .size_robustness import read_public
from .spotify_repair import role_rows
from .spotify_repair_stages import local_rows_selection

CONFIG_SHA = "9b30398a2a3c2788a908b3669371965399af99cb2910a0ea696aa762e6ec2158"


def read_config(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ValueError("ten-packet declaration changed")
    return json.loads(raw)


def restrict_to_ten(source, output, provenance, allow_fixture=False):
    source, output = Path(source), Path(output)
    predictor = Predictor(source, allow_fixture=allow_fixture)
    if predictor.meta["kind"] != "forest" or predictor.fixed_prefix_packets:
        raise ValueError("requires an unrestricted forest source")
    meta = deepcopy(predictor.meta)
    meta["architecture"]["fixed_prefix_packets"] = 10
    meta["policy"] = {
        "version": "ten-packet-unfitted-v1",
        "min_packets": 10,
        "threshold": 1.0,
        "temperature": 1.0,
        "fitted": False,
        "tie_break": "label_order",
        "validation_scope": "uncalibrated_ten_packet_development",
        "locally_checked_labels": [],
        "note": "New explicit ten-packet decision contract; no inherited confidence policy. Requires separate fresh verification/calibration before live use.",
    }
    meta["provenance"] = {
        **meta["provenance"],
        "ten_packet_mode": {
            **provenance,
            "runtime_sources": {
                name: sha256(Path(__file__).parent / name) for name in ["bundle.py", "contract.py"]
            },
            "source_artifact_id": predictor.identity,
            "source_weight_sha256": sha256(source / "forest.json"),
            "new_fits": 0,
            "input_contract": "At least10 observed; use exactly first10, ignore later packets for scoring",
        },
    }
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source / "forest.json", output / "forest.json")
    write_json(output / "metadata.json", meta)
    write_json(
        output / "checksums.json",
        {
            "metadata.json": sha256(output / "metadata.json"),
            **meta["files"],
        },
    )
    result = Predictor(output, allow_fixture=allow_fixture)
    if sha256(output / "forest.json") != sha256(source / "forest.json"):
        raise ValueError("mode export changed weights")
    return result


def exact_ten_cohort(flows, targets, ids):
    eligible = [i for i, x in enumerate(flows) if len(x) >= 10]
    excluded = [
        {"id": ident, "packets": len(x), "reason": "fewer_than_ten_packets"}
        for ident, x in zip(ids, flows)
        if len(x) < 10
    ]
    return (
        [flows[i][:10] for i in eligible],
        np.asarray(targets)[eligible],
        [ids[i] for i in eligible],
    ), excluded


def gates(candidate, control, cfg):
    rules, eps = cfg["gates"], 1e-12
    s, old = candidate["spotify"], control["spotify"]
    return {
        "spotify_recall": s["accuracy"] + eps >= rules["spotify_min_recall"],
        "spotify_correct_gain": s["accuracy"] * s["n"] + eps
        >= old["accuracy"] * old["n"] + rules["spotify_min_correct_gain"],
        "local_f1_retention": candidate["local"]["macro_f1"] + eps >= control["local"]["macro_f1"],
        "local_class_retention": all(
            candidate["local"]["classes"][label]["recall"] + eps
            >= control["local"]["classes"][label]["recall"]
            for label in ["youtube", "instagram"]
        ),
        "public_f1_retention": candidate["public"]["macro_f1"] + eps
        >= control["public"]["macro_f1"] - rules["public_max_macro_f1_loss"],
        "public_class_retention": all(
            candidate["public"]["classes"][label]["recall"] + eps
            >= c["recall"] - rules["public_max_class_recall_loss"]
            for label, c in control["public"]["classes"].items()
        ),
    }


def guard(event, args, cfg, recipe):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("ten-packet study is offline")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    if p.is_relative_to(Path("data").resolve()) and p not in [
        Path(recipe["public_data"]).resolve() / n for n in ["selection.jsonl", "manifest.json"]
    ]:
        raise ValueError("training/calibration/final data excluded")
    if p.is_relative_to(Path("artifacts/local").resolve()):
        root = Path(cfg["previous_root"]).resolve()
        current = p.parent == root and (
            p.name.startswith("spotify-dev-01-")
            or p.name in ["spotify-train-0" + str(i) + "-archive.json" for i in [1, 2, 3]]
        )
        old = p.parent == Path(recipe["local_root"]).resolve() and any(
            p.name == t + "-development-rows.jsonl" for t in recipe["selection_trials"]
        )
        if not (current or old):
            raise ValueError("private training or protected cohort excluded")
    if p.is_relative_to(Path("experiments").resolve()):
        allowed = [
            cfg["source_bundle"],
            cfg["output"],
            recipe["reference_bundle"],
            "experiments/ipv6-public-policy-v1/bundle",
        ]
        if p != Path(cfg["prior_decision"]).resolve() and not any(
            p.is_relative_to(Path(a).resolve()) for a in allowed
        ):
            raise ValueError("unrelated experiment excluded")


def run(path):
    cfg = read_config(path)
    prior, recipe = read_plan(cfg["previous_plan"]), read_recipe(cfg["recipe"])
    out = Path(cfg["output"])
    if out.exists():
        raise FileExistsError("preserve existing ten-packet comparison")
    sys.addaudithook(lambda e, a: guard(e, a, cfg, recipe))
    torch.set_num_threads(cfg["threads"])
    if sha256(cfg["prior_decision"]) != cfg["prior_decision_sha256"]:
        raise ValueError("prior failed study changed")
    source = Predictor(cfg["source_bundle"])
    control = Predictor(prior["source_bundle"])
    if (
        source.identity != cfg["source_artifact_id"]
        or sha256(Path(cfg["source_bundle"]) / "forest.json") != cfg["source_weights_sha256"]
    ):
        raise ValueError("frozen candidate differs")
    if control.identity != prior["source_artifact_id"] or control.labels != source.labels:
        raise ValueError("control identity/labels differ")
    retained, bindings = local_rows_selection(Predictor(recipe["reference_bundle"]), recipe)
    spotify, spbindings = role_rows(cfg["previous_root"], prior, "selection")
    raw, y, ids, _ = read_public(recipe["public_data"], "selection", cfg["public_selection_per_class"])
    public, excluded = exact_ten_cohort(raw, y, ids)
    if len(raw) != 500 or len(public[0]) != 452 or len(retained) != 17 or len(spotify) != 4:
        raise ValueError("declared exact-prefix support differs")
    if sha256(Path(recipe["public_data"]) / "manifest.json") != recipe["public_manifest_sha256"]:
        raise ValueError("public manifest changed")
    cohorts = {"public": public}
    for name, rows in [("local", retained), ("spotify", spotify)]:
        group, short = exact_ten_cohort(
            [Flow(packets=r["packets"]).array() for r in rows],
            [source.labels.index(r["label"]) for r in rows],
            [r["id"] for r in rows],
        )
        if short:
            raise ValueError("local exact-ten support differs")
        cohorts[name] = group
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "protocol.json", cfg)
    write_json(
        out / "data-manifest.json",
        {
            "eligible_ids": {d: c[2] for d, c in cohorts.items()},
            "public_excluded": excluded,
            "public_source_n": len(raw),
            "public_eligible_n": len(public[0]),
            "old_selection_bindings": bindings,
            "spotify_selection_bindings": spbindings,
            "training_accessed": False,
        },
    )
    model = restrict_to_ten(
        cfg["source_bundle"],
        out / "bundle",
        {
            "config_sha256": CONFIG_SHA,
            "source_sha256": sha256(__file__),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "limits": cfg["limits"],
        },
    )
    invariant_views = 0
    invariant_difference = 0.0
    for row in retained + spotify:
        full = Flow(packets=row["packets"]).array()
        views = [full[:b] for b in [10, 20, 30] if len(full) >= b]
        # Actual real-artifact checks; later packets must not influence scores.
        original = model.probabilities([full[:10]])[0]
        for view in views:
            invariant_difference = max(
                invariant_difference, float(np.max(np.abs(model.probabilities([view])[0] - original)))
            )
            invariant_views += 1
    if invariant_difference != 0:
        raise ValueError("real-artifact fixed-prefix invariance failed")
    write_json(
        out / "prefix-check.json",
        {
            "views": invariant_views,
            "maximum_difference": invariant_difference,
            "basis": "real archived local flows at available10/20/30; scores must always use first10",
        },
    )
    reports = {}
    maximum_parity_difference = 0.0
    with threadpool_limits(limits=cfg["threads"]):
        for arm, predictor in [("control", control), ("candidate", model)]:
            metrics, predictions = {}, []
            for name, (flows, targets, identities) in cohorts.items():
                result, cases = clean_assessment(
                    predictor,
                    flows,
                    targets,
                    identities,
                    "public" if name == "public" else "local",
                    {"budgets": [10]},
                )
                metrics[name] = result["budgets"]["10"]
                predictions.extend({**c, "domain": name, "model_packets": 10} for c in cases)
                if arm == "candidate":
                    expected = np.concatenate(
                        [source.probabilities(flows[i : i + 128]) for i in range(0, len(flows), 128)]
                    )
                    maximum_parity_difference = max(
                        maximum_parity_difference,
                        float(np.max(np.abs(expected - np.asarray([c["probabilities"] for c in cases])))),
                    )
            reports[arm] = metrics
            write_json(out / (arm + "-metrics.json"), metrics)
            write_json(out / (arm + "-predictions.json"), predictions)
        if maximum_parity_difference != 0:
            raise ValueError("ten-packet restriction changed source probabilities")
        probe = public[0][0]
        for _ in range(cfg["cpu"]["warmup"]):
            model.predict(probe)
        durations = []
        for _ in range(cfg["cpu"]["calls"]):
            start = time.perf_counter()
            model.predict(probe)
            durations.append((time.perf_counter() - start) * 1000)
    write_json(
        out / "cpu.json",
        {
            **cfg["cpu"],
            "threads": cfg["threads"],
            "model_packets": 10,
            "p50_ms": float(np.percentile(durations, 50)),
            "p95_ms": float(np.percentile(durations, 95)),
            "basis": "trained-model CPU predict call on one real selection prefix; no capture, browser receipt or hard real-time guarantee",
        },
    )
    checks = gates(reports["candidate"], reports["control"], cfg)
    decision = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": CONFIG_SHA,
        "status": "reused_development_pass_only" if all(checks.values()) else "failed_stop",
        "gates": checks,
        "artifact_id": model.identity,
        "bundle": str(out / "bundle"),
        "weights_sha256": sha256(out / "bundle/forest.json"),
        "source_probability_max_difference": maximum_parity_difference,
        "new_fits": 0,
        "policy_fitted": False,
        "default_promoted": False,
        "limits": cfg["limits"],
        "files": {str(p): sha256(p) for p in out.rglob("*") if p.is_file()},
    }
    write_json(out / "decision.json", decision)
    return decision
