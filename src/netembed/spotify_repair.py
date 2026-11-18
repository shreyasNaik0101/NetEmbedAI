"""Role-bound six-visit Spotify data repair. Never starts capture."""

from datetime import datetime
import json
from pathlib import Path

from .bundle import Predictor, sha256, write_json
from .contract import Flow
from .paired_study import SPOTIFY_REPAIR_SHA, local_date, read_archive, validate_archive_plan


def check_schedule(cfg, trial, previous, now_ms, session=None):
    index = next((i for i, s in enumerate(cfg["trials"]) if s["id"] == trial), None)
    if index is None or len(previous) != index:
        raise ValueError("archive exactly the declared preceding slots first")
    if now_ms <= datetime.fromisoformat(cfg["declared_utc"]).timestamp() * 1000:
        raise ValueError("capture predates declaration")
    for spec, report in zip(cfg["trials"], previous):
        if report["trial_id"] != spec["id"] or report["status"] != "usable":
            raise ValueError("prior unusable slot stops scope; no replacements")
        if session is not None and session == report["session_id"]:
            raise ValueError("session reused across roles")
        if now_ms <= report["last_packet_ms"]:
            raise ValueError("overlapping or out-of-order sessions")
    required = cfg["trials"][index].get("later_date_than", [])
    for name in required:
        earlier = next(r for r in previous if r["trial_id"] == name)
        if local_date(now_ms, cfg) <= local_date(earlier["first_packet_ms"], cfg):
            raise ValueError("this slot requires a later local calendar date")


def bound_archives(root, cfg, roles, verify_files=True):
    result = {}
    for spec in cfg["trials"]:
        if spec["role"] not in roles:
            continue
        report = (
            read_archive(root, spec["id"])
            if verify_files
            else json.loads((Path(root) / (spec["id"] + "-archive.json")).read_text())
        )
        validate_archive_plan(root, spec["id"], report, cfg)
        if report["status"] != "usable" or report["collection_role"] != spec["role"]:
            raise ValueError("usable role-bound archives required")
        previous = []
        for earlier in cfg["trials"][: cfg["trials"].index(spec)]:
            prior = json.loads((Path(root) / (earlier["id"] + "-archive.json")).read_text())
            validate_archive_plan(root, earlier["id"], prior, cfg)
            if prior["collection_role"] != earlier["role"]:
                raise ValueError("prior archive role changed")
            previous.append(prior)
        check_schedule(cfg, spec["id"], previous, report["first_packet_ms"], report["session_id"])
        result[spec["id"]] = sha256(Path(root) / (spec["id"] + "-archive.json"))
    return result


def role_rows(root, cfg, role):
    rows = []
    sessions = set()
    bindings = bound_archives(root, cfg, [role])
    for spec in cfg["trials"]:
        if spec["role"] != role:
            continue
        report = read_archive(root, spec["id"])
        if report["session_id"] in sessions:
            raise ValueError("duplicate acquisition session")
        sessions.add(report["session_id"])
        cap = json.loads((Path(root) / (spec["id"] + "-capture.json")).read_text())
        if cap["fixture"] or cap["source"] != "user_started_capture":
            raise ValueError("real user capture required")
        for row in json.loads((Path(root) / (spec["id"] + "-rows.json")).read_text()):
            if row["label"] != "spotify":
                continue
            if not row["id"].startswith("browser:" + report["session_id"] + ":"):
                raise ValueError("row session differs")
            Flow(packets=row["packets"])
            rows.append({**row, "group_id": report["session_id"], "trial_id": spec["id"]})
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("duplicate flow IDs")
    return rows, bindings


def stage_receipt(root, cfg, stage):
    path = Path(root) / (stage + "-stage.json")
    if not path.exists():
        raise ValueError("awaiting " + stage + " stage; do not record this role yet")
    receipt = json.loads(path.read_text())
    if receipt["plan_sha256"] != SPOTIFY_REPAIR_SHA or receipt["stage"] != stage or receipt["fixture"]:
        raise ValueError("stage declaration/identity differs")
    if receipt["status"] != "passed":
        raise ValueError(stage + " failed; scope stopped")
    if not receipt.get("gates") or not all(receipt["gates"].values()):
        raise ValueError("stage gates did not pass")
    roles = {
        "training": ["train"],
        "development": ["train", "selection"],
        "calibration": ["train", "selection", "calibration"],
    }[stage]
    if receipt["archives"] != bound_archives(root, cfg, roles, False):
        raise ValueError("stage archive bindings differ")
    for filename, digest in receipt["files"].items():
        p = Path(filename).resolve()
        if not p.is_relative_to(Path("experiments/spotify-data-repair-v1").resolve()) or sha256(p) != digest:
            raise ValueError("stage output changed or outside declared output root")
    if stage != "training":
        prior = "training" if stage == "development" else "development"
        stage_receipt(root, cfg, prior)
        if receipt["prior_stage_sha256"] != sha256(Path(root) / (prior + "-stage.json")):
            raise ValueError("prior stage changed")
    return receipt


def source_for(root, cfg, trial, now_ms):
    spec = next(s for s in cfg["trials"] if s["id"] == trial)
    source = dict(cfg)
    if spec.get("requires_stage"):
        stage = stage_receipt(root, cfg, spec["requires_stage"])
        if now_ms <= datetime.fromisoformat(stage["created_utc"]).timestamp() * 1000:
            raise ValueError("stage freeze must precede preparation")
        if spec["role"] in ("calibration", "evaluation"):
            model = Predictor(stage["candidate"]["bundle"])
            if model.identity != stage["candidate"]["artifact_id"] or model.meta["provenance"].get(
                "fixture", True
            ):
                raise ValueError("bound candidate differs")
            if model.meta["provenance"].get("study_plan_sha256") != SPOTIFY_REPAIR_SHA:
                raise ValueError("candidate belongs to another study")
            if bool(model.meta["policy"]["fitted"]) != (spec["role"] == "evaluation"):
                raise ValueError("capture source policy stage differs")
            if (
                sha256(Path(stage["candidate"]["bundle"]) / "forest.json")
                != stage["candidate"]["weight_sha256"]
            ):
                raise ValueError("candidate weights changed")
            source.update(source_bundle=stage["candidate"]["bundle"], source_artifact_id=model.identity)
    source["require_zero_drops"] = spec["role"] == "evaluation"
    return source


def write_stage(root, cfg, stage, status, gates, candidate, files):
    from datetime import timezone

    path = Path(root) / (stage + "-stage.json")
    if path.exists():
        raise FileExistsError("preserve existing stage decision")
    roles = {
        "training": ["train"],
        "development": ["train", "selection"],
        "calibration": ["train", "selection", "calibration"],
    }[stage]
    prior = "training" if stage == "development" else "development" if stage == "calibration" else None
    receipt = {
        "fixture": False,
        "stage": stage,
        "status": status,
        "gates": gates,
        "candidate": candidate,
        "plan_sha256": SPOTIFY_REPAIR_SHA,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "archives": bound_archives(root, cfg, roles, False),
        "files": {str(Path(p)): sha256(p) for p in files},
        "prior_stage_sha256": sha256(Path(root) / (prior + "-stage.json")) if prior else None,
        "no_automatic_activation": True,
    }
    write_json(path, receipt)
    return receipt


def status(root, cfg, now_ms):
    from .paired_study import collection_status

    report = collection_status(root, cfg, now_ms)
    next_slot = report["next_slot"]
    if next_slot and report["next_action"] in ("ready_to_prepare", "prepared"):
        spec = next(s for s in cfg["trials"] if s["id"] == next_slot["trial"])
        if spec.get("requires_stage"):
            try:
                stage_receipt(root, cfg, spec["requires_stage"])
            except (ValueError, FileNotFoundError) as error:
                report["next_action"] = "awaiting_stage_or_stopped"
                next_slot["reason"] = str(error)
    if next_slot and report["next_action"] == "blocked_by_schedule_or_prior_slot":
        spec = next(s for s in cfg["trials"] if s["id"] == next_slot["trial"])
        required = spec.get("later_date_than", [])
        if required:
            from datetime import timedelta

            dates = []
            for name in required:
                p = Path(root) / (name + "-archive.json")
                if p.exists():
                    dates.append(
                        datetime.fromisoformat(
                            local_date(json.loads(p.read_text())["first_packet_ms"], cfg)
                        ).date()
                    )
            if dates:
                report["earliest_next_local_date"] = (max(dates) + timedelta(days=1)).isoformat()
    report["maximum_visits"] = 6
    report["scope"] = "role-bound Spotify repair; no automatic capture or fitting"
    return report
