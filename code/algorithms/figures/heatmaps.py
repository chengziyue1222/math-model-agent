"""Heat maps, matrices, and response surfaces."""
from __future__ import annotations
from . import styles as _style
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from .base import attach_metadata, finite_array, contract_from


def heatmap(matrix, *, x=None, y=None, units="", diverging=False, vmin=None, vcenter=None, vmax=None, contract=None, ax=None, **kwargs):
    z=finite_array(matrix,"matrix",ndim=2); ax=ax or _style.subplots(constrained_layout=True)[1]
    norm=TwoSlopeNorm(vcenter,vmin=vmin if vmin is not None else z.min(),vmax=vmax if vmax is not None else z.max()) if diverging else None
    cmap=kwargs.get("cmap", _style.cmap("diverging" if diverging else "sequential", "RdBu_r" if diverging else "YlOrRd")); im=ax.imshow(z,aspect="auto",cmap=cmap,vmin=None if norm else vmin,vmax=None if norm else vmax,norm=norm); ax.figure.colorbar(im,ax=ax,label=units)
    for axis_name, names, count in (("x", kwargs.get("column_labels", x), z.shape[1]),
                                   ("y", kwargs.get("row_labels", y), z.shape[0])):
        if names is not None:
            if len(names) != count:
                raise ValueError(f"{axis_name} labels must match matrix dimensions")
            getattr(ax, "set_" + axis_name + "ticks")(np.arange(count), names)
    ax.set(xlabel=kwargs.get("xlabel", "列变量"), ylabel=kwargs.get("ylabel", "行变量"))
    return attach_metadata(ax.figure,name="heatmap",contract=contract_from(kwargs,contract),diverging=diverging,vmin=vmin,vcenter=vcenter,vmax=vmax)


def confusion_matrix(matrix, *, labels=None, contract=None, ax=None, **kwargs):
    values = finite_array(matrix, "matrix", ndim=2)
    if values.shape[0] != values.shape[1] or np.any(values < 0):
        raise ValueError("confusion matrix must be square and nonnegative")
    names = list(labels) if labels is not None else [f"类别{i+1}" for i in range(len(values))]
    if len(names) != len(values):
        raise ValueError("labels must match confusion matrix")
    fig=heatmap(values,x=names,y=names,contract=contract,ax=ax,**kwargs)
    axis=fig.axes[0]
    axis.set(xlabel="预测类别", ylabel="真实类别")
    axis.grid(False)
    image=axis.images[0]
    for (i, j), value in np.ndenumerate(values):
        rgba=image.cmap(image.norm(value))
        luminance=.2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
        axis.text(j,i,f"{value:g}",ha="center",va="center",fontsize=_style.font(),
                  color="white" if luminance < .45 else "#20252B")
    fig._figure_metadata.update(name="confusion_matrix", matrix=values.tolist(), labels=names)
    fig._figure_type="confusion_matrix"
    return fig


def response_surface(x=None, y=None, z=None, *, x_grid=None, y_grid=None, contract=None, ax=None, **kwargs):
    import numpy as np
    x_arr = finite_array(x_grid if x_grid is not None else x, "x_grid")
    y_arr = finite_array(y_grid if y_grid is not None else y, "y_grid")
    z_arr = finite_array(z, "z", ndim=2)
    if z_arr.shape != (y_arr.size, x_arr.size):
        raise ValueError("z must have shape (len(y), len(x))")
    axis = ax or _style.subplots(constrained_layout=True)[1]
    X, Y = np.meshgrid(x_arr, y_arr)
    filled = axis.contourf(X, Y, z_arr, levels=14, cmap=_style.cmap('sequential', 'GnBu'))
    axis.contour(X, Y, z_arr, levels=7, colors="white", linewidths=_style.stroke(0.45), alpha=.9)
    axis.figure.colorbar(filled, ax=axis, fraction=.046, pad=.04, label=kwargs.get("units", "响应值"))
    axis.set(xlabel=kwargs.get("xlabel", "参数 1"), ylabel=kwargs.get("ylabel", "参数 2"))
    axis.set_title("响应面图", loc="left", fontweight="bold")
    return attach_metadata(axis.figure, name="response_surface", contract=contract_from(kwargs, contract),
                           encoding="rectangular grid + filled contours", grid_shape=list(z_arr.shape))

