"""Constructed metadata only. These tests never collect traffic or validate quality."""

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import netembed.browser_adaptation as adaptation
import netembed.browser_followup as followup
from netembed.browser_collection import read_collection_plan, read_plan, stage_gate, trial_spec
from scripts import collect_browser

REPO = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def environment(tmp_path, monkeypatch):
    root = tmp_path / "collection"
    root.mkdir()
    config_root = tmp_path / "configs"
    config_root.mkdir()
    path = root / "browser-selection-followup-v1.json"
    protocol = json.loads((REPO / "configs" / path.name).read_text())
    parent_name = Path(protocol["parent_plan"]["path"]).name
    (root / parent_name).write_bytes((REPO / "configs" / parent_name).read_bytes())
    for name in protocol["parent_runner_configs"]:
        (tmp_path / name).write_bytes((REPO / name).read_bytes())
    records, proofs, calls = {}, {}, []
    counts = {
        "instagram-dev-01": {"instagram": 3},
        "instagram-dev-02": {"instagram": 2},
        "youtube-dev-01": {"youtube": 6},
        "youtube-dev-02": {"youtube": 6},
        "instagram-dev-03": {"instagram": 5, "youtube": 1},
        "instagram-dev-04": {"instagram": 7},
        "instagram-dev-05": {"instagram": 5},
        "youtube-dev-03": {"youtube": 8},
        "instagram-dev-06": {"instagram": 7},
        "youtube-dev-04": {"youtube": 5},
    }
    for i, (trial, binding) in enumerate(protocol["parent_evidence"].items()):
        session = "fixture-" + trial
        rows = [
            {
                "id": f"{session}:{label}:{index}",
                "group_id": session,
                "label": label,
                "packets": [{"iat_ms": 0, "direction": 1, "payload_bytes": 100}] * 30,
            }
            for label, count in counts[trial].items()
            for index in range(count)
        ]
        records[trial] = rows
        summary = root / f"{trial}-collection-summary.json"
        rows_path = root / f"{trial}-development-rows.jsonl"
        write_json(summary, {"fixture": True, "session_id": session})
        rows_path.write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")
        binding["collection_summary_sha256"] = followup.sha256(summary)
        binding["packet_rows_sha256"] = followup.sha256(rows_path)
        proofs[trial] = {
            "session_id": session,
            "counts": counts[trial],
            "first_packet_range_unix_ms": [10000000 + i * 100000, 10000001 + i * 100000],
            "observed_packet_range_unix_ms": [10000000 + i * 100000, 10000005 + i * 100000],
        }
    write_json(path, protocol)
    monkeypatch.setattr(followup, "PROTOCOL_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())
    monkeypatch.setattr(followup, "REPO", tmp_path)

    def load(root, trial, labels, stage, bound=None):
        calls.append((trial, stage, bound))
        if trial not in records:
            raise FileNotFoundError("missing fixture recording")
        return copy.deepcopy(records[trial]), copy.deepcopy(proofs[trial])

    monkeypatch.setattr(adaptation, "load_reference_trial", load)
    return SimpleNamespace(
        root=root,
        path=path,
        protocol=protocol,
        records=records,
        proofs=proofs,
        calls=calls,
        plan=read_collection_plan(path),
        repo=tmp_path,
    )


def test_production_protocol_is_pinned_and_v3_limit_stays_closed():
    path = REPO / "configs/browser-selection-followup-v1.json"
    plan = read_collection_plan(path)
    assert [r["id"] for r in plan["trials"]] == ["youtube-dev-05"]
    with pytest.raises(ValueError, match="bounded development plan"):
        read_plan(path)


def test_v3_cannot_be_extended_by_adding_a_seventh_trial(tmp_path):
    source = json.loads((REPO / "configs/browser-collection-v3.json").read_text())
    source["trials"].append({"id": "youtube-dev-05", "role": "selection"})
    target = tmp_path / "extra.json"
    write_json(target, source)
    with pytest.raises(ValueError, match="bounded development plan"):
        read_collection_plan(target)


@pytest.mark.parametrize("part", ["protocol", "parent"])
def test_changed_protocol_or_parent_is_refused(environment, part):
    e = environment
    target = e.path if part == "protocol" else e.root / "browser-collection-v3.json"
    data = json.loads(target.read_text())
    data["tampered"] = True
    write_json(target, data)
    with pytest.raises(ValueError, match="specification|parent plan changed"):
        read_collection_plan(e.path)


@pytest.mark.parametrize("suffix", ["collection-summary.json", "development-rows.jsonl"])
def test_changed_inherited_evidence_cannot_be_rebound(environment, suffix):
    e = environment
    (e.root / f"youtube-dev-04-{suffix}").write_text("changed")
    with pytest.raises(ValueError, match="inherited evidence changed"):
        followup.parent_state(e.root, e.path, e.plan)


def test_parent_roles_and_original_per_trial_plans_are_preserved(environment):
    e = environment
    cfg = {"reference_collection_plan_filename": e.path.name}
    adaptation.load_role_trial(e.root, "instagram-dev-03", "train", [], cfg, e.plan)
    assert e.calls[-1][2] == e.root / "browser-collection-v3.json"
    adaptation.load_role_trial(e.root, "instagram-dev-01", "train", [], cfg, e.plan)
    assert e.calls[-1][2] is None
    for trial in ("instagram-dev-06", "youtube-dev-04", "youtube-dev-05"):
        with pytest.raises(ValueError, match="role"):
            adaptation.load_role_trial(e.root, trial, "train", [], cfg, e.plan)
    for trial in ("youtube-dev-06", "instagram-cal-02", "youtube-eval-01"):
        with pytest.raises(ValueError, match="not reserved"):
            adaptation.load_role_trial(e.root, trial, "selection", [], cfg, e.plan)


def test_parent_session_reuse_is_rejected(environment):
    e = environment
    e.proofs["youtube-dev-04"]["session_id"] = e.proofs["instagram-dev-06"]["session_id"]
    with pytest.raises(ValueError, match="sessions/records are reused"):
        followup.parent_state(e.root, e.path, e.plan)


def test_followup_chronology_uses_last_retained_packet_and_training_gap(environment):
    e = environment
    state = followup.parent_state(e.root, e.path, e.plan)
    for now in (state["selection_end_ms"], state["training_gap_end_ms"] - 1):
        with pytest.raises(ValueError, match="post-training time gap"):
            stage_gate(e.root, e.path, "youtube-dev-05", now)
    now = max(state["selection_end_ms"] + 1, state["training_gap_end_ms"])
    stage_gate(e.root, e.path, "youtube-dev-05", now)
    with pytest.raises(ValueError, match="single declared"):
        stage_gate(e.root, e.path, "youtube-dev-06", now)
    with pytest.raises(ValueError, match="not reserved"):
        trial_spec(e.plan, "instagram-dev-06")


def snapshot_inputs(e, monkeypatch, invalid=None):
    state = followup.parent_state(e.root, e.path, e.plan)
    first = max(state["selection_end_ms"], state["training_gap_end_ms"]) + 1000
    session = "fixture-new-session"
    status = {
        "running": False,
        "session_id": session,
        "selected_interface_id": "9",
        "observation_windows_enabled": False,
    }
    cap = {
        "fixture": False,
        "source": "user_started_capture",
        "counters": status,
        "reference_enabled": True,
        "adapter_version": "tshark-prefix-ns-v3",
        "artifact_id": e.protocol["source_artifact_id"],
        "session_id": session,
        "flows": [{"connection_match": {"first_packet_unix_ms": first}}],
    }
    intent = {
        "previous_session_excluded": "fixture-old-session",
        "expected_adapter": cap["adapter_version"],
        "expected_artifact_id": cap["artifact_id"],
        "selected_interface_id": "9",
        "recorded_before_capture_utc": datetime.fromtimestamp((first - 1) / 1000, timezone.utc).isoformat(),
    }
    if invalid == "empty":
        cap["flows"] = []
    elif invalid == "fixture":
        cap["fixture"] = True
    elif invalid == "windows":
        status["observation_windows_enabled"] = True
    elif invalid == "reused":
        status["session_id"] = cap["session_id"] = next(iter(state["sessions"]))
    values = {
        "/capture/status": status,
        "/capture/local-evaluation": cap,
        "/capture/summary": {"session_id": cap["session_id"]},
    }
    calls = []

    def get(base, route):
        calls.append(route)
        return json.dumps(values[route]).encode()

    monkeypatch.setattr(collect_browser, "get", get)
    return SimpleNamespace(trial="youtube-dev-05", service="http://localhost:8001"), intent, calls


def test_single_attempt_is_immutable_and_resume_uses_saved_bytes(environment, monkeypatch):
    e = environment
    args, intent, calls = snapshot_inputs(e, monkeypatch)
    collect_browser.followup_snapshot(args, e.root, intent, e.plan, e.path)
    bound = (e.root / "youtube-dev-05-attempt.json").read_bytes()
    assert calls == ["/capture/status", "/capture/local-evaluation", "/capture/summary"]
    monkeypatch.setattr(collect_browser, "get", lambda *a: pytest.fail("must resume bound snapshot offline"))
    collect_browser.followup_snapshot(args, e.root, intent, e.plan, e.path)
    assert (e.root / "youtube-dev-05-attempt.json").read_bytes() == bound
    with pytest.raises(ValueError, match="already bound"):
        collect_browser.prepare(args, e.root, e.path, e.plan)


@pytest.mark.parametrize("invalid", ["empty", "fixture", "windows", "reused"])
def test_unusable_attempt_consumes_limit_and_preserves_raw_evidence(environment, monkeypatch, invalid):
    e = environment
    args, intent, calls = snapshot_inputs(e, monkeypatch, invalid)
    with pytest.raises(ValueError):
        collect_browser.followup_snapshot(args, e.root, intent, e.plan, e.path)
    outcome = json.loads((e.root / "youtube-dev-05-followup-outcome.json").read_text())
    assert outcome["status"] == "unusable_attempt_stop"
    assert not (e.root / "youtube-dev-05-capture.json").exists()
    assert (e.root / "youtube-dev-05-attempt-capture.json").exists()
    with pytest.raises(ValueError, match="already bound"):
        collect_browser.prepare(args, e.root, e.path, e.plan)


def test_attempt_payload_tampering_is_refused(environment, monkeypatch):
    e = environment
    args, intent, calls = snapshot_inputs(e, monkeypatch)
    collect_browser.followup_snapshot(args, e.root, intent, e.plan, e.path)
    (e.root / "youtube-dev-05-attempt-timing.json").write_text("changed")
    with pytest.raises(ValueError, match="attempt evidence changed"):
        collect_browser.followup_snapshot(args, e.root, intent, e.plan, e.path)


def test_generated_configs_keep_every_undeclared_field_and_reject_tuning(environment):
    e = environment
    allowed = {
        "purpose",
        "selection_trials",
        "split_plan_filename",
        "reference_collection_plan_filename",
        "followup_protocol_sha256",
        "selection",
        "limits",
    }
    for seed in (17, 42, 123):
        cfg = followup.expected_config(e.path, seed)
        original = json.loads((e.repo / f"configs/browser-expanded-v3-seed{seed}.json").read_text())
        assert {k: v for k, v in cfg.items() if k not in allowed} == {
            k: v for k, v in original.items() if k not in allowed
        }
    cfg = followup.expected_config(e.path, 17)
    cfg["learning_rate"] *= 2
    with pytest.raises(ValueError, match="runner settings"):
        followup.validate_run(e.path, cfg, e.repo / e.protocol["output_directories"]["17"])


def test_git_line_endings_are_tolerated_only_for_config_text(environment):
    e = environment
    original = followup.expected_config(e.path, 17)
    source = e.repo / "configs/browser-expanded-v3-seed17.json"
    source.write_bytes(source.read_bytes().replace(b"\r\n", b"\n"))
    assert followup.expected_config(e.path, 17) == original
    source.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))
    assert followup.expected_config(e.path, 17) == original
    source.write_bytes(source.read_bytes().replace(b"0.0001", b"0.0002"))
    with pytest.raises(ValueError, match="parent runner config changed"):
        followup.expected_config(e.path, 17)


def prior_result(e, seed, chosen="forest", evidence=None):
    folder = e.repo / e.protocol["output_directories"][str(seed)]
    folder.mkdir(parents=True)
    write_json(folder / "data-manifest.json", {"browser_evidence": evidence or {}})
    write_json(
        folder / "config.json",
        {
            "config": followup.expected_config(e.path, seed),
            "browser_split_plan_sha256": followup.sha256(e.path),
            "data_manifest_sha256": followup.sha256(folder / "data-manifest.json"),
        },
    )
    write_json(folder / "result.json", {"candidate_for_separate_calibration": chosen})


def test_repetitions_cannot_rescue_seed17_or_change_cohort(environment):
    e = environment
    cfg = followup.expected_config(e.path, 42)
    dest = e.repo / e.protocol["output_directories"]["42"]
    with pytest.raises(FileNotFoundError):
        followup.validate_run(e.path, cfg, dest)
    prior_result(e, 17, chosen=None)
    with pytest.raises(ValueError, match="ineligible seed17"):
        followup.validate_run(e.path, cfg, dest)
    write_json(
        e.repo / e.protocol["output_directories"]["17"] / "result.json",
        {"candidate_for_separate_calibration": "forest"},
    )
    assert followup.validate_run(e.path, cfg, dest) == "forest"
    with pytest.raises(ValueError, match="frozen cohort"):
        followup.validate_run(e.path, cfg, dest, {"fixture-different-cohort": True})


@pytest.mark.parametrize("choices", [(None,), ("forest", None, "forest"), ("forest", "forest", "forest")])
def test_repetition_summary_never_chooses_a_better_seed(environment, choices):
    e = environment
    for seed, chosen in zip((17, 42, 123), choices):
        prior_result(e, seed, chosen)
    decision = followup.repetition_decision(e.path)
    stable = choices == ("forest", "forest", "forest")
    assert decision["eligible_in_all_three_seeds"] == stable
    expected = str(e.repo / e.protocol["output_directories"]["17"] / "forest/bundle") if stable else None
    assert decision["candidate_for_separate_calibration"] == expected
    assert decision["default_promoted"] is False and decision["policy_fitted"] is False


@pytest.mark.parametrize("new_count", [0, 1])
def test_real_runner_checks_support_before_public_data_or_fitting(environment, monkeypatch, new_count):
    e = environment
    trial = "youtube-dev-05"
    cfg = followup.expected_config(e.path, 17)
    cfg_path = e.repo / "runner.json"
    write_json(cfg_path, cfg)
    state = followup.parent_state(e.root, e.path, e.plan)
    first = max(state["selection_end_ms"], state["training_gap_end_ms"]) + 1000
    e.records[trial] = [
        {
            "id": "fixture-new-row",
            "group_id": "fixture-new",
            "label": "youtube",
            "packets": [{"iat_ms": 0, "direction": 1, "payload_bytes": 100}] * 30,
        }
    ] * new_count
    e.proofs[trial] = {
        "session_id": "fixture-new",
        "first_packet_range_unix_ms": [first, first],
        "observed_packet_range_unix_ms": [first, first + 1],
    }
    monkeypatch.setattr(
        adaptation, "Predictor", lambda *a: SimpleNamespace(meta={"kind": "tcn"}, labels=e.plan["labels"])
    )
    monkeypatch.setattr(adaptation, "train_epoch", lambda *a: pytest.fail("must not fit"))

    def data_boundary(*a):
        raise RuntimeError("fixture public-data boundary reached after admission")

    monkeypatch.setattr(adaptation, "read_split", data_boundary)
    error = RuntimeError if new_count else ValueError
    message = "public-data boundary" if new_count else "insufficient independently"
    dest = e.repo / e.protocol["output_directories"]["17"]
    with pytest.raises(error, match=message):
        adaptation.run("unused", e.root, "unused", cfg_path, dest)
    assert not dest.exists()
