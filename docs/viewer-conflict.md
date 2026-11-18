# Edge rejected while a VS Code preview owns the stream

On9 November, the service was healthy and capture was idle, but Edge repeatedly displayed App connection lost. The server logged successful viewer admission followed by repeated HTTP403 WebSocket rejections. Windows UI inspection showed one Edge tab with Stream disconnected and two NetEmbedAI browser-preview editor tabs inside VS Code; the visible embedded preview showed Stream connected. This identifies a competing viewer for this incident, not a failed inference model or missing capture permissions. It does not establish the cause of every earlier interruption.

The application intentionally supports one event-stream/session owner. A healthy background preview can therefore keep ownership while a second browser window is rejected. Refreshing only the rejected Edge page cannot release the preview. The user must close both NetEmbedAI preview tabs inside VS Code, leaving the modified notebook open, and reconnect the existing Edge tab. Desktop control attempts did not close those previews; no notebook was closed or edited. After the user reported connected, the Edge UI visibly showed Stream connected and Capture is off; the service confirmed a healthy owner before the controlled delivery check.

## Clearer admission and recovery

Allowed-origin competing viewers now complete the WebSocket handshake and receive a close with code4009 and an explicit ownership-conflict reason. A pre-accept denial previously appeared to the browser as an opaque HTTP403/connection failure. The rejected viewer is never registered as an owner and never stops the existing viewer/capture.

The UI now displays Another app window is connected, explains that VS Code previews also count, and retains a manual Reconnect control. It stops automatic conflict retries because they cannot release a healthy owner. Temporary previous-viewer cleanup gets1013 and continues using the existing bounded retry policy. Invalid origins still fail before acceptance; capture does not start on any reconnect or conflict. The one-viewer policy and explicit user Start remain unchanged.

The service status exposes viewer_connected and viewer_cleanup, so future diagnosis need not guess from an aggregate disconnect message. The service was reloaded only after verifying that it had no capture session or active collection. Model weights, policy and the blocked prospective-study state are unchanged. The prepared one-attempt delivery check has not started and is not consumed by this admission error.

## Verification

569 Python tests pass with the two existing dependency warnings.27 UI tests and the production build pass; active lint,156-file Python formatting and UI formatting pass. The API contract test confirms that a second viewer gets4009 while the first remains connected. The UI test verifies the conflict explanation, absence of automatic retry loops, working manual Reconnect and no capture Start. It caught a missing Reconnect button for the new reason state; that rendering condition was corrected before the passing run.

These tests verify software behavior. The actual Edge UI was subsequently verified connected. The later controlled delivery check is documented separately in delivery-check-v1.md; this viewer-conflict fix alone supplies no classification-quality result.
