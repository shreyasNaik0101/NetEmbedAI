"""One declared selection extension; no capture, downloads or policy fitting."""

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from .bundle import sha256

REPO = Path(__file__).resolve().parents[2]
PROTOCOL_SHA256 = "8bacececc733c8380a7de0b8d166fcb85803b107ab053650ba41d0a6abf7fadb"


def config_digest_matches(path, digest):
    """Only committed config text tolerates Git's LF/CRLF conversion."""
    raw = Path(path).read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    return any(hashlib.sha256(value).hexdigest() == digest for value in (raw, lf, lf.replace(b"\n", b"\r\n")))


def read_followup(path):
    # Git may materialize CRLF on Windows. Only line endings are canonicalized
    # for the committed protocol; raw evidence hashes are never canonicalized.
    content = Path(path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(content).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("follow-up protocol differs from the declared specification")
    protocol = json.loads(content)
    parent_path = Path(path).parent / Path(protocol["parent_plan"]["path"]).name
    if not config_digest_matches(parent_path, protocol["parent_plan"]["sha256"]):
        raise ValueError("follow-up parent plan changed")
    from .browser_collection import read_plan

    parent = read_plan(parent_path)
    spec = protocol["one_additional_trial"]
    return {
        **parent,
        "version": "selection-followup-v1",
        "trials": [{"id": spec["id"], "role": spec["role"], "activity": spec["activity"]}],
        "train_trials": protocol["new_train_trials"],
        "selection_trials": protocol["new_selection_trials"],
        "followup_protocol": protocol,
    }


def load_parent_trial(root, path, plan, trial, split, labels):
    protocol = plan["followup_protocol"]
    binding = protocol["parent_evidence"].get(trial)
    if binding is None or binding["role"] != split:
        raise ValueError("follow-up inherited trial role cannot change")
    root = Path(root)
    if (
        sha256(root / f"{trial}-collection-summary.json") != binding["collection_summary_sha256"]
        or sha256(root / f"{trial}-development-rows.jsonl") != binding["packet_rows_sha256"]
    ):
        raise ValueError("follow-up inherited evidence changed")
    from .browser_adaptation import load_reference_trial
    from .browser_collection import read_plan

    parent_path = Path(path).parent / Path(protocol["parent_plan"]["path"]).name
    parent = read_plan(parent_path)
    bound = parent_path if trial in {r["id"] for r in parent["trials"]} else None
    return load_reference_trial(root, trial, labels, "development", bound)


def parent_state(root, path, plan):
    protocol = plan["followup_protocol"]
    records, proofs = {"train": [], "selection": []}, {}
    sessions, ids = set(), set()
    for trial, binding in protocol["parent_evidence"].items():
        rows, proof = load_parent_trial(root, path, plan, trial, binding["role"], plan["labels"])
        row_ids = {r["id"] for r in rows}
        if proof["session_id"] in sessions or ids & row_ids or len(row_ids) != len(rows):
            raise ValueError("follow-up parent sessions/records are reused")
        sessions.add(proof["session_id"])
        ids.update(row_ids)
        records[binding["role"]].extend(rows)
        proofs[trial] = proof
    counts = {role: dict(Counter(r["label"] for r in rows)) for role, rows in records.items()}
    if counts != protocol["counts_at_declaration"]:
        raise ValueError("follow-up inherited cohort counts changed")

    def bounds(p):
        return p.get("observed_packet_range_unix_ms", p["first_packet_range_unix_ms"])

    training_end = max(bounds(proofs[t])[1] for t in protocol["new_train_trials"])
    selection_end = max(bounds(proofs[t])[1] for t in protocol["new_selection_trials"][:-1])
    return {
        "counts": counts,
        "proofs": proofs,
        "sessions": sessions,
        "ids": ids,
        "selection_end_ms": selection_end,
        "training_gap_end_ms": training_end + plan["selection_gap_minutes"] * 60000,
    }


def stage_gate(root, path, plan, trial, now_ms):
    if trial != plan["followup_protocol"]["one_additional_trial"]["id"]:
        raise ValueError("only the single declared follow-up trial can be collected")
    state = parent_state(root, path, plan)
    if now_ms <= state["selection_end_ms"] or now_ms < state["training_gap_end_ms"]:
        raise ValueError("follow-up must follow parent selection and the post-training time gap")
    return state


def expected_config(path, seed):
    plan = read_followup(path)
    protocol = plan["followup_protocol"]
    name = f"configs/browser-expanded-v3-seed{seed}.json"
    if name not in protocol["parent_runner_configs"]:
        raise ValueError("undeclared follow-up seed")
    source = REPO / name
    if not config_digest_matches(source, protocol["parent_runner_configs"][name]):
        raise ValueError("follow-up parent runner config changed")
    cfg = copy.deepcopy(json.loads(source.read_text()))
    cfg.update(
        purpose="Declared one-session selection follow-up; unchanged training and numeric gates",
        selection_trials=plan["selection_trials"],
        split_plan_filename=Path(path).name,
        reference_collection_plan_filename=Path(path).name,
        followup_protocol_sha256=PROTOCOL_SHA256,
        selection="Mean-budget local macro-F1 gain >=0.01 over paired previous forest; original numeric quality/recall/retention guards",
        limits="One supplemental selection recording only. Seed17 first; fixed repetitions cannot rescue it. No calibration, capture or promotion by this runner.",
    )
    return cfg


def validate_run(path, cfg, destination, evidence=None):
    if cfg != expected_config(path, cfg["seed"]):
        raise ValueError("follow-up runner settings differ from the declared inherited config")
    protocol = read_followup(path)["followup_protocol"]
    seed = cfg["seed"]
    if Path(destination).resolve() != (REPO / protocol["output_directories"][str(seed)]).resolve():
        raise ValueError("follow-up requires its unique declared output directory")
    previous = [17, 42, 123][: [17, 42, 123].index(seed)]
    chosen = None
    for earlier in previous:
        folder = REPO / protocol["output_directories"][str(earlier)]
        result = json.loads((folder / "result.json").read_text())
        provenance = json.loads((folder / "config.json").read_text())
        if (
            provenance["config"] != expected_config(path, earlier)
            or provenance["browser_split_plan_sha256"] != sha256(path)
            or provenance["data_manifest_sha256"] != sha256(folder / "data-manifest.json")
        ):
            raise ValueError("follow-up previous seed provenance changed")
        if evidence is not None:
            previous_manifest = json.loads((folder / "data-manifest.json").read_text())
            if previous_manifest["browser_evidence"] != evidence:
                raise ValueError("follow-up repetition changed the frozen cohort")
        candidate = result["candidate_for_separate_calibration"]
        if earlier == 17:
            chosen = candidate
            if chosen is None:
                raise ValueError("ineligible seed17 stops follow-up repetitions")
        # Seed42 failure is reported, but does not turn seed123 into a rescue.
        # Both declared repetitions can finish; neither changes seed17's choice.
        if candidate is not None and candidate != chosen:
            raise ValueError("follow-up repetition changed the seed17 family/checkpoint")
    return chosen


def repetition_decision(protocol_path):
    """Report stability; never select another seed or fit a confidence policy."""
    protocol = read_followup(protocol_path)["followup_protocol"]
    results, digests = {}, {}
    for seed in (17, 42, 123):
        folder = REPO / protocol["output_directories"][str(seed)]
        validate_run(protocol_path, expected_config(protocol_path, seed), folder)
        result = json.loads((folder / "result.json").read_text())
        results[seed] = result["candidate_for_separate_calibration"]
        digests[str(seed)] = sha256(folder / "result.json")
        if seed == 17 and results[seed] is None:
            break
    chosen = results[17]
    stable = chosen is not None and len(results) == 3 and all(v == chosen for v in results.values())
    return {
        "seed17_candidate": chosen,
        "eligible_in_all_three_seeds": stable,
        "candidate_for_separate_calibration": str(
            REPO / protocol["output_directories"]["17"] / chosen / "bundle"
        )
        if stable
        else None,
        "result_sha256": digests,
        "default_promoted": False,
        "policy_fitted": False,
        "note": "Development stability only; no seed substitution, calibration or deployment.",
    }
