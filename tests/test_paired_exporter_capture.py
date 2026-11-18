"""Synthetic and offline checks: tests never start a real capture."""

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import paired_exporter_capture as paired
from test_capture import line


def test_selection_needs_ten_verified_ordered_packets():
    lines = [line(t=f"100.{i:03d}", type="0" if i == 0 else "") + "\t5" for i in range(10)]
    assert paired.candidate_stream(lines) == 5
    with pytest.raises(ValueError, match="ten"):
        paired.candidate_stream(lines[:9])
    with pytest.raises(ValueError, match="ten"):
        paired.candidate_stream([x.replace("eth:ip:udp:quic", "eth:ip:udp") for x in lines])


def test_selection_refuses_existing_destination(tmp_path):
    source = tmp_path / "source.pcap"
    source.write_bytes(b"fixture")
    destination = tmp_path / "selected.pcap"
    destination.write_bytes(b"previous evidence")
    with pytest.raises(FileExistsError):
        paired.select(source, destination)
    assert destination.read_bytes() == b"previous evidence"


def test_compare_rejects_changed_selected_pcap_before_docker(tmp_path, monkeypatch):
    import json

    source = tmp_path / "selected.pcap"
    source.write_bytes(b"changed")
    source.with_suffix(".selection.json").write_text(json.dumps({"selected_sha256": "wrong"}))
    monkeypatch.setattr(paired.subprocess, "run", lambda *a, **k: pytest.fail("should not launch Docker"))
    with pytest.raises(ValueError, match="changed"):
        paired.compare(source, tmp_path / "result.json", fixture=True)


def test_explicit_capture_is_bounded_and_never_runs_at_import(tmp_path, monkeypatch):
    monkeypatch.setattr(paired, "ROOT", tmp_path / "test-capture")
    calls = []

    def fake_popen(command, **kwargs):
        calls.append((command, kwargs))
        (paired.ROOT / "capture.pcap").write_bytes(b"constructed test")
        return SimpleNamespace(returncode=0, communicate=lambda **kw: calls.append(kw))

    monkeypatch.setattr(paired.subprocess, "Popen", fake_popen)
    assert calls == []
    paired.capture("9")
    assert len(calls) == 2
    command, kwargs = calls[0]
    assert ["-a", "duration:30"] == command[command.index("-a") : command.index("-a") + 2]
    assert "filesize:4096" in command and "12000" in command and "udp port 443" in command
    assert calls[1]["timeout"] == 45 and kwargs.get("shell", False) is False
    with pytest.raises(FileExistsError):
        paired.capture("9")
    assert len(calls) == 2


@pytest.mark.parametrize("interface", ["Wi-Fi", "1;command", "", "-1"])
def test_interface_argument_is_numeric(interface):
    with pytest.raises(ValueError, match="interface"):
        paired.capture(interface)


def test_timed_out_capture_stops_process_tree_and_keeps_partial_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(paired, "ROOT", tmp_path / "timed-out-capture")
    actions = []

    class FakeProcess:
        pid = 1234
        returncode = None
        calls = 0

        def communicate(self, timeout=None):
            self.calls += 1
            if self.calls == 1:
                raise paired.subprocess.TimeoutExpired("fixture", timeout)
            actions.append("reaped")

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -1
            actions.append("killed")

    proc = FakeProcess()
    monkeypatch.setattr(paired.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(paired.subprocess, "run", lambda *a, **k: actions.append("tree-stop"))
    monkeypatch.setattr(paired.os, "killpg", lambda *a: actions.append("tree-stop"), raising=False)
    with pytest.raises(RuntimeError, match="timeout"):
        paired.capture("9")
    assert "tree-stop" in actions and "reaped" in actions
    assert (paired.ROOT / "intent.json").exists()
    assert not (paired.ROOT / "capture-receipt.json").exists()
