"""Run the fixed three-weight offline study, never capture or deployment."""

import json
from netembed.spotify_weights import run

if __name__ == "__main__":
    print(json.dumps(run("configs/spotify-weight-study-v1.json"), indent=2))
