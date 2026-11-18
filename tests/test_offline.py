import shutil
import json
from pathlib import Path
import numpy as np
import pytest
from netembed.capture import tshark_path
from netembed.offline import extract


def test_stalled_native_reader_has_a_deadline_and_is_reaped_without_capture(monkeypatch):
    import threading
    import netembed.offline as offline

    class Reader:
        closed = False

        def __iter__(self):
            assert released.wait(2), "deadline did not terminate the stalled reader"
            return iter(())

        def close(self):
            self.closed = True

    class Process:
        stdout = Reader()
        code = None
        waited = False

        def kill(self):
            self.code = -1
            released.set()

        def poll(self):
            return self.code

        def wait(self, timeout=None):
            self.waited = True
            return self.code

    released = threading.Event()
    process = Process()

    def spawn(command, **kwargs):
        assert "-r" in command and "-i" not in command
        return process

    monkeypatch.setattr(offline.subprocess, "Popen", spawn)
    monkeypatch.setattr(offline, "OFFLINE_TIMEOUT_SECONDS", 0.01)
    with pytest.raises(ValueError, match="timed out"):
        extract("software-fixture-only.pcap")
    assert process.waited and process.stdout.closed


@pytest.mark.parametrize("reference", [False, True])
def test_rfc_vector_parity(reference):
    if not Path(tshark_path()).exists() and not shutil.which(tshark_path()):
        pytest.skip("native TShark unavailable; offline integration only")
    result = extract(Path(__file__).parent / "fixtures" / "rfc9001.pcap", reference)
    assert len(result["flows"]) == 1
    packets = result["flows"][0]["packets"]
    reference_report = json.loads(
        (Path(__file__).parent / "fixtures/rfc9001.ipfixprobe-reference.json").read_text()
    )
    np.testing.assert_allclose(
        [[p["iat_ms"], p["direction"], p["payload_bytes"]] for p in packets],
        [
            [p["iat_ms"], p["direction"], p["payload_bytes"]]
            for p in reference_report["reference_features"]["packets"]
        ],
        atol=1e-7,
    )
    assert result["counters"]["ignored"] == 0
    if reference:
        assert result["flows"][0]["reference"] == {"status": "unmapped", "label": None}
        assert "example.com" not in str(result)
