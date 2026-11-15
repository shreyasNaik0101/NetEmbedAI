"""Small matched forest study. Old calibration/comparison/final records stay excluded."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support

from .browser_adaptation import UNCOMMITTED, check_roles, forest_weights
from .bundle import Predictor, export_bundle, sha256, write_json
from .contract import Flow, forest_features, validate_array

CONFIG_SHA = "8ff86861442284f840321aae8eb84f85c5c867d2eb94d1291a72a57baf9c29e1"
MAPS = {"clean": "summary-v1", "size-jitter": "summary-v1", "relative-size": "summary-relative-size-v1"}


def guard(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve().as_posix().lower()
        if any(
            value in path
            for value in (
                "forest-policy-calibration",
                "prospective-paired",
                "youtube-failure-diagnostic",
                "-cal-",
                "-eval-",
                "/calibration.jsonl",
                "/test.jsonl",
            )
        ):
            raise ValueError("calibration, paired comparison, diagnostics and final inputs excluded")
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("size study is offline")


def read_config(path):
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA:
        raise ValueError("fixed size-study declaration changed")
    return json.loads(raw)


def shift_large(raw, delta):
    """Abstract metadata treatment; no timing/direction/order changes or claims of wire validity."""
    x = validate_array(raw).copy()
    if not isinstance(delta, (int, np.integer)) or not -32 <= delta <= 32:
        raise ValueError("size delta must be an integer in [-32,32]")
    mask = x[:, 2] >= 1200
    x[mask, 2] = np.clip(x[mask, 2] + delta, 1200, 65527)
    return x


def training_delta(sample_id, seed=70017):
    key = hashlib.sha256(f"{seed}:{sample_id}".encode()).digest()
    rng = np.random.default_rng(int.from_bytes(key[:8], "big"))
    return 0 if rng.integers(3) == 0 else int(rng.integers(-32, 33))


def read_public(directory, split, per_class=None):
    if split not in ("train", "selection"):
        raise ValueError("only public training/selection is permitted")
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    path = directory / (split + ".jsonl")
    if sha256(path) != manifest["files"][path.name]:
        raise ValueError("public split checksum changed")
    flows, targets, ids, counts = [], [], [], Counter()
    with path.open(encoding="utf-8") as source:
        for index, line in enumerate(source):
            if index >= 15000 or len(line) > 131072:
                raise ValueError("public source exceeds bounded study")
            row = json.loads(line)
            label = row["label"]
            if per_class is None or counts[label] < per_class:
                flows.append(Flow(packets=row["packets"]).array())
                targets.append(manifest["labels"].index(label))
                ids.append(row["id"])
                counts[label] += 1
    if per_class and any(counts[label] != per_class for label in manifest["labels"]):
        raise ValueError("public retention cohort lacks a class")
    return flows, np.asarray(targets), ids, manifest


def local_rows(reference, cfg):
    source = reference.meta["provenance"]
    rows, bindings = {}, {}
    root = Path(cfg["local_root"])
    for role in ("train", "selection"):
        if cfg[role + "_trials"] != source["config"][role + "_trials"]:
            raise ValueError("original local roles changed")
        rows[role] = []
        for trial in cfg[role + "_trials"]:
            proof = source["browser_evidence"][trial]
            path = root / (trial + "-development-rows.jsonl")
            summary = root / (trial + "-collection-summary.json")
            if sha256(path) != proof["rows_sha256"] or sha256(summary) != proof["summary_sha256"]:
                raise ValueError("validated local export changed")
            bindings[str(path)] = sha256(path)
            bindings[str(summary)] = sha256(summary)
            values = [json.loads(line) for line in path.read_text().splitlines()]
            if any(r["group_id"] != proof["session_id"] for r in values):
                raise ValueError("local export session changed")
            rows[role].extend(r for r in values if r["label"] in cfg["local_labels"])
    check_roles(rows["train"], rows["selection"])
    if any(len({r["id"] for r in values}) != len(values) for values in rows.values()):
        raise ValueError("duplicated local flow")
    proofs = source["browser_evidence"]
    if max(
        proofs[t].get("observed_packet_range_unix_ms", proofs[t]["first_packet_range_unix_ms"])[1]
        for t in cfg["train_trials"]
    ) >= min(proofs[t]["first_packet_range_unix_ms"][0] for t in cfg["selection_trials"]):
        raise ValueError("original local training/selection chronology overlaps")
    if {k: dict(Counter(r["label"] for r in v)) for k, v in rows.items()} != source["local_counts"]:
        raise ValueError("local cohort count changed")
    return rows, bindings


def case_metrics(truth, probabilities, labels, macro_labels):
    predicted = probabilities.argmax(1)
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predicted, labels=range(len(labels)), zero_division=0
    )
    return {
        "n": len(truth),
        "accuracy": float(np.mean(predicted == truth)),
        "macro_f1": float(f1_score(truth, predicted, labels=macro_labels, average="macro", zero_division=0)),
        "classes": {
            label: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, label in enumerate(labels)
        },
        "confusion_matrix": confusion_matrix(truth, predicted, labels=range(len(labels))).tolist(),
    }


def assess(model, flows, targets, ids, domain, cfg):
    report, records = {}, []
    for variant, delta in (("clean", 0), ("minus20", -20), ("plus20", 20)):
        by_budget = {}
        for budget in cfg["budgets"]:
            indices = [i for i, raw in enumerate(flows) if domain == "public" or len(raw) >= budget]
            if not indices:
                raise ValueError("development checkpoint has no eligible examples")
            raw = [shift_large(flows[i][:budget], delta) for i in indices]
            probabilities = np.concatenate(
                [model.probabilities(raw[i : i + 128]) for i in range(0, len(raw), 128)]
            )
            macro = range(len(model.labels)) if domain == "public" else sorted(set(targets.tolist()))
            by_budget[str(budget)] = case_metrics(targets[indices], probabilities, model.labels, macro)
            for i, values, scores in zip(indices, raw, probabilities):
                records.append(
                    {
                        "domain": domain,
                        "variant": variant,
                        "id": ids[i],
                        "requested_budget": budget,
                        "observed_packets": len(values),
                        "reference": model.labels[int(targets[i])],
                        "top1": model.labels[int(scores.argmax())],
                        "probabilities": scores.tolist(),
                    }
                )
        report[variant] = {
            "budgets": by_budget,
            "macro_f1": float(np.mean([r["macro_f1"] for r in by_budget.values()])),
            "class_recall": {
                label: float(np.mean([r["classes"][label]["recall"] for r in by_budget.values()]))
                for label in model.labels
                if any(r["classes"][label]["support"] for r in by_budget.values())
            },
        }
    report["stress"] = {
        "macro_f1": (report["minus20"]["macro_f1"] + report["plus20"]["macro_f1"]) / 2,
        "class_recall": {
            label: (report["minus20"]["class_recall"][label] + report["plus20"]["class_recall"][label]) / 2
            for label in report["clean"]["class_recall"]
        },
        "primary_class_recall": {
            label: float(
                np.mean(
                    [report[v]["budgets"]["10"]["classes"][label]["recall"] for v in ("minus20", "plus20")]
                )
            )
            for label in report["clean"]["class_recall"]
        },
    }
    return report, records


def gates(candidate, control, cfg):
    rules = cfg["gates"]
    loc, base = candidate["local"], control["local"]
    pub, original = candidate["public"], control["public"]
    epsilon = 1e-12
    return {
        "local_clean_floor": loc["clean"]["macro_f1"] >= rules["minimum_local_clean_f1"],
        "local_clean_f1": loc["clean"]["macro_f1"] + epsilon
        >= base["clean"]["macro_f1"] - rules["maximum_local_clean_f1_loss"],
        "local_clean_classes": all(
            loc["clean"]["class_recall"][c] + epsilon >= base["clean"]["class_recall"][c]
            for c in cfg["local_labels"]
        ),
        "local_stress_gain": loc["stress"]["macro_f1"] + epsilon
        >= base["stress"]["macro_f1"] + rules["minimum_local_stress_f1_gain"],
        "local_stress_classes": all(
            loc["stress"]["class_recall"][c] + epsilon
            >= max(rules["minimum_local_stress_class_recall"], base["stress"]["class_recall"][c])
            for c in cfg["local_labels"]
        ),
        "local_primary_stress_floor": all(
            loc["stress"]["primary_class_recall"][c] >= rules["minimum_local_stress_class_recall"]
            for c in cfg["local_labels"]
        ),
        "public_clean_f1": pub["clean"]["macro_f1"] + epsilon
        >= original["clean"]["macro_f1"] - rules["maximum_public_clean_f1_loss"],
        "public_clean_classes": all(
            pub["clean"]["class_recall"][c] + epsilon >= value - rules["maximum_public_class_recall_loss"]
            for c, value in original["clean"]["class_recall"].items()
        ),
        "public_stress_f1": pub["stress"]["macro_f1"] + epsilon >= original["stress"]["macro_f1"],
        "public_stress_classes": all(
            pub["stress"]["class_recall"][c] + epsilon >= value - rules["maximum_public_class_recall_loss"]
            for c, value in original["stress"]["class_recall"].items()
        ),
    }


def choose(reports, cfg):
    eligible = [
        name
        for name in ("size-jitter", "relative-size")
        if all(gates(reports[name], reports["clean"], cfg).values())
    ]
    if not eligible:
        return None
    best = max(eligible, key=lambda name: reports[name]["local"]["stress"]["macro_f1"])
    if (
        "relative-size" in eligible
        and reports["relative-size"]["local"]["stress"]["macro_f1"]
        >= reports[best]["local"]["stress"]["macro_f1"] - 0.01
    ):
        return "relative-size"
    return best


def run(seed, config_path, output_root):
    cfg = read_config(config_path)
    if seed not in cfg["seeds"]:
        raise ValueError("undeclared forest seed")
    root = Path(output_root)
    out = root / f"seed{seed}"
    if out.exists():
        raise FileExistsError("preserve previous run")
    chosen = None
    if seed != 17:
        first = json.loads((root / "seed17/result.json").read_text())
        if first["config"] != cfg or first["chosen"] is None:
            raise ValueError("seed17 ineligible: no repetitions")
        chosen = first["chosen"]
        if seed == 123 and not (root / "seed42/result.json").exists():
            raise ValueError("run fixed seed42 before seed123")
    reference = Predictor(cfg["reference_bundle"])
    if (
        reference.identity != cfg["reference_id"]
        or sha256(Path(cfg["reference_bundle"]) / "forest.json") != cfg["reference_weight_sha256"]
    ):
        raise ValueError("reference artifact changed")
    if sha256(Path(cfg["public_data"]) / "manifest.json") != cfg["public_manifest_sha256"]:
        raise ValueError("public manifest changed")
    rows, evidence = local_rows(reference, cfg)
    public, py, pids, manifest = read_public(cfg["public_data"], "train")
    validation, vy, vids, _ = read_public(cfg["public_data"], "selection", cfg["public_selection_per_class"])
    if manifest["labels"] != reference.labels or len(public) != 14000:
        raise ValueError("public training inventory differs")
    local = {role: [Flow(packets=r["packets"]).array() for r in values] for role, values in rows.items()}
    targets = {
        role: np.array([reference.labels.index(r["label"]) for r in values]) for role, values in rows.items()
    }
    train = public + local["train"]
    train_ids = pids + [r["id"] for r in rows["train"]]
    if len(set(train_ids)) != len(train_ids):
        raise ValueError("duplicate training ID")
    deltas = [training_delta(ident, cfg["augmentation_seed"]) for ident in train_ids]
    weights = forest_weights(len(public) * 4, np.repeat(targets["train"], 4), cfg["local_training_mass"])
    y = np.repeat(np.concatenate([py, targets["train"]]), 4)
    out.mkdir(parents=True, exist_ok=False)
    augmentation = []
    for ident, raw, delta in zip(train_ids, train, deltas):
        altered = shift_large(raw, delta)
        augmentation.append(
            {
                "id": ident,
                "nominal_delta_bytes": delta,
                "actual_byte_delta": int(altered[:, 2].sum() - raw[:, 2].sum()),
                "changed_packets": int((altered[:, 2] != raw[:, 2]).sum()),
                "duration_delta_ms": 0,
                "removed_packets": 0,
            }
        )
    write_json(out / "training-augmentation-manifest.json", augmentation)
    write_json(
        out / "data-manifest.json",
        {
            "local_exports": evidence,
            "public_manifest": cfg["public_manifest_sha256"],
            "training_ids": train_ids,
            "public_selection_ids": vids,
            "local_selection_ids": [r["id"] for r in rows["selection"]],
            "local_session_counts": {k: len({r["group_id"] for r in v}) for k, v in rows.items()},
            "limits": "Original validated exports reused; raw browser logs not reopened for fresh QC. Reused development, not independent final evidence.",
        },
    )
    provenance = {
        "fixture": False,
        "experimental": True,
        "config": cfg,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": sha256(__file__),
        "forest_seed": seed,
        "augmentation_seed": cfg["augmentation_seed"],
        "inference_sources": {
            name: sha256(Path(__file__).parent / name) for name in ("contract.py", "bundle.py")
        },
        "data_manifest_sha256": sha256(out / "data-manifest.json"),
        "augmentation_manifest_sha256": sha256(out / "training-augmentation-manifest.json"),
        "license": "Public CESNET CC-BY-4.0; local browser examples private development",
        "limits": cfg["limits"],
    }
    write_json(out / "config.json", provenance)
    reports, identities = {}, {}
    for arm in ["clean", "size-jitter", "relative-size"] if seed == 17 else ["clean", chosen]:
        started = time.perf_counter()
        features = np.asarray(
            [
                forest_features(shift_large(raw, delta)[:budget], reference.normalizer, MAPS[arm])
                for raw, delta in zip(train, deltas if arm == "size-jitter" else [0] * len(train))
                for budget in cfg["budgets"]
            ]
        )
        model = RandomForestClassifier(**cfg["forest"], random_state=seed, n_jobs=cfg["threads"])
        model.fit(features, y, sample_weight=weights)
        folder = out / arm
        bundle = export_bundle(
            folder / "bundle",
            model,
            reference.normalizer,
            reference.labels,
            {**provenance, "arm": arm},
            {"feature_map": MAPS[arm]},
            UNCOMMITTED,
        )
        if seed == 17 and arm == "clean" and sha256(bundle / "forest.json") != cfg["reference_weight_sha256"]:
            raise ValueError(
                "matched clean control did not reproduce original forest; stop before treatments"
            )
        predictor = Predictor(bundle)
        # Plain-JSON inference must agree with sklearn before reporting quality.
        expected = model.predict_proba(features[:16])
        actual = (
            predictor.probabilities([raw[:budget] for raw in train[:4] for budget in cfg["budgets"]])
            if arm != "size-jitter"
            else predictor.probabilities(
                [
                    shift_large(raw, delta)[:budget]
                    for raw, delta in zip(train[:4], deltas[:4])
                    for budget in cfg["budgets"]
                ]
            )
        )
        if not np.allclose(expected, actual, rtol=0, atol=1e-12):
            raise ValueError("exported inference differs from fitted forest")
        del features, model
        loc, lp = assess(
            predictor,
            local["selection"],
            targets["selection"],
            [r["id"] for r in rows["selection"]],
            "local",
            cfg,
        )
        pub, pp = assess(predictor, validation, vy, vids, "public", cfg)
        report = {
            "local": loc,
            "public": pub,
            "seconds": time.perf_counter() - started,
            "export_maximum_difference": float(np.max(np.abs(expected - actual))),
            "artifact_id": predictor.identity,
        }
        write_json(folder / "development.json", report)
        write_json(folder / "predictions.json", lp + pp)
        reports[arm], identities[arm] = report, predictor.identity
        print(
            json.dumps(
                {
                    "seed": seed,
                    "arm": arm,
                    "local_clean_f1": loc["clean"]["macro_f1"],
                    "local_stress_f1": loc["stress"]["macro_f1"],
                    "public_clean_f1": pub["clean"]["macro_f1"],
                    "seconds": report["seconds"],
                }
            ),
            flush=True,
        )
    selected = choose(reports, cfg) if seed == 17 else chosen
    result = {
        "config": cfg,
        "forest_seed": seed,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "chosen": selected,
        "gates": {
            name: gates(value, reports["clean"], cfg) for name, value in reports.items() if name != "clean"
        },
        "artifact_ids": identities,
        "development_sha256": {name: sha256(out / name / "development.json") for name in reports},
        "prediction_sha256": {name: sha256(out / name / "predictions.json") for name in reports},
        "config_sha256": sha256(out / "config.json"),
        "policy_fitted": False,
        "default_promoted": False,
        "note": "Exploratory reused development plus abstract stress; no actual family-stratified forward result.",
    }
    write_json(out / "result.json", result)
    return result


def finish(config_path, output_root):
    """Consolidate the fixed seed17 choice; no alternate seed or arm can rescue it."""
    cfg, root = read_config(config_path), Path(output_root)
    if (root / "decision.json").exists():
        raise FileExistsError("preserve size-study decision")
    first = json.loads((root / "seed17/result.json").read_text())
    chosen = first["chosen"]
    seeds = [17] if chosen is None else cfg["seeds"]
    reports, passed, hashes, data_hash, augmentation_hash = {}, {}, {}, None, None
    for seed in seeds:
        folder = root / f"seed{seed}"
        result = json.loads((folder / "result.json").read_text())
        if result["config"] != cfg or result["forest_seed"] != seed or result["chosen"] != chosen:
            raise ValueError("repetition declaration or frozen choice changed")
        if sha256(folder / "config.json") != result["config_sha256"]:
            raise ValueError("run provenance changed")
        provenance = json.loads((folder / "config.json").read_text())
        current_data = sha256(folder / "data-manifest.json")
        current_augmentation = sha256(folder / "training-augmentation-manifest.json")
        if (
            current_data != provenance["data_manifest_sha256"]
            or current_augmentation != provenance["augmentation_manifest_sha256"]
        ):
            raise ValueError("run data or augmentation changed")
        if data_hash is not None and (current_data != data_hash or current_augmentation != augmentation_hash):
            raise ValueError("repetitions changed the training/development examples or augmented views")
        data_hash, augmentation_hash = current_data, current_augmentation
        reports[seed] = {}
        for arm in result["artifact_ids"]:
            if (
                sha256(folder / arm / "development.json") != result["development_sha256"][arm]
                or sha256(folder / arm / "predictions.json") != result["prediction_sha256"][arm]
            ):
                raise ValueError("saved development evidence changed")
            model = Predictor(folder / arm / "bundle")
            if model.identity != result["artifact_ids"][arm] or model.meta["policy"]["fitted"]:
                raise ValueError("run artifact changed or acquired a policy")
            reports[seed][arm] = json.loads((folder / arm / "development.json").read_text())
        for arm in result["gates"]:
            if result["gates"][arm] != gates(reports[seed][arm], reports[seed]["clean"], cfg):
                raise ValueError("saved gate outcome differs")
        if seed == 17 and choose(reports[seed], cfg) != chosen:
            raise ValueError("seed17 selection changed")
        passed[str(seed)] = chosen is not None and all(result["gates"][chosen].values())
        hashes[str(seed)] = sha256(folder / "result.json")
    stable = chosen is not None and len(seeds) == 3 and all(passed.values())
    summary = {}
    if chosen is not None:
        for arm in ("clean", chosen):
            summary[arm] = {}
            for domain in ("local", "public"):
                for condition in ("clean", "stress"):
                    values = [reports[seed][arm][domain][condition]["macro_f1"] for seed in seeds]
                    summary[arm][f"{domain}_{condition}_macro_f1"] = {
                        "per_seed": dict(zip(map(str, seeds), values)),
                        "mean": float(np.mean(values)),
                        "std_population": float(np.std(values)),
                        "range": [min(values), max(values)],
                    }
    benchmarks = None
    if stable:
        source = Path(cfg["local_root"])
        raw, ident = None, None
        for trial in cfg["train_trials"]:
            rows = [
                json.loads(line)
                for line in (source / (trial + "-development-rows.jsonl")).read_text().splitlines()
            ]
            eligible = next((r for r in rows if len(r["packets"]) >= 30), None)
            if eligible is not None:
                raw, ident = Flow(packets=eligible["packets"]).array(), eligible["id"]
                break
        if raw is None:
            raise ValueError("benchmark requires a complete training prefix")
        benchmarks = {
            "input_id": ident,
            "input_sha256": hashlib.sha256(raw.tobytes()).hexdigest(),
            "config": cfg["benchmark"],
            "results": {},
        }
        for arm in ("clean", chosen):
            model = Predictor(root / "seed17" / arm / "bundle")
            benchmarks["results"][arm] = {"artifact_id": model.identity}
            for budget in cfg["benchmark"]["budgets"]:
                for _ in range(cfg["benchmark"]["warmup"]):
                    model.predict(raw[:budget])
                timings = []
                for _ in range(cfg["benchmark"]["calls"]):
                    start = time.perf_counter()
                    model.predict(raw[:budget])
                    timings.append((time.perf_counter() - start) * 1000)
                benchmarks["results"][arm][str(budget)] = {
                    "p50_ms": float(np.percentile(timings, 50)),
                    "p95_ms": float(np.percentile(timings, 95)),
                }
        write_json(root / "benchmark.json", benchmarks)
    decision = {
        "config_sha256": CONFIG_SHA,
        "seed17_choice": chosen,
        "eligible_by_seed": passed,
        "eligible_all_three_seeds": stable,
        "metrics": summary,
        "result_sha256": hashes,
        "development_candidate": str(root / "seed17" / chosen / "bundle") if stable else None,
        "benchmark_sha256": sha256(root / "benchmark.json") if benchmarks else None,
        "policy_fitted": False,
        "default_promoted": False,
        "status": "development_candidate_only" if stable else "stop_no_validated_candidate",
        "limits": cfg["limits"],
    }
    write_json(root / "decision.json", decision)
    return decision
