"""Snapshot signing and verification tools for verifiable knowledge."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = ["Snapshot", "SnapshotClaim", "sign_snapshot", "verify_snapshot"]


@dataclass(frozen=True)
class SnapshotClaim:
    """A single claim in a knowledge snapshot."""

    id: str
    text: str
    confidence: float  # 0.0 to 1.0
    sources: List[str] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.sources is None:
            object.__setattr__(self, "sources", [])


@dataclass(frozen=True)
class Snapshot:
    """Verifiable knowledge snapshot with signature."""

    version: int = 1
    timestamp: str = ""  # ISO 8601
    model_id: str = ""
    knowledge_hash: str = ""
    claims: List[SnapshotClaim] = None  # type: ignore
    signature: Optional[str] = None

    def __post_init__(self) -> None:
        if self.claims is None:
            object.__setattr__(self, "claims", [])


def sign_snapshot(snapshot: Snapshot, secret: str) -> Snapshot:
    """Sign a snapshot using HMAC-SHA256.
    
    Args:
        snapshot: Snapshot to sign (signature field should be None).
        secret: Shared secret for HMAC.
        
    Returns:
        Snapshot with signature field populated.
    """
    # Create canonical JSON (sorted keys, no whitespace)
    payload = {
        "version": snapshot.version,
        "timestamp": snapshot.timestamp,
        "model_id": snapshot.model_id,
        "knowledge_hash": snapshot.knowledge_hash,
        "claims": [asdict(c) for c in snapshot.claims],
    }
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    # Compute HMAC
    signature = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return Snapshot(
        version=snapshot.version,
        timestamp=snapshot.timestamp,
        model_id=snapshot.model_id,
        knowledge_hash=snapshot.knowledge_hash,
        claims=snapshot.claims,
        signature=f"sha256:{signature}",
    )


def verify_snapshot(snapshot: Snapshot, secret: str) -> bool:
    """Verify snapshot signature.
    
    Args:
        snapshot: Snapshot with signature field.
        secret: Shared secret for HMAC.
        
    Returns:
        True if signature matches, False otherwise.
    """
    if not snapshot.signature:
        return False

    # Extract algorithm and expected signature
    try:
        algo, expected_sig = snapshot.signature.split(":", 1)
    except ValueError:
        return False

    if algo != "sha256":
        return False

    # Recreate canonical JSON
    payload = {
        "version": snapshot.version,
        "timestamp": snapshot.timestamp,
        "model_id": snapshot.model_id,
        "knowledge_hash": snapshot.knowledge_hash,
        "claims": [asdict(c) for c in snapshot.claims],
    }
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    # Compute and compare
    computed_sig = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sig, computed_sig)


def snapshot_to_json(snapshot: Snapshot) -> str:
    """Serialize snapshot to JSON."""
    payload = {
        "version": snapshot.version,
        "timestamp": snapshot.timestamp,
        "model_id": snapshot.model_id,
        "knowledge_hash": snapshot.knowledge_hash,
        "claims": [asdict(c) for c in snapshot.claims],
        "signature": snapshot.signature,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def snapshot_from_json(data: str) -> Snapshot:
    """Deserialize snapshot from JSON."""
    payload = json.loads(data)
    claims = [SnapshotClaim(**c) for c in payload.get("claims", [])]
    return Snapshot(
        version=payload.get("version", 1),
        timestamp=payload.get("timestamp", ""),
        model_id=payload.get("model_id", ""),
        knowledge_hash=payload.get("knowledge_hash", ""),
        claims=claims,
        signature=payload.get("signature"),
    )

