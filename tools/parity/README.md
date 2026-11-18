# Optional independent offline exporter reference

Docker is used only for this developer reference check; running NetEmbedAI does
not require it. No command here opens a live interface or transmits the fixture.

The Dockerfile adapts [CESNET's container instructions](https://github.com/CESNET/ipfixprobe/blob/ee200bcef5ae23648089bbf6c2fad90c3ae6a5b3/docker/Dockerfile)
using the same official COPR and EPEL repositories. It pins Rocky Linux's base
digest and `ipfixprobe` / `ipfixprobe-input-pcap` to
`5.8.0-20260901120711.el9`. Dependencies install inside the image only.
Repository availability is still required for a new build; unavailable pinned
packages must fail rather than silently choose a different version. The full RPM
manifest is stored at `/usr/share/netembed-package-manifest.txt` in the image.

From the repository root:

~~~powershell
docker build --progress plain -t netembed-ipfixprobe-parity:local tools/parity
.venv/Scripts/python.exe scripts/check_ipfixprobe_fixture.py --image netembed-ipfixprobe-parity:local --output artifacts/local/ipfixprobe/parity-new.json
~~~

The checker requires an existing explicitly named local image and never pulls or
builds one. It verifies the known RFC PCAP checksum, mounts its directory read-only,
uses the `pcap;file=...` input with PSTATS/text output and runs as UID 65534 with all
capabilities dropped, no network, a read-only root filesystem, a 512 MiB memory
limit and one CPU. Each exporter invocation is time-bounded; containers auto-remove.
The output report and stdout path must be new so previous evidence is preserved.

The successful 25 October 2026 run used ipfixprobe 5.8.0 and local image digest
`sha256:461d082e71bffe2304d60ba2f409bb2e00002d1dd83d1eca0c46ef0a3781ea61`.
The raw exporter output has SHA-256
`4c557358b427087ce811194bb54b85fed40366888a6c462c3f5a6b084b795429`.
Its packet sizes, directions and reconstructed millisecond gaps match TShark's
adapter within `1e-7`: `[0,+1,1200]`, `[8.5,-1,135]`, `[1.5,+1,1200]`.
The committed [reference report](../../tests/fixtures/rfc9001.ipfixprobe-reference.json)
and [raw output](../../tests/fixtures/rfc9001.ipfixprobe.stdout.txt) preserve that
actual run, and the normal tests bind them to the PCAP hash and parser output.

PSTATS text writes timestamps as integer seconds, a dot, then **unpadded integer
microseconds**. `100.8500` means 100 seconds plus 8,500 microseconds, not the decimal
100.8500 seconds. The parser follows the exporter's
[get_text implementation](https://github.com/CESNET/ipfixprobe/blob/ee200bcef5ae23648089bbf6c2fad90c3ae6a5b3/src/plugins/process/pstats/src/pstats.hpp).

This is an independently exported constructed protocol fixture, not captured user
traffic or a model-quality result. Current 5.8.0 PSTATS timestamp handling does not
prove the historical 2022 CSV conversion's integer-millisecond quantization.
Independent comparison on a real authorized captured trace and local service
quality still require evidence. Rebuilding the image can change image/dependency
bytes; the report records the actual image ID and exporter version for each run.

For a small authorized existing recording prefix, the helper also accepts
`--pcap PATH --source-description TEXT`. It caps the file at 16 MiB and mounts
only that file read-only, with the same no-network/no-capture constraints. Its
report distinguishes recordings from constructed fixtures; provenance is not
inferred from filenames. See [the recorded-prefix investigation](../../docs/local-diagnosis.md)
for source/frame hashes, the timing precision correction and exact independent
comparison, plus the remaining provenance and quality limits.
