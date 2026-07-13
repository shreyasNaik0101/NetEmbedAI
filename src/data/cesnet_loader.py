"""CESNET-QUIC22 loader → (N, 30, 3) per-packet sequences.

Pulls a bounded subset of the CESNET-QUIC22 dataset via `cesnet-datazoo` and
reshapes the per-packet information (PPI) into sequence tensors suitable for a
TCN / LSTM encoder.

PPI channels (from cesnet_datazoo.constants): IPT=0, DIR=1, SIZE=2 (QUIC is UDP,
so the push-flags channel is unused). We keep [IPT, DIR, SIZE] and transpose the
stored (3, 30) layout to (30, 3) = (timesteps, channels).

Downloading: instantiating `CESNET_QUIC22(..., size="XS")` triggers a ~2.7 GB
download to `data_root` on first run. Subsequent runs reuse the local file.

Usage:
    python -m src.data.cesnet_loader --topx 15 --train 60000 --test 20000
"""
from __future__ import annotations

import argparse
import os

import numpy as np

# Channel positions in the stored PPI array.
from cesnet_datazoo.constants import IPT_POS, DIR_POS, SIZE_POS

_KEEP_CHANNELS = [IPT_POS, DIR_POS, SIZE_POS]  # [0, 1, 2]

# Curated, traffic-type-diverse app set (Option 1): recognizable apps spanning
# streaming / social / messaging / cloud. Restricted to apps that are actually
# well-represented in the QUIC XS subsample (>700 train flows) — niche apps like
# gmail (mostly TLS), revolut, uber, ebay-kleinanzeigen had only 19-96 flows and
# were dropped after inspecting the real class distribution.
CURATED_APPS = [
    "youtube", "spotify",                                     # streaming/media
    "instagram", "tiktok", "snapchat",                        # social
    "whatsapp", "facebook-messenger", "discord",              # messaging
    "google-drive", "microsoft-outlook",                      # cloud/productivity
]

DEFAULT_DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cesnet")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")


def build_dataset(data_root: str, size: str = "XS"):
    """Instantiate the dataset. NOTE: triggers download on first call."""
    from cesnet_datazoo.datasets import CESNET_QUIC22

    return CESNET_QUIC22(data_root=os.path.abspath(data_root), size=size, silent=False)


def make_config(dataset, apps, train_size, val_size, test_size, seed: int = 42):
    """Config for a bounded, fixed-app subset with 3-channel PPI."""
    from cesnet_datazoo.config import DatasetConfig, AppSelection

    return DatasetConfig(
        dataset=dataset,
        apps_selection=AppSelection.FIXED,
        apps_selection_fixed_known=list(apps),
        apps_selection_fixed_unknown=[],
        train_period_name=dataset.default_train_period_name,
        test_period_name=dataset.default_test_period_name,
        train_size=train_size,
        val_known_size=val_size,
        test_known_size=test_size,
        use_push_flags=False,      # QUIC → keep PPI to [IPT, DIR, SIZE]
        use_packet_histograms=False,
        return_tensors=False,      # numpy in the dataframe PPI cells
        random_state=seed,
    )


def _ppi_to_seq(ppi_series) -> np.ndarray:
    """Stack a pandas Series of per-flow PPI arrays into (N, 30, 3) float32.

    Each cell is a (C, 30) array; we select [IPT, DIR, SIZE] and transpose to
    (30, 3). Flows already come zero-padded to 30 packets by the dataset.
    """
    seqs = np.stack([np.asarray(p, dtype=np.float32)[_KEEP_CHANNELS] for p in ppi_series])
    return np.transpose(seqs, (0, 2, 1))  # (N, 3, 30) -> (N, 30, 3)


def dataframe_to_arrays(df):
    """(dataframe) -> (X: (N,30,3) float32, y_raw: (N,) int64 encoder ids)."""
    from cesnet_datazoo.constants import PPI_COLUMN, APP_COLUMN

    X = _ppi_to_seq(df[PPI_COLUMN])
    y = df[APP_COLUMN].to_numpy().astype(np.int64)
    return X, y


def remap_labels(splits, names):
    """Remap encoder ids present across all splits to contiguous 0..C-1.

    Drops any class with zero samples (e.g. an app disabled for too few flows),
    keeping labels dense and names aligned to the new ids.

    Args:
        splits: list of (X, y_raw) tuples.
        names:  list of app names indexed by original encoder id.
    Returns:
        (remapped_splits, kept_names)
    """
    present = sorted(set(np.concatenate([y for _, y in splits]).tolist()))
    old_to_new = {old: new for new, old in enumerate(present)}
    kept_names = [names[old] for old in present]
    out = []
    for X, y in splits:
        out.append((X, np.array([old_to_new[v] for v in y], dtype=np.int64)))
    return out, kept_names


def main():
    ap = argparse.ArgumentParser(description="Build CESNET-QUIC22 packet-sequence subset")
    ap.add_argument("--data_root", default=DEFAULT_DATA_ROOT)
    ap.add_argument("--size", default="XS", choices=["XS", "S", "M", "L"])
    ap.add_argument("--apps", nargs="+", default=CURATED_APPS,
                    help="Fixed app list to keep (default: curated diverse set)")
    ap.add_argument("--train", type=int, default=60000)
    ap.add_argument("--val", type=int, default=15000)
    ap.add_argument("--test", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print(f"[1/4] Instantiating CESNET-QUIC22 (size={args.size}) - downloads ~2.7 GB on first run...")
    dataset = build_dataset(args.data_root, size=args.size)

    print(f"[2/4] Configuring subset: {len(args.apps)} fixed apps, "
          f"train={args.train} val={args.val} test={args.test}")
    print(f"      apps: {', '.join(args.apps)}")
    cfg = make_config(dataset, args.apps, args.train, args.val, args.test, args.seed)
    dataset.set_dataset_config_and_initialize(cfg)

    print("[3/4] Extracting dataframes -> (N, 30, 3) tensors...")
    Xtr, ytr = dataframe_to_arrays(dataset.get_train_df(flatten_ppi=False))
    Xva, yva = dataframe_to_arrays(dataset.get_val_df(flatten_ppi=False))
    Xte, yte = dataframe_to_arrays(dataset.get_test_df(flatten_ppi=False))

    # Class names in encoder-id order, then remap present labels to contiguous.
    names = list(dataset.get_known_apps())
    (splits, class_names) = remap_labels([(Xtr, ytr), (Xva, yva), (Xte, yte)], names)
    (Xtr, ytr), (Xva, yva), (Xte, yte) = splits

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "quic22_seq.npz")
    np.savez_compressed(out, Xtr=Xtr, ytr=ytr, Xva=Xva, yva=yva, Xte=Xte, yte=yte,
                        class_names=np.array(class_names))

    counts = np.bincount(ytr, minlength=len(class_names))
    print(f"[4/4] Saved {out}")
    print(f"      shapes: train {Xtr.shape}, val {Xva.shape}, test {Xte.shape}")
    print(f"      classes ({len(class_names)}):")
    for i, (nm, ct) in enumerate(zip(class_names, counts)):
        print(f"        {i:2d}  {nm:22s} {ct:6d}  ({ct / len(ytr) * 100:4.1f}%)")
    print(f"      imbalance ratio: {counts.max() / max(counts.min(), 1):.1f}x")


if __name__ == "__main__":
    main()
