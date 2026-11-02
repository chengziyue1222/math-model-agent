"""Claim binding and manuscript insertion are independent handoff states."""
from __future__ import annotations
import json
from pathlib import Path


def claim_binding(root: Path, figure_id: str):
    root = Path(root)
    paths = [root / p for p in ("paper/claim-registry.json", "paper/claim_registry.json", "claims/claim-registry.json", "claims.json")]
    found = []
    for path in paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("claims", payload.get("figures", payload.get("items", []))) if isinstance(payload, dict) else payload
        if isinstance(rows, dict):
            rows = [{"figure_id": key, "claim_ids": value} for key, value in rows.items()]
        if not isinstance(rows, list):
            raise ValueError(f"claim registry {path.name} must contain a list or mapping")
        valid = {r.get("claim_id", r.get("id")) for r in rows if isinstance(r, dict)}
        for row in rows:
            if not isinstance(row, dict):
                continue
            if figure_id in row.get("figure_ids", []) or row.get("figure_id") == figure_id:
                ids = row.get("claim_ids", [row.get("claim_id", row.get("id"))])
                if isinstance(ids, str):
                    raise ValueError("claim_ids must be a list")
                found.extend(i for i in ids if isinstance(i, str) and i.strip())
        # Explicit figure mappings are accepted as claim binding records;
        # insertion still needs separately verified manuscript registration.
        if valid - {None} and any(i not in valid for i in found):
            raise ValueError("figure references an unknown claim_id")
    ids = list(dict.fromkeys(found))
    # A renderer cannot establish that the author inserted a figure in text.
    return ids, False, "NEEDS_BODY_INSERTION" if ids else "NEEDS_CLAIM_BINDING"
