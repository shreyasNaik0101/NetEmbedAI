"""Bounded matched training; final test is never opened here."""

import copy
import hashlib
import json
import platform
import subprocess
import time
import uuid
from pathlib import Path
import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from .bundle import Predictor, export_bundle, sha256, write_json
from .contract import BUDGETS, Normalizer, summary
from .data import read_split
from .evaluation import STRESS, fit_policy
from .models import Classifier, supcon
from .transforms import perturb

DEFAULT = {
    "kind": "tcn",
    "loss": "ce",
    "augmentation": False,
    "augmentation_policy": "single-edit-50-clean-v1",
    "seed": 17,
    "epochs": 20,
    "batch_size": 128,
    "learning_rate": 0.001,
    "supcon_weight": 0.5,
    "threads": 4,
    "architecture": {"hidden": 64, "levels": 4, "embedding_dim": 32},
    "patience": 5,
    "clean_floor": None,
}


def augment_one(raw, sample_id, epoch, seed):
    """Same per-flow, per-epoch choice for matched CE and SupCon runs."""
    key = hashlib.sha256(f"{seed}:{sample_id}:{epoch}:single-edit-50-clean-v1".encode()).digest()
    slot = int.from_bytes(key[:8], "big") % 6
    if slot < 3:
        return raw, "clean"
    kind = ("timing", "padding", "observation_loss")[slot - 3]
    return perturb(raw, kind, STRESS[kind], seed, f"{sample_id}:{epoch}")[0], kind


def train(directory, destination, supplied, resume=None):
    cfg = {**DEFAULT, **supplied}
    if cfg["kind"] not in ("tcn", "forest") or cfg["loss"] not in ("ce", "supcon"):
        raise ValueError("unsupported candidate")
    if cfg["epochs"] < 1 or cfg["batch_size"] < 2:
        raise ValueError("invalid budget")
    if cfg["augmentation_policy"] != "single-edit-50-clean-v1":
        raise ValueError("unsupported augmentation policy")
    if (cfg["augmentation"] or cfg["loss"] == "supcon") and cfg["clean_floor"] is None:
        raise ValueError("declare clean_floor from reproduced supervised development baseline first")
    torch.set_num_threads(cfg["threads"])
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(cfg["seed"])
    flows, y, ids, manifest = read_split(directory, "train")
    dev, dy, dids, _ = read_split(directory, "selection")
    calibration, cy, _, _ = read_split(directory, "calibration")
    normalizer = Normalizer.fit(flows)
    labels = manifest["labels"]
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    out = Path(destination) / run_id
    out.mkdir(parents=True)
    seeds = {
        "initialization": cfg["seed"],
        "loader_prefix": cfg["seed"] + 1000,
        "augmentation": cfg["seed"] + 2000,
        "split": 17,
        "evaluation_stress": 2026,
    }
    rng = np.random.default_rng(seeds["loader_prefix"])
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    provenance = {
        "run_id": run_id,
        "fixture": bool(manifest["source"].get("fixture", False)),
        "config": cfg,
        "seeds": seeds,
        "source_commit": commit,
        "data_manifest_sha256": sha256(Path(directory) / "manifest.json"),
        "normalizer_fit": "train only",
        "hardware": platform.platform(),
        "license": manifest["source"]["license"],
        "data": manifest["source"],
        "augmentation_policy": {
            "version": cfg["augmentation_policy"],
            "slots": ["clean", "clean", "clean", "timing", "padding", "observation_loss"],
            "stresses": STRESS,
        },
    }
    provenance["source_files"] = {
        str(f.relative_to(Path(__file__).parent)): sha256(f) for f in Path(__file__).parent.rglob("*.py")
    }
    write_json(out / "config.json", provenance)
    started = time.perf_counter()
    history = []
    if cfg["kind"] == "forest":
        if cfg["loss"] != "ce" or cfg["augmentation"]:
            raise ValueError("forest baseline has no neural loss/augmentation")
        rows, targets = [], []
        for x, label in zip(flows, y):
            for budget in BUDGETS:
                rows.append(summary(x[:budget]))
                targets.append(label)
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=18,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=cfg["seed"],
            n_jobs=cfg["threads"],
        )
        model.fit(rows, targets)
    else:
        model = Classifier(len(labels), **cfg["architecture"])
        optimizer = torch.optim.Adam(model.parameters(), lr=cfg["learning_rate"])
        counts = np.bincount(y, minlength=len(labels))
        weights = np.sqrt(len(y) / (len(labels) * counts))
        ce = torch.nn.CrossEntropyLoss(weight=torch.tensor(weights / weights.mean(), dtype=torch.float32))
        best, best_state, waiting, first = -1.0, None, 0, 0
        if resume:
            state = torch.load(resume, weights_only=False, map_location="cpu")
            if state["config"] != cfg or state["data"] != provenance["data_manifest_sha256"]:
                raise ValueError("resume configuration/data mismatch")
            model.load_state_dict(state["model"])
            optimizer.load_state_dict(state["optimizer"])
            rng.bit_generator.state = state["numpy_rng"]
            torch.set_rng_state(state["torch_rng"])
            first, best, best_state, waiting, history = (
                state["epoch"],
                state["best"],
                state["best_state"],
                state["waiting"],
                state["history"],
            )
            if best_state is None:
                waiting = 0
        validation_cases = []
        for budget in BUDGETS:
            for kind, strength in STRESS.items():
                xs = [
                    x[:budget] if strength is None else perturb(x[:budget], kind, strength, 2026, ident)[0]
                    for x, ident in zip(dev, dids)
                ]
                batches = []
                for start in range(0, len(xs), 128):
                    x, lengths = normalizer.batch(xs[start : start + 128])
                    batches.append((torch.from_numpy(x), torch.from_numpy(lengths)))
                validation_cases.append((kind, batches))
        for epoch in range(first, cfg["epochs"]):
            model.train()
            losses = []
            order = rng.permutation(len(flows))
            for start in range(0, len(order), cfg["batch_size"]):
                idx = order[start : start + cfg["batch_size"]]
                batch = [flows[i][: int(rng.choice(BUDGETS))].copy() for i in idx]
                if cfg["augmentation"]:
                    for j, i in enumerate(idx):
                        batch[j], _ = augment_one(batch[j], ids[i], epoch, seeds["augmentation"])
                x, lengths = normalizer.batch(batch)
                logits, embedding = model(torch.from_numpy(x), torch.from_numpy(lengths))
                targets = torch.from_numpy(y[idx])
                loss = ce(logits, targets)
                if cfg["loss"] == "supcon":
                    loss = loss + cfg["supcon_weight"] * supcon(embedding, targets)
                if not torch.isfinite(loss):
                    raise ValueError("nonfinite training loss")
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                losses.append(loss.item())
            model.eval()
            scores, clean_scores = [], []
            with torch.inference_mode():
                for kind, batches in validation_cases:
                    preds = []
                    for x, lengths in batches:
                        logits, _ = model(x, lengths)
                        preds.extend(logits.argmax(1).tolist())
                    score = f1_score(dy, preds, average="macro", zero_division=0)
                    scores.append(score)
                    if kind == "clean":
                        clean_scores.append(score)
            score = float(np.mean(scores))
            history.append(
                {
                    "epoch": epoch + 1,
                    "loss": float(np.mean(losses)),
                    "selection_score": score,
                    "clean_macro_f1": float(np.mean(clean_scores)),
                }
            )
            eligible = cfg["clean_floor"] is None or float(np.mean(clean_scores)) >= cfg["clean_floor"]
            if score > best and eligible:
                best, best_state, waiting = score, copy.deepcopy(model.state_dict()), 0
            elif best_state is not None:
                waiting += 1
            torch.save(
                {
                    "config": cfg,
                    "data": provenance["data_manifest_sha256"],
                    "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "numpy_rng": rng.bit_generator.state,
                    "torch_rng": torch.get_rng_state(),
                    "epoch": epoch + 1,
                    "best": best,
                    "best_state": best_state,
                    "waiting": waiting,
                    "history": history,
                },
                out / "resume.pt",
            )
            write_json(out / "history.json", history)
            print(json.dumps(history[-1]), flush=True)
            if best_state is not None and waiting >= cfg["patience"]:
                break
        if best_state is None:
            write_json(
                out / "failure.json",
                {
                    "reason": "no epoch met predeclared clean floor",
                    "clean_floor": cfg["clean_floor"],
                    "best_clean_macro_f1": max(h["clean_macro_f1"] for h in history),
                    "epochs_completed": len(history),
                },
            )
            raise ValueError("no epoch meets predeclared clean floor")
        model.load_state_dict(best_state)
        provenance["selection_score"] = best
        provenance["best_epoch"] = max(
            (h for h in history if cfg["clean_floor"] is None or h["clean_macro_f1"] >= cfg["clean_floor"]),
            key=lambda h: h["selection_score"],
        )["epoch"]
    provenance["seconds"] = time.perf_counter() - started
    arch = cfg["architecture"] if cfg["kind"] == "tcn" else {}
    draft = export_bundle(out / "uncalibrated", model, normalizer, labels, provenance, arch)
    policy = fit_policy(Predictor(draft, allow_fixture=provenance["fixture"]), calibration, cy)
    export_bundle(out / "bundle", model, normalizer, labels, provenance, arch, policy)
    write_json(out / "result.json", provenance)
    return str(out)
