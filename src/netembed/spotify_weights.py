"""Three fixed offline weighting candidates; no capture, policy fitting or deployment."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from threadpoolctl import threadpool_limits

from .browser_adaptation import UNCOMMITTED, check_roles
from .bundle import Predictor, export_bundle, sha256, write_json
from .contract import Flow, forest_features
from .ipv6_pilot import clean_assessment, new_training, read_config as read_recipe
from .paired_study import read_plan
from .size_robustness import local_rows, read_public
from .spotify_repair import role_rows, stage_receipt
from .spotify_repair_stages import local_rows_selection, retention_gates

CONFIG_SHA = "b2bf81f86cdd9d4247eee771c695da8b482c6df483553130fc76131d87ecb6fc"


def read_config(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ValueError("fixed weighting protocol changed")
    return json.loads(raw)


def sample_weights(public_count, local_labels, spotify_mass):
    """Keep public mass fixed; reduce Spotify while preserving YT/IG balance."""
    counts = Counter(local_labels)
    if public_count <= 0 or set(counts) != {"youtube", "instagram", "spotify"}:
        raise ValueError("requires public examples and exactly the three local classes")
    if not 0 < spotify_mass < 0.25:
        raise ValueError("Spotify mass must be positive and below total local mass")
    mass = {"spotify": spotify_mass, "youtube": (0.25 - spotify_mass) / 2}
    mass["instagram"] = mass["youtube"]
    return np.concatenate(
        [
            np.full(public_count, 0.75 / public_count),
            np.asarray([mass[label] / counts[label] for label in local_labels]),
        ]
    )


def access_guard(event, args, cfg, recipe):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("weight study is offline")
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    public = Path(recipe["public_data"]).resolve()
    if p.is_relative_to(Path("data").resolve()) and p not in [
        public / n for n in ["manifest.json", "train.jsonl", "selection.jsonl"]
    ]:
        raise ValueError("calibration/final or unrelated public data excluded")
    if p.is_relative_to(Path("artifacts/local").resolve()):
        root = Path(cfg["previous_root"]).resolve()
        current = p.parent == root and (
            p.name in ["training-stage.json", "development-stage.json"]
            or any(
                p.name.startswith(t + "-")
                for t in ["spotify-train-01", "spotify-train-02", "spotify-train-03", "spotify-dev-01"]
            )
        )
        old = p.parent == Path(recipe["local_root"]).resolve() and any(
            p.name == t + suffix
            for t in recipe["train_trials"] + recipe["selection_trials"]
            for suffix in ["-development-rows.jsonl", "-collection-summary.json"]
        )
        adopted = p.parent == Path(recipe["new_training_root"]).resolve() and any(
            p.name.startswith(t + "-") for t in recipe["new_training_archives"]
        )
        if not (current or old or adopted):
            raise ValueError("private cohort/role excluded from weight study")
    if p.is_relative_to(Path("experiments").resolve()):
        allowed = [
            cfg["output"],
            recipe["reference_bundle"],
            "experiments/ipv6-public-policy-v1/bundle",
            "experiments/spotify-data-repair-v1/training",
            "experiments/spotify-data-repair-v1/development",
        ]
        if not any(p.is_relative_to(Path(a).resolve()) for a in allowed):
            raise ValueError("unrelated experiment excluded from weight study")


def choose(reports):
    eligible = [a for a, r in reports.items() if all(r["gates"].values())]
    return (
        max(
            eligible,
            key=lambda a: (
                min(reports[a]["metrics"]["spotify"]["budgets"][b]["accuracy"] for b in ["10", "20", "30"]),
                reports[a]["metrics"]["spotify"]["budgets"]["10"]["accuracy"]
                * reports[a]["metrics"]["spotify"]["budgets"]["10"]["n"],
                -reports[a]["spotify_mass"],
            ),
        )
        if eligible
        else None
    )


def assess(model, cohorts, recipe):
    metrics, predictions = {}, []
    for domain, (raw, y, ids) in cohorts.items():
        metrics[domain], cases = clean_assessment(
            model, raw, y, ids, "public" if domain == "public" else "local", recipe
        )
        predictions.extend({**p, "domain": domain} for p in cases)
    return metrics, predictions


def run(path):
    cfg = read_config(path)
    prior = read_plan(cfg["previous_plan"])
    recipe = read_recipe(prior["training_recipe"])
    out = Path(cfg["output"])
    if out.exists():
        raise FileExistsError("preserve existing weighting run; no extra fits")
    sys.addaudithook(lambda e, a: access_guard(e, a, cfg, recipe))
    torch.set_num_threads(cfg["threads"])
    failed = Path(cfg["previous_failed_decision"])
    if sha256(failed) != cfg["previous_failed_decision_sha256"] or all(
        json.loads(failed.read_text())["gates"].values()
    ):
        raise ValueError("prior failure binding changed")
    stage_receipt(cfg["previous_root"], prior, "training")
    ref = Predictor(prior["source_bundle"])
    old = Predictor(recipe["reference_bundle"])
    if (
        ref.identity != prior["source_artifact_id"]
        or sha256(Path(prior["source_bundle"]) / "forest.json") != prior["source_weight_sha256"]
    ):
        raise ValueError("control changed")
    original, old_bindings = local_rows(old, recipe)
    adopted, adopted_bindings = new_training(recipe)
    spotify, bindings = role_rows(cfg["previous_root"], prior, "train")
    selection, selection_bindings = role_rows(cfg["previous_root"], prior, "selection")
    retained, _ = local_rows_selection(old, recipe)
    train = original["train"] + adopted + spotify
    check_roles(train, retained + selection)
    if len(train) != 79 or len(spotify) != 17 or len(selection) != 4 or len(retained) != 17:
        raise ValueError("frozen local inventory differs")
    if len({r["id"] for r in train}) != len(train):
        raise ValueError("duplicate training rows")
    public, py, pids, _ = read_public(recipe["public_data"], "train")
    validation, vy, vids, _ = read_public(recipe["public_data"], "selection", 50)
    previous_manifest = Path("experiments/spotify-data-repair-v1/training/data-manifest.json")
    if sha256(previous_manifest) != cfg["previous_training_manifest_sha256"]:
        raise ValueError("previous training manifest changed")
    previous = json.loads(previous_manifest.read_text())
    if (
        pids != previous["public_training_ids"]
        or [r["id"] for r in spotify] != previous["new_spotify_training_ids"]
        or [r["id"] for r in train[:62]] != previous["old_local_training_ids"]
    ):
        raise ValueError("not the same training data")
    if (
        len(public) != 14000
        or sha256(Path(recipe["public_data"]) / "manifest.json") != recipe["public_manifest_sha256"]
    ):
        raise ValueError("public manifest/inventory changed")
    cohorts = {"public": (validation, vy, vids)}
    for domain, rows in [("spotify", selection), ("local", retained)]:
        cohorts[domain] = (
            [Flow(packets=r["packets"]).array() for r in rows],
            np.asarray([ref.labels.index(r["label"]) for r in rows]),
            [r["id"] for r in rows],
        )
    control, cp = assess(ref, cohorts, recipe)
    if control != json.loads(
        Path("experiments/spotify-data-repair-v1/development/control-metrics.json").read_text()
    ):
        raise ValueError("control development reproduction differs")
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "protocol.json", cfg)
    write_json(out / "control-metrics.json", control)
    write_json(out / "control-predictions.json", cp)
    manifest = {
        "training_ids": pids + [r["id"] for r in train],
        "selection_ids": {d: ids for d, (_, _, ids) in cohorts.items()},
        "training_archives": bindings,
        "selection_archives": selection_bindings,
        "old_exports": old_bindings,
        "adopted": adopted_bindings,
        "previous_training_manifest_sha256": sha256(previous_manifest),
    }
    write_json(out / "data-manifest.json", manifest)
    raw = public + [Flow(packets=r["packets"]).array() for r in train]
    started = time.perf_counter()
    features = np.asarray(
        [forest_features(x[:b], ref.normalizer, cfg["feature_map"]) for x in raw for b in cfg["budgets"]]
    )
    write_json(
        out / "feature-build.json", {"seconds": time.perf_counter() - started, "shape": list(features.shape)}
    )
    local_labels = np.repeat([r["label"] for r in train], 4)
    targets = np.repeat(np.concatenate([py, [ref.labels.index(r["label"]) for r in train]]), 4)
    reports = {}
    with threadpool_limits(limits=cfg["threads"]):
        for arm in cfg["arms"]:
            name = arm["name"]
            started = time.perf_counter()
            weights = sample_weights(len(public) * 4, local_labels, arm["spotify_mass"])
            fitted = RandomForestClassifier(**cfg["forest"], random_state=cfg["seed"], n_jobs=cfg["threads"])
            fitted.fit(features, targets, sample_weight=weights)
            bundle = export_bundle(
                out / name / "bundle",
                fitted,
                ref.normalizer,
                ref.labels,
                {
                    "fixture": False,
                    "experimental": True,
                    "config_sha256": CONFIG_SHA,
                    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                    "source_sha256": sha256(__file__),
                    "arm": arm,
                    "data_manifest_sha256": sha256(out / "data-manifest.json"),
                    "license": "CESNET CC-BY-4.0 and private user-authorized local training",
                    "limits": cfg["limits"],
                },
                {"feature_map": cfg["feature_map"]},
                UNCOMMITTED,
            )
            model = Predictor(bundle)
            probe = [x[:b] for x in raw[:4] + raw[-4:] for b in cfg["budgets"]]
            expected = fitted.predict_proba(
                np.asarray([forest_features(x, ref.normalizer, cfg["feature_map"]) for x in probe])
            )
            difference = float(np.max(np.abs(expected - model.probabilities(probe))))
            if difference > 1e-12:
                raise ValueError("portable export parity failed")
            metrics, predictions = assess(model, cohorts, recipe)
            report = {
                "spotify_mass": arm["spotify_mass"],
                "metrics": metrics,
                "gates": retention_gates(metrics, control, cfg),
                "artifact_id": model.identity,
                "bundle": str(bundle),
                "weight_sha256": sha256(bundle / "forest.json"),
                "export_maximum_difference": difference,
                "fit_export_assess_seconds": time.perf_counter() - started,
            }
            write_json(out / name / "report.json", report)
            write_json(out / name / "predictions.json", predictions)
            reports[name] = report
            print(json.dumps({"arm": name, "gates": report["gates"]}), flush=True)
    selected = choose(reports)
    decision = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": CONFIG_SHA,
        "status": "development_candidate_only" if selected else "failed_stop",
        "selected": selected,
        "gates": {a: r["gates"] for a, r in reports.items()},
        "artifacts": {
            a: {k: r[k] for k in ["artifact_id", "bundle", "weight_sha256"]} for a, r in reports.items()
        },
        "new_fits": len(reports),
        "policy_fitted": False,
        "default_promoted": False,
        "limits": cfg["limits"],
        "files": {str(p): sha256(p) for p in out.rglob("*") if p.is_file()},
    }
    write_json(out / "decision.json", decision)
    return decision
