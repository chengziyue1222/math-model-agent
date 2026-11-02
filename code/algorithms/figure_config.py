"""Portable figure configuration. Explicit overrides > project YAML > defaults."""
from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path

DEFAULTS = {
    "width_mm": 150.0, "height_mm": 90.0, "maximum_height_mm": 247.0,
    "minimum_text_pt": 7.0, "text_pt": 8.5, "tick_pt": 8.0,
    "legend_pt": 8.0, "title_pt": 10.0, "panel_pt": 9.0,
    "line_width": 1.25, "marker_size": 4.5, "grid": True,
    "background": "#FFFFFF", "theme": "cumcm-research",
    "latin_font": "DejaVu Sans", "chinese_font": "auto",
    "dpi": 450, "minimum_dpi": 450, "width_tolerance_mm": 0.1,
    "formats": ["pdf", "svg", "png"], "semantic_styles": {},
}


def load_figure_config(config=None, **overrides):
    """Resolve an explicit mapping/file, or nearest cwd ancestor's paper style.

    An installed wheel never searches the author's source checkout. Missing explicit
    files are errors; absent implicit configuration uses recorded built-in defaults.
    """
    resolved = deepcopy(DEFAULTS)
    supplied = config is not None
    sources = ["builtin:algorithms.figure_config.DEFAULTS"]
    if config is None:
        config = next((p / "config/paper_style.yaml" for p in
                       (Path.cwd(), *Path.cwd().parents)
                       if (p / "config/paper_style.yaml").is_file()), {})
    if isinstance(config, (str, Path)):
        import yaml
        path = Path(config).resolve()
        raw = path.read_bytes()
        config = yaml.safe_load(raw) or {}
        sources.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
    if "figures" in config:
        typography = config.get("typography", {})
        resolved.update(chinese_font=typography.get("chinese_heading", "auto"),
                        latin_font=typography.get("latin_body", "DejaVu Sans"))
        config = config["figures"]
    explicit_height = supplied and any(k in config for k in ("height_mm", "default_height_mm"))
    aliases = {"default_width_mm": "width_mm", "default_height_mm": "height_mm",
               "palette": "theme", "weak_grid": "grid", "color": "primary_color"}
    resolved.update({aliases.get(k, k): deepcopy(v) for k, v in config.items() if k != "sources"})
    if resolved["theme"] == "muted-modeling-v1":
        resolved["theme"] = "modeling-default"
    sources.extend(config.get("sources", []))
    resolved.update({k: v for k, v in overrides.items() if v is not None})
    for key in ("width_mm", "height_mm", "minimum_text_pt", "text_pt", "tick_pt",
                "legend_pt", "title_pt", "panel_pt", "dpi", "maximum_height_mm",
                "line_width", "marker_size"):
        if isinstance(resolved[key], bool) or not isinstance(resolved[key], (float, int)) or not 0 < resolved[key] < float("inf"):
            raise ValueError(f"{key} must be finite and positive")
    if resolved.get("categorical_colors"):
        from matplotlib.colors import is_color_like
        colors = resolved["categorical_colors"]
        if isinstance(colors, str) or not all(is_color_like(c) for c in colors):
            raise ValueError("categorical_colors must be a sequence of valid colors")
    if resolved.get("primary_color"):
        from matplotlib.colors import is_color_like
        if not is_color_like(resolved["primary_color"]):
            raise ValueError("color must be a valid scalar color")
    from matplotlib.colors import Colormap
    if isinstance(resolved.get("cmap"), Colormap):
        import numpy as np
        colormap = resolved["cmap"]
        resolved["cmap_definition"] = {"name": colormap.name,
            "colors": colormap(np.linspace(0, 1, colormap.N)).tolist(),
            "bad": colormap.get_bad().tolist(), "under": colormap.get_under().tolist(),
            "over": colormap.get_over().tolist()}
        resolved["cmap"] = colormap.name
    resolved["sources"] = [source for index, source in enumerate(sources) if source not in sources[:index]]
    resolved["explicit_height"] = bool(explicit_height or overrides.get("height_mm") is not None)
    return resolved


def semantic_style(name, config=None):
    """Bind stable object names to color + marker + line, independent of row order.

    Persist explicit semantic_styles for important comparisons to avoid hash collisions.
    """
    from .sci_figures import get_modeling_palette
    cfg = load_figure_config(config)
    palette = get_modeling_palette(cfg["theme"])["categorical"]
    number = int.from_bytes(hashlib.sha256(str(name).encode("utf-8")).digest()[:8], "big")
    style = {"color": palette[number % len(palette)],
             "marker": ("o", "s", "^", "D", "v", "P")[(number // len(palette)) % 6],
             "linestyle": ("-", "--", ":", "-.")[(number // 36) % 4]}
    style.update(cfg["semantic_styles"].get(str(name), {}))
    return style
