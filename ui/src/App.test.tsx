import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import App from "./App";
class WS {
  static OPEN = 1;
  static instances: WS[] = [];
  readyState = WS.OPEN;
  send = vi.fn();
  onopen: unknown;
  onclose: unknown;
  onmessage: unknown;
  constructor() {
    WS.instances.push(this);
  }
  close() {}
}
beforeEach(() => {
  sessionStorage.clear();
  WS.instances = [];
  vi.stubGlobal("WebSocket", WS);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => ({
      ok: true,
      json: async () =>
        url.endsWith("/model")
          ? {
              artifact_id: "software-fixture",
              labels: ["fixture-a", "fixture-b"],
            }
          : url.endsWith("/capture/interfaces")
            ? []
            : url.endsWith("/predict")
              ? {
                  label: "fixture-a",
                  status: "classified",
                  observed_packets: JSON.parse(String(init?.body)).packets
                    .length,
                  alternatives: [{ label: "fixture-a", score: 0.8 }],
                  pipeline_ms: 1,
                  artifact_id: "software-fixture",
                }
              : { status: "pending" },
    })),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("explains a withheld service outside the fitted acceptance scope", async () => {
  render(<App />);
  act(() =>
    (WS.instances[0].onmessage as (e: { data: string }) => void)({
      data: JSON.stringify({
        type: "prediction",
        flow_id: "scope-fixture",
        session_id: "fixture",
        status: "insufficient_confidence",
        label: null,
        decision_reason: "outside_policy_scope",
        observed_packets: 10,
        model_packets: 10,
        model_prefix_limit: 10,
        pipeline_ms: 1,
        artifact_id: "fixture",
        alternatives: [{ label: "whatsapp", score: 0.9 }],
        packets: [],
      }),
    }),
  );
  await waitFor(() =>
    expect(
      screen.getByText("Service outside this acceptance policy"),
    ).toBeInTheDocument(),
  );
  expect(
    screen.getByText(/top guess is outside the services checked/),
  ).toBeInTheDocument();
});
it("distinguishes fixed model budget from observed replay packets", async () => {
  const baseFetch = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input).endsWith("/model"))
      return {
        ok: true,
        json: async () => ({
          artifact_id: "fixed-ten-fixture",
          labels: ["spotify"],
          architecture: { fixed_prefix_packets: 10 },
        }),
      } as Response;
    if (String(input).endsWith("/predict")) {
      const n = JSON.parse(String(init?.body)).packets.length;
      return {
        ok: true,
        json: async () => ({
          artifact_id: "fixed-ten-fixture",
          observed_packets: n,
          model_prefix_limit: 10,
          model_packets: n < 10 ? 0 : 10,
          status: n < 10 ? "insufficient_evidence" : "insufficient_confidence",
          decision_reason: n < 10 ? "too_few_packets" : "policy_not_fitted",
          label: null,
          alternatives: n < 10 ? [] : [{ label: "spotify", score: 0.7 }],
          pipeline_ms: 1,
        }),
      } as Response;
    }
    return baseFetch(input, init);
  });
  render(<App />);
  await waitFor(() =>
    expect(
      screen.getByRole("note", { name: "Model packet budget" }),
    ).toHaveTextContent("Fixed 10-packet model"),
  );
  fireEvent.click(screen.getByRole("button", { name: "Recorded replay" }));
  fireEvent.change(screen.getByLabelText("Recorded flow JSON"), {
    target: {
      value: JSON.stringify({
        packets: Array.from({ length: 30 }, (_, i) => ({
          iat_ms: i ? 1 : 0,
          direction: 1,
          payload_bytes: 100,
        })),
      }),
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Load recording" }));
  await waitFor(() =>
    expect(
      screen.getByText(
        "Waiting for 10 packets; 5 observed. No model scores yet.",
      ),
    ).toBeInTheDocument(),
  );
  expect(screen.queryByText("70.0%")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "30 packets" }));
  await waitFor(() =>
    expect(
      screen.getByText(
        "Prediction uses the first 10 packets; 30 packets observed.",
      ),
    ).toBeInTheDocument(),
  );
  expect(
    screen.getByText(/Later packets do not add classification evidence/),
  ).toBeInTheDocument();
  expect(screen.getByText("70.0%")).toBeInTheDocument();
  expect(
    vi
      .mocked(fetch)
      .mock.calls.some((c) => String(c[0]).endsWith("/capture/start")),
  ).toBe(false);
});

it("explains an unfitted policy while retaining raw alternatives", async () => {
  const baseFetch = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/model"))
      return {
        ok: true,
        json: async () => ({
          artifact_id: "fixture-unfitted",
          labels: ["instagram"],
          policy: { fitted: false },
        }),
      } as Response;
    if (url.endsWith("/predict"))
      return {
        ok: true,
        json: async () => ({
          label: null,
          status: "insufficient_confidence",
          decision_reason: "policy_not_fitted",
          policy_fitted: false,
          observed_packets: 5,
          alternatives: [{ label: "instagram", score: 0.55 }],
          pipeline_ms: 1,
          artifact_id: "fixture-unfitted",
        }),
      } as Response;
    return baseFetch(input, init);
  });
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Recorded replay" }));
  fireEvent.change(screen.getByLabelText("Recorded flow JSON"), {
    target: {
      value: JSON.stringify({
        packets: Array.from({ length: 5 }, (_, i) => ({
          iat_ms: i ? 1 : 0,
          direction: 1,
          payload_bytes: 100,
        })),
      }),
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Load recording" }));
  await waitFor(() =>
    expect(
      screen.getByRole("heading", { name: "Confidence check pending" }),
    ).toBeInTheDocument(),
  );
  expect(
    screen.getByText(/acceptance policy has not been fitted/),
  ).toBeInTheDocument();
  expect(screen.getByText("55.0%")).toBeInTheDocument();
  expect(
    vi
      .mocked(fetch)
      .mock.calls.some((c) => String(c[0]).endsWith("/capture/start")),
  ).toBe(false);
});

it("offers bounded stopped-session downloads without another capture", async () => {
  const baseFetch = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input).endsWith("/capture/recent-sessions/stopped-one"))
      return {
        ok: true,
        json: async () => ({
          session_id: "stopped-one",
          capture: { fixture: true },
          timing: {},
          status: {},
        }),
      } as Response;
    return baseFetch(input, init);
  });
  class FixtureURL extends URL {
    static createObjectURL = vi.fn(() => "blob:fixture");
    static revokeObjectURL = vi.fn();
  }
  vi.stubGlobal("URL", FixtureURL);
  const download = vi
    .spyOn(HTMLAnchorElement.prototype, "click")
    .mockImplementation(() => {});
  try {
    render(<App />);
    act(() =>
      (WS.instances[0].onmessage as (e: { data: string }) => void)({
        data: JSON.stringify({
          type: "status",
          running: false,
          reason: "viewer heartbeat expired",
          recent_sessions: [
            {
              session_id: "stopped-one",
              reason: "viewer heartbeat expired",
              connections: 2,
              retained_packets: 57,
            },
          ],
        }),
      }),
    );
    expect(
      screen.getByText("Recent stopped recordings (1)"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/kept in memory through another Start/),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByText("Recent stopped recordings (1)"));
    fireEvent.click(screen.getByRole("button", { name: /Save stopped-/ }));
    await waitFor(() => expect(download).toHaveBeenCalledTimes(1));
    expect(
      vi
        .mocked(fetch)
        .mock.calls.some((c) =>
          String(c[0]).endsWith("/capture/recent-sessions/stopped-one"),
        ),
    ).toBe(true);
    expect(
      vi
        .mocked(fetch)
        .mock.calls.some((c) => String(c[0]).endsWith("/capture/start")),
    ).toBe(false);
  } finally {
    download.mockRestore();
  }
});

it("uses real prediction packet metadata and never shrinks to a delayed shorter update", async () => {
  render(<App />);
  const ws = WS.instances[0];
  const deliver = (v: unknown) =>
    (ws.onmessage as (e: { data: string }) => void)({
      data: JSON.stringify(v),
    });
  const packets = Array.from({ length: 30 }, (_, i) => ({
    iat_ms: i ? 1 : 0,
    direction: 1,
    payload_bytes: 100,
  }));
  act(() =>
    deliver({
      type: "prediction",
      session_id: "fixture",
      flow_id: "flow",
      sequence: 1,
      label: null,
      status: "insufficient_confidence",
      alternatives: [],
      pipeline_ms: 1,
      observed_packets: 30,
      packets,
    }),
  );
  await waitFor(() =>
    expect(
      screen.getByText("30/30 packets", { exact: false }),
    ).toBeInTheDocument(),
  );
  act(() =>
    deliver({
      type: "packets",
      session_id: "fixture",
      flow_id: "flow",
      packets: packets.slice(0, 5),
    }),
  );
  await act(async () => {
    await new Promise((r) => requestAnimationFrame(r));
  });
  expect(
    screen.getByText("30/30 packets", { exact: false }),
  ).toBeInTheDocument();
  expect(JSON.parse(ws.send.mock.calls[0][0]).sequence).toBe(1);
});

it("shows the actual stored scope of a public-only confidence policy", async () => {
  const baseFetch = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (String(input).endsWith("/model"))
      return {
        ok: true,
        json: async () => ({
          artifact_id: "fixture-public-policy",
          labels: ["fixture-a"],
          policy: { fitted: true, validation_scope: "cesnet_calibration_only" },
        }),
      } as Response;
    return baseFetch(input, init);
  });
  render(<App />);
  await waitFor(() =>
    expect(
      screen.getByText(
        /Acceptance threshold fitted on historical CESNET data only/,
      ),
    ).toBeInTheDocument(),
  );
  expect(
    screen.getByText(/Local acceptance quality still needs validation/),
  ).toBeInTheDocument();
});
it("remembers explicit reference opt-in on remount without starting capture", async () => {
  const first = render(<App />);
  expect(screen.getByText(/Reference evidence OFF:/)).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("checkbox", { name: /separate handshake reference/ }),
  );
  expect(screen.getByText(/Reference evidence ON/)).toBeInTheDocument();
  first.unmount();
  render(<App />);
  expect(
    screen.getByRole("checkbox", { name: /separate handshake reference/ }),
  ).toBeChecked();
  expect(
    vi
      .mocked(fetch)
      .mock.calls.filter((c) => String(c[0]).endsWith("/capture/start")),
  ).toHaveLength(0);
});
it("changes prefixes through API and renders actual returned result", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /Recorded replay/ }));
  const packets = Array.from({ length: 10 }, (_, i) => ({
    iat_ms: i ? 2 : 0,
    direction: 1,
    payload_bytes: 100,
  }));
  fireEvent.change(screen.getByLabelText("Recorded flow JSON"), {
    target: { value: JSON.stringify({ schema_version: "1", packets }) },
  });
  fireEvent.click(screen.getByRole("button", { name: "Load recording" }));
  await waitFor(() =>
    expect(screen.getByText("Prediction uses 5 packets.")).toBeInTheDocument(),
  );
  fireEvent.click(screen.getByRole("button", { name: "10 packets" }));
  await waitFor(() =>
    expect(screen.getByText("Prediction uses 10 packets.")).toBeInTheDocument(),
  );
  expect(screen.getByText("80.0%")).toBeInTheDocument();
  const calls = vi
    .mocked(fetch)
    .mock.calls.filter((c) => String(c[0]).endsWith("/predict"));
  expect(calls.length).toBe(2);
});

it("rejects malformed replay packets without crashing and accepts a corrected recording", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Recorded replay" }));
  const input = screen.getByLabelText("Recorded flow JSON");
  fireEvent.change(input, {
    target: { value: JSON.stringify({ packets: [{}] }) },
  });
  fireEvent.click(screen.getByRole("button", { name: "Load recording" }));
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Packet 1 needs a finite, nonnegative interval",
  );
  expect(
    screen.getByRole("heading", { name: "Waiting for evidence" }),
  ).toBeInTheDocument();
  expect(
    vi.mocked(fetch).mock.calls.some((c) => String(c[0]).endsWith("/predict")),
  ).toBe(false);
  fireEvent.change(input, {
    target: {
      value: JSON.stringify({
        schema_version: "1",
        packets: [{ iat_ms: 0, direction: 1, payload_bytes: 100 }],
      }),
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Load recording" }));
  await waitFor(() =>
    expect(screen.getByText("Prediction uses 1 packet.")).toBeInTheDocument(),
  );
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
it("keeps capture disabled without a selected interface or stream", async () => {
  render(<App />);
  expect(screen.getByRole("button", { name: "Start capture" })).toBeDisabled();
  expect(screen.getByText(/alone does not establish QUIC/)).toBeInTheDocument();
  expect(
    screen.getByRole("checkbox", { name: /separate handshake reference/ }),
  ).not.toBeChecked();
  expect(
    screen.getByRole("checkbox", { name: /experimental 1- and 3-second/ }),
  ).not.toBeChecked();
});

it("shows a getting-started guide without starting capture", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "How to use" }));
  expect(
    screen.getByRole("region", { name: "Getting started" }),
  ).toHaveTextContent("Choose your connection");
  expect(screen.getByRole("button", { name: "How to use" })).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  expect(
    vi
      .mocked(fetch)
      .mock.calls.some((c) => String(c[0]).endsWith("/capture/start")),
  ).toBe(false);
});

it("filters connections and switches analysis without changing the model output", async () => {
  render(<App />);
  const ws = WS.instances[0];
  const deliver = (value: unknown) =>
    (ws.onmessage as (e: { data: string }) => void)({
      data: JSON.stringify(value),
    });
  act(() => {
    for (const [id, label, count] of [
      ["flow-a", "youtube", 5],
      ["flow-b", "instagram", 10],
    ] as const) {
      deliver({
        type: "packets",
        session_id: "software-fixture",
        flow_id: id,
        packets: Array.from({ length: count }, (_, i) => ({
          iat_ms: i ? 1 : 0,
          direction: 1,
          payload_bytes: 100,
        })),
      });
      deliver({
        type: "prediction",
        session_id: "software-fixture",
        flow_id: id,
        sequence: count,
        label,
        status: "classified",
        observed_packets: count,
        alternatives: [{ label, score: 0.8 }],
        pipeline_ms: 1,
      });
    }
  });
  await waitFor(() =>
    expect(
      screen.getByRole("heading", { name: "YouTube" }),
    ).toBeInTheDocument(),
  );
  fireEvent.change(
    screen.getByRole("searchbox", { name: "Find a connection" }),
    { target: { value: "no-such-flow" } },
  );
  expect(screen.getByText("No matching connections")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "YouTube" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Clear search" }));
  expect(document.querySelectorAll("button.flow")).toHaveLength(2);
  fireEvent.change(
    screen.getByRole("searchbox", { name: "Find a connection" }),
    { target: { value: "instagram" } },
  );
  fireEvent.click(screen.getByRole("button", { name: /Instagram.*flow-b/ }));
  expect(
    screen.getByRole("heading", { name: "Instagram" }),
  ).toBeInTheDocument();
  expect(screen.getByText("Prediction uses 10 packets.")).toBeInTheDocument();
  expect(screen.getByText("80.0%")).toBeInTheDocument();
  expect(
    vi
      .mocked(fetch)
      .mock.calls.some(
        (c) =>
          String(c[0]).endsWith("/predict") ||
          String(c[0]).endsWith("/capture/start"),
      ),
  ).toBe(false);
});

it("shows a conflicting handshake reference without replacing the model prediction", async () => {
  render(<App />);
  const ws = WS.instances[0];
  const deliver = ws.onmessage as (event: { data: string }) => void;
  act(() => {
    deliver({
      data: JSON.stringify({
        type: "status",
        reference_enabled: true,
        running: false,
      }),
    });
    deliver({
      data: JSON.stringify({
        type: "prediction",
        session_id: "trial",
        sequence: 1,
        flow_id: "flow-1",
        label: "whatsapp",
        status: "classified",
        observed_packets: 30,
        pipeline_ms: 1,
        alternatives: [{ label: "whatsapp", score: 0.9 }],
        reference: { status: "mapped", label: "youtube" },
      }),
    });
  });
  await waitFor(() =>
    expect(
      screen.getByRole("heading", { name: "WhatsApp" }),
    ).toBeInTheDocument(),
  );
  expect(
    screen.getByRole("region", { name: "Separate handshake reference" }),
  ).toHaveTextContent("YouTube");
  expect(
    screen.getByText("Model differs from this reference."),
  ).toBeInTheDocument();
});

it("sends the reference opt-in only when selected before Start", async () => {
  const original = fetch;
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) =>
      url.endsWith("/capture/interfaces")
        ? Promise.resolve({
            ok: true,
            json: async () => [
              {
                id: "9",
                description: "\\Device\\NPF_{software-fixture} (Wi-Fi)",
              },
            ],
          })
        : url.endsWith("/capture/start")
          ? Promise.resolve({
              ok: true,
              json: async () => ({ session_id: "trial", running: true }),
            })
          : original(url, init),
    ),
  );
  render(<App />);
  await waitFor(() =>
    expect(screen.getByRole("option", { name: "Wi-Fi" })).toBeInTheDocument(),
  );
  act(() => (WS.instances[0].onopen as () => void)());
  fireEvent.change(screen.getByLabelText("Local interface"), {
    target: { value: "9" },
  });
  fireEvent.click(
    screen.getByRole("checkbox", { name: /separate handshake reference/ }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Start capture" }));
  await waitFor(() =>
    expect(
      vi
        .mocked(fetch)
        .mock.calls.some((c) => String(c[0]).endsWith("/capture/start")),
    ).toBe(true),
  );
  const call = vi
    .mocked(fetch)
    .mock.calls.find((c) => String(c[0]).endsWith("/capture/start"));
  expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
    interface: "9",
    reference_check: true,
    observation_windows: false,
  });
});

it("acknowledges a window on receipt without creating a model prediction", async () => {
  vi.stubGlobal(
    "requestAnimationFrame",
    vi.fn(() => 10),
  );
  render(<App />);
  const ws = WS.instances[0];
  act(() =>
    (ws.onmessage as (e: { data: string }) => void)({
      data: JSON.stringify({
        type: "observation",
        session_id: "trial",
        sequence: 11,
        flow_id: "window-flow",
        observation: {
          version: "software-fixture",
          quality: "unverified fixture",
          windows: [
            {
              horizon_ms: 3000,
              state: "elapsed",
              client_packets: 40,
              server_packets: 60,
              client_bytes: 12000,
              server_bytes: 72000,
              mean_payload_bytes: 840,
              late_packets_after_elapsed_snapshot: 0,
            },
          ],
        },
      }),
    }),
  );
  expect(ws.send).toHaveBeenCalledTimes(1);
  expect(JSON.parse(ws.send.mock.calls[0][0])).toMatchObject({
    session_id: "trial",
    event_type: "observation",
    sequence: 11,
  });
  // Receipt acknowledgement does not wait for a frame or claim display/paint.
  expect(
    screen.queryByRole("region", { name: "Experimental observation windows" }),
  ).not.toBeInTheDocument();
});

it("renders descriptive window metadata without creating a prediction", async () => {
  render(<App />);
  const ws = WS.instances[0];
  act(() =>
    (ws.onmessage as (e: { data: string }) => void)({
      data: JSON.stringify({
        type: "observation",
        session_id: "trial",
        sequence: 12,
        flow_id: "window-flow",
        observation: {
          version: "software-fixture",
          quality: "unverified fixture",
          windows: [
            {
              horizon_ms: 3000,
              state: "elapsed",
              client_packets: 40,
              server_packets: 60,
              client_bytes: 12000,
              server_bytes: 72000,
              mean_payload_bytes: 840,
              late_packets_after_elapsed_snapshot: 0,
            },
          ],
        },
      }),
    }),
  );
  await waitFor(() =>
    expect(
      screen.getByRole("region", { name: "Experimental observation windows" }),
    ).toHaveTextContent("100 packets"),
  );
  expect(screen.getByText("Waiting for evidence")).toBeInTheDocument();
  expect(ws.send).toHaveBeenCalledTimes(1);
});

it("loads separate delivery summaries when a session stops automatically", async () => {
  const original = fetch;
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) =>
      url.endsWith("/capture/summary")
        ? Promise.resolve({
            ok: true,
            json: async () => ({
              session_id: "auto-stop",
              browser_receipt_n: 4,
              browser_receipt_p50_ms: 200,
              browser_receipt_p95_ms: 300,
              observation_receipt_n: 8,
              observation_receipt_p50_ms: 25,
              observation_receipt_p95_ms: 50,
            }),
          })
        : original(url, init),
    ),
  );
  render(<App />);
  const deliver = WS.instances[0].onmessage as (e: { data: string }) => void;
  act(() =>
    deliver({
      data: JSON.stringify({
        type: "status",
        session_id: "auto-stop",
        running: false,
        reason: "capture duration limit reached",
      }),
    }),
  );
  await waitFor(() =>
    expect(
      screen.getByText(/Window event → browser receipt/),
    ).toHaveTextContent("25.0 ms"),
  );
  expect(screen.getByText(/Window event → browser receipt/)).toHaveTextContent(
    "does not measure paint",
  );
  expect(screen.getByText(/Capture → browser receipt/)).toHaveTextContent(
    "4 acknowledged predictions",
  );
});

it("ignores a stopped-session summary that finishes during the next session", async () => {
  const original = fetch;
  let finish: (response: unknown) => void = () => {};
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) =>
      url.endsWith("/capture/summary")
        ? new Promise((resolve) => {
            finish = resolve;
          })
        : original(url, init),
    ),
  );
  render(<App />);
  const deliver = WS.instances[0].onmessage as (e: { data: string }) => void;
  act(() =>
    deliver({
      data: JSON.stringify({
        type: "status",
        session_id: "old",
        running: false,
      }),
    }),
  );
  await waitFor(() =>
    expect(
      vi
        .mocked(fetch)
        .mock.calls.some((c) => String(c[0]).endsWith("/capture/summary")),
    ).toBe(true),
  );
  act(() =>
    deliver({
      data: JSON.stringify({
        type: "status",
        session_id: "new",
        running: true,
      }),
    }),
  );
  await act(async () => {
    finish({
      ok: true,
      json: async () => ({
        session_id: "old",
        observation_receipt_n: 9,
        observation_receipt_p50_ms: 999,
        observation_receipt_p95_ms: 999,
      }),
    });
  });
  expect(
    screen.queryByText(/Window event → browser receipt/),
  ).not.toBeInTheDocument();
});

it("acknowledges a prediction on receipt even without an animation frame", async () => {
  let paint: FrameRequestCallback = () => {};
  vi.stubGlobal(
    "requestAnimationFrame",
    vi.fn((callback) => {
      paint = callback;
      return 7;
    }),
  );
  render(<App />);
  const ws = WS.instances[0];
  act(() => {
    (ws.onmessage as (event: { data: string }) => void)({
      data: JSON.stringify({
        type: "prediction",
        session_id: "live-1",
        sequence: 7,
        flow_id: "flow-1",
        status: "insufficient_confidence",
        label: null,
        alternatives: [{ label: "whatsapp", score: 0.4 }],
        observed_packets: 5,
        pipeline_ms: 1,
      }),
    });
  });
  expect(ws.send).toHaveBeenCalledTimes(1);
  expect(JSON.parse(ws.send.mock.calls[0][0])).toMatchObject({ sequence: 7 });
  expect(screen.getByText("Waiting for evidence")).toBeInTheDocument();
  act(() => paint(0));
  expect(screen.getByText("No confident match yet")).toBeInTheDocument();
});

it("coalesces a packet burst for display while acknowledging every prediction", async () => {
  let paint: FrameRequestCallback = () => {};
  const schedule = vi.fn((callback) => {
    paint = callback;
    return 8;
  });
  vi.stubGlobal("requestAnimationFrame", schedule);
  render(<App />);
  const ws = WS.instances[0];
  const deliver = (value: unknown) =>
    (ws.onmessage as (event: { data: string }) => void)({
      data: JSON.stringify(value),
    });
  act(() => {
    for (let n = 1; n <= 30; n++) {
      deliver({
        type: "packets",
        session_id: "burst",
        flow_id: "flow-1",
        packets: Array.from({ length: n }, (_, i) => ({
          iat_ms: i ? 1 : 0,
          direction: 1,
          payload_bytes: 100,
        })),
      });
      if ([5, 10, 20, 30].includes(n))
        deliver({
          type: "prediction",
          session_id: "burst",
          flow_id: "flow-1",
          sequence: n,
          status: "insufficient_confidence",
          label: null,
          alternatives: [],
          observed_packets: n,
          pipeline_ms: 1,
        });
    }
  });
  expect(schedule).toHaveBeenCalledTimes(1);
  expect(
    ws.send.mock.calls.map((call) => JSON.parse(call[0]).sequence),
  ).toEqual([5, 10, 20, 30]);
  act(() => paint(0));
  expect(screen.getByText("Prediction uses 30 packets.")).toBeInTheDocument();
  expect(
    screen.getByText("30/30 packets", { exact: false }),
  ).toBeInTheDocument();
});

it("bounds pending display rows while the browser does not paint and cancels on unmount", async () => {
  let paint: FrameRequestCallback = () => {};
  vi.stubGlobal(
    "requestAnimationFrame",
    vi.fn((callback) => {
      paint = callback;
      return 9;
    }),
  );
  const cancel = vi.fn();
  vi.stubGlobal("cancelAnimationFrame", cancel);
  const app = render(<App />);
  const ws = WS.instances[0];
  const deliver = ws.onmessage as (event: { data: string }) => void;
  act(() => {
    for (let n = 0; n < 300; n++)
      deliver({
        data: JSON.stringify({
          type: "packets",
          session_id: "burst",
          flow_id: "flow-" + n,
          packets: [{ iat_ms: 0, direction: 1, payload_bytes: 100 }],
        }),
      });
    paint(0);
  });
  expect(app.container.querySelectorAll("button.flow")).toHaveLength(256);
  expect(screen.queryByText("flow-0")).not.toBeInTheDocument();
  act(() =>
    deliver({
      data: JSON.stringify({
        type: "packets",
        session_id: "burst",
        flow_id: "later",
        packets: [],
      }),
    }),
  );
  act(() => paint(0));
  await waitFor(() =>
    expect(screen.getByRole("button", { name: /flow-45 / })).toHaveAttribute(
      "aria-pressed",
      "true",
    ),
  );
  act(() =>
    deliver({
      data: JSON.stringify({
        type: "packets",
        session_id: "burst",
        flow_id: "last-pending",
        packets: [],
      }),
    }),
  );
  app.unmount();
  expect(cancel).toHaveBeenCalledWith(9);
});
it("shows backend failure without a fake prediction", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: false,
      json: async () => ({ detail: "Model missing" }),
    })),
  );
  render(<App />);
  await waitFor(() =>
    expect(screen.getByRole("alert")).toHaveTextContent("Model missing"),
  );
  expect(screen.getByText("Waiting for evidence")).toBeInTheDocument();
});

it("ignores an older prediction that arrives after the next prefix", async () => {
  const pending: ((v: unknown) => void)[] = [];
  const original = fetch;
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) =>
      String(url).endsWith("/predict")
        ? new Promise((resolve) => pending.push(resolve))
        : original(url, init),
    ),
  );
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /Recorded replay/ }));
  const packets = Array.from({ length: 10 }, (_, i) => ({
    iat_ms: i ? 2 : 0,
    direction: 1,
    payload_bytes: 100,
  }));
  fireEvent.change(screen.getByLabelText("Recorded flow JSON"), {
    target: { value: JSON.stringify({ packets }) },
  });
  fireEvent.click(screen.getByRole("button", { name: "Load recording" }));
  await waitFor(() => expect(pending.length).toBe(1));
  fireEvent.click(screen.getByRole("button", { name: "10 packets" }));
  await waitFor(() => expect(pending.length).toBe(2));
  const response = (n: number) => ({
    ok: true,
    json: async () => ({
      status: "classified",
      label: "prefix-" + n,
      observed_packets: n,
      alternatives: [],
      pipeline_ms: 1,
      artifact_id: "fixture",
    }),
  });
  pending[1](response(10));
  await waitFor(() =>
    expect(screen.getByText("prefix-10")).toBeInTheDocument(),
  );
  pending[0](response(5));
  await new Promise((r) => setTimeout(r, 20));
  expect(screen.queryByText("prefix-5")).not.toBeInTheDocument();
});

it("reconnects on request without starting capture", async () => {
  render(<App />);
  const first = WS.instances[0];
  act(() => (first.onclose as () => void)());
  fireEvent.click(screen.getByRole("button", { name: "Reconnect" }));
  expect(WS.instances).toHaveLength(2);
  expect(first.onmessage).toBeNull();
  expect(first.onclose).toBeNull();
  act(() => (WS.instances[1].onopen as () => void)());
  expect(screen.getByText("Stream connected")).toBeInTheDocument();
  expect(
    vi
      .mocked(fetch)
      .mock.calls.some((c) => String(c[0]).endsWith("/capture/start")),
  ).toBe(false);
});

it("explains an existing viewer and stops automatic conflict retries", () => {
  vi.useFakeTimers();
  try {
    render(<App />);
    act(() =>
      (WS.instances[0].onclose as (e: { code: number }) => void)({
        code: 4009,
      }),
    );
    expect(
      screen.getByText("Another app window is connected"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/VS Code previews, then click Reconnect/),
    ).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(60000));
    expect(WS.instances).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Reconnect" }));
    expect(WS.instances).toHaveLength(2);
    expect(
      vi
        .mocked(fetch)
        .mock.calls.some((c) => String(c[0]).endsWith("/capture/start")),
    ).toBe(false);
  } finally {
    vi.useRealTimers();
  }
});

it("answers server heartbeats without browser timers or animation frames", () => {
  vi.useFakeTimers();
  try {
    const app = render(<App />);
    const ws = WS.instances[0];
    act(() => vi.advanceTimersByTime(60000));
    expect(ws.send).not.toHaveBeenCalled();
    const wasHidden = vi
      .spyOn(document, "visibilityState", "get")
      .mockReturnValue("hidden");
    try {
      for (let i = 0; i < 2; i++)
        act(() =>
          (ws.onmessage as (e: { data: string }) => void)({
            data: JSON.stringify({ type: "heartbeat" }),
          }),
        );
      expect(ws.send.mock.calls.map((c) => JSON.parse(c[0]))).toEqual([
        { type: "heartbeat" },
        { type: "heartbeat" },
      ]);
    } finally {
      wasHidden.mockRestore();
    }
    app.unmount();
    act(() => vi.advanceTimersByTime(6000));
    expect(ws.send).toHaveBeenCalledTimes(2);
    expect(ws.onmessage).toBeNull();
  } finally {
    vi.useRealTimers();
  }
});

it("retries temporary viewer rejection with a finite backoff and no capture", () => {
  vi.useFakeTimers();
  try {
    const app = render(<App />);
    for (const delay of [500, 1000, 2000, 4000, 8000]) {
      const before = WS.instances.length;
      act(() => (WS.instances.at(-1)!.onclose as () => void)());
      expect(screen.getByText("Reconnecting…")).toBeInTheDocument();
      act(() => vi.advanceTimersByTime(delay));
      expect(WS.instances.length).toBe(before + 1);
    }
    act(() => (WS.instances.at(-1)!.onclose as () => void)());
    act(() => vi.advanceTimersByTime(30000));
    expect(WS.instances).toHaveLength(6);
    expect(
      vi
        .mocked(fetch)
        .mock.calls.some((c) => String(c[0]).endsWith("/capture/start")),
    ).toBe(false);
    app.unmount();
  } finally {
    vi.useRealTimers();
  }
});

it("cancels a pending reconnect when the viewer unmounts", () => {
  vi.useFakeTimers();
  try {
    const app = render(<App />);
    act(() => (WS.instances[0].onclose as () => void)());
    app.unmount();
    act(() => vi.advanceTimersByTime(30000));
    expect(WS.instances).toHaveLength(1);
  } finally {
    vi.useRealTimers();
  }
});
