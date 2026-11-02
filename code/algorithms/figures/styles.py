"""Render-time configuration, separated from numerical input and pyplot globals."""
from __future__ import annotations
from collections.abc import Sequence
from contextlib import contextmanager
from contextvars import ContextVar
import textwrap
import matplotlib.pyplot as plt
import numpy as np
from ..sci_figures import get_modeling_palette, paper_figure_rc_params

_CURRENT = ContextVar("model_figure_style", default=None)


def wrap_label(text, width):
    """Keep full captions while avoiding punctuation alone at a line boundary."""
    lines = []
    closing = "，。！？；：、）】》〉」』〕％%)]}:;,"
    opening = "（【《〈「『〔([{"
    for block in str(text).splitlines() or [""]:
        wrapped = textwrap.wrap(block, width) or [""]
        for line in wrapped:
            if lines and line:
                while line and line[0] in closing:
                    lines[-1] += line[0]
                    line = line[1:]
                while lines[-1] and lines[-1][-1] in opening and line:
                    line = lines[-1][-1] + line
                    lines[-1] = lines[-1][:-1]
            if line:
                lines.append(line)
    return "\n".join(lines)


@contextmanager
def rendering_style(config, name, data, *, explicit_height=False):
    token = _CURRENT.set((config, name, data, explicit_height))
    try:
        yield
    finally:
        _CURRENT.reset(token)


def current_config():
    value = _CURRENT.get()
    return value[0] if value else None


def style(name=None):
    cfg = current_config()
    palette = get_modeling_palette(name or (cfg["theme"] if cfg else "modeling-default"))
    if cfg and cfg.get("categorical_colors"):
        palette["categorical"] = tuple(cfg["categorical_colors"])
    if cfg and cfg.get("primary_color"):
        palette["categorical"] = (cfg["primary_color"], *palette["categorical"][1:])
    return palette


def color(role=0, fallback="#3C6E8F"):
    if current_config() is None:
        return fallback
    palette = style()
    return palette["categorical"][role % len(palette["categorical"])] if isinstance(role, int) else palette[role]


def font(role="text", fallback=8):
    cfg = current_config()
    return cfg.get(role+"_pt", cfg["text_pt"]) if cfg else fallback


def stroke(fallback=1.25):
    cfg = current_config()
    return cfg["line_width"] * fallback / 1.25 if cfg else fallback


def marker(fallback=4.5, *, area=False):
    cfg = current_config()
    if cfg is None:
        return fallback
    ratio = cfg["marker_size"] / 4.5
    return fallback * ratio**2 if area else fallback * ratio


def cmap(kind="sequential", fallback="viridis"):
    if current_config() is None:
        return fallback
    if current_config().get("cmap_definition"):
        from matplotlib.colors import ListedColormap
        definition = current_config()["cmap_definition"]
        return ListedColormap(definition["colors"], name=definition["name"]).with_extremes(
            bad=definition["bad"], under=definition["under"], over=definition["over"])
    if current_config().get("cmap"):
        return plt.get_cmap(current_config()["cmap"])
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("model_"+kind, style()[kind])


def hatch(index):
    return ("", "///", "...", "xxx", "\\\\", "++")[index % 6]


def node_axes(nodes, ax=None):
    """Keep full node names in a separate key when direct labels would crowd."""
    nodes = list(nodes)
    keyed = len(nodes) > 8 or any(len(str(node)) > 10 for node in nodes)
    if not keyed:
        return ax if ax is not None else subplots(constrained_layout=True)[1], {node: str(node) for node in nodes}
    if ax is not None:
        raise ValueError("long or dense node labels require automatic key layout; omit ax")
    cfg = current_config()
    columns = 1 if cfg is not None and cfg['width_mm'] < 100 else 2
    rows = (len(nodes) + columns - 1) // columns
    wrap_width = 18
    if columns == 1:
        wrap_width = max(5, int((cfg['width_mm']/25.4*72-60)/font())-2)
    codes = {node: f"N{i+1}" for i, node in enumerate(nodes)}
    texts = [textwrap.fill(f"{codes[node]}  {node}", width=wrap_width) for node in nodes]
    row_lines = [max(texts[i+j*rows].count('\n')+1 for j in range(columns) if i+j*rows < len(texts)) for i in range(rows)]
    key_mm = (sum(row_lines)*font()*1.3+12)/72*25.4
    available_mm = _height(2) if cfg is not None else 120
    fig, axes = subplots(2, 1, constrained_layout=True,
                         gridspec_kw={"height_ratios": [max(30, available_mm-key_mm-15), key_mm]})
    key = axes[1]
    key.set_axis_off()
    key._model_label_key = True
    total_lines = sum(row_lines)
    for i, node in enumerate(nodes):
        column, row = i // rows, i % rows
        row_center = (sum(row_lines[:row])+row_lines[row]/2)/total_lines
        key.text(.02+.96/columns*column, 1-row_center,
                 texts[i],
                 transform=key.transAxes, ha="left", va="center", fontsize=font())
    fig._node_label_key = {code: str(node) for node, code in codes.items()}
    return axes[0], codes


class Palette(Sequence):
    """Resolve categorical colors on use, retaining a legacy fallback."""
    def __init__(self, fallback):
        self.fallback = tuple(fallback)

    def _values(self):
        if current_config() is None:
            return self.fallback
        explicit = _CURRENT.get()[2].get("group_colors")
        if explicit is not None:
            return tuple(explicit)
        palette = style()["categorical"]
        groups = _CURRENT.get()[2].get("groups", [])
        bindings = current_config()["semantic_styles"]
        if "primary_color" in current_config().get("explicit_style_fields", []):
            bindings = {key: {k: v for k, v in value.items() if k != "color"}
                        for key, value in bindings.items()}
        return tuple(bindings.get(str(groups[i]), {}).get("color", shade)
                     if i < len(groups) else shade for i, shade in enumerate(palette))

    def __len__(self):
        return len(self._values())

    def __getitem__(self, index):
        return self._values()[index]

    def __mul__(self, count):
        return list(self._values()) * count

    __rmul__ = __mul__


def pictogram_columns(data):
    """Reflow grouped icons at narrow print widths; explicit columns win."""
    cfg = current_config()
    return data.get("columns", 5 if cfg is not None and cfg["width_mm"] < 100 else 10)


def _height(nrows=1):
    cfg, name, data, explicit = _CURRENT.get()
    if explicit:
        return cfg["height_mm"]
    height = cfg["height_mm"]
    labels = [v for key in ("categories", "labels", "groups", "row_labels", "column_labels", "metrics", "nodes", "source", "target")
              for v in data.get(key, []) if isinstance(v, str)]
    if any(len(v) > 10 for v in labels):
        height = max(height, 155)
    if data.get("nodes"):
        count = len(data["nodes"])
        height = max(height, 40+17*count if count > 8 else 60+6*count)
    if name == "pictogram" and data.get("pictogram_mode", "array") == "array" and data.get("array_layout", "grouped") == "grouped":
        counts = np.ceil(np.asarray(data["values"])/data.get("icon_value", 1))
        rows = np.maximum(1, np.ceil(counts/pictogram_columns(data))).sum()
        # A long row caption wraps beside the icons; it does not need the
        # generic 155 mm canvas used by densely labelled Cartesian plots.
        height = max(48, 18+14*rows+8*len(counts))
    elif name in {"correlation_matrix", "pairgrid"}:
        p = np.asarray(data.get("data", [])).shape[-1]
        height = max(height, 30*p + 25)
    elif name == "correlation_bubble":
        height = max(height, 12*np.asarray(data.get("data", [])).shape[-1]+40)
    elif name in {"matrix_pie", "sparkline_matrix"}:
        height = max(height, 32*len(data.get("row_labels", []))+35)
    elif name == "faceted_heatmap":
        matrices = data.get("matrices", [])
        height = max(height, 180 if len(matrices) > 2 else 145)
        if len(matrices) and np.asarray(matrices).shape[-1] > 6:
            height = max(height, 65*len(matrices)+20)
        if len(matrices) and any(len(str(v)) > 12 for v in (*data.get('row_labels', []), *data.get('column_labels', []))):
            wrap = 7 if cfg['width_mm'] >= 100 else 5
            row_lines = sum(len(textwrap.wrap(str(v), wrap)) for v in data['row_labels'])
            column_lines = max(len(textwrap.wrap(str(v), wrap)) for v in data['column_labels'])
            title_lines = max(len(textwrap.wrap(str(v), 7)) for v in data['facets'])
            panel_points = (row_lines*cfg['tick_pt']*1.35
                            + column_lines*cfg['tick_pt']*1.25
                            + title_lines*cfg['title_pt']*1.2 + 34)
            height = max(height, len(matrices)*panel_points/72*25.4+12)
    elif name in {"correlation_heatmap", "covariance_heatmap"}:
        height = max(height, 12*len(data.get("labels", []))+40)
    elif name == "circular_heatmap":
        height = max(height, 8*len(data.get("row_labels", []))+50, 125)
    elif name == "dendrogram":
        height = max(height, 7*len(data.get("labels", []))+35)
    elif name.startswith("calendar"):
        years = len({str(d)[:4] for d in data.get("dates", [])})
        height = max(height, 140 if data.get("layout") == "vertical" else 36*years+30)
    elif name in {"radar", "polar_stacked_bar", "rose", "chord", "pie", "donut"}:
        height = max(height, 125)
    elif name in {"forest", "tornado", "ranking", "horizontal_bar", "cleveland_dot", "lollipop"}:
        labels = data.get("labels", data.get("categories", data.get("parameters", [])))
        height = max(height, 7*len(labels)+35)
    if nrows > 1:
        height = max(height, 32*nrows+25)
    return min(height, cfg["maximum_height_mm"])


def subplots(*args, **kwargs):
    if current_config() is not None:
        rows = kwargs.get("nrows", args[0] if args and isinstance(args[0], int) else 1)
        cfg = current_config()
        kwargs["figsize"] = (cfg["width_mm"]/25.4, _height(rows)/25.4)
    return plt.subplots(*args, **kwargs)


def figure(*args, **kwargs):
    if current_config() is not None:
        cfg = current_config()
        kwargs["figsize"] = (cfg["width_mm"]/25.4, _height()/25.4)
    return plt.figure(*args, **kwargs)


def finish(fig, config):
    """Text/layout and explicit object styles; no data or axis-scale changes."""
    import matplotlib as mpl
    from matplotlib import font_manager
    from ..sci_figures import resolve_cjk_font
    configured = config["chinese_font"]
    installed_names = {item.name.casefold() for item in font_manager.fontManager.ttflist}
    cjk = (configured if configured != "auto" and configured.casefold() in installed_names
           else resolve_cjk_font())
    caller = _CURRENT.get()[2] if _CURRENT.get() else {}
    for ax in fig.axes:
        for artist in [*ax.lines, *ax.collections]:
            label = artist.get_label()
            binding = config["semantic_styles"].get(label, {})
            for attribute in ("color", "marker", "linestyle"):
                if attribute in binding and attribute not in caller and hasattr(artist, "set_" + attribute):
                    if attribute == "color" and (any(k in caller for k in ("group_colors", "colors")) or "primary_color" in config.get("explicit_style_fields", [])):
                        continue
                    getattr(artist, "set_" + attribute)(binding[attribute])
    # Tick text is owned by the Formatter; changing Text alone is overwritten
    # on the next draw/export. Keep every tick position and full label.
    for ax in fig.axes:
        if not config["grid"]:
            ax.grid(False, which="both")
        for label in (ax.xaxis.label, ax.yaxis.label):
            if len(label.get_text()) > 10 and any("\u4e00" <= c <= "\u9fff" for c in label.get_text()):
                label.set_text(wrap_label(label.get_text(), 7 if len(fig.axes) > 2 else 14))
        for axis_name in ("x", "y"):
            labels = getattr(ax, "get_" + axis_name + "ticklabels")()
            texts = [t.get_text() for t in labels]
            if any(len(t) > 10 and any("\u4e00" <= c <= "\u9fff" for c in t) for t in texts):
                width = 7 if config["width_mm"] >= 100 else 5
                wrapped = [wrap_label(t, width) if any("\u4e00" <= c <= "\u9fff" for c in t) else t for t in texts]
                getattr(ax, "set_" + axis_name + "ticks")(getattr(ax, "get_" + axis_name + "ticks")(), wrapped)
                if axis_name == "x" and ax.name != "polar":
                    for t in ax.get_xticklabels():
                        t.set_rotation(0)
                        t.set_ha("center")
    long_legends = []
    from matplotlib.legend import Legend
    for legend in fig.findobj(Legend):
        for handle, label in zip(legend.legend_handles, legend.get_texts()):
            binding = config["semantic_styles"].get(label.get_text(), {})
            for attribute in ("color", "marker", "linestyle"):
                if attribute in binding and attribute not in caller and hasattr(handle, "set_" + attribute):
                    if attribute == "color" and (any(k in caller for k in ("group_colors", "colors")) or "primary_color" in config.get("explicit_style_fields", [])):
                        continue
                    getattr(handle, "set_" + attribute)(binding[attribute])
        if any(max((len(line) for line in t.get_text().splitlines()), default=0) > 14
               for t in legend.get_texts()):
            for t in legend.get_texts():
                t.set_text(wrap_label(t.get_text(), 14 if config["width_mm"] >= 100 else 8))
            legend.set_ncols(1)
            long_legends.append(legend)
    if long_legends:
        handles, texts = [], []
        titles = [legend.get_title().get_text() for legend in long_legends]
        seen = set()
        for legend in long_legends:
            title = legend.get_title().get_text()
            for handle, t in zip(legend.legend_handles, legend.get_texts()):
                key = (title, t.get_text())
                if key not in seen:
                    seen.add(key)
                    handles.append(handle)
                    # Different legends can use the same label under different
                    # units/headings. Keep that context when combining them.
                    label = f"{title}：{t.get_text()}" if len(set(titles)) > 1 and title else t.get_text()
                    texts.append(label)
            legend.remove()
        fig.legend(handles, texts, loc="outside lower center", ncol=1,
                   fontsize=config["legend_pt"], title=titles[0] if len(set(titles)) == 1 else "")
    for artist in fig.findobj(mpl.text.Text):
        if not artist.get_text():
            continue
        if any("\u4e00" <= c <= "\u9fff" for c in artist.get_text()) and cjk:
            artist.set_fontfamily([cjk, config['latin_font'], 'DejaVu Sans'])
        if artist.get_fontsize() < config["minimum_text_pt"]:
            artist.set_fontsize(config["minimum_text_pt"])
        text = artist.get_text()
        if len(text) > 10 and any("\u4e00" <= c <= "\u9fff" for c in text) and "\n" not in text and "$" not in text and not getattr(artist.axes, '_model_label_key', False):
            artist.set_text(wrap_label(text, 7 if len(fig.axes) > 2 else 12))
    for ax in fig.axes:
        for label in [ax.xaxis.label, ax.yaxis.label]:
            if len(label.get_text()) > 24 and "\n" not in label.get_text():
                label.set_text(wrap_label(label.get_text(), 24))
        if ax.get_legend():
            for label in ax.get_legend().get_texts():
                if len(label.get_text()) > 20 and "\n" not in label.get_text():
                    label.set_text(wrap_label(label.get_text(), 20))
    fig._figure_config = config
    # Resolve collisions using the actual final-font boxes and final panel
    # width. Keep every tick and never reduce its font to disguise crowding.
    has_rect_axes = any(ax.name == 'rectilinear' and ax.axison for ax in fig.axes)
    if has_rect_axes:
        fig.canvas.draw()
    ticks_changed = False
    for ax in fig.axes:
        if ax.name != 'rectilinear' or not ax.axison:
            continue
        ticks = ax.get_xticklabels()
        if len(ticks) < 2:
            continue
        renderer = fig.canvas.get_renderer()
        boxes = [t.get_window_extent(renderer) for t in ticks]
        if not any(a.x1+.15*min(a.width,b.width) > b.x0 for a, b in zip(boxes, boxes[1:])):
            continue
        ticks_changed = True
        centers = [ax.transData.transform((value, 0))[0] for value in ax.get_xticks()]
        spacing = min(abs(b-a) for a, b in zip(centers, centers[1:]))
        available = max(1, int((.85*spacing-3)/(max(t.get_fontsize() for t in ticks)*fig.dpi/72)))
        texts = [t.get_text().replace('\n', '') for t in ticks]
        if available >= 3:
            ax.set_xticks(ax.get_xticks(), [wrap_label(t, min(available, 14)) for t in texts])
            plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
        else:
            ax.set_xticks(ax.get_xticks(), texts)
            plt.setp(ax.get_xticklabels(), rotation=90, ha='center', va='top')
    # Wrapping can itself change constrained-layout panel widths. Settle that
    # feedback with two additional measurements of the real rendered boxes.
    for _ in range(2 if ticks_changed else 0):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        for ax in fig.axes:
            if ax.name != 'rectilinear' or not ax.axison:
                continue
            labels = ax.get_xticklabels()
            boxes = [t.get_window_extent(renderer) for t in labels]
            if len(boxes) < 2 or not any(a.x1+.15*min(a.width,b.width) > b.x0 for a, b in zip(boxes, boxes[1:])):
                continue
            centers = [box.x0+box.width/2 for box in boxes]
            gap = min(abs(b-a) for a,b in zip(centers,centers[1:]))
            characters = max(max(map(len,t.get_text().splitlines()), default=1) for t in labels)
            width = max(1, int(characters*(.85*gap-5)/max(box.width for box in boxes)))
            texts = [t.get_text().replace('\n','') for t in labels]
            ax.set_xticks(ax.get_xticks(), [textwrap.fill(t,width) for t in texts] if width >= 3 else texts)
            plt.setp(ax.get_xticklabels(), rotation=0 if width >= 3 else 90, ha='center')
    for finalize in getattr(fig, "_publication_layout_finalizers", ()):
        finalize()


def rc_params(*, language="zh", theme=None):
    return paper_figure_rc_params(language=language, config={"theme": theme} if theme else current_config())

