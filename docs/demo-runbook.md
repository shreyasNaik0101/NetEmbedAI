# A five-minute honest showcase

The fixed-ten forest is an **experimental showcase profile**. Its acceptance
policy is unfitted: after ten packets it displays raw alternatives and
withholds an accepted label. A later threshold-zero policy failed its final
screen and is not the profile to present as reliable.

1. From `traffic_classification`, start the local server:

   ```powershell
   .\.venv\Scripts\python.exe scripts/serve_showcase.py
   ```

2. Open `http://127.0.0.1:8002` in one Edge or Chrome tab. Wait for **Stream
   connected**, choose the actual network interface, and leave the optional
   reference check and longer observation windows off for a simple demo.
3. Click **Start** yourself. Open a fresh supported QUIC connection in another
   browser and show actual packet metadata arriving. Background traffic may
   include other connections; opening one site does not label every flow.
4. Select a connection. Explain that the fixed-ten model waits for ten packets,
   then displays top guesses while withholding an accepted label. Scores are
   model outputs, not chances of being correct. The labels shown in the app are
   the model's possible outputs; most have not been validated locally.
5. Click **Stop**. Show the measured event timing and distinguish capture-to-event
   and browser receipt from rendering or time needed to observe ten packets.
   Switch to **Recorded replay** only for saved packet metadata, and say it is
   replay rather than live capture.

For ordinary showcasing you do **not** need Chrome NetLog or reference checking.
Those optional tools are separate evaluation inputs and can contain sensitive
metadata. Packet payloads, hostnames, endpoints and processes are not model
features. A user must start capture deliberately.

## If the app is unavailable

The bundle is local and Git-ignored. If readiness fails, check that the bundle
exists and passes its checksums; there is no random-weight fallback. If the
stream is disconnected, close duplicate app viewers and use **Reconnect**;
it will not resume a stopped capture. A laptop sleep or frozen browser can end
the session. Preserve any desired stopped evidence before restarting the service:
the three-session recovery buffer is in memory and clears on service exit.
If port 8002 is already occupied by a different service, choose another port with
`--port 8003`, rather than killing an unknown process. The launcher configures
the matching loopback origin for its chosen port.

## Explain the result

“I classified encrypted QUIC using packet sizes, directions and timing rather
than content. A fresh local three-service raw-guess check was encouraging, but
the later accepted-label screen failed because it accepted a YouTube connection
as Spotify. I kept the threshold policy out of the showcase and report those
limits. This is a small prototype, not universal app identification.”

The historical CESNET TCN benchmark and this locally adapted forest are different
models and evaluation settings. The benchmark score does not measure this
forest's current Wi-Fi accuracy. See the [showcase model card](showcase-model-card.md)
and [beginner interview guide](interview-guide.md). Earlier runbook instructions
are preserved in [history](demo-runbook-history-20261110.md).
