from __future__ import annotations

from typing import Any

from .status import PACKAGE_REQUIREMENT_IDS, STRICT_REQUIREMENT_IDS


def _gate(label: str, status: str, ready: bool, evidence: str, blocker: str, score: float) -> dict[str, Any]:
    return {
        "label": label,
        "status": status,
        "ready": ready,
        "evidence": evidence,
        "blocker": blocker,
        "score": float(score),
    }

def _requirement_payload(
    requirement_id: str,
    label: str,
    status: str,
    complete: bool,
    evidence: str,
    missing: str,
    next_action: str,
    claim_effect: str,
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "status": status,
        "complete": bool(complete),
        "evidence": evidence,
        "missing": missing,
        "next_action": next_action,
        "claim_effect": claim_effect,
    }

def _checked_requirement_payload(
    requirement_id: str,
    label: str,
    status: str,
    complete: bool,
    evidence: str,
    missing: str,
    next_action: str,
    claim_effect: str,
    allowed_requirement_ids: tuple[str, ...],
    requirement_kind: str,
) -> dict[str, Any]:
    if requirement_id not in allowed_requirement_ids:
        raise ValueError(f"Unknown {requirement_kind} requirement id: {requirement_id}")
    return _requirement_payload(
        requirement_id,
        label,
        status,
        complete,
        evidence,
        missing,
        next_action,
        claim_effect,
    )

def _requirement(
    requirement_id: str,
    label: str,
    status: str,
    complete: bool,
    evidence: str,
    missing: str,
    next_action: str,
    claim_effect: str,
) -> dict[str, Any]:
    return _checked_requirement_payload(
        requirement_id,
        label,
        status,
        complete,
        evidence,
        missing,
        next_action,
        claim_effect,
        STRICT_REQUIREMENT_IDS,
        "strict",
    )

def _package_requirement(
    requirement_id: str,
    label: str,
    status: str,
    complete: bool,
    evidence: str,
    missing: str,
    next_action: str,
    claim_effect: str,
) -> dict[str, Any]:
    return _checked_requirement_payload(
        requirement_id,
        label,
        status,
        complete,
        evidence,
        missing,
        next_action,
        claim_effect,
        PACKAGE_REQUIREMENT_IDS,
        "package",
    )
