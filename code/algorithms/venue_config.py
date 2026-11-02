"""Small explicit venue profile layer shared by paper skills."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import yaml


VENUE_PROFILES = {
    "CUMCM": {
        "body_page_limit": 30, "ai_declaration": True, "formats": ["pdf", "zip"],
        "references_style": "GB/T 7714", "figure_column": "single-or-double",
        "anonymous": True, "support_package": True,
    },
    "MCM/ICM": {
        "body_page_limit": None, "ai_declaration": True, "formats": ["pdf", "zip"],
        "references_style": "venue-template", "figure_column": "single-or-double",
        "anonymous": True, "support_package": True,
    },
    "MathorCup": {
        "body_page_limit": None, "ai_declaration": "check-current-rules", "formats": ["pdf", "zip"],
        "references_style": "venue-template", "figure_column": "single-or-double",
        "anonymous": True, "support_package": True,
    },
    "journal": {
        "body_page_limit": None, "ai_declaration": "journal-policy", "formats": ["pdf", "source"],
        "references_style": "journal-template", "figure_column": "journal-template",
        "anonymous": "double-blind-if-required", "support_package": "journal-policy",
    },
    "generic-research-report": {
        "body_page_limit": None, "ai_declaration": False, "formats": ["pdf"],
        "references_style": "author-choice", "figure_column": "single-or-double",
        "anonymous": False, "support_package": False,
    },
}


def venue_profile(venue: str = "generic-research-report") -> dict:
    """Return a copy of an explicit venue profile.

    The default is a generic research report; CUMCM rules are never applied
    implicitly.
    """
    if venue not in VENUE_PROFILES:
        choices = ", ".join(VENUE_PROFILES)
        raise ValueError(f"unknown venue {venue!r}; choose one of: {choices}")
    return {"venue": venue, "policy_source": "local configurable defaults; verify current official rules",
            "max_delivery_bytes": 20_000_000 if venue == "CUMCM" else None,
            **deepcopy(VENUE_PROFILES[venue])}


def load_venue_config(config=None, *, venue=None):
    """Explicit venue > configuration file > generic report defaults."""
    if config is None:
        data = {}
    elif isinstance(config, dict):
        data = config
    else:
        data = yaml.safe_load(Path(config).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("venue config must be a mapping")
    selected = venue or data.get("venue", "generic-research-report")
    profile = venue_profile(selected)
    overrides = data.get("overrides", {})
    if not isinstance(overrides, dict) or set(overrides) - set(profile):
        raise ValueError("venue overrides contain unknown fields or are not a mapping")
    if "venue" in overrides:
        raise ValueError("choose venue explicitly; it cannot be changed through overrides")
    profile.update(deepcopy(overrides))
    if selected != "CUMCM" and "body_page_limit" not in overrides:
        profile["body_page_limit"] = None
    return profile


def resolve_project_venue(project_root, *, venue=None, config=None):
    """One resolver for runners, writing, review and submission.

    Legacy states need explicit selection. A conflicting override is rejected
    rather than applying different submission rules to the same project.
    """
    import json
    root = Path(project_root)
    state_path = root / ".modeling" / "project-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    if state_path.is_file() and not state.get("venue"):
        raise ValueError("legacy project requires explicit venue selection")
    saved = state.get("venue_config", {})
    if config is None and (root / "config/venue.yaml").is_file():
        config = root / "config/venue.yaml"
    if config is None and saved:
        config = {"venue": saved["venue"], "overrides": {k: v for k, v in saved.items() if k != "venue"}}
    configured = config if isinstance(config, dict) else (
        yaml.safe_load(Path(config).read_text(encoding="utf-8")) or {} if config is not None else {})
    if not isinstance(configured, dict):
        raise ValueError("venue config must be a mapping")
    if state.get("venue") and configured.get("venue", state["venue"]) != state["venue"]:
        raise ValueError("venue config differs from project state; rewind before changing it")
    resolved = load_venue_config(config, venue=venue or state.get("venue"))
    if state.get("venue") and resolved["venue"] != state["venue"]:
        raise ValueError("venue differs from project state; rewind before changing it")
    return resolved


__all__ = ["VENUE_PROFILES", "venue_profile", "load_venue_config", "resolve_project_venue"]
