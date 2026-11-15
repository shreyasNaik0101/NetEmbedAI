# UI refresh — 29 October 2026

The existing Live/Replay screen now has a clearer capture setup, connection
browser and analysis area. This is a presentation/usability change; the model,
preprocessing, supported services, capture adapter, thresholds and data roles
are unchanged. It provides no new local-accuracy or live-latency evidence.

## What changed

- Dark navy surfaces, mint/violet packet colors, consistent icons, spacing and
  typography, with responsive layouts and visible keyboard focus.
- A compact interface/Start/Stop row and a three-step **How to use** guide.
  Windows interface descriptions show friendly names such as **Wi-Fi** while
  preserving the actual interface ID sent to capture. Nothing is preselected.
- Real loading, connected, disconnected, stopped and unavailable states, with
  practical reconnection guidance. Research options live in an expandable
  section, remain off by default and retain their original request fields.
- Search by service or flow ID. Search only filters displayed connections;
  it never changes model inputs or decisions. When a selected row is evicted
  from the bounded list, selection moves to a retained connection.
- A packet chart next to the service estimate, readable alternatives and a
  plain explanation when the model withholds a label. Packet details,
  processing times, diagnostics and evaluation remain available on expansion.
- Separate visual sections for longer-window statistics and handshake
  reference evidence. Name-derived identity never becomes a packet prediction.
- Replay rejects malformed packet objects, invalid intervals/directions/sizes,
  a nonzero first interval and incompatible schema before trying to draw them.
  A corrected recording loads without refreshing. The server remains the
  authoritative feature validator.

Counters describe retained UI state and the selected prefix. Empty values
stay empty; no sample traffic, scores or timing values populate the live view.
The user still chooses an interface and deliberately presses Start.

## Verification

**Sixteen UI tests pass**, including replay stepping/stale-response handling,
reference/model disagreement, receipt acknowledgements before paint, bounded
display updates, automatic-Stop summaries, friendly interface IDs, searching,
guide behavior and malformed-input recovery. TypeScript/Vite production build,
Prettier and `git diff --check` pass. Backend Python sources are unchanged;
their preceding 295-test checkpoint was not rerun for this UI-only work.

```powershell
npm --prefix ui test
npm --prefix ui run build
npm --prefix ui run format:check
```

Actual browser checks on the served local app covered the empty desktop screen,
a 390×844 viewport (375-pixel content width after the scrollbar, with no
horizontal overflow), friendly native interface names, and recorded replay.
The existing nineteen-packet `experiments/full-real/benchmark-flow.json` loaded
and stepped from five to ten packets, displaying actual unchanged B17 output.
Invalid replay input displayed an error and a corrected recording recovered.
The displayed service estimate has no independent truth label in this visual
check; it is not an accuracy observation. Browser sizing was restored afterward.

Local preview files are private/ignored:

- `artifacts/local/ui-refresh-20261029/live-idle-desktop.jpg`
- `artifacts/local/ui-refresh-20261029/live-idle-mobile.jpg`
- `artifacts/local/ui-refresh-20261029/replay-desktop.jpg`

The service at `http://127.0.0.1:8001` serves the new production build. Refresh
the existing app tab to load it. B17 identity remains
`18c43fe12262b81d4a3001df150a278865f3908ddd3aab934822fc0c9e5750fb`.
No capture was started and no service restart was needed. Genuine window-panel
capture validation, new window delivery/paint measurements and the remaining
prospective data gates retain their prior pending status.
