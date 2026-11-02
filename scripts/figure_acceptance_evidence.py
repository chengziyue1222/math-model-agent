"""Artist evidence for a numerical regression audit, independent of styling."""
from __future__ import annotations

import numpy as np


def serial(value):
    if value is None:
        return None
    array = np.ma.asarray(value)
    if array.dtype.kind in 'biufc':
        array = np.ma.filled(array.astype(float), np.nan)
        return np.where(np.isfinite(array), array, None).tolist()
    return array.tolist()


def artist_evidence(fig):
    """Retain all plotted arrays and data-coordinate patch geometry."""
    axes = []
    for ax in fig.axes:
        collections = []
        for artist in ax.collections:
            collections.append({'type': type(artist).__name__,
                                'offsets': serial(artist.get_offsets()),
                                'array': serial(artist.get_array()),
                                'sizes': serial(artist.get_sizes()) if hasattr(artist, 'get_sizes') else None,
                                'paths': [serial(path.vertices) for path in artist.get_paths()],
                                'color_domain': serial(artist.get_clim()),
                                'mesh_coordinates': serial(artist.get_coordinates()) if hasattr(artist, 'get_coordinates') else None,
                                'contour_levels': serial(artist.levels) if hasattr(artist, 'levels') else None})
            collections[-1]['facecolors'] = serial(artist.get_facecolors())
            collections[-1]['path_codes'] = [serial(path.codes) for path in artist.get_paths()]
            if getattr(ax, '_colorbar', None) is not None and artist.get_array() is not None:
                collections[-1]['colormap_lut'] = serial(artist.cmap(np.linspace(0, 1, artist.cmap.N)))
        patches = []
        for patch in ax.patches:
            try:
                points = ax.transData.inverted().transform(patch.get_transform().transform(patch.get_path().vertices))
                patches.append({'type': type(patch).__name__, 'vertices': serial(points),
                                'endpoint_anchors': serial(patch._posA_posB) if getattr(patch, '_posA_posB', None) is not None else None})
                if getattr(fig, '_figure_metadata', {}).get('canonical_key') == 'pictogram':
                    clip = patch.get_clip_box()
                    patches[-1]['clip_box'] = serial(ax.transData.inverted().transform(clip.get_points())) if clip is not None else None
                if getattr(fig, '_figure_metadata', {}).get('canonical_key') == 'circular_heatmap':
                    patches[-1]['facecolor'] = serial(patch.get_facecolor())
            except (ValueError, AttributeError):
                patches.append({'type': type(patch).__name__, 'vertices': serial(patch.get_path().vertices)})
        axes.append({'projection': ax.name, 'xscale': ax.get_xscale(), 'yscale': ax.get_yscale(),
                     'xlim': list(ax.get_xlim()), 'ylim': list(ax.get_ylim()),
                     'lines': [serial(line.get_xydata()) for line in ax.lines],
                     'collections': collections, 'patches': patches,
                     'images': [serial(image.get_array()) for image in ax.images],
                     'image_color_domains': [serial(image.get_clim()) for image in ax.images],
                     'auxiliary_role': 'label_key' if getattr(ax, '_model_label_key', False) else
                                       'colorbar' if getattr(ax, '_colorbar', None) is not None else 'data',
                     'texts': [{'text': text.get_text(), 'position': serial(text.get_position()),
                                'anchor': serial(text.xy) if hasattr(text, 'xy') else None}
                               for text in ax.texts],
                     'tick_labels': {'x': [text.get_text() for text in ax.get_xticklabels()],
                                     'y': [text.get_text() for text in ax.get_yticklabels()]},
                     'figure_legends': [[t.get_text() for t in legend.get_texts()] for legend in fig.legends] if ax is fig.axes[0] else []})
    return axes
