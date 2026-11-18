import numpy as np
import pytest
import torch
from netembed.bundle import Predictor, export_bundle
from netembed.contract import Normalizer
from netembed.models import Classifier, supcon


def test_prefix_padding_future_and_readout(raw):
    torch.manual_seed(17)
    model = Classifier(2, hidden=8, levels=2, embedding_dim=4).eval()
    norm = Normalizer.fit([raw])
    x, length = norm.batch([raw[:3]])
    with torch.inference_mode():
        short = model(torch.tensor(x[:, :3]), torch.tensor(length))[0]
        padded = model(torch.tensor(x), torch.tensor(length))[0]
        x[:, 3:] = 9000
        future = model(torch.tensor(x), torch.tensor(length))[0]
    torch.testing.assert_close(short, padded)
    torch.testing.assert_close(short, future)


def test_bundle_no_fit_or_dataset_access(bundle, raw, monkeypatch):
    monkeypatch.setattr(Normalizer, "fit", lambda _: (_ for _ in ()).throw(AssertionError("inference fit")))
    a = Predictor(bundle, allow_fixture=True)
    b = Predictor(bundle, allow_fixture=True)
    np.testing.assert_allclose(a.probabilities([raw]), b.probabilities([raw]), atol=1e-7)
    assert a.predict(raw)["status"] == "insufficient_confidence"
    with pytest.raises(ValueError, match="software-test"):
        Predictor(bundle)


def test_checksum_failure(bundle):
    with (bundle / "weights.pt").open("ab") as f:
        f.write(b"bad")
    with pytest.raises(ValueError, match="checksum"):
        Predictor(bundle, allow_fixture=True)


@pytest.mark.parametrize("labels", [[0, 1, 2], [0, 0, 1], [0]])
def test_supcon_backward(labels):
    z = torch.randn(len(labels), 4, requires_grad=True)
    loss = supcon(z, torch.tensor(labels))
    loss.backward()
    assert torch.isfinite(loss) and torch.isfinite(z.grad).all()


def test_forest_export_parity(tmp_path, raw):
    from sklearn.ensemble import RandomForestClassifier
    from netembed.contract import summary

    xs = [raw, raw[:2], raw[:3], raw[:4]]
    rf = RandomForestClassifier(n_estimators=3, random_state=17).fit([summary(x) for x in xs], [0, 1, 0, 1])
    path = export_bundle(tmp_path / "rf", rf, Normalizer.fit(xs), ["a", "b"], {"fixture": True})
    p = Predictor(path, allow_fixture=True)
    np.testing.assert_allclose(p.probabilities(xs), rf.predict_proba([summary(x) for x in xs]))
    queries = [x.copy() for x in xs * 40]
    for i, x in enumerate(queries):
        x[-1, 2] += i % 19
    np.testing.assert_allclose(
        p.probabilities(queries), rf.predict_proba([summary(x) for x in queries]), atol=1e-12
    )
    # Single-flow fast path must preserve the existing batched implementation,
    # including different prefix lengths, feature values and tree leaves.
    single = np.concatenate([p.probabilities([x]) for x in queries])
    np.testing.assert_array_equal(single, p.probabilities(queries))


def test_scalar_forest_boundary_root_leaf_and_cycle(raw, monkeypatch):
    import netembed.bundle as module

    monkeypatch.setattr(module, "forest_features", lambda x, *args: [x[0, 2]])
    p = Predictor.__new__(Predictor)
    p.meta, p.labels, p.normalizer, p.forest_feature_map = {"kind": "forest"}, ["a", "b"], None, "summary-v1"
    tree = {
        "left": np.array([1, -1, -1]),
        "right": np.array([2, -1, -1]),
        "feature": np.array([0, -2, -2]),
        "threshold": np.array([1200.0, 0, 0]),
        "value": np.array([[0.0, 0.0], [1.0, 3.0], [9.0, 1.0]]),
    }
    p.trees = [tree]
    np.testing.assert_array_equal(p.probabilities([raw]), [[0.25, 0.75]])
    high = raw.copy()
    high[0, 2] = 1201
    np.testing.assert_array_equal(p.probabilities([high]), [[0.9, 0.1]])
    np.testing.assert_array_equal(p.probabilities([raw, high]), [[0.25, 0.75], [0.9, 0.1]])
    p.trees = [{k: v[1:2] for k, v in tree.items()}]
    np.testing.assert_array_equal(p.probabilities([raw]), [[0.25, 0.75]])
    p.trees = [{**tree, "left": np.array([0, -1, -1]), "right": np.array([0, -1, -1])}]
    with pytest.raises(ValueError, match="cyclic"):
        p.probabilities([raw])
