"""Existing-log observer-specific window diagnostic. No capture or live promotion."""

import argparse
import importlib.util
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score
from threadpoolctl import threadpool_limits

from netembed.browser_adaptation import check_roles, load_role_trial
from netembed.bundle import Predictor, export_bundle, sha256, write_json
from netembed.contract import Flow, Normalizer, summary
from netembed.netlog_reference import _sessions, _targets, finite
from netembed.netlog_stream import read_quic_reference_stream
from netembed.packet_study import protected_input
from netembed.window_features import VERSION, WindowForest, browser_windows, features


def guard(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = str(args[0]).replace("\\", "/").lower()
        if protected_input(path) or "/window-validation/" in path:
            raise ValueError("protected or unscored data excluded from window study")


def extract(root, cfg, labels, parity):
    role_cfg = json.loads(Path(cfg["reference_config"]).read_text())
    plan_path = root / role_cfg["split_plan_filename"]
    plan = json.loads(plan_path.read_text())
    output, proofs, inventory = {"train": [], "selection": []}, {}, []
    for role in output:
        for trial in role_cfg[role + "_trials"]:
            rows, proof = load_role_trial(root, trial, role, labels, role_cfg, plan)
            proofs[trial] = proof
            cap_path, log_path = root / f"{trial}-capture.json", root / f"{trial}-netlog.json"
            cap = json.loads(cap_path.read_text())
            log, digest, reader = read_quic_reference_stream(log_path, include_sockets=True)
            reference = json.loads((root / f"{trial}-reference.json").read_text())
            if digest != reference["netlog_sha256"]:
                raise ValueError("browser log binding changed")
            salt, targets = _targets(cap)
            sessions, skipped = _sessions(log, salt, targets)
            offset = finite(log["constants"]["timeTickOffset"])
            coverage_end = max(offset + finite(event["time"]) for event in log["events"])
            originals = {f["flow_id"]: (i, f) for i, f in enumerate(cap["flows"])}
            excluded, retained = [], 0
            for row in rows:
                index, original = originals[row["id"].rsplit(":", 1)[-1]]
                target = targets[index]
                qc, records = parity.socket_datagrams(log, salt, target)
                reason = qc["status"] if qc["status"] != "unique_socket" else None
                if not reason and not records:
                    reason = "no_socket_datagrams"
                if not reason and abs(records[0][0] - target["first"]) > 100:
                    reason = "first_transfer_anchor_outside_100ms"
                if not reason and coverage_end < records[0][0] + 3000:
                    reason = "incomplete_three_second_log_coverage"
                active = [
                    s
                    for s in sessions.values()
                    if s["tuple_token"] == target["token"]
                    and target["first"] - 2000 <= s["begin"] <= target["first"] + 3000
                ]
                if not reason and (len(active) != 1 or active[0]["invalid"] or active[0]["overflow"]):
                    reason = "nonunique_or_invalid_quic_session_in_window"
                if not reason and (
                    active[0]["reference"]["status"] != "mapped"
                    or active[0]["reference"]["label"] != row["label"]
                ):
                    reason = "session_reference_disagrees"
                windows = browser_windows(records) if not reason else None
                if windows and sum(windows[3000][k] for k in ("client_packets", "server_packets")) < 5:
                    reason = "fewer_than_five_datagrams_in_three_seconds"
                if reason:
                    excluded.append({"id": row["id"], "reason": reason})
                    continue
                first = records[0][0]
                elapsed = first
                prefix = []
                for timestamp, _, direction, size in records[:30]:
                    prefix.append(
                        {"iat_ms": timestamp - elapsed, "direction": direction, "payload_bytes": size}
                    )
                    elapsed = timestamp
                Flow(packets=prefix)
                output[role].append(
                    {
                        "id": row["id"],
                        "group_id": row["group_id"],
                        "trial": trial,
                        "label": row["label"],
                        "observer": cfg["observer"],
                        "windows": {str(k): v for k, v in windows.items()},
                        "capture_prefix": original["packets"],
                        "browser_prefix": prefix,
                        "browser_minus_capture_start_ms": first - target["first"],
                    }
                )
                retained += 1
            inventory.append(
                {
                    "trial": trial,
                    "role": role,
                    "original_eligible": len(rows),
                    "retained": retained,
                    "excluded": excluded,
                    "reader": reader,
                    "skipped_reference_events": skipped,
                    "netlog_sha256": digest,
                }
            )
            print(
                json.dumps({"stage": "extract", "trial": trial, "retained": retained, "excluded": excluded}),
                flush=True,
            )
    check_roles(output["train"], output["selection"])
    if max(proofs[k]["first_packet_range_unix_ms"][1] for k in role_cfg["train_trials"]) >= min(
        proofs[k]["first_packet_range_unix_ms"][0] for k in role_cfg["selection_trials"]
    ):
        raise ValueError("window train/selection chronology overlaps")
    return output, proofs, inventory


def metric(truth, probabilities, labels):
    predicted = np.asarray(probabilities).argmax(1)
    return {
        "n": len(truth),
        "correct": int((predicted == truth).sum()),
        "macro_f1": float(f1_score(truth, predicted, labels=list(range(len(labels))), average="macro")),
        "recall": {label: float((predicted[truth == i] == i).mean()) for i, label in enumerate(labels)},
        "confusion": confusion_matrix(truth, predicted, labels=list(range(len(labels)))).tolist(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/browser-window-study.json")
    parser.add_argument("--collection", default="artifacts/local/browser-development")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sys.addaudithook(guard)
    cfg = json.loads(Path(args.config).read_text())
    if cfg["feature_version"] != VERSION or cfg["horizons_ms"] != [1000, 3000]:
        raise ValueError("window study contract differs")
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(out)
    source = Path(__file__).resolve().parent / "check_browser_receive_parity.py"
    spec = importlib.util.spec_from_file_location("socket_reference_support", source)
    parity = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parity)
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        rows, proofs, inventory = extract(Path(args.collection), cfg, cfg["labels"], parity)
        out.mkdir(parents=True)
        provenance = {
            "fixture": False,
            "study": cfg,
            "config_sha256": sha256(args.config),
            "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "source_sha256": {
                str(p): sha256(p) for p in (Path(__file__), Path("src/netembed/window_features.py"), source)
            },
            "versions": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "scikit_learn": sklearn.__version__,
            },
            "browser_evidence": proofs,
            "inventory": inventory,
            "observer": cfg["observer"],
            "new_capture": False,
            "protected_calibration_final_and_unscored_trials_used": False,
        }
        write_json(out / "protocol.json", provenance)
        for role, values in rows.items():
            write_json(out / f"{role}-records.json", values)
            counts = Counter(r["label"] for r in values)
            minimum = cfg[f"minimum_{role}_per_class"]
            if any(counts[label] < minimum for label in cfg["labels"]):
                write_json(
                    out / "report.json",
                    {
                        "stage": "insufficient_support",
                        "role": role,
                        "counts": dict(counts),
                        "models_fit": False,
                    },
                )
                return
        run_models(cfg, rows, provenance, out)


def run_models(cfg, rows, provenance, out):
    labels = cfg["labels"]
    y = {role: np.array([labels.index(r["label"]) for r in values]) for role, values in rows.items()}
    report = {
        "cohort": {role: dict(Counter(r["label"] for r in values)) for role, values in rows.items()},
        "models": {},
        "majority": {},
        "provenance": provenance,
        "default_promoted": False,
        "policy_fitted": False,
        "live_capture_accuracy": None,
    }
    majority = int(np.argmax(np.bincount(y["train"], minlength=len(labels))))
    for role in rows:
        prob = np.zeros((len(rows[role]), len(labels)))
        prob[:, majority] = 1
        report["majority"][role] = metric(y[role], prob, labels)
    for name in ("browser_prefix", "capture_prefix", "window1000", "window3000"):
        horizon = int(name.removeprefix("window")) if name.startswith("window") else None
        x = {
            role: np.array(
                [
                    features(r["windows"][str(horizon)])
                    if horizon
                    else summary(Flow(packets=r[name]).array())
                    for r in values
                ]
            )
            for role, values in rows.items()
        }
        forest = RandomForestClassifier(**cfg["forest"]).fit(x["train"], y["train"])
        native = {role: forest.predict_proba(values) for role, values in x.items()}
        if horizon:
            model = WindowForest.from_fitted(forest, labels, horizon, provenance)
            model.save(out / name)
            loaded = WindowForest.load(out / name)

            def predict(r):
                return loaded.predict(r["windows"][str(horizon)], cfg["observer"])
        else:
            train_flows = [Flow(packets=r[name]).array() for r in rows["train"]]
            path = export_bundle(
                out / name,
                forest,
                Normalizer.fit(train_flows),
                labels,
                {**provenance, "observation_source": name},
            )
            loaded = Predictor(path)

            def predict(r):
                return loaded.predict(Flow(packets=r[name]).array())

        probabilities, records, maximum = {}, {}, 0
        for role, values in rows.items():
            replies = [predict(row) for row in values]
            probabilities[role] = np.array(
                [
                    [a["score"] for label in labels for a in reply["alternatives"] if a["label"] == label]
                    for reply in replies
                ]
            )
            delta = float(np.max(np.abs(probabilities[role] - native[role])))
            maximum = max(maximum, delta)
            if delta > 1e-7:
                raise ValueError("exported model probabilities differ")
            records[role] = [
                {
                    "id": row["id"],
                    "group_id": row["group_id"],
                    "reference": row["label"],
                    "raw_top1": labels[int(prob.argmax())],
                    "probabilities": prob.tolist(),
                }
                for row, prob in zip(values, probabilities[role])
            ]
            write_json(out / f"{name}-{role}-predictions.json", records[role])
        measured = {}
        for _ in range(cfg["benchmark_warmup"]):
            predict(rows["selection"][0])
        times = []
        for _ in range(cfg["benchmark_calls"]):
            start = time.perf_counter()
            predict(rows["selection"][0])
            times.append((time.perf_counter() - start) * 1000)
        measured = {
            "calls": len(times),
            "p50_ms": float(np.percentile(times, 50)),
            "p95_ms": float(np.percentile(times, 95)),
        }
        report["models"][name] = {role: metric(y[role], p, labels) for role, p in probabilities.items()}
        report["models"][name].update(export_maximum_probability_delta=maximum, cpu=measured)
        print(json.dumps({"stage": name, "metrics": report["models"][name]}), flush=True)
    control = report["models"]["browser_prefix"]["selection"]
    for name in ("window1000", "window3000"):
        candidate = report["models"][name]["selection"]
        report["models"][name]["development_gate"] = {
            "f1_gain": candidate["macro_f1"]
            >= control["macro_f1"] + cfg["decision"]["minimum_f1_gain_over_matched_prefix"],
            "recall_nonregression": all(
                candidate["recall"][label] >= control["recall"][label] for label in labels
            ),
        }
    report["limits"] = (
        "Reused two-service local development only; few correlated visits, not independent accuracy. "
        "Browser-side datagrams/clock, not wire capture; window model refuses implicit observer transfer. "
        "Prefix and temporal windows have different observation durations; no isolated causal feature claim. "
        "No all10-service evidence, activity labels, calibration, unknown detection or live promotion."
    )
    report["prediction_sha256"] = {p.name: sha256(p) for p in out.glob("*-predictions.json")}
    write_json(out / "report.json", report)
    print(json.dumps({"stage": "complete", "report": str(out / "report.json")}), flush=True)


if __name__ == "__main__":
    main()
