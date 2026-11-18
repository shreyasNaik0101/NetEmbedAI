"""Bounded offline supervised adaptation. No capture, final data, or deployment."""

import copy
import json
import re
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

from .bundle import Predictor, export_bundle, sha256, write_json
from .contract import BUDGETS, Flow, summary
from .data import read_split

UNCOMMITTED = {
    "version": "browser-adaptation-uncalibrated-v1",
    "threshold": 1.0,
    "min_packets": 5,
    "temperature": 1.0,
    "fitted": False,
    "note": "Changed model needs separate calibration; no transferred correctness confidence.",
}


def check_roles(train_rows, selection_rows):
    for key in ("id", "group_id"):
        if {row[key] for row in train_rows} & {row[key] for row in selection_rows}:
            raise ValueError("browser session/record crosses train and selection")


def load_reference_trial(root, trial, labels, stage, collection_plan_path=None):
    prefixes = {"development": "dev", "calibration": "cal"}
    spec = None
    if collection_plan_path is not None:
        from .browser_collection import read_collection_plan, trial_spec

        if stage != "development":
            raise ValueError("new development plan cannot authorize calibration/final access")
        collection_plan = read_collection_plan(collection_plan_path)
        spec = trial_spec(collection_plan, trial)
    elif stage not in prefixes or not re.fullmatch(rf"(?:instagram|youtube)-{prefixes[stage]}-0[12]", trial):
        raise ValueError("unexpected trial role; final recordings are excluded")
    row_kind = "development" if stage == "development" else "calibration"
    report = json.loads((root / f"{trial}-collection-summary.json").read_text())
    if spec:
        intent = json.loads((root / f"{trial}-intent.json").read_text())
        if (
            report["trial_id"] != trial
            or intent["trial_id"] != trial
            or report["collection_plan_sha256"] != sha256(collection_plan_path)
            or intent["collection_plan_sha256"] != sha256(collection_plan_path)
            or report["collection_role"] != spec["role"]
            or intent["collection_role"] != spec["role"]
        ):
            raise ValueError("new development role or plan binding changed")
        required = {
            f"{trial}-{name}.json"
            for name in ("intent", "capture", "reference", "socket-parity", "audit", "timing", "netlog")
        }
        required |= {f"{trial}-development-rows.jsonl", Path(collection_plan_path).name}
        if "followup_protocol" in collection_plan:
            required |= {f"{trial}-attempt{suffix}.json" for suffix in ("", "-capture", "-timing", "-status")}
            attempt = json.loads((root / f"{trial}-attempt.json").read_text())
            if attempt["session_id"] != report["session_id"] or attempt["protocol_sha256"] != sha256(
                collection_plan_path
            ):
                raise ValueError("follow-up archive differs from its single bound attempt")
        if not required.issubset(report["evidence_sha256"]):
            raise ValueError("new collection omits required evidence hashes")
    for name, digest in report["evidence_sha256"].items():
        if Path(name).name != name or sha256(root / name) != digest:
            raise ValueError("collection evidence changed")
    evidence = json.loads((root / f"{trial}-capture.json").read_text())
    reference = json.loads((root / f"{trial}-reference.json").read_text())
    if (
        evidence["fixture"]
        or reference.get("fixture")
        or evidence["source"] != "user_started_capture"
        or evidence["counters"]["running"]
    ):
        raise ValueError("requires stopped genuine user capture")
    if evidence["adapter_version"] != "tshark-prefix-ns-v3":
        raise ValueError("browser pilot requires a consistent v3 adapter")
    if evidence["session_id"] != reference["session_id"] or evidence["session_id"] != report["session_id"]:
        raise ValueError("browser reference session mismatch")
    if reference["evidence_sha256"] != sha256(root / f"{trial}-capture.json"):
        raise ValueError("reference does not bind capture")
    if (
        reference["netlog_sha256"] != sha256(root / f"{trial}-netlog.json")
        or reference["artifact_id"] != evidence["artifact_id"]
    ):
        raise ValueError("reference log/artifact binding changed")
    parity = json.loads((root / f"{trial}-socket-parity.json").read_text())
    if parity["evidence_sha256"] != sha256(root / f"{trial}-capture.json") or parity[
        "reference_sha256"
    ] != sha256(root / f"{trial}-reference.json"):
        raise ValueError("feature QC does not bind capture/reference")
    checked = {row["flow_id"]: row for row in parity["flows"]}
    original = {row["flow_id"]: row for row in evidence["flows"]}
    references = [row for row in reference["flows"] if row["reference"]["status"] == "mapped"]
    if spec:
        from .browser_collection import eligible_references

        references, excluded = eligible_references(reference, parity)
        if report["excluded_mapped_flows"] != excluded:
            raise ValueError("predeclared feature exclusions changed")
    expected = {f"browser:{evidence['session_id']}:{row['flow_id']}": row for row in references}
    rows_path = root / f"{trial}-{row_kind}-rows.jsonl"
    rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
    if len(rows) != len(expected) or {row["id"] for row in rows} != set(expected):
        raise ValueError("mapped reference inventory was filtered or duplicated")
    for row in rows:
        if set(row) != {"id", "group_id", "date", "label", "schema_version", "packets"}:
            raise ValueError("unexpected field in packet-only training export")
        ref = expected[row["id"]]
        quality = checked[ref["flow_id"]]
        if (
            quality["socket"]["status"] != "unique_socket"
            or quality["missing_browser_prefix_packets"]
            or any(
                item["ordered_payload_size_mismatches"] or item["missing_browser_prefix_packets"]
                for item in quality["by_direction"].values()
            )
            or ref["packets"] != original[ref["flow_id"]]["packets"]
        ):
            raise ValueError("browser feature QC failed")
        if (
            row["label"] not in labels
            or row["label"] != ref["reference"]["label"]
            or row["packets"] != ref["packets"]
            or row["group_id"] != evidence["session_id"]
        ):
            raise ValueError("training label/features differ from independent reference")
        if len(Flow(packets=row["packets"]).packets) < 5:
            raise ValueError("short local flow")
    first_times = [f["connection_match"]["first_packet_unix_ms"] for f in evidence["flows"]]
    if spec and (
        min(first_times) <= datetime.fromisoformat(intent["recorded_before_capture_utc"]).timestamp() * 1000
        or evidence["artifact_id"] != intent["expected_artifact_id"]
        or evidence["counters"].get("selected_interface_id") != intent["selected_interface_id"]
    ):
        raise ValueError("new capture differs from its pre-capture intent")
    proof = {
        "summary_sha256": sha256(root / f"{trial}-collection-summary.json"),
        "rows_sha256": sha256(rows_path),
        "session_id": evidence["session_id"],
        "counts": dict(Counter(r["label"] for r in rows)),
        "first_packet_range_unix_ms": [min(first_times), max(first_times)],
    }
    if spec:
        from .browser_collection import observed_packet_bounds

        proof["observed_packet_range_unix_ms"] = observed_packet_bounds(evidence["flows"])
    return rows, proof


def load_trial(root, trial, labels):
    return load_reference_trial(root, trial, labels, "development")


def forest_weights(public_count, local_targets, local_fraction):
    counts = Counter(local_targets)
    if not public_count or not counts or not 0 < local_fraction < 1:
        raise ValueError("invalid domain-weight budget")
    return np.concatenate(
        [
            np.full(public_count, (1 - local_fraction) / public_count),
            np.asarray([local_fraction / (len(counts) * counts[label]) for label in local_targets]),
        ]
    )


def train_epoch(model, normalizer, public, py, local, ly, optimizer, rng, cfg):
    local_count = round(cfg["batch_size"] * cfg["local_fraction"])
    public_count = cfg["batch_size"] - local_count
    by_class = {label: np.flatnonzero(ly == label) for label in np.unique(ly)}
    model.train()
    losses = []
    for _ in range(cfg["steps_per_epoch"]):
        public_idx = rng.integers(len(public), size=public_count)
        local_idx = [int(rng.choice(by_class[label])) for label in rng.choice(list(by_class), local_count)]
        raw = [public[i] for i in public_idx] + [local[i] for i in local_idx]
        targets = np.concatenate([py[public_idx], ly[local_idx]])
        order = rng.permutation(len(raw))
        inputs = [raw[i][: int(rng.choice(BUDGETS))] for i in order]
        values, lengths = normalizer.batch(inputs)
        logits, _ = model(torch.from_numpy(values), torch.from_numpy(lengths))
        loss = torch.nn.functional.cross_entropy(logits, torch.from_numpy(targets[order]))
        if not torch.isfinite(loss):
            raise ValueError("nonfinite adaptation loss")
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    model.eval()
    return float(np.mean(losses))


def development(predictor, public, py, local, ly, local_rows):
    local_classes = sorted(set(ly.tolist()))
    report, predictions, local_scores, public_scores = {}, [], [], []
    recall = {label: [] for label in local_classes}
    for budget in BUDGETS:
        prob = np.concatenate(
            [
                predictor.probabilities([x[:budget] for x in public[i : i + 128]])
                for i in range(0, len(public), 128)
            ]
        )
        public_scores.append(
            float(
                f1_score(
                    py,
                    prob.argmax(1),
                    labels=list(range(len(predictor.labels))),
                    average="macro",
                    zero_division=0,
                )
            )
        )
        indices = [i for i, raw in enumerate(local) if len(raw) >= budget]
        prob = predictor.probabilities([local[i][:budget] for i in indices])
        truth, predicted = ly[indices], prob.argmax(1)
        score = float(f1_score(truth, predicted, labels=local_classes, average="macro", zero_division=0))
        local_scores.append(score)
        per_class = {}
        for label in local_classes:
            chosen = truth == label
            if not chosen.any():
                raise ValueError("missing local development class at a packet budget")
            value = float((predicted[chosen] == label).mean())
            recall[label].append(value)
            per_class[predictor.labels[label]] = {"n": int(chosen.sum()), "recall": value}
        report[str(budget)] = {
            "n": len(indices),
            "accuracy": float(accuracy_score(truth, predicted)),
            "observed_class_macro_f1": score,
            "classes": per_class,
            "public_clean_macro_f1": public_scores[-1],
        }
        for index, scores in zip(indices, prob):
            predictions.append(
                {
                    "id": local_rows[index]["id"],
                    "reference": local_rows[index]["label"],
                    "observed_packets": budget,
                    "top1": predictor.labels[int(scores.argmax())],
                    "probabilities": scores.tolist(),
                }
            )
    return {
        "budgets": report,
        "local_macro_f1": float(np.mean(local_scores)),
        "public_clean_macro_f1": float(np.mean(public_scores)),
        "local_recall": {predictor.labels[k]: float(np.mean(v)) for k, v in recall.items()},
    }, predictions


def passes_guard(candidate, baseline, cfg):
    return (
        candidate["local_macro_f1"] >= cfg.get("local_quality_floor", 0)
        and all(
            value >= cfg.get("local_class_recall_floor", 0) for value in candidate["local_recall"].values()
        )
        and candidate["local_macro_f1"] >= baseline["local_macro_f1"] + cfg["local_macro_f1_gain_minimum"]
        and candidate["public_clean_macro_f1"]
        >= baseline["public_clean_macro_f1"] - cfg["public_clean_loss_limit"]
        and all(
            candidate["local_recall"][label] >= value for label, value in baseline["local_recall"].items()
        )
    )


def load_role_trial(root, trial, split, labels, cfg, plan):
    if "followup_protocol" in plan:
        from .browser_followup import load_parent_trial

        path = Path(root) / cfg["reference_collection_plan_filename"]
        if trial in plan["followup_protocol"]["parent_evidence"]:
            return load_parent_trial(root, path, plan, trial, split, labels)
        from .browser_collection import trial_spec

        if trial_spec(plan, trial)["role"] != split:
            raise ValueError("follow-up selection role cannot be interchanged")
        return load_reference_trial(root, trial, labels, "development", path)
    if "-cal-" not in trial:
        if cfg.get("reference_collection_plan_filename"):
            from .browser_collection import bound_plan, trial_spec

            path, collection_plan, _ = bound_plan(root, cfg["reference_collection_plan_filename"])
            if trial in [r["id"] for r in collection_plan["trials"]]:
                if trial_spec(collection_plan, trial)["role"] != split:
                    raise ValueError("new collection role cannot be interchanged")
                return load_reference_trial(root, trial, labels, "development", path)
        return load_trial(root, trial, labels)
    if split != "selection":
        raise ValueError("retired calibration is selection-only in this forward study")
    retirement_path = Path(cfg["retirement_decision"])
    failure_path = Path(cfg["retired_calibration_report"])
    if sha256(retirement_path) != plan["retirement_decision_sha256"]:
        raise ValueError("retirement decision changed")
    retirement = json.loads(retirement_path.read_text())
    failure = json.loads(failure_path.read_text())
    if (
        trial not in retirement["retired_trials"]
        or failure["policy"]["fitted"]
        or sha256(failure_path) != retirement["calibration_report_sha256"]
    ):
        raise ValueError("only explicitly retired failed calibration may become development")
    return load_reference_trial(root, trial, labels, "calibration")


def benchmark_calls(predictor, raw, cfg):
    for _ in range(cfg["benchmark_warmup"]):
        predictor.predict(raw)
    samples = []
    for _ in range(cfg["benchmark_calls"]):
        start = time.perf_counter()
        predictor.predict(raw)
        samples.append(1000 * (time.perf_counter() - start))
    return {
        "n": len(samples),
        "p50_ms": float(np.percentile(samples, 50)),
        "p95_ms": float(np.percentile(samples, 95)),
        "boundary": "single-flow shared predict pipeline, 30-packet training sample; excludes HTTP/capture/UI",
    }


def run(data, collection, initial_bundle, config_path, destination):
    cfg = json.loads(Path(config_path).read_text())
    if not (
        1 <= cfg["epochs"] <= 5
        and 1 <= cfg["steps_per_epoch"] <= 50
        and cfg["batch_size"] == 64
        and 0 < cfg["local_fraction"] < 1
        and 1 <= cfg["threads"] <= 2
        and cfg["forest"]["n_estimators"] <= 32
    ):
        raise ValueError("adaptation exceeds fixed pilot resource budget")
    if not 0 < round(cfg["batch_size"] * cfg["local_fraction"]) < cfg["batch_size"]:
        raise ValueError("both training domains need batch support")
    root, out = Path(collection), Path(destination)
    if out.exists():
        raise FileExistsError(out)
    plan_name = cfg.get("split_plan_filename", "adaptation-collection-split-v1.json")
    if Path(plan_name).name != plan_name:
        raise ValueError("split plan must be a named collection file")
    plan_path = root / plan_name
    if cfg.get("followup_protocol_sha256"):
        from .browser_collection import read_collection_plan
        from .browser_followup import validate_run

        plan = read_collection_plan(plan_path)
        repeat_candidate = validate_run(plan_path, cfg, out)
    else:
        plan = json.loads(plan_path.read_text())
        repeat_candidate = None
    if cfg["train_trials"] != plan["train_trials"] or cfg["selection_trials"] != plan["selection_trials"]:
        raise ValueError("adaptation role assignments changed")
    torch.set_num_threads(cfg["threads"])
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(cfg["seed"])
    base = Predictor(initial_bundle)
    if base.meta["kind"] != "tcn":
        raise ValueError("pilot requires existing TCN reference")
    rows, evidence = {}, {}
    for split in ("train", "selection"):
        rows[split] = []
        for trial in cfg[f"{split}_trials"]:
            records, proof = load_role_trial(root, trial, split, base.labels, cfg, plan)
            if cfg.get("reference_collection_plan_filename"):
                proof["unscored_other_supported_counts"] = dict(
                    Counter(r["label"] for r in records if r["label"] not in cfg["local_labels"])
                )
                records = [r for r in records if r["label"] in cfg["local_labels"]]
            rows[split].extend(records)
            evidence[trial] = proof
        minimum = cfg[f"minimum_{split}_per_local_class"]
        if any(
            Counter(r["label"] for r in rows[split])[label]
            < (minimum[label] if isinstance(minimum, dict) else minimum)
            for label in cfg["local_labels"]
        ):
            raise ValueError("insufficient independently referenced local class support")
        if split == "selection" and cfg.get("minimum_selection_full_prefix_per_class"):
            if any(
                sum(r["label"] == label and len(r["packets"]) == 30 for r in rows[split]) < minimum
                for label, minimum in cfg["minimum_selection_full_prefix_per_class"].items()
            ):
                raise ValueError("insufficient complete selection prefixes for per-budget assessment")
    check_roles(rows["train"], rows["selection"])
    if "followup_protocol" in plan:
        from .browser_followup import stage_gate as followup_gate

        name = plan["trials"][0]["id"]
        state = followup_gate(root, plan_path, plan, name, evidence[name]["observed_packet_range_unix_ms"][0])
        if evidence[name]["session_id"] in state["sessions"]:
            raise ValueError("follow-up session reuses inherited evidence")
        validate_run(plan_path, cfg, out, evidence)
    elif cfg.get("reference_collection_plan_filename"):
        from .browser_collection import bound_plan, stage_gate

        collection_path, collection_plan, _ = bound_plan(root, cfg["reference_collection_plan_filename"])
        previous_end = None
        for spec in collection_plan["trials"]:
            proof = evidence[spec["id"]]
            first, last = proof.get("observed_packet_range_unix_ms", proof["first_packet_range_unix_ms"])
            stage_gate(root, collection_path, spec["id"], first)
            if previous_end is not None and first <= previous_end:
                raise ValueError("prospective collection order or timing changed")
            previous_end = last
    if max(
        evidence[k].get("observed_packet_range_unix_ms", evidence[k]["first_packet_range_unix_ms"])[1]
        for k in cfg["train_trials"]
    ) >= min(evidence[k]["first_packet_range_unix_ms"][0] for k in cfg["selection_trials"]):
        raise ValueError("browser train/selection chronology overlaps")
    public, py, _, manifest = read_split(data, "train")
    validation, vy, vids, _ = read_split(data, "selection")
    if manifest["labels"] != base.labels or base.meta["provenance"]["data_manifest_sha256"] != sha256(
        Path(data) / "manifest.json"
    ):
        raise ValueError("base model/public training manifest mismatch")
    counts, selected = Counter(), []
    for index, label in enumerate(vy):
        if counts[int(label)] < cfg["public_selection_per_class"]:
            selected.append(index)
            counts[int(label)] += 1
    validation, vy = [validation[i] for i in selected], vy[selected]
    if any(counts[label] != cfg["public_selection_per_class"] for label in range(len(base.labels))):
        raise ValueError("historical retention cohort lacks a class")
    local = {k: [Flow(packets=r["packets"]).array() for r in v] for k, v in rows.items()}
    ly = {k: np.asarray([base.labels.index(r["label"]) for r in v], dtype=np.int64) for k, v in rows.items()}
    out.mkdir(parents=True)
    write_json(
        out / "data-manifest.json",
        {
            "public_manifest_sha256": sha256(Path(data) / "manifest.json"),
            "browser_evidence": evidence,
            "train_trials": cfg["train_trials"],
            "selection_trials": cfg["selection_trials"],
            "split_plan_sha256": sha256(plan_path),
            "note": "Composite adaptation data identity includes explicit training and separate development selection. Any reused failed calibration has a bound retirement decision and cannot be independent calibration again. No fresh calibration/final data used.",
        },
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    provenance = {
        "fixture": False,
        "experimental": True,
        "config": cfg,
        "source_commit": commit,
        "seeds": {"torch": cfg["seed"], "sampling_prefix": cfg["seed"] + 7000, "forest": cfg["seed"]},
        "source_sha256": sha256(__file__),
        "base_artifact_id": base.identity,
        "data_manifest_sha256": sha256(out / "data-manifest.json"),
        "public_data_manifest_sha256": sha256(Path(data) / "manifest.json"),
        "browser_split_plan_sha256": sha256(plan_path),
        "retirement_decision_sha256": sha256(cfg["retirement_decision"])
        if cfg.get("retirement_decision")
        else None,
        "browser_evidence": evidence,
        "local_counts": {k: dict(Counter(r["label"] for r in v)) for k, v in rows.items()},
        "public_selection_ids": [vids[i] for i in selected],
        "normalizer_fit": "reuse base statistics fitted only on original CESNET22 training data",
        "license": "public CESNET components CC-BY-4.0; browser examples private local-use development",
        "note": "Historical public selection is a retention control, not a forward test after 2026 browser training. Local roles are explicit and whole-session. Retired failed calibration may become development selection only with a bound retirement decision. New models uncommitted pending fresh separate calibration; no deployment.",
    }
    write_json(out / "config.json", provenance)
    baseline, base_rows = development(
        base, validation, vy, local["selection"], ly["selection"], rows["selection"]
    )
    write_json(out / "baseline.json", baseline)
    write_json(out / "baseline-predictions.json", base_rows)
    guard_baseline = copy.deepcopy(baseline)
    if cfg.get("local_comparison_bundle"):
        reference = Predictor(cfg["local_comparison_bundle"])
        comparison, comparison_rows = development(
            reference, validation, vy, local["selection"], ly["selection"], rows["selection"]
        )
        write_json(out / "previous-candidate.json", {"artifact_id": reference.identity, **comparison})
        write_json(out / "previous-candidate-predictions.json", comparison_rows)
        # Local improvement is relative to the failed candidate. The historical
        # retention floor remains relative to the original neural reference.
        guard_baseline = {
            **baseline,
            "local_macro_f1": comparison["local_macro_f1"],
            "local_recall": comparison["local_recall"],
        }
    model = copy.deepcopy(base.model)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["learning_rate"])
    rng = np.random.default_rng(cfg["seed"] + 7000)
    reports, history = {}, []

    def record(name, fitted, epoch=None):
        bundle = export_bundle(
            out / name / "bundle",
            fitted,
            base.normalizer,
            base.labels,
            {**provenance, "candidate": name, "epoch": epoch},
            base.meta["architecture"] if epoch is not None else {},
            UNCOMMITTED,
        )
        predictor = Predictor(bundle)
        report, predictions = development(
            predictor, validation, vy, local["selection"], ly["selection"], rows["selection"]
        )
        report.update(
            artifact_id=predictor.identity,
            bundle=str(bundle),
            epoch=epoch,
            eligible_for_calibration=passes_guard(report, guard_baseline, cfg),
        )
        write_json(out / name / "development.json", report)
        write_json(out / name / "predictions.json", predictions)
        reports[name] = report
        print(
            json.dumps(
                {
                    "candidate": name,
                    "local_macro_f1": report["local_macro_f1"],
                    "public_clean_macro_f1": report["public_clean_macro_f1"],
                    "eligible_for_calibration": report["eligible_for_calibration"],
                }
            ),
            flush=True,
        )

    started = time.perf_counter()
    for epoch in range(1, cfg["epochs"] + 1):
        loss = train_epoch(
            model, base.normalizer, public, py, local["train"], ly["train"], optimizer, rng, cfg
        )
        record(f"tcn-epoch-{epoch}", model, epoch)
        history.append({"epoch": epoch, "loss": loss})
        torch.save(
            {
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "epoch": epoch,
                "config": cfg,
                "numpy_rng": rng.bit_generator.state,
                "torch_rng": torch.get_rng_state(),
            },
            out / "resume.pt",
        )
        write_json(out / "history.json", history)
    tcn_seconds = time.perf_counter() - started
    started = time.perf_counter()
    features = np.asarray([summary(x[:budget]) for x in public + local["train"] for budget in BUDGETS])
    targets = np.repeat(np.concatenate([py, ly["train"]]), len(BUDGETS))
    weights = forest_weights(
        len(public) * len(BUDGETS), np.repeat(ly["train"], len(BUDGETS)), cfg["local_fraction"]
    )
    forest = RandomForestClassifier(**cfg["forest"], random_state=cfg["seed"], n_jobs=cfg["threads"])
    forest.fit(features, targets, sample_weight=weights)
    record("forest", forest)
    forest_seconds = time.perf_counter() - started
    eligible = [name for name, value in reports.items() if value["eligible_for_calibration"]]
    for name in eligible:
        reports[name]["cpu_pipeline"] = benchmark_calls(
            Predictor(out / name / "bundle"), local["train"][0], cfg
        )
    chosen = max(eligible, key=lambda name: reports[name]["local_macro_f1"]) if eligible else None
    if (
        chosen
        and "forest" in eligible
        and reports["forest"]["local_macro_f1"] >= reports[chosen]["local_macro_f1"] - 0.01
    ):
        if reports["forest"]["cpu_pipeline"]["p50_ms"] <= reports[chosen]["cpu_pipeline"]["p50_ms"]:
            chosen = "forest"
    if repeat_candidate is not None:
        chosen = repeat_candidate if repeat_candidate in eligible else None
    write_json(
        out / "result.json",
        {
            "baseline": baseline,
            "guard_reference": guard_baseline,
            "candidates": reports,
            "candidate_for_separate_calibration": chosen,
            "default_promoted": False,
            "final_evaluation": False,
            "policy_fitted": False,
            "stage_seconds_including_development_export": {"tcn": tcn_seconds, "forest": forest_seconds},
            "local_training_flows": len(rows["train"]),
            "local_selection_flows": len(rows["selection"]),
            "note": "Development-only study. Explicitly retired failed calibration can serve as later development selection only when a bound retirement decision permits it; it can never again be calibration/final evidence. Whole-session grouping and small correlated samples preclude general local-accuracy claims. No fresh calibration/final data read, no capture or deployment.",
        },
    )
    return str(out)
