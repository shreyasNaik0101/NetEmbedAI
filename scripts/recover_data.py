"""Resume into a separate file; preserve original incomplete data. Never captures traffic."""

import argparse
import shutil
import time
import urllib.request
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--seconds", type=int, default=300)
a = p.parse_args()
source = Path("data/cesnet/XS/CESNET-QUIC22-XS.h5")
target = Path("data/recovered/CESNET-QUIC22-XS.h5")
target.parent.mkdir(parents=True, exist_ok=True)
if not target.exists() and source.exists():
    shutil.copyfile(source, target)
start = target.stat().st_size if target.exists() else 0
url = "https://liberouter.org/datazoo/download?bucket=cesnet-quic22&file=CESNET-QUIC22-XS.h5"
request = urllib.request.Request(url, headers={"Range": f"bytes={start}-"})
deadline = time.monotonic() + a.seconds
with urllib.request.urlopen(request, timeout=30) as response:
    if start and (
        response.status != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {start}-")
    ):
        raise RuntimeError("Server did not honor resume; original and recovery files preserved")
    with target.open("ab") as output:
        while time.monotonic() < deadline:
            block = response.read(1024 * 1024)
            if not block:
                break
            output.write(block)
print(f"Recovery file: {target}; bytes={target.stat().st_size}; validate HDF5 before use")
