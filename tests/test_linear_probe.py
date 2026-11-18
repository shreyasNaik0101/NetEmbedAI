import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from netembed import linear_probe as module
from netembed.bundle import sha256
from netembed.linear_probe import DIMENSIONS, LinearProbe, PoolEncoder
from netembed.linear_probe_study import guard_for, prefix_training, protected_input, read_config


class ToyBackbone(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.cnn_ppi_global_pool = torch.nn.Identity()
        self.mlp_shared = torch.nn.Linear(DIMENSIONS, DIMENSIONS)

    def forward(self, x):
        pooled = x.mean((1, 2))[:, None].expand(-1, DIMENSIONS)
        return self.mlp_shared(self.cnn_ppi_global_pool(pooled))


class ToyWrapper(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone_model = ToyBackbone()

    def forward(self, x):
        return self.backbone_model(x)[:, :256]


def toy_encoder():
    encoder = PoolEncoder.__new__(PoolEncoder)
    encoder.model = ToyWrapper().eval().requires_grad_(False)
    encoder.transform = lambda x: x
    return encoder


def test_pool_tap_is_before_refinement_and_hooks_are_removed(raw):
    encoder = toy_encoder()
    before = {k: v.clone() for k, v in encoder.model.state_dict().items()}
    values = encoder.encode([raw, raw[:2]])
    expected = np.array([raw.sum(), raw[:2].sum()]) / 90
    np.testing.assert_allclose(values[:, 0], expected)
    assert values.shape == (2, 448)
    assert not encoder.model.backbone_model.cnn_ppi_global_pool._forward_hooks
    assert not encoder.model.backbone_model.mlp_shared._forward_pre_hooks
    assert all(torch.equal(v, encoder.model.state_dict()[k]) for k, v in before.items())
    # Mutating only refinement cannot change the extracted representation.
    with torch.no_grad():
        encoder.model.backbone_model.mlp_shared.bias.fill_(100)
    np.testing.assert_array_equal(values, encoder.encode([raw, raw[:2]]))


def test_pool_cleans_hooks_on_error_and_refuses_training_mode(raw):
    encoder = toy_encoder()
    encoder.transform = lambda x: (_ for _ in ()).throw(ValueError("probe error"))
    with pytest.raises(ValueError, match="probe error"):
        encoder.encode([raw])
    assert not encoder.model.backbone_model.cnn_ppi_global_pool._forward_hooks
    assert not encoder.model.backbone_model.mlp_shared._forward_pre_hooks
    encoder.model.train()
    with pytest.raises(ValueError, match="evaluation mode"):
        encoder.encode([raw])


def test_portable_head_matches_sklearn_and_never_accepts(raw):
    rng = np.random.default_rng(17)
    x = rng.normal(size=(18, DIMENSIONS))
    y = np.arange(len(x)) % 3
    scaler = StandardScaler().fit(x)
    head = LogisticRegression().fit(scaler.transform(x), y)
    encoder = SimpleNamespace(encode=lambda flows: np.repeat(x[:1], len(flows), axis=0))
    model = LinearProbe(encoder, ["a", "b", "c"], scaler.mean_, scaler.scale_, head.coef_, head.intercept_)
    np.testing.assert_allclose(model.from_features(x), head.predict_proba(scaler.transform(x)), atol=1e-12)
    assert model.predict(raw)["label"] is None
    assert model.predict(raw)["status"] == "uncalibrated"
    assert model.predict(raw[:2])["status"] == "insufficient_evidence"
    with pytest.raises(ValueError, match="invalid"):
        model.from_features(np.full((1, DIMENSIONS), np.nan))
    with pytest.raises(ValueError, match="invalid"):
        LinearProbe(encoder, ["a", "b", "c"], scaler.mean_, np.zeros(DIMENSIONS), head.coef_, head.intercept_)


def test_each_training_flow_keeps_its_mass_and_actual_prefix(raw):
    flows, targets, weights = prefix_training([raw, raw[:2]], [0, 1], np.array([3.0, 1.0]))
    assert [len(x) for x in flows] == [5, 2] * 4
    np.testing.assert_array_equal(targets, [0, 1] * 4)
    assert weights[targets == 0].sum() == 3
    assert weights[targets == 1].sum() == 1


@pytest.mark.parametrize(
    "path",
    [
        "x/instagram-cal-01-reference.json",
        "x/youtube-cal-02-netlog.json",
        "x/youtube-dev-06-capture.json",
        "x/instagram-eval-01.json",
        "data/processed/v2/test.jsonl",
        "data/processed/v2/calibration.jsonl",
        "x/final/report.json",
    ],
)
def test_protected_inputs_are_rejected(path):
    cfg = read_config("configs/pool-linear-probe-v1.json")
    assert protected_input(path, set(cfg["train_trials"] + cfg["selection_trials"]))
    with pytest.raises(ValueError, match="excluded"):
        guard_for(cfg)("open", (path, "r"))


def test_frozen_config_tampering_and_offline_guard(tmp_path):
    cfg = read_config("configs/pool-linear-probe-v1.json")
    cfg["head"]["C"] = 2
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match="frozen"):
        read_config(path)
    guard = guard_for(cfg)
    guard("open", ("x/youtube-dev-05-development-rows.jsonl", "r"))
    with pytest.raises(ValueError, match="offline"):
        guard("socket.connect", (None,))


def test_artifact_reload_integrity_and_schema(tmp_path, monkeypatch, raw):
    weights, wheel = tmp_path / "weights", tmp_path / "wheel"
    weights.write_bytes(b"test-only weights")
    wheel.write_bytes(b"test-only wheel")
    monkeypatch.setattr(module, "WEIGHT_SHA", sha256(weights))
    monkeypatch.setattr(module, "WHEEL_SHA", sha256(wheel))
    encoder = SimpleNamespace(
        weights=weights,
        transform=SimpleNamespace(to_dict=lambda: {"test": True}),
        encode=lambda flows: np.zeros((len(flows), DIMENSIONS)),
    )
    monkeypatch.setattr(module, "PoolEncoder", lambda path: encoder)
    model = LinearProbe(
        encoder,
        ["a", "b", "c"],
        np.zeros(DIMENSIONS),
        np.ones(DIMENSIONS),
        np.zeros((3, DIMENSIONS)),
        np.array([1, 2, 3]),
    )
    bundle = tmp_path / "bundle"
    model.save(bundle, wheel)
    loaded = LinearProbe.load(bundle)
    assert model.predict(raw) == loaded.predict(raw)
    metadata = json.loads((bundle / "metadata.json").read_text())
    metadata["policy"]["fitted"] = True
    (bundle / "metadata.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="checksum"):
        LinearProbe.load(bundle)
    checksums = json.loads((bundle / "checksums.json").read_text())
    checksums["metadata.json"] = sha256(bundle / "metadata.json")
    (bundle / "checksums.json").write_text(json.dumps(checksums))
    with pytest.raises(ValueError, match="unsupported"):
        LinearProbe.load(bundle)
