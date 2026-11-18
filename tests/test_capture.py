import asyncio
import pytest
from netembed.capture import Capture, FlowTable, parse_line


def line(**overrides):
    fields = {
        "t": "100.000",
        "ip4s": "192.0.2.1",
        "ip6s": "",
        "ip4d": "198.51.100.1",
        "ip6d": "",
        "sp": "50000",
        "dp": "443",
        "size": "1208",
        "cap": "1242",
        "wire": "1242",
        "protocols": "eth:ip:udp:quic",
        "type": "0",
        "version": "0x00000001",
        "offset": "0",
        "mf": "0",
        "frag6": "",
    }
    fields.update(overrides)
    return "\t".join(fields.values())


def test_parser_units_pairing_and_freeze():
    table = FlowTable()
    first = table.ingest(parse_line(line()), now=0)
    second = table.ingest(
        parse_line(line(t="100.0085", ip4s="198.51.100.1", ip4d="192.0.2.1", sp="443", dp="50000", type="")),
        now=1,
    )
    assert first is second
    assert second.packets[0].iat_ms == 0 and second.packets[0].payload_bytes == 1200
    assert second.packets[1].iat_ms == pytest.approx(8.5)
    assert second.packets[1].direction == -1
    for i in range(40):
        table.ingest(parse_line(line(t=str(101 + i))), now=2)
    assert len(first.packets) == 30 and table.counters["frozen"] > 0


def test_epoch_sized_timestamps_preserve_microsecond_and_nanosecond_gaps():
    table = FlowTable()
    state = table.ingest(parse_line(line(t="1780000000.123456789")), now=0)
    table.ingest(parse_line(line(t="1780000000.123457789")), now=1)
    assert state.packets[1].iat_ms == 0.001
    table.ingest(parse_line(line(t="1780000000.123457790")), now=2)
    assert state.packets[2].iat_ms == 0.000001
    assert table.ingest(parse_line(line(t="1780000000.123457789")), now=3) is None
    assert table.counters["reordered"] == 1


@pytest.mark.parametrize("timestamp", ["100.1234567890", "1e3", "-1.0", "1000000000000.0"])
def test_unsupported_or_out_of_range_timestamp_precision_is_rejected(timestamp):
    with pytest.raises(ValueError, match="timestamp"):
        parse_line(line(t=timestamp))


@pytest.mark.parametrize(
    "fields",
    [{"protocols": "eth:ip:udp"}, {"cap": "20"}, {"offset": "1"}, {"mf": "1"}, {"size": "8"}, {"t": "nan"}],
)
def test_unsupported(fields):
    with pytest.raises(ValueError):
        parse_line(line(**fields))


def test_midflow_reorder_eviction_ipv6():
    table = FlowTable(limit=1, idle_seconds=2)
    assert table.ingest(parse_line(line(type="")), now=0) is None
    state = table.ingest(parse_line(line()), now=0)
    assert table.ingest(parse_line(line(t="99")), now=1) is None
    other = table.ingest(parse_line(line(ip4s="", ip4d="", ip6s="2001:db8::1", ip6d="2001:db8::2")), now=1)
    assert other is not state and len(table.states) == 1
    table.ingest(parse_line(line()), now=4)
    assert table.counters["evicted"] == 2


def test_stop_idempotence_and_event_bounds():
    async def scenario():
        c = Capture(None)
        q = asyncio.Queue(maxsize=2)
        c.clients.add(q)
        for i in range(5):
            c.emit({"type": "test", "n": i})
        assert q.qsize() == 2 and c.drops == 3
        await c.stop()
        await c.stop()
        assert not c.running and not c.tasks and not c.pending

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "reason", ["capture duration limit reached", "capture process exited", "stopped by user"]
)
def test_later_disconnect_or_shutdown_preserves_the_original_stop_evidence(reason):
    async def scenario():
        c = Capture(None)
        c.session_id, c.running = "software-session", True
        c.table.ingest(parse_line(line()), now=0)
        first = await c.stop(reason)
        sequence = c.sequence
        assert await c.stop("viewer disconnected") == first
        assert await c.stop("service shutdown") == first
        assert c.reason == reason and c.sequence == sequence

    asyncio.run(scenario())


def test_no_automatic_process(monkeypatch):
    async def forbidden(*a, **k):
        raise AssertionError("capture should not start")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", forbidden)
    c = Capture(None)
    assert c.status()["running"] is False
    assert c.status()["adapter_version"] == "tshark-prefix-ns-v3"


def test_default_idle_boundary_retains_delayed_prefix_before_cesnet_expiry():
    table = FlowTable()
    first = table.ingest(parse_line(line(t="100")), now=0)
    retained = table.ingest(parse_line(line(t="131", type="")), now=31)
    assert retained is first and retained.packets[1].iat_ms == 31000
    # Beyond the documented 65-second idle boundary, mid-flow data cannot
    # invent a new eligible handshake window; a new Initial is required.
    assert table.ingest(parse_line(line(t="197", type="")), now=97) is None
    assert table.counters["evicted"] == 1
    new = table.ingest(parse_line(line(t="198")), now=98)
    assert new is not first and new.packets[0].iat_ms == 0


def test_normal_tshark_startup_is_not_an_error():
    from types import SimpleNamespace

    async def scenario():
        reader = asyncio.StreamReader()
        reader.feed_data(b"Capturing on 'Wi-Fi'\n78060 packets captured\nPermission denied\n")
        reader.feed_eof()
        c = Capture(None)
        c.process = SimpleNamespace(stderr=reader)
        await c.drain()
        assert c.status()["error_detail"] == "Permission denied"
        assert c.status()["stderr_lines"] == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "duration,reason", [(1, "capture duration limit reached"), (100, "viewer disconnected")]
)
def test_automatic_stop_reasons_are_distinct_without_real_capture(monkeypatch, duration, reason):
    import netembed.capture as capture_module

    async def scenario():
        clock = [0]
        real_sleep = asyncio.sleep
        monkeypatch.setattr(capture_module.time, "monotonic", lambda: clock[0])

        async def tick(_):
            clock[0] += 1
            await real_sleep(0)

        monkeypatch.setattr(capture_module.asyncio, "sleep", tick)
        c = Capture(None)
        c.running, c.last_client = True, 0
        stopped = []

        async def stop(value):
            stopped.append(value)
            c.running = False

        c.stop = stop
        await c.guard(duration)
        await real_sleep(0)
        assert stopped == [reason]

    asyncio.run(scenario())


@pytest.mark.parametrize("reference", [False, True])
def test_mocked_process_lifecycle_and_real_worker(monkeypatch, reference):
    """Software simulation, not live validation. Start/Stop never touch an interface."""
    from types import SimpleNamespace

    async def scenario():
        calls = []

        def predict(x):
            calls.append(len(x))
            assert x.shape == (len(x), 3)  # The reference channel cannot enter the predictor.
            return {
                "pipeline_ms": 0.1,
                "status": "classified",
                "observed_packets": len(x),
                "label": "whatsapp",
                "alternatives": [{"label": "whatsapp", "score": 0.9}],
                "artifact_id": "fixture",
            }

        c = Capture(SimpleNamespace(meta={"provenance": {}}, predict=predict, identity="fixture"))
        q = asyncio.Queue(maxsize=64)
        c.clients.add(q)

        async def interfaces():
            return [{"id": "1"}]

        c.interfaces = interfaces

        class Process:
            pid = 123456
            returncode = None

            def __init__(self):
                self.stdout = asyncio.StreamReader()
                self.stderr = asyncio.StreamReader()

            def terminate(self):
                self.returncode = 0
                self.stdout.feed_eof()
                self.stderr.feed_eof()

            def kill(self):
                self.terminate()

            async def wait(self):
                return self.returncode

        proc = Process()

        async def spawn(*args, **kwargs):
            if args[0] == "taskkill":
                assert "/T" in args and "/F" in args
                proc.terminate()
                return proc
            assert "-i" in args and args[args.index("-i") + 1] == "1"
            assert kwargs.get("shell", False) is False
            return proc

        monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
        c.delivery.append(900)
        c.observation_delivery.append(800)
        c.observation_delivery_pending[77] = 100
        c.receipt_tracking_evicted["observation"] = 2
        await c.start("1", 10, reference)
        assert not c.delivery and not c.observation_delivery and not c.observation_delivery_pending
        assert c.receipt_tracking_evicted == {"prediction": 0, "observation": 0}
        assert c.status()["selected_interface_id"] == "1"
        with pytest.raises(RuntimeError, match="already running"):
            await c.start("1", 10)
        for i in range(5):
            suffix = ("\twww.youtube.com\t\t" if i == 0 else "\t\t\t") if reference else ""
            reverse = (
                dict(ip4s="198.51.100.1", ip4d="192.0.2.1", sp="443", dp="50000", type="")
                if i in (1, 2, 4)
                else {}
            )
            proc.stdout.feed_data((line(t=str(100 + i / 1000), **reverse) + suffix + "\n").encode())
        event = None
        for _ in range(10):
            event = await asyncio.wait_for(q.get(), 2)
            if event.get("type") == "prediction":
                break
        assert event["observed_packets"] == 5 and calls == [5]
        assert event["source"] == "capture"  # transport path exercised with mocked process
        assert event["label"] == "whatsapp"  # A different reference never replaces a model decision.
        if reference:
            assert event["reference"] == {"status": "mapped", "label": "youtube"}
            evidence = c.local_evaluation()
            assert evidence["agreement_by_prefix"]["5"]["accepted_mismatches"] == 1
            assert len(evidence["connection_matching"]["salt"]) == 64
            assert evidence["flows"][0]["connection_match"]["first_packet_unix_ms"] == 100000
            from netembed.netlog_reference import correlate

            netlog = {
                "constants": {
                    "timeTickOffset": "99000",
                    "logEventPhase": {"PHASE_BEGIN": 1},
                    "logEventTypes": {"QUIC_SESSION": 70, "QUIC_SESSION_PACKET_RECEIVED": 71},
                },
                "events": [
                    {
                        "type": 70,
                        "phase": 1,
                        "source": {"id": 9},
                        "time": "999",
                        "params": {"host": "www.youtube.com", "port": 443},
                    },
                    *[
                        {
                            "type": 71,
                            "source": {"id": 9},
                            "time": str(1000 + i),
                            "params": {
                                "self_address": "192.0.2.1:50000",
                                "peer_address": "198.51.100.1:443",
                                "size": 1200,
                            },
                        }
                        for i in (1, 2, 4)
                    ],
                ],
            }
            assert correlate(evidence, netlog)["agreement_by_prefix"]["5"]["accepted_mismatches"] == 1
        else:
            assert event["reference"] is None and not c.evidence
        await c.stop()
        assert proc.returncode == 0 and not c.tasks and not c.running
        assert c.status()["selected_interface_id"] == "1"
        await c.stop()

    asyncio.run(scenario())


@pytest.mark.parametrize("queue_size,expected,drops", [(64, [5, 10, 20, 30], 0), (2, [20, 30], 2)])
def test_burst_retains_distinct_prefixes_with_bounded_overload(queue_size, expected, drops):
    from types import SimpleNamespace

    async def scenario():
        c = Capture(None, queue_size=queue_size)
        reader = asyncio.StreamReader()
        c.process = SimpleNamespace(stdout=reader)
        c.running = True
        task = asyncio.create_task(c.read())
        for i in range(30):
            reader.feed_data((line(t=str(100 + i / 1000)) + "\n").encode())
        await asyncio.sleep(0)
        assert len(c.pending) <= queue_size
        assert [len(value[0].packets) for value in c.pending.values()] == expected
        assert c.drops == drops and c.coalesced == 0
        emitted = []

        def predict(x):
            return {"pipeline_ms": 0.1, "observed_packets": len(x)}

        c.predictor = SimpleNamespace(predict=predict)

        def emit(event):
            emitted.append(event)
            if len(emitted) == len(expected):
                c.running = False

        c.emit = emit
        await asyncio.wait_for(c.worker(), 2)
        assert [event["observed_packets"] for event in emitted] == expected
        assert len({event["flow_id"] for event in emitted}) == 1
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    asyncio.run(scenario())
