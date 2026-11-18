"""Family coverage contracts; family is evaluation metadata, never a model input."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path

from .bundle import Predictor, sha256
from .connection_reference import connection_token, parse_endpoint
from .netlog_reference import _targets


def families_for_rows(capture, netlog, rows):
    salt, targets = _targets(capture)
    types = netlog["constants"]["logEventTypes"]
    socket_type = netlog["constants"]["logSourceType"]["UDP_SOCKET"]
    begin = netlog["constants"]["logEventPhase"]["PHASE_BEGIN"]
    sockets, families = defaultdict(list), defaultdict(set)
    for event in netlog["events"]:
        if event.get("source", {}).get("type") == socket_type:
            sockets[event["source"]["id"]].append(event)
    for events in sockets.values():
        local = {
            parse_endpoint(e["params"]["address"]) for e in events if e["type"] == types["UDP_LOCAL_ADDRESS"]
        }
        remote = {
            parse_endpoint(e["params"]["address"])
            for e in events
            if e["type"] == types["UDP_CONNECT"] and e["phase"] == begin
        }
        for a in local:
            for b in remote:
                families[connection_token(a, b, salt)].add(
                    (ipaddress.ip_address(a[0]).version, ipaddress.ip_address(b[0]).version)
                )
    target_by_id = {f["flow_id"]: targets[i] for i, f in enumerate(capture["flows"])}
    result = []
    for row in rows:
        pair = families[target_by_id[row["id"].split(":")[-1]]["token"]]
        if len(pair) != 1:
            raise ValueError("family coverage unavailable or ambiguous for retained flow")
        local, remote = next(iter(pair))
        if local != remote:
            raise ValueError("mixed endpoint family unsupported")
        result.append(
            {"id": row["id"], "label": row["label"], "family": local, "packets": len(row["packets"])}
        )
    return result


def require_coverage(rows, spec, cfg):
    validate_rows(rows)
    eligible = [
        r for r in rows if r["label"] == spec["target"] and (spec["role"] != "train" or r["family"] == 6)
    ]
    requirements = ((30, 1),) if cfg.get("scope") == "session_acquisition_only" else ((10, 3), (30, 1))
    for budget, minimum in requirements:
        count = sum(r["packets"] >= budget for r in eligible)
        if count < minimum:
            raise ValueError(
                f"family coverage shortfall: {spec['target']} {spec['role']} at{budget}: {count}/{minimum}; stop, no replacement recording"
            )
    return dict(Counter(f"{r['label']}:IPv{r['family']}" for r in rows))


def require_cells(rows, cfg):
    validate_rows(rows)
    for label in cfg["local_labels"]:
        for family in (4, 6):
            for budget, minimum in ((10, 3), (30, 1)):
                count = sum(
                    r["label"] == label and r["family"] == family and r["packets"] >= budget for r in rows
                )
                if count < minimum:
                    raise ValueError(
                        f"selection cell shortfall: {label}/IPv{family} at{budget}: {count}/{minimum}; stop"
                    )


def validate_rows(rows):
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("duplicate family flow cannot count as independent support")
    if any(r["family"] not in (4, 6) or not 1 <= r["packets"] <= 30 for r in rows):
        raise ValueError("invalid family or prefix length")


def freeze_training(root, cfg, plan_path):
    if cfg.get("scope") in ("feasibility_only", "session_acquisition_only"):
        raise ValueError("feasibility scope cannot freeze training or enable model selection")
    from .paired_study import check_order, read_archive
    from .bundle import write_json

    root = Path(root)
    archives, previous = {}, []
    for spec in cfg["trials"][:4]:
        report = read_archive(root, spec["id"])
        if (
            report["status"] != "usable"
            or report["collection_role"] != "train"
            or report["plan_sha256"] != sha256(plan_path)
        ):
            raise ValueError("all four declared training archives required")
        check_order(cfg, spec["id"], previous, report["first_packet_ms"], report["session_id"])
        previous.append(report)
        families_path = root / (spec["id"] + "-families.json")
        if families_path.name not in report["files"]:
            raise ValueError("training archive lacks bound family metadata")
        require_coverage(json.loads(families_path.read_text()), spec, cfg)
        archives[spec["id"]] = sha256(root / (spec["id"] + "-archive.json"))
    path = root / "training-freeze.json"
    value = {"plan_sha256": sha256(plan_path), "archives": archives, "recipe": cfg["training_recipe"]}
    if path.exists():
        existing = json.loads(path.read_text())
        if any(existing[k] != v for k, v in value.items()):
            raise ValueError("training changed after freeze")
        return existing
    value["frozen_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(path, value)
    return value


def selection_ready(root, cfg, plan_path):
    freeze_training(root, cfg, plan_path)
    path = Path(root) / "trained-seed17.json"
    if not path.exists():
        raise ValueError(
            "selection blocked: frozen training needs a bound seed17 fit before any selection capture"
        )
    fitted = json.loads(path.read_text())
    if not Path(fitted["bundle"]).resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("trained bundle must be inside this study root")
    digest = sha256(Path(root) / "training-freeze.json")
    model = Predictor(fitted["bundle"])
    if (
        fitted["training_freeze_sha256"] != digest
        or model.identity != fitted["artifact_id"]
        or model.meta["policy"]["fitted"]
        or model.meta["kind"] != "forest"
        or model.meta["architecture"].get("feature_map", "summary-v1") != "summary-v1"
        or model.meta["provenance"].get("forest_seed") != 17
        or model.meta["provenance"].get("family_training_freeze_sha256") != digest
    ):
        raise ValueError("training/model binding changed")
