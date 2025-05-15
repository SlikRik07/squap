import numpy as np

from pyqtgraph import PlotDataItem, PlotItem, TextItem, ImageItem, mkPen
from PySide6.QtGui import Qt, QLinearGradient, QRadialGradient, QConicalGradient, QGradient, QPen, QBrush
from .helper_funcs import is_iter, get_single_color, is_multiple_colors
from matplotlib import colormaps as mpl_colormaps
from matplotlib.colors import Colormap
import cmasher


x_old = None
y_old = None


class PlotWidget(PlotItem):
    def __init__(self, row, col, **kargs):
        super().__init__(**kargs)
        self.row = row          # for merging
        self.col = col
        self.curves = []        # for clearing

    def base_plot(self, curve_type, *args, **kwargs):
        if len(args) == 1:
            kwargs["y"] = args[0]
            args = ()

        curve = PlotCurve(curve_type, *args, **kwargs)
        if "name" in kwargs:    # for legend
            curve.setData(name=kwargs["name"])

        self.addItem(curve)

        self.curves.append(curve)
        return curve

    def imshow(self, *args, **kwargs):
        img = ImageCurve(*args, **kwargs)
        self.addItem(img)
        return img

    def lock_zoom(self, curve):
        """
        locks zoom onto current range of a pecified curve or curves.
        :param curve: curve or curves on which the zoom should lock
        :type curve: pyqtgraph.PlotDataItem or iterable containing multiple instances of PlotDataItem
        """

        if isinstance(curve, PlotDataItem):
            x, y = curve.getData()
            self.set_xlim(min(x), max(x))
            self.set_ylim(min(y), max(y))
        else:
            try:
                x_min, x_max, y_min, y_max = [], [], [], []

                for c in curve:
                    x, y = c.getData()
                    x_min.append(min(x))
                    x_max.append(max(x))
                    y_min.append(min(y))
                    y_max.append(max(y))
                self.set_xlim(min(x_min), max(x_max))
                self.set_ylim(min(y_min), max(y_max))
            except AttributeError:
                raise TypeError(f"curve should be a curve or multiple curves, is now '{curve}'")        # error #1012

    def plot(
            self, *args, color=None, width=None, connect=None, gradient=None, antialias=None, auto_downsample=None,
            downsample=None, downsample_method=None, skip_finite_check=None, **kwargs
    ):
        """
        This function creates a new plot curve, and calls set_data with the other arguments. If both `x` and `y` are
        provided, you can set them together using `plot(x, y, ...)`. If only y is provided, using `plot(y, ...)`, `x` is
        set as the index of `y`. `x` and `y` can also be passed as keyword arguments by doing `plot(x=x, ...)`,
        `plot(y=y)` or plot(x=x, y=y, ...)`. Furthermore, you can include additional keyword
        arguments such as color and size to customize the appearance of the curve.

        :param args: Provide `x` and `y`, just `y`, or no data at all. Data can also be passed as keyword arguments.
        :param color: color of the plot. Default is 'y' (yellow).
        :param width: width of the plot line. Default is 1.
        :type width: int
        :param connect: Can be one of the following options:
            - ‘all’ connects all points.
            - ‘pairs’ generates lines between every other point.
            - ‘finite’ creates a break when a nonfinite points is encountered.
            - ‘auto’ mode, it will normally use connect=‘all’, but if any nonfinite data points are detected,
                it will automatically switch to ‘finite’.
            - If an ndarray is passed, it should contain N int32 values of 0 or 1. Values of 1 indicate that the
                respective point will be connected to the next.
            Defaults to `auto`.
            :type connect: str
        :param gradient: gradient of the line. Use `squap.get_gradient` to get the gradient. The gradient can
            be seen as a 2D image of a gradient which appears at each pixel that lies on the line. When `style` of the
            gradient is set to "horizontal" or "vertical", or "radial" without providing `position`, the bounds of the
            gradient will be automatically determined when set_data is called, which can decrease performance. So,
            specify `position` for optimal performance. Default is None.
        :type gradient: QLinearGradient or QRadialGradient or QConicalGradient

        :param downsample: Reduce the number of samples displayed by the given factor.
        :type downsample: int
        :param downsample_method: Can be one of the following options:
            - ‘subsample’: Downsample by taking the first of N samples. This method is fastest and least accurate.
                Length of datasets will be divided by downsample
            - ‘mean’: Downsample by taking the mean of N samples. Length of datasets will be divided by downsample
            - ‘peak’: Downsample by drawing a saw wave that follows the min and max of the original data. This method
                produces the best visual representation of the data but is slower. Length of dataset will stay the same.
                Defaults to "mean".
        :param auto_downsample: Can increase performance by not drawing one pixel multiple times, but is slower
                for fewer data.
        :type auto_downsample: bool
        :param antialias: By default, antialiasing is disabled to improve performance.
        :type antialias: bool
        :param skip_finite_check: Optimization flag that can speed up plotting by not checking and compensating for NaN
            values. If set to True, and NaN values exist, unpredictable behavior will occur. The data may not be displayed
            or the plot may take a significant performance hit. Defaults to False.
        :type skip_finite_check: bool
        :param kwargs: Can contain the following:
            - `x`: You can provide `x` as keyword argument as well.
            - `y`: You can provide `y` as keyword argument as well.

        :return: returns the curve generated.
        """
        # if "c" in kwargs:
        #     kwargs["color"] = kwargs["c"]
        # elif "colour" in kwargs:
        #     kwargs["color"] = kwargs["c"]

        all_kwargs = [
            "color", "width", "connect", "downsample", "downsample_method", "auto_downsample",
            "antialias", "skip_finite_check"
        ]

        for index, kwarg in enumerate([
            color, width, connect, gradient, downsample, downsample_method, auto_downsample, antialias,
            skip_finite_check
        ]):
            if kwarg is not None:
                kwargs[all_kwargs[index]] = kwarg  # only adds the ones who are not None to kwargs,
                # so that the user can still see the optional parameters, while they don't need to be passed to set_data()

        return self.base_plot("plot", *args, **kwargs)

    def scatter(
            self, *args, color=None, size=None, edge_width=None, edge_color=None, pixel_mode=None, downsample=None,
            downsample_method=None, auto_downsample=None, antialias=None, **kwargs
    ):
        """
        This function creates a new scatter curve, and calls set_data with the other arguments. If both `x` and `y` are
        provided, you can set them together using `scatter(x, y, ...)`. If only y is provided, using `scatter(y, ...)`, `x`
        is set as the index of `y`. `x` and `y` can also be passed as keyword arguments by doing `scatter(x=x, ...)`,
        `scatter(y=y)` or scatter(x=x, y=y, ...)`. Furthermore, you can include additional keyword
        arguments such as color and size to customize the appearance of the curve.

        :param args: Provide `x` and `y`, just `y`, or no data at all. Data can also be passed as keyword arguments.
        :param color: Changes the color of the curve. Can be a single color name, an RGB tuple, an RGBA tuple
            (with values between 0 and 1), or a hex code. If provided as a list or array, it should have the same length as
            `x` and `y`. `c` and `colour` are also allowed instead of `color`. Default is 'y' (yellow).
        :param size: The size of the scatter plot points. `s` is also allowed instead of `size`. Default is 7.
        :type size: float
        :param edge_width: Width of the edge around each point. Default is -1 (no edge).
        :type edge_width: int
        :param edge_color: Color of the edge around each point. Default is white.
        :param pixel_mode: Whether to fix the size of each point. If True, size is specified in pixels.
            If False, size is specified in data coordinates. Defaults to True.
        :type pixel_mode: bool
        :param downsample: Reduce the number of samples displayed by the given factor. Default is 1 (no downsampling).
        :type downsample: int
        :param downsample_method: Can be one of the following options:
            - ‘subsample’: Downsample by taking the first of N samples. This method is fastest and least accurate.
                Length of datasets will be divided by downsample.
            - ‘mean’: Downsample by taking the mean of N samples. Length of datasets will be divided by downsample.
            - ‘peak’: Downsample by drawing a saw wave that follows the min and max of the original data. This method produces
                the best visual representation of the data but is slower. Length of dataset will stay the same.
            Defaults to "mean".
        :type downsample_method: str
        :param auto_downsample: Can increase performance by not drawing one pixel multiple times, but is slower
                for fewer data.
        :type auto_downsample: bool
        :param antialias: Antialiasing is disabled by default to improve performance.
        :type antialias: bool


        :param kwargs: Can contain the following:
            - `x`: You can provide `x` as keyword argument as well.
            - `y`: You can provide `y` as keyword argument as well.

        :return: returns the curve generated.
        """
        all_kwargs = [
            "color", "size", "edge_width", "edge_color", "pixel_mode", "downsample", "downsample_method",
            "auto_downsample",
            "antialias"
        ]

        for index, kwarg in enumerate([
            color, size, edge_width, edge_color, pixel_mode, downsample, downsample_method, auto_downsample, antialias
        ]):
            if kwarg is not None:
                kwargs[all_kwargs[index]] = kwarg  # only adds the ones who are not None to kwargs,
                # so that the user can still see the optional parameters, but it won't waste a lot of time.
        # if window.is3D:           # ??
        #     del kwargs["edge_width"]

        return self.base_plot("scatter", *args, **kwargs)

    def set_xlim(self, x_min, x_max):
        """
        :param x_min: minimum x value for the plot range
        :type x_min: float
        :param x_max: maximum x value for the plot range
        :type x_max: float
        """
        self.setXRange(x_min, x_max)

    def set_ylim(self, y_min, y_max):
        """
        :param y_min: minimum x value for the plot range
        :type y_min: float
        :param y_max: maximum x value for the plot range
        :type y_max: float
        """
        self.setYRange(y_min, y_max)

    def legend(self):
        """
        Call before creating the curves!

        """
        self.addLegend()

    def set_title(self, text):
        """
        sets title to `text`

        :param text: title, can be a string or any argument accepted by `str`
        :return:
        """
        self.setTitle(text)

    def add_text(self, text, pos):
        textbox = TextItem(str(text))
        self.addItem(textbox)
        textbox.setPos(*pos)

    def clear(self):
        for curve in self.curves:
            curve.clear()


class PlotCurve(PlotDataItem):
    kwarg_mapping = {
        "c": "color", "colour": "color", "w": "width", "downsample_method": "downsampleMethod",
        "skip_finite_check": "skipFiniteCheck", "auto_downsample": "autoDownsample",
        "s": "symbolSize", "size": "symbolSize", "symbol_size": "symbolSize", "pixel_mode": "pxMode",
        "clip_to_view": "clipToView", "symbol_colour": "symbol_color", "symbol_lc": "symbol_line_color",
        "symbol_lw": "symbol_line_width"
    }   # last line is the ones for scatter only, downsample for both, rest for line. (not completely sure)
    all_pen_kwargs = ["line_color", "width", "dashed", "dash_pattern"]
    all_symbol_kwargs = ["symbol_color", "symbol_line_width",  "symbol_line_color"]
    all_other_kwargs = [
        "symbolSize", "symbolBrush", "symbol", "connect", "pxMode", "antialias", "skipFiniteCheck", "downsample",
        "downsampleMethod", "autoDownsample", "clipToView", "symbolPen"
    ]

    def __init__(self, curve_type="plot", *args, **kwargs):
        super().__init__()
        self.curve_type = curve_type
        if curve_type == "plot":
            self.pen = mkPen(color="y")
            self.pen.setCosmetic(True)
            self.setPen(self.pen)
            self.set_data(downsample_method="subsample")
        elif curve_type == "scatter":
            self.pen = None
            self.setPen(self.pen)
            self.set_data(symbol='o', s=6, downsample_method="subsample")
            self.setSymbolPen(None)
            self.setSymbolBrush(get_single_color("y"))
        else:
            raise ValueError(f"curve_type {curve_type} is not a valid type of curve.")  # error #1000

        self.symbol_lw = 0
        self.symbol_lc = "white"
        self.gradient = None     # is only changed when autoscaling of the gradient is required

        self.set_data(*args, **kwargs)

    # def setData(self, suppress_warnings=False, *args, **kwargs):
    #     if not suppress_warnings:     # temporarily disabled warning
    #         print("warning")
    #         warnings.warn("Method setData deprecated for usage in squap.")
    #     else:
    #         print("not warning")
        # super(PlotCurve, self).setData(*args, **kwargs)

    def clear(self):
        self.setData()

    def set_data(self, x=x_old, y=y_old, **kwargs):
        """
        This function updates the data of a plot curve. If both x and y are provided, you can set them together
        using set_data(x, y, ...). If either x or y is provided, you can set them individually, for example,
        set_data(x=x, ...) or set_data(y=y, ...). Furthermore, you can include additional keyword
        arguments such as color and width to customize the appearance of the curve. Note that for scatter points,
        symbol_color is used for the color of points instead of color. In scatter(), color is allowed for the points.

        :param x: New x-locations of each point. Defaults to the previous value of x.
        :param y: New y-locations of each point. Defaults to the previous value of y.

        :param kwargs: Can contain the following:
            - `color`: Changes the color of the curve. For a scatter-plot this is equivalent to symbol_color, for a
                regular plot is equivalent to line_color. `colour` or `c` is also allowed instead of `color`.
            - `width` (float): Changes the width (in pixels) of the curve. `w` is also allowed instead of `width`.
            - `line_color`: Changes the color of the line. It can only be a single color name, an RGB tuple,
                a float between 0.0 (black) and 1.0 (white), an integer (where each integer corresponds to a different
                color already), a hex code or of type gradient (created with `squap.get_gradient`).
            - `dashed` (bool): If True, draws a dashed line between the points (for more options see dash_pattern).
                Starts off as False.
            - `dash_pattern` (List[int]): How the dashes are spaced. For example, if `dash_pattern` is [16, 16, 4, 16],
                the pattern will be: one dash of 16 pixels long, then a space of 16 pixels long, then a dash of 4 pixels
                long and then a dash of 16 pixels long. This pattern is then repeated. This should be a list with a
                length that is an integer multiple of 2. Starts off at [16, 16].
            - `line_style` (str): todo: some presets for simplicity, `ls` is also allowed instead of `line_style`.
            - `gradient`: gradient of the line. Use `squap.get_gradient` to get the gradient. The gradient can
                be seen as a 2D image of a gradient which appears at each pixel that lies on the line. When `style` of
                the gradient is set to "horizontal" or "vertical", or "radial" without providing `position`, the bounds
                of the gradient will be automatically determined when set_data is called, which can decrease
                performance. So, specify `position` for optimal performance. Default is None.
            - `fill_level`: fills the area under the curve to this Y-value. When provided, either provide `fill_color`
                or `fill_gradient`. Default is None.
            - `fill_color`: color of the filled area.
            - `fill_gradient`: gradient of the filled area.
            - `symbol_size` (int): The size (in pixels) of each symbol. Can also be a list or array.
                `s` and `size` are also allowed instead of `symbol_size`.
            - `symbol_color`: Changes the color of the symbols. It can be a single color name, an RGB tuple (with values
                between 0 and 1), one float between 0.0 (black) and 1.0 (white), an integer (where each integer
                corresponds to a different color already), or a hex code, or it can be multiple colors of the
                previous types. If multiple colors are provided, there should be as many colors as there are points.
            - `symbol` (str): symbol to draw at each (x, y) location. Can be e.g.: "o" for circles (default), "t" for
                triangles, "s" for squares, "d" for diamonds. For all options see an example that I still have to make.
            - `symbol_line_width` (int): the line width each symbol is drawn with, `symbol_lw is` also allowed.
            - `symbol_line_color`: Change the color of the line around each symbol (Same allowed values
                as symbol_color), `symbol_lc` is also allowed.
            - `connect` (str): Can be one of the following options:
                - ‘all’ connects all points.
                - ‘pairs’ generates lines between every other point.
                - ‘finite’ creates a break when a nonfinite point is encountered.
                - ‘auto’ mode, it will normally use connect=‘all’, but if any nonfinite data points are detected,
                    it will automatically switch to ‘finite’.
                - If an ndarray is passed, it should contain N int32 values of 0 or 1. Values of 1 indicate that the
                    respective point will be connected to the next.
            - `pixel_mode` (bool): Whether to fix the size of each point. If True, size is specified
                in pixels. If False, size is specified in data coordinates.
            - `antialias` (bool): Antialiasing is disabled by default to improve performance.
            - `skip_finite_check` (bool): Optimization flag that can speed up plotting by not checking and
                compensating for NaN values. If set to True, and NaN values exist, unpredictable behavior will occur.
                The data may not be displayed or the plot may take a significant performance hit. Defaults to False.
            - `downsample` (int): Reduce the number of samples by the given factor
            - `downsample_method` (str): Can be one of the following options:
                - ‘subsample’: Downsample by taking the first of N samples. This method is fastest and least accurate.
                    Length of datasets will be divided by downsample.
                - ‘mean’: Downsample by taking the mean of N samples. Length of datasets will be divided by downsample.
                - ‘peak’: Downsample by drawing a saw wave that follows the min and max of the original data.
                    This method produces the best visual representation of the data but is slower. Length of dataset
                    will stay the same.
                Defaults to `subsample`.
            - `auto_downsample` (bool): Can increase performance by not drawing one pixel multiple times, but is slower
                for fewer data.
            - `clip_to_view` (bool): If True, only data visible within the X range of the containing ViewBox is plotted.
                This can improve performance when plotting very large data sets where only a fraction of the data
                is visible at any time.
        """
        if x is None and y is None:     # needed for autoscaling gradient, so done here.
            x, y = self.getData()
        elif y is None:
            y = self.getData()[1]
            if y is None:
                y = np.zeros(len(x))
        elif x is None:
            x = self.getData()[0]
            if x is None:
                x = np.zeros(len(y))

        other_kwargs = {}           # `setData` needs to be done in one command, so other kwargs that need to be passed
        # to it are added to this dict. If the data is updated, this is also passed as the kwargs.
        if kwargs:      # if anything else is changed, run this bit
            new_kwargs = self.transform_kwargs(kwargs)

            if "color" in new_kwargs:
                if self.curve_type == "scatter":
                    new_kwargs["symbol_color"] = new_kwargs["color"]
                else:
                    new_kwargs["line_color"] = new_kwargs["color"]

            pen_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_pen_kwargs if kwarg in new_kwargs}
            if pen_kwargs:
                if self.pen is None:
                    self.pen = mkPen()
                if "line_color" in pen_kwargs:
                    if isinstance(pen_kwargs["line_color"], QGradient):
                        self.gradient = pen_kwargs["line_color"]
                        if self.gradient.autoscale:
                            if self.gradient.style == "horizontal":
                                self.gradient.setStart(min(x), 0)
                                self.gradient.setFinalStop(max(x), 0)
                            elif self.gradient.style == "vertical":
                                self.gradient.setStart(0, min(y))
                                self.gradient.setFinalStop(0, max(y))
                            else:           # gradient.style must be "radial" here
                                self.gradient.setStart(min(x), min(y))

                        cmap = self.gradient.cmap


                        if isinstance(cmap, str):
                            if cmap in mpl_colormaps:
                                cmap = mpl_colormaps[cmap]
                            elif hasattr(cmasher, cmap):
                                cmap = getattr(cmasher, cmap)
                            else:
                                if cmap[:4] == "mpl_":
                                    cmap = cmap[4:]
                                    if cmap in mpl_colormaps:
                                        cmap = mpl_colormaps[cmap]
                                    else:
                                        raise ValueError(
                                            f"cmap {cmap[4:]} is not an existing cmap in matplotlib."
                                        )
                                elif cmap[:8] == "cmasher_":
                                    cmap = cmap[8:]
                                    if hasattr(cmasher, cmap):
                                        cmap = getattr(cmasher, cmap)
                                    else:
                                        raise ValueError(
                                            f"cmap {cmap[8:]} is not an existing cmap in cmasher."
                                        )
                                else:
                                    raise ValueError(
                                        f"cmap {self.gradient.cmap} is not an existing cmap in matplotlib or cmasher."
                                    )
                        if isinstance(cmap, Colormap):
                            for i in range(self.gradient.resolution):
                                value = cmap(i/(self.gradient.resolution-1))
                                self.gradient.setColorAt(i/(self.gradient.resolution-1), get_single_color(value))
                        elif isinstance(cmap, list):
                            N = len(cmap)
                            for i, value in enumerate(cmap):
                                self.gradient.setColorAt(i/(N-1), get_single_color(value))
                        elif isinstance(cmap, dict):
                            for key, value in cmap.items():
                                self.gradient.setColorAt(key, get_single_color(value))
                        else:
                            raise TypeError("cmap is of incorrect type. Must be str, list or dict.")

                        self.pen.setBrush(self.gradient)
                    else:
                        self.pen.setBrush(get_single_color(pen_kwargs["line_color"]))

                if "width" in pen_kwargs:
                    self.pen.setWidth(pen_kwargs["width"])
                if "dashed" in pen_kwargs:
                    if pen_kwargs["dashed"]:
                        self.pen.setStyle(Qt.PenStyle.DashLine)
                        self.pen.setDashPattern([16, 16])
                    else:
                        self.pen.setStyle(Qt.PenStyle.SolidLine)
                if "dash_pattern" in pen_kwargs:
                    self.pen.setDashPattern(pen_kwargs["dash_pattern"])
                self.setPen(self.pen)
            symbol_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_symbol_kwargs if kwarg in new_kwargs}
            if symbol_kwargs:
                if "symbol_color" in symbol_kwargs:
                    col = symbol_kwargs["symbol_color"]
                    if is_multiple_colors(col):
                        new_kwargs["symbolBrush"] = [get_single_color(col_i) for col_i in col]
                    else:
                        new_kwargs["symbolBrush"] = get_single_color(col)

                if "symbol_line_width" in symbol_kwargs or "symbol_line_color" in symbol_kwargs:
                    if "symbol_line_width" in symbol_kwargs:
                        self.symbol_lw = symbol_kwargs["symbol_line_width"]
                    if "symbol_line_color" in symbol_kwargs:
                        self.symbol_lc = symbol_kwargs["symbol_line_color"]
                    mult_col, mult_lw = is_multiple_colors(self.symbol_lc), is_iter(self.symbol_lw)
                    if mult_col:
                        if mult_lw:
                            symbol_pen = [
                                mkPen(color, width=width) for color, width in zip(self.symbol_lc, self.symbol_lw)
                            ]
                        else:
                            symbol_pen = [mkPen(color, width=self.symbol_lw) for color in self.symbol_lc]
                    else:
                        if mult_lw:
                            symbol_pen = [mkPen(self.symbol_lc, width=width) for width in self.symbol_lw]
                        else:
                            symbol_pen = mkPen(self.symbol_lc, width=self.symbol_lw)
                    new_kwargs["symbolPen"] = symbol_pen

            other_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_other_kwargs if kwarg in new_kwargs}

        x_is_iter_or_none, y_is_iter_or_none = is_iter(x) or x is None, is_iter(y) or y is None
        if x_is_iter_or_none == y_is_iter_or_none:  # Ensures both are iterables or neither
            self.setData(x=[x] if not x_is_iter_or_none else x,
                         y=[y] if not y_is_iter_or_none else y,
                         **other_kwargs)
        else:
            raise TypeError(f"`x` and `y` must both be iterables or both not be iterables. "
                            f"Currently, `x` is {'not ' if not is_iter(x) else ''}iterable "
                            f"and `y` is {'not ' if not is_iter(y) else ''}iterable.")

    def transform_kwargs(self, kwargs):
        return {self.kwarg_mapping.get(k, k): v for k, v in kwargs.items()}


class ImageCurve(ImageItem):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if args:
            self.setImage(*args)

    def set_data(self, *args, **kwargs):
        if args:
            self.setImage(*args)
