"""Export and assess the declared fixed-ten mode without fitting or capture."""

import json
from netembed.ten_packet import run

if __name__ == "__main__":
    print(json.dumps(run("configs/spotify-ten-packet-v1.json"), indent=2))
