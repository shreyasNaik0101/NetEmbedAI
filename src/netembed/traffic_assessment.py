"""Explicit metadata identity and packet estimate; never fuse their scores."""

from .data import LABELS


def assess(reference, prediction):
    reference, prediction = reference or {}, prediction or {}
    named = reference.get("label") if reference.get("status") == "mapped" else None
    if named not in LABELS:
        named = None
    committed = prediction.get("label") if prediction.get("status") == "classified" else None
    if committed not in LABELS:
        committed = None
    return {
        "identity": {
            "label": named,
            "basis": "visible_handshake_name_map" if named else "unresolved",
            "score": None,
        },
        "packet_model": {
            "label": committed,
            "status": prediction.get("status", "pending"),
            "alternatives": prediction.get("alternatives", []),
            "artifact_id": prediction.get("artifact_id"),
        },
        "relationship": "agrees"
        if named and committed == named
        else "conflicts"
        if named and committed
        else "model_withheld_or_pending"
        if named
        else "no_named_identity",
        "identity_accuracy_eligible_against_name_derived_truth": False,
        "note": "Name evidence is not a model prediction or a correctness probability. No activity inference.",
    }
