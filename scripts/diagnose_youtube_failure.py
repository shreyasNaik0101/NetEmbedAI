"""Bounded, post-hoc saved-packet diagnosis. No training or capture startup."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from check_browser_receive_parity import compare_socket_prefix, socket_datagrams
from netembed.bundle import Predictor, sha256, write_json
from netembed.connection_reference import connection_token, parse_endpoint
from netembed.contract import Flow, forest_features
from netembed.netlog_reference import _targets
from netembed.netlog_stream import read_quic_reference_stream
from netembed.paired_study import read_archive


def guard(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve().as_posix().lower()
        if "/data/processed/" in path or "-eval-" in path or path.endswith("/test.jsonl"):
            raise ValueError("public data and final records excluded from post-hoc diagnosis")
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise ValueError("diagnosis is offline")


def replace_exact_size(raw, before, after):
    """Abstract size sensitivity: leave all timings, directions and other sizes intact."""
    changed = raw.copy()
    mask = changed[:, 2] == before
    changed[mask, 2] = after
    assert np.array_equal(raw[:, :2], changed[:, :2])
    return changed, int(mask.sum())


def socket_families(netlog, salt):
    """Family only, matched by the reference token. Never passed to a predictor."""
    types = netlog["constants"]["logEventTypes"]
    source_type = netlog["constants"]["logSourceType"]["UDP_SOCKET"]
    begin = netlog["constants"]["logEventPhase"]["PHASE_BEGIN"]
    grouped = defaultdict(list)
    for event in netlog["events"]:
        if event.get("source", {}).get("type") == source_type:
            grouped[event["source"]["id"]].append(event)
    result = defaultdict(set)
    for events in grouped.values():
        local = {
            parse_endpoint(e["params"]["address"]) for e in events if e["type"] == types["UDP_LOCAL_ADDRESS"]
        }
        peers = {
            parse_endpoint(e["params"]["address"])
            for e in events
            if e["type"] == types["UDP_CONNECT"] and e["phase"] == begin
        }
        for first in local:
            for second in peers:
                result[connection_token(first, second, salt)].add(
                    (ipaddress.ip_address(first[0]).version, ipaddress.ip_address(second[0]).version)
                )
    return result


def packet_summary(raw):
    sizes = raw[:, 2]
    reverse = np.flatnonzero(raw[:, 1] == -1)
    return {
        "packets": len(raw),
        "first_payload": int(sizes[0]),
        "maximum_payload": int(sizes.max()),
        "payload_counts": dict(Counter(str(int(x)) for x in sizes)),
        "client_packets": int((raw[:, 1] == 1).sum()),
        "server_packets": int((raw[:, 1] == -1).sum()),
        "elapsed_ms": float(raw[:, 0].sum()),
        "first_server_delay_ms": float(raw[: reverse[0] + 1, 0].sum()) if len(reverse) else None,
        "submillisecond_gaps": int((raw[1:, 0] < 1).sum()),
        "first_ten_direction_size": raw[:10, 1:].astype(int).tolist(),
    }


def feature_names():
    result = ["prefix_length"]
    for group in ("all", "client", "server"):
        result.append(group + ".count")
        for channel in ("iat_ms", "payload_bytes"):
            result.extend(f"{group}.{channel}.{stat}" for stat in ("sum", "mean", "std", "min", "max"))
    return result


def changed_routes(model, original, changed):
    before = forest_features(original, model.normalizer, model.forest_feature_map)
    after = forest_features(changed, model.normalizer, model.forest_feature_map)
    names = feature_names()
    divergence = Counter()
    leaves_changed = 0
    for tree in model.trees:

        def walk(features):
            node, path = 0, []
            for _ in range(len(tree["left"])):
                path.append(node)
                if tree["left"][node] == -1:
                    return node, path
                node = int(
                    tree["left"][node]
                    if features[tree["feature"][node]] <= tree["threshold"][node]
                    else tree["right"][node]
                )
            raise ValueError("invalid tree")

        first_leaf, first_path = walk(before)
        second_leaf, second_path = walk(after)
        leaves_changed += first_leaf != second_leaf
        for index, (first, second) in enumerate(zip(first_path, second_path)):
            if first != second:
                parent = first_path[index - 1]
                feature = int(tree["feature"][parent])
                divergence[
                    (
                        names[feature],
                        float(tree["threshold"][parent]),
                        float(before[feature]),
                        float(after[feature]),
                    )
                ] += 1
                break
    return {
        "trees_reaching_different_leaf": leaves_changed,
        "first_divergent_splits": [
            {"feature": key[0], "threshold": key[1], "before": key[2], "after": key[3], "trees": count}
            for key, count in sorted(divergence.items())
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/youtube-failure-diagnostic-v1.json")
    parser.add_argument("--output", default="experiments/youtube-failure-diagnostic-v1")
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError("preserve existing diagnostic output; choose a new output directory")
    cfg = json.loads(Path(args.config).read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    sys.addaudithook(guard)
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        model = Predictor(cfg["candidate_bundle"])
        assert model.identity == cfg["candidate_id"] and model.forest_feature_map == "summary-v1"
        assert not model.meta["policy"]["fitted"]
        evidence, records, cohorts, maximum = {}, [], {}, 0.0
        for spec in cfg["cohorts"]:
            root, trial = Path(spec["root"]), spec["trial"]
            archive = read_archive(root, trial)
            assert archive["status"] == "usable"
            evidence[str(root / (trial + "-archive.json"))] = sha256(root / (trial + "-archive.json"))
            capture = json.loads((root / (trial + "-capture.json")).read_text())
            reference = json.loads((root / (trial + "-reference.json")).read_text())
            rows = json.loads((root / (trial + "-rows.json")).read_text())
            parity = json.loads((root / (trial + "-socket-parity.json")).read_text())
            predictions_path = root / spec["saved_predictions"]
            saved = json.loads(predictions_path.read_text())
            evidence[str(predictions_path)] = sha256(predictions_path)
            selected = [r for r in rows if r["label"] == "youtube"]
            assert not capture["fixture"] and not reference["fixture"]
            assert capture["adapter_version"] == "tshark-prefix-ns-v3" and not capture["counters"]["running"]
            netlog, netlog_sha, reader = read_quic_reference_stream(
                root / (trial + "-netlog.json"), include_sockets=True
            )
            assert netlog_sha == reference["netlog_sha256"]
            salt, targets = _targets(capture)
            families = socket_families(netlog, salt)
            details = []
            for row in selected:
                ident = row["id"].split(":")[-1]
                index = next(i for i, f in enumerate(capture["flows"]) if f["flow_id"] == ident)
                target = targets[index]
                assert capture["flows"][index]["packets"] == row["packets"]
                ref = next(r for r in reference["flows"] if r["flow_id"] == ident)
                assert ref["reference"]["label"] == "youtube" and ref["packets"] == row["packets"]
                status, datagrams = socket_datagrams(netlog, salt, target)
                assert status["status"] == "unique_socket" and len(datagrams) >= len(row["packets"])
                quality = compare_socket_prefix(row["packets"], target["first"], datagrams)
                archived_quality = next(p for p in parity["flows"] if p["flow_id"] == ident)
                assert all(archived_quality[k] == v for k, v in quality.items())
                assert all(p["ordered_payload_sizes_equal"] for p in quality["by_direction"].values())
                raw = Flow(packets=row["packets"]).array()
                datagrams = datagrams[: len(raw)]
                socket = Flow.from_array(
                    np.array(
                        [
                            [time - datagrams[i - 1][0] if i else 0, direction, size]
                            for i, (time, _, direction, size) in enumerate(datagrams)
                        ]
                    )
                ).array()
                family = sorted(families[target["token"]])
                assert len(family) == 1
                details.append(
                    {
                        "id": row["id"],
                        "ip_families": family[0],
                        "capture": packet_summary(raw),
                        "socket": packet_summary(socket),
                        "merged_direction_mismatch_indices": quality["merged_direction_mismatch_indices"],
                        "merged_size_mismatch_indices": quality["merged_payload_size_mismatch_indices"],
                        "max_clock_difference_by_direction_ms": {
                            d: q["maximum_absolute_timestamp_difference_ms"]
                            for d, q in quality["by_direction"].items()
                        },
                    }
                )
                for budget in cfg["budgets"]:
                    if len(raw) < budget:
                        continue
                    observed = raw[:budget]
                    variants = {"capture": observed, "recorded_browser_socket": socket[:budget]}
                    modifications = {}
                    for change in cfg["abstract_sensitivities"]:
                        altered, count = replace_exact_size(
                            observed, change["from_bytes"], change["to_bytes"]
                        )
                        variants[change["name"]] = altered
                        modifications[change["name"]] = {
                            "changed_packets": count,
                            **changed_routes(model, observed, altered),
                        }
                    scored = {}
                    for name, values in variants.items():
                        p = model.probabilities([values])[0]
                        scored[name] = {
                            "top1": model.labels[int(p.argmax())],
                            "score": float(p.max()),
                            "probabilities": p.tolist(),
                        }
                    old = next(r for r in saved if r["id"] == row["id"] and r["budget"] == budget)
                    expected = (
                        old["forest"]["probabilities"]
                        if spec["prediction_format"] == "paired"
                        else old["probabilities"]
                    )
                    maximum = max(
                        maximum,
                        float(np.max(np.abs(np.array(expected) - scored["capture"]["probabilities"]))),
                    )
                    records.append(
                        {
                            "trial": trial,
                            "id": row["id"],
                            "reference": "youtube",
                            "budget": budget,
                            "variants": scored,
                            "abstract_size_changes": modifications,
                        }
                    )
            cohorts[trial] = {
                "connections": len(selected),
                "capture_counters": capture["counters"],
                "netlog_reader": reader,
                "flows": details,
                "browser_version": netlog["constants"].get("clientInfo", {}).get("version"),
            }
        assert maximum == 0.0
        inventory = defaultdict(Counter)
        for trial in model.meta["provenance"]["config"]["train_trials"]:
            path = Path("artifacts/local/browser-development") / (trial + "-development-rows.jsonl")
            digest = sha256(path)
            assert digest == model.meta["provenance"]["browser_evidence"][trial]["rows_sha256"]
            evidence[str(path)] = digest
            for row in (json.loads(line) for line in path.read_text().splitlines()):
                inventory[row["label"]][str(row["packets"][0]["payload_bytes"])] += 1
        metrics = {}
        for trial in cohorts:
            metrics[trial] = {}
            for budget in cfg["budgets"]:
                cases = [r for r in records if r["trial"] == trial and r["budget"] == budget]
                metrics[trial][str(budget)] = {
                    name: {
                        "n": len(cases),
                        "correct": sum(r["variants"][name]["top1"] == "youtube" for r in cases),
                        "top1_counts": dict(Counter(r["variants"][name]["top1"] for r in cases)),
                    }
                    for name in records[0]["variants"]
                }
        report = {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit": commit,
            "source_sha256": sha256(__file__),
            "config_sha256": sha256(args.config),
            "config": cfg,
            "candidate_id": model.identity,
            "evidence_sha256": evidence,
            "capture_vectors_replayed": len(records),
            "maximum_probability_difference": maximum,
            "training_first_payload_inventory": dict(inventory),
            "cohorts": cohorts,
            "metrics": metrics,
            "fixture": False,
            "fitting_run": False,
            "default_promoted": False,
            "note": cfg["limits"],
        }
        output.mkdir(parents=True, exist_ok=False)
        write_json(output / "report.json", report)
        write_json(output / "predictions.json", records)
        write_json(
            output / "checksums.json",
            {name: sha256(output / name) for name in ("report.json", "predictions.json")},
        )
        print(
            json.dumps(
                {
                    "metrics": metrics,
                    "training_first_payload_inventory": dict(inventory),
                    "replayed": len(records),
                    "maximum_difference": maximum,
                    "output": str(output),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
