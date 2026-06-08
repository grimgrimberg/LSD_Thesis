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
    if requirement_id not in STRICT_REQUIREMENT_IDS:
        raise ValueError(f"Unknown strict requirement id: {requirement_id}")
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
    if requirement_id not in PACKAGE_REQUIREMENT_IDS:
        raise ValueError(f"Unknown package requirement id: {requirement_id}")
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
