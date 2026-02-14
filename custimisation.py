from .helper_funcs import get_single_color, get_cmap, Font, ColorType
from typing import Iterable, Callable
from PySide6.QtGui import QLinearGradient, QRadialGradient, QConicalGradient, QGradient, QCursor, QGuiApplication
from PySide6.QtCore import QPointF
from matplotlib import colors
import numpy as np


def get_font(*args, **kwargs) -> Font:
    """Get font object. Used for defining more complex fonts.

    todo: write docstring and add args and kwargs to view.
    """
    return Font(*args, **kwargs)


def get_gradient(cmap: str | colors.Colormap | Iterable | dict, style: str = "horizontal",
                 position: Iterable | None = None, extend: str = "pad", resolution: int = 256) -> QGradient:
    """Obtain a gradient. Gradients can sometimes be used instead of normal colors.

    The gradient can be seen as a 2D image of a gradient spaced depending on `position`. Only the parts are shown at
    each pixel that is drawn by eg. a plot line. When `style` of the gradient is set to "horizontal" or "vertical", or
    "radial" without providing `position`, the bounds of the gradient will be automatically determined when set_data is
    called. Specify `position` for optimal performance.

    Args:
        cmap (str, ditc, Iterable, Colormap): The colormap used as gradient. Can either be a string, a dictionary,
            a list of colors or an instance of `matplotlib.colors.Colormap`.
            When a string is passed, it is any colormap name accepted by matplotlib. When a colormap exists for both
            matplotlib and cmasher, matplotlib will be used. Use "mpl_ocean" and "cmasher_ocean" to explicitly select
            matplotlib or cmasher.
            When a dictionary is passed, it specifies the color for different inputs. The color corresponding to
            0 is indicated by cmap[0], and cmap[1] is the end. The rest of the dictionary entries are other points at which
            the color is specified. The gradient is a linear interpolation between each of these points.
            When a list of colors is passed, the colormap is a linear interpolation between the colors, equally spaced
            between 0 and 1.
        style (str): The style of the gradient. Can be "horizontal" or "vertical" for a simple horizontal or vertical
            gradient. Can be "linear", which forms a gradient from `position[0]` (tuple) to `position[1]` (tuple). Can
            be "radial", which forms a radial gradient with centre `position[0]` (tuple) and radius
            `position[1]` (float). If `position` is not specified, this is automatically determined. Can be "conical",
            which forms a conical gradient (a gradient that is constant along the radius and varies along as the
            angle varies). `position[0]` (tuple) specifies the centre, and `postion[1]` (float) the starting angle
             (in degrees from the positive y-axis). If `position` is not provided, it is automatically determined, with
             starting angle set to 0. Defaults to "horizontal".
        position (Iterable): See style.
        extend (str): How the gradient behaves outside the range specified in `position`. Can be "pad", "repeat" or
            "reflect" (only applies when style is "linear" or "radial" and `position` is specified). Defaults to "pad".
        resolution (int): The resolution of the gradient, when it is a matplotlib (or cmasher) cmap. Does not do
            anything when the cmap is a dict or a list. Defaults to 256.

    Returns: A gradient object.
    """
    style = style.lower()
    extend = extend.lower()
    if style in ["horizontal", "vertical"]:
        if position is not None:
            raise ValueError(f"If gradient has style {style}, position must not be specified.")
        else:
            gradient = QLinearGradient()
            gradient.autoscale = True

    elif style == "linear":
        if position is None:
            raise ValueError(f"If gradient has style {style}, position must be specified.")
        else:
            gradient = QLinearGradient(QPointF(*position[0]), QPointF(*position[1]))
            gradient.autoscale = False
    elif style == "radial":
        if position is None:
            gradient = QRadialGradient()
            gradient.autoscale = True
        else:
            gradient = QRadialGradient(QPointF(*position[0]), position[1])
            gradient.autoscale = False
    elif style == "conical":
        if position is None:
            gradient = QConicalGradient()
            gradient.autoscale = True
        else:
            gradient = QConicalGradient(QPointF(*position[0]), position[1])
            gradient.autoscale = False
    else:
        raise ValueError('`style` must be "horizontal", "vertical", "linear", "radial" or "conical".')

    if extend == "pad":
        gradient.setSpread(QGradient.PadSpread)
    elif extend == "repeat":
        gradient.setSpread(QGradient.RepeatSpread)
    elif extend == "reflect":
        gradient.setSpread(QGradient.ReflectSpread)
    else:
        raise ValueError('`extend` must be "pad", "repeat" or "reflect".')

    gradient.cmap = cmap
    gradient.style = style
    gradient.resolution = resolution
    return gradient


def cmap_to_colors(cmap, N_points):       # todo: temporary, make this better
    colors = np.zeros((N_points, 4))
    if isinstance(cmap, dict):
        col_arr = np.array(list(np.array(get_single_color(col).toTuple()) for col in cmap.values()))
        x_arr = np.linspace(0, 1, N_points)
        for i in range(4):
            colors[:, i] = np.interp(x_arr, list(cmap.keys()), col_arr[:, i])
    else:
        for i in range(N_points):
            colors[i] = cmap(i / (N_points - 1))

    return colors

