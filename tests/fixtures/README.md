# Offline protocol fixture

rfc9001.pcap is constructed, not captured traffic. It wraps RFC 9001 Appendix A.2 client Initial (1,200 bytes), A.3 server Initial (135 bytes), and a repeated client Initial in generated Ethernet/IPv4/UDP headers using documentation-only addresses. Assigned relative times are 0, 8.5, and 10 ms. No packets are transmitted. Expected raw output is [[0,+1,1200],[8.5,-1,135],[1.5,+1,1200]].

On 25 October 2026, independent ipfixprobe 5.8.0 PSTATS/text export matched these
raw features and TShark's adapter within `1e-7`. Actual exporter output and bound
provenance are `rfc9001.ipfixprobe.stdout.txt` and
`rfc9001.ipfixprobe-reference.json`. See [the offline reproduction guide](../../tools/parity/README.md).
This verifies a current independent exporter on this constructed fixture only;
it does not establish parity for a real captured trace, historical 2022 CSV timing
quantization, or local service accuracy. The fixture and generated reference do
not contain actual user traffic or trained-model benchmark evidence.

## Variable-header regression fixture

`encapsulation.pcap` reuses only the above public RFC payload vectors. It contains
four constructed flows (12 packets): plain IPv4, IPv4 with variable VLAN/options,
plain IPv6, and IPv6 with variable VLAN/hop-by-hop extension headers. All four
must yield exactly `[[0,+1,1200],[8.5,-1,135],[1.5,+1,1200]]`, at epoch-sized
timestamps. Link/IP overhead varies within flows, preventing a constant header
subtraction from passing as transport-payload size extraction. IPv4 and UDP
checksums are valid, including mandatory IPv6 UDP checksums. No packets are sent.

The regression design was informed by a related-project review; this builder is
new NetEmbedAI code using the already committed public RFC fixture, not copied
private capture data or proprietary source. Fixture SHA-256:
`c67fdebdaa7b3e71d5aebc5207a52dc3e647b3da748e8b590bb502580317e06d`.
Reproduce to a new destination (existing files are never overwritten):

~~~powershell
.venv/Scripts/python.exe scripts/build_encapsulation_fixture.py --output artifacts/local/encapsulation-copy.pcap
.venv/Scripts/python.exe -m pytest tests/test_encapsulation.py -q
~~~

The pure byte/checksum tests always run. Actual TShark extraction tests explicitly
skip if the native executable is unavailable; they passed locally. This is an
offline software contract test, not captured traffic, model accuracy, or a live
validation result. The RFC attribution and license below apply to both fixtures.

## Longer-window regression fixture

`windows.pcap` is also constructed, never captured or transmitted. It reuses the
same public RFC vectors and four encapsulations, interleaving 66 datagrams per
flow (264 total) at assigned times through 3.1 seconds. Exact one-/three-second
boundaries exercise half-open windows. Each flow contains 61 observations before
one second and 64 before three seconds; its model input remains the first thirty.
An independent construction oracle checks directional counts, transport bytes,
size moments, switches and all 100 ms bins against native TShark and the live
flow builder. An early-EOF variant must remain partial. This is a software parity
check, not independent real-capture parity, service accuracy or live timing.
SHA-256: `0e650ab918445e577608cb603b49cbddc071f98b0b5dc920695193528d22afa0`.

```powershell
.venv/Scripts/python.exe -m scripts.build_window_fixture --output artifacts/local/windows-copy.pcap
.venv/Scripts/python.exe -m netembed.cli capture-file --pcap artifacts/local/windows-copy.pcap --output artifacts/local/windows-copy.json --observation-windows
.venv/Scripts/python.exe -m pytest tests/test_window_pcap.py -q
```

The builder refuses an existing output. Offline extraction uses recorded times
and never opens an interface; a ten-second deadline covers reading as well as
process exit. Native tests explicitly skip when TShark is absent. The pure fixture
rebuild/oracle check always runs. The following RFC attribution/license covers
all three constructed fixtures.

Source: https://www.rfc-editor.org/rfc/rfc9001.html#appendix-A
Copyright (c) 2021 IETF Trust and the persons identified as document authors. All rights reserved.

Code components extracted from RFC 9001 are under the Revised BSD License in section 4.e of https://trustee.ietf.org/license-info/.
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of Internet Society, IETF or IETF Trust, nor the names of specific contributors, may be used to endorse or promote products derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
