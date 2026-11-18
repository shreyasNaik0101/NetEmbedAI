"""Software burst contracts, not genuine live delivery measurements."""

import asyncio

import pytest

from netembed.capture import Capture, ViewerQueue


def packet(flow, n):
    return {"type": "packets", "flow_id": flow, "packets": list(range(n))}


def test_cumulative_updates_coalesce_without_losing_metadata_or_model_checkpoints():
    q = ViewerQueue(8)
    for n in range(1, 31):
        coalesced, dropped = q.offer(packet("a", n))
        assert coalesced == (n > 1) and dropped is None
    assert q.qsize() == 1 and q.get_nowait()["packets"] == list(range(30))
    for n in [5, 10, 20, 30]:
        q.offer({"type": "prediction", "flow_id": "a", "observed_packets": n})
    assert [q.get_nowait()["observed_packets"] for _ in range(4)] == [5, 10, 20, 30]


def test_predictions_take_priority_and_true_model_event_loss_is_reported():
    q = ViewerQueue(2)
    q.offer({"type": "prediction", "flow_id": "a", "observed_packets": 10})
    q.offer(packet("b", 3))
    assert q.offer({"type": "prediction", "flow_id": "c", "observed_packets": 10}) == (False, "packets")
    assert q.offer(packet("d", 2)) == (False, "packets")
    assert q.offer({"type": "prediction", "flow_id": "e", "observed_packets": 10}) == (False, "prediction")
    assert [q.get_nowait()["flow_id"] for _ in range(2)] == ["c", "e"]


def test_async_waiter_and_timeout_remain_usable():
    async def run():
        q = ViewerQueue(1)
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(q.get(), 0.001)
        task = asyncio.create_task(q.get())
        await asyncio.sleep(0)
        q.put_nowait(packet("a", 1))
        assert (await asyncio.wait_for(task, 1))["flow_id"] == "a"
        assert q.empty()
        with pytest.raises(asyncio.QueueEmpty):
            q.get_nowait()

    asyncio.run(run())


def test_capture_reports_coalescing_separately_from_dropped_events():
    c = Capture(None)
    q = ViewerQueue(2)
    c.clients.add(q)
    for n in range(1, 31):
        c.emit(packet("a", n))
    assert c.status()["packet_updates_coalesced"] == 29
    assert c.status()["drops"] == 0
    c.emit({"type": "status"})
    c.emit(packet("b", 1))
    assert c.status()["drops"] == 1
    assert c.status()["viewer_event_drops"]["packets"] == 1
    assert c.status()["inference_queue_drops"] == 0
    assert q.qsize() == 2
