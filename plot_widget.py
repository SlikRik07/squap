import numpy as np
import os.path

from pyqtgraph import PlotDataItem, PlotItem, InfiniteLine, TextItem, ImageItem, mkPen, InfLineLabel, GridItem, \
    getConfigOption, ErrorBarItem
from PySide6.QtGui import QFont, QLinearGradient, QRadialGradient, QConicalGradient, QGradient, QPen, QBrush, Qt
from .helper_funcs import is_iter, get_single_color, is_multiple_colors, cmap_to_gradient, update_pen, Font, \
    transform_kwargs, get_cmap, get_new_kwargs, ColorType
from copy import copy
from typing import Iterable, Any
from numbers import Number      # for type hinting


class PlotWidget(PlotItem):
    def __init__(self, row: int, col: int, **kwargs):
        super().__init__(**kwargs)
        self.row = row          # for merging subplots
        self.col = col
        self.curves = []        # for clearing curves

    def base_plot(self, curve_type: str, *args, **kwargs):
        if len(args) == 1:
            kwargs["y"] = args[0]
            args = ()

        curve = PlotCurve(self, curve_type, *args, **kwargs)
        if "name" in kwargs:    # for legend
            curve.setData(name=kwargs["name"])

        self.addItem(curve)

        self.curves.append(curve)
        return curve

    def plot_text(self, text: str, pos: Iterable[Number], color: ColorType = (200, 200, 200), angle: Number = 0,
                  font: str | Font | None = None, font_size: int | None = None, html: str | None = None,
                  text_width: int | None = None, **kwargs):
        """ Displays text at coordinates pos. See `squap.get_font` for more information on fonts.

        Args:
            text (str): The text to be displayed.
            pos (Iterable[Number]): The position of the text in coordinates on the 2D plane.
            color (optional): Color of the text. Defaults to gray.
            angle (Number, optional): Angle at which the text is placed in degrees. Defaults to 0.
            font (str | Font, optional): The font of the text. Defaults to Segoe UI.
            font_size (int, optional): if set to 0 or negative, system default fontsize is used (usually 12)
            html (str, optional): The html to display, overwrites all other font arguments. Defaults to None.
            text_width (int, optional): The width of the text. Todo: check how it works
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["text_width", "font", "font_size", "html"],
                                    exclude_args=["self", "kwargs", "text", "pos"])

        text = TextWidget(text, pos, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases
        self.addItem(text)
        return text

    def imshow(self, data: Iterable | None = None, location: Iterable | None = None, cmap: Any = None,
               auto_levels: bool = False, levels=None, axis_order="row-major",
               border_color: ColorType | None = None, **kwargs):      # **kwargs for aliases
        """
        Plots an image at location `location`. This image consists of equally spaced pixels, colored according to `data`
        and `cmap`.

        Args:
            data (np.ndarray, optional): Array containing data to be shown. Can be shape:
                (Nx, Ny, 3): array of colors, between 0 and 1.
                (Nx, Ny, 4): array of colors, between 0 and 1, with alpha values.
                (Nx, Ny): array of values between 0 and 1, corresponding to grayscale or colors corresponding to `cmap`
                if it is provided.

            location (tuple, optional): Location of the image. `(location[0], location[1])` is the bottom left coordinate, and
                `(location[2], location[3])` is the top right coordinate.
            cmap: Colormap from `squap.get_colormap` or `data` argument accepted by squap.get_colormap`.
            auto_levels (bool, optional): todo: describe
            levels (optional): todo: describe
            axis_order (bool, optional): Whether the ordering of the pixels listed in `data` is "row-major" or
                "col-major". Todo: test if it does anything.
            border_color (optional): Color of the border around the image. Defaults to `None`, meaning no border.
            todo: border thickness?
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["location"],
                                    exclude_args=["self", "args", "kwargs"])

        img = ImageCurve(**new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases
        self.addItem(img)
        return img

    def lock_zoom(self, curves: Iterable):
        """
        Locks zoom onto current range of specified curves. Works only if curves are normal curves with x- and y- data.

        Args
            curves (Iterable): curves on which the zoom should lock
        """
        x_min, x_max, y_min, y_max = [], [], [], []

        for curve in curves:
            x, y = curve.getData()
            x_min.append(min(x))
            x_max.append(max(x))
            y_min.append(min(y))
            y_max.append(max(y))
        self.set_xlim(min(x_min), max(x_max))
        self.set_ylim(min(y_min), max(y_max))

    def plot(
            self, *args, color="y", width=1, dashed=False, dash_pattern=None, connect="auto", gradient=None,
            line_style=None, antialias=False, auto_downsample=False, downsample=1, downsample_method="mean",
            skip_finite_check=False, **kwargs
    ):
        """
        Create a new plot curve, and calls set_data with the other arguments. If both `x` and `y` are
        provided, you can set them together using `plot(x, y, ...)`. If only y is provided, using `plot(y, ...)`, `x` is
        set as the index of `y`. `x` and `y` can also be passed as keyword arguments by doing `plot(x=x, ...)`,
        `plot(y=y)` or plot(x=x, y=y, ...)`. Furthermore, you can include additional keyword
        arguments such as color and size to customize the appearance of the curve.

        :param args: Provide `x` and `y`, just `y`, or no data at all. Data can also be passed as keyword arguments.
        :param color: color of the line. Default is 'y' (yellow). Can also be a gradient (see `squap.get_gradient`).
        :param width: width of the plot line. Default is 1.
        :type width: int
        :param dashed: If True, draws a dashed line between the points (for more options see dash_pattern).
            Default is False.
        :type dashed: bool
        :param dash_pattern: How the dashes are spaced. For example, if `dash_pattern` is [16, 16, 4, 16], the pattern
            will be: one dash of 16 pixels long, then a space of 16 pixels long, then a dash of 4 pixels long and then
            a dash of 16 pixels long. This pattern is then repeated. This should be a list with a length that is an
            integer multiple of 2. Starts off at [16, 16].
        :type dash_pattern: List[int]
        :param connect: Can be one of the following options:
            - ‘all’ connects all points.
            - ‘pairs’ generates lines between every other point.
            - ‘finite’ creates a break when a nonfinite points is encountered.
            - ‘auto’ mode, it will normally use connect=‘all’, but if any nonfinite data points are detected,
                it will automatically switch to ‘finite’.
            - If an ndarray is passed, it should contain N int32 values of 0 or 1. Values of 1 indicate that the
                respective point will be connected to the next.
            Defaults to `auto`.
        :type connect: str or np.ndarray
        :param gradient: gradient of the line. Use `squap.get_gradient` to get the gradient. The gradient can
            be seen as a 2D image of a gradient which appears at each pixel that lies on the line. When `style` of the
            gradient is set to "horizontal" or "vertical", or "radial" without providing `position`, the bounds of the
            gradient will be automatically determined when set_data is called, which can decrease performance. So,
            specify `position` for optimal performance. Default is None.
        :type gradient: QLinearGradient or QRadialGradient or QConicalGradient
        :param line_style: todo: some presets for simplicity, `ls` is also allowed instead of `line_style`.
        :type line_style: str
        :param downsample: Reduce the number of samples displayed by the given factor. Default is 1 (no downsampling).
        :type downsample: int
        :param downsample_method: Can be one of the following options:
            - ‘subsample’: Downsample by taking the first of N samples. This method is fastest and least accurate.
                Length of datasets will be divided by downsample
            - ‘mean’: Downsample by taking the mean of N samples. Length of datasets will be divided by downsample
            - ‘peak’: Downsample by drawing a saw wave that follows the min and max of the original data. This method
                produces the best visual representation of the data but is slower. Length of dataset will stay the same.
                Defaults to "mean".
        :param auto_downsample: Can increase performance by not drawing one pixel multiple times, but is slower
                for fewer data. Defaults to False.
        :type auto_downsample: bool
        :param antialias: By default, antialiasing is disabled to improve performance.
        :type antialias: bool
        :param skip_finite_check: Optimization flag that can speed up plotting by not checking and compensating for NaN
            values. If set to True, and NaN values exist, unpredictable behavior will occur. The data may not be
            displayed or the plot may take a significant performance hit. Defaults to False.
        :type skip_finite_check: bool
        :param kwargs: Can contain the following:
            - `x`: You can provide `x` as keyword argument as well.
            - `y`: You can provide `y` as keyword argument as well.

        :return: returns the curve generated.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["dash_pattern", "gradient", "line_style"],
                                    exclude_args=["self", "args", "kwargs"])

        return self.base_plot("plot", *args, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

    def scatter(
            self, *args, color="y", size=7, edge_width=-1, edge_color="white", pixel_mode=True, downsample=1,
            downsample_method="mean", auto_downsample=False, antialias=False, **kwargs
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
        :param edge_color: Color of the edge around each point. Default is white.
        :param edge_width: Width of the edge around each point. Default is -1 (no edge).
        :type edge_width: int
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
                for less data. Defaults to False.
        :type auto_downsample: bool
        :param antialias: Antialiasing is disabled by default to improve performance.
        :type antialias: bool


        :param kwargs: Can contain the following:
            - `x`: You can provide `x` as keyword argument as well.
            - `y`: You can provide `y` as keyword argument as well.

        :return: returns the curve generated.
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self", "args", "kwargs"])

        return self.base_plot("scatter", *args, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

    def errorbar(self, *args, x_err=None, y_err=None, color: ColorType = "y", width: int = 1, errorbar_width: int = 1,
                 beam_size: Number = 0, dashed: bool = False, dash_pattern: Iterable[int] = None, connect: str = "auto",
                 gradient=None, line_style=None,
                 antialias=False, auto_downsample=False, downsample=1, downsample_method="mean",
                 skip_finite_check=False, **kwargs):
        """
        Create a line with errorbars at the x and y positions.

        Args:
            *args: For providing `x` and `y`. (Can also be provided as keyword arguments). `x` and `y` must be the same
                length. If only one argument is provided, it is interpreted as `y` and `x` is set
                to `list(range(len(y))`
            x_err: Size of the errorbar at each x value. Can be the following types:
                None or single value: x-error at all points.
                Array of same size as x: x-error at each point.
                Array of size (Nx, 2): `x_err[0]` is the error on the left at each point, and `x_err[1]` is the error
                    on the right at each point.
                Defaults to None: no x-error.
            y_err: Same as `x_err` but for `y`.
            color: Color of the line and errorbar. Default is 'y' (yellow). Can also be a gradient (see
                `squap.get_gradient`). If the color of the line and of the errorbar should be different, provide both
                `line_color` and `error_color`.
            width (int): Width of the plot line. Default is 1. Does not affect the width of the errorbars.
            errorbar_width (int): Width of the errorbar lines. Default is 1.
            beam_size (float): Size of the bars at the ends of the errorbar lines. Default is 0.
            connect (str): Can be one of the following options:
                - ‘all’ connects all points.
                - ‘pairs’ generates lines between every other point.
                - ‘finite’ creates a break when a nonfinite points is encountered.
                - ‘auto’ mode, it will normally use connect=‘all’, but if any nonfinite data points are detected,
                    it will automatically switch to ‘finite’.
                - If an ndarray is passed, it should contain N int32 values of 0 or 1. Values of 1 indicate that the
                    respective point will be connected to the next.
                Defaults to `auto`.
            gradient (QGradient): gradient of the line. Use `squap.get_gradient` to get the gradient. The gradient can
                be seen as a 2D image of a gradient which appears at each pixel that lies on the line. When `style` of
                the gradient is set to "horizontal" or "vertical", or "radial" without providing `position`, the bounds
                of the gradient will be automatically determined when set_data is called, which can decrease
                performance. So, specify `position` for optimal performance. Default is None.
            dashed (bool): If set to `True`, draws a dashed line between the points (for more options see dash_pattern).
            dash_pattern (List[int]): How the dashes are spaced. For example, if `dash_pattern` is [16, 16, 4, 16],
                the pattern will be: one dash of 16 pixels long, then a space of 16 pixels long, then a dash of 4 pixels
                long and then a dash of 16 pixels long. This pattern is then repeated. This should be a list with a
                length that is an integer multiple of 2. Starts off at [16, 16].
            line_style (str): todo: some presets for simplicity, `ls` is also allowed instead of `line_style`.
            downsample (int): Reduce the number of samples displayed by the given factor. Default is 1 (no
                downsampling).
            downsample_method (str): Can be one of the following options:
                - ‘subsample’: Downsample by taking the first of N samples. This method is fastest and least accurate.
                    Length of datasets will be divided by downsample
                - ‘mean’: Downsample by taking the mean of N samples. Length of datasets will be divided by downsample
                - ‘peak’: Downsample by drawing a saw wave that follows the min and max of the original data. This method
                    produces the best visual representation of the data but is slower. Length of dataset will stay the same.
                    Defaults to "mean".
            auto_downsample (bool): Can increase performance by not drawing one pixel multiple times, but is slower
                for fewer data.
            antialias (bool): By default, antialiasing is disabled to improve performance.
            skip_finite_check (bool): Optimization flag that can speed up plotting by not checking and compensating
                for NaN values. If set to True, and NaN values exist, unpredictable behavior will occur. The data may
                not be displayed or the plot may take a significant performance hit. Defaults to False.
            **kwargs: Can contain the following:
                - `x`: You can provide `x` as keyword argument as well.
                - `y`: You can provide `y` as keyword argument as well.
                - `line_color`: For seperating errorbar and line color.
                - `error_color`: For seperating errorbar and line color.
                - `line_width`: For seperating errorbar and line width.
                - `error_width`: For seperating errorbar and line width.

        Returns:
             The created curve. The errorbar curve is located at `curve.errorbar_curve`, but everything can be set with
             just `curve.set_data(...)`.
        """

        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["errorbar_color", "errorbar_width", "dash_pattern", "gradient",
                                                 "line_style"],
                                    exclude_args=["self", "args", "kwargs"])

        return self.base_plot("plot", *args, **new_kwargs, **kwargs)

    def inf_dline(self, pos, angle=45, color="y", width=1, dashed=False, dash_pattern=None, line_style=None,
                  movable=False, bounds=None, span=(0, 1), line_movable=None, label=False, label_text="{value}",
                  label_movable=None, label_position=0.5, label_anchors=None, hover_color="red", hover_width=1,
                  name=None, **kwargs):
        """
        This function is used to create an infinite line and add it to the view.

        :param pos: A position through which the line runs. When `angle` is 0 or 90 this can be a single value: the
            y- or x-value of the line respectively.
        :type pos: tuple or float
        :param angle: The angle of the line in degrees. 0 is horizontal, 90 is vertical. Default is 45.
        :type angle: float
        :param color: Color of the line. Default is 'y' (yellow). Can also be a gradient (see `squap.get_gradient`).
        :param width: Width of the plot line. Default is 1.
        :type width: int
        :param dashed: If True, the line becomes dashed (for more options see dash_pattern). Default is False.
        :type dashed: bool
        :param dash_pattern: How the dashes are spaced. For example, if `dash_pattern` is [16, 16, 4, 16], the pattern
            will be: one dash of 16 pixels long, then a space of 16 pixels long, then a dash of 4 pixels long and then
            a dash of 16 pixels long. This pattern is then repeated. This should be a list with a length that is an
            integer multiple of 2. Defaults to [16, 16].
        :type dash_pattern: List[int]
        :param line_style: todo: some presets for simplicity, `ls` is also allowed instead of `line_style`.
        :type line_style: str
        :param bounds: Optional (min, max) bounding values. Bounds are only valid if the line is vertical or horizontal.
            Default is no bounds.
        :type bounds: tuple
        :param span: The length of the line on screen. The first number is how far it extends to
        :type span: tuple
        :param movable: Whether the line (and label if it exists) is movable or not. Default is False.
        :type movable: bool
        :param line_movable: Whether the line is movable or not. Overwrites `movable` if changed. Default is None.
        :type line_movable: bool
        :param label: The label doesn't work completely yet, I think this is due to pyqtgraph itself. Will look into
            this later. If True, a label is added to the line. Default is False.
        :type label: bool
        :param label_text: The text that is shown on the label. `{value}` can be used inside the string, which will be
            replaced by the lines current position. Default is False.
        :type label_text: str
        :param label_movable: Whether the label is movable or not. Overwrites `movable` if changed. Default is None.
        :type label_movable: bool
        :param label_position: The relative position (between 0.0 and 1.0) of this label within the view box and
            along the line. Default is 0.5, meaning in the middle.
        :type label_position: float
        :param label_anchors: todo: write
        :type label_anchors: List[tuple]
        :param hover_color: Color to use when the mouse cursor hovers over the line. Only used when movable=True.
            Default is red.
        :param hover_width: Width to use when the mouse cursor hovers over the line. Default is 1.
        :type hover_width: int
        :param name: Name of the item
        :type name: str

        :param kwargs: some aliases are allowed
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["dash_pattern", "line_style"],
                                    exclude_args=["self", "pos", "kwargs"])

        line = InfLine(pos, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

        self.addItem(line)
        self.curves.append(line)
        return line

    def inf_hline(self, pos, color="y", width=1, dashed=False, dash_pattern=None, line_style=None,
                  movable=False, bounds=None, span=(0, 1), line_movable=None, label=False, label_text="y={value}",
                  label_movable=None, label_position=0.5, label_anchors=None, hover_color="red", hover_width=1,
                  name=None, **kwargs):
        """
        This function is used to create a horizontal infinite line and add it to the view. This function is the same as
        inf_dline(pos, angle=0, ...) but instead the default label_text is now 'y={value}'
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["dash_pattern", "line_style"],
                                    exclude_args=["self", "pos", "kwargs"])

        line = InfLine(pos, angle=0, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

        self.addItem(line)
        self.curves.append(line)
        return line

    def inf_vline(self, pos, color="y", width=1, dashed=False, dash_pattern=None, line_style=None,
                  movable=False, bounds=None, span=(0, 1), line_movable=None, label=False, label_text="x={value}",
                  label_movable=None, label_position=0.5, label_anchors=None, hover_color="red", hover_width=1,
                  name=None, **kwargs):
        """
        This function is used to create a horizontal infinite line and add it to the view. This function is the same as
        inf_dline(pos, angle=90, ...) but instead the default label_text is now 'x={value}'
        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=["dash_pattern", "line_style"],
                                    exclude_args=["self", "pos", "kwargs"])

        line = InfLine(pos, angle=90, **new_kwargs, **kwargs)
        # new_kwargs gets constructed from normal keyword args, but skips kwargs, which mostly just contains aliases

        self.addItem(line)
        self.curves.append(line)
        return line

    def grid(self, tick_spacing=None, color=None, width=1, **kwargs):
        """
        This function is used to create a grid and add it to view. Todo: improve

        :param tick_spacing: Set the grid spacing. When set to `None` grid line distance is chosen automatically.
            When an iterable is given, give x- and y-spacing. When 1 value is given, this value is used for both x
            and y. For more complex scaling you can set the x- and y-spacing on different scales. Eg. passing
            `([1, 100], None)` will mean x-spacing is automatically determined to be either 1 or 100, and y-spacing is
            completely automatic. Replacing `[1, 100]` by `[1, 100, None]` will mean it can be 1 or 100 depending on
            zoom level, or it can be completely automatic for anything outside this range.
        :param tick_spacing: tuple or number
        :param color: Color of the lines. Defaults to the config foreground color.
        :param width: Width of the plot line. Default is 1.
        :type width: int

        :param kwargs: some aliases are allowed

        """
        new_kwargs = get_new_kwargs(locals(),
                                    none_kwargs=[],
                                    exclude_args=["self", "kwargs"])

        grid = GridCurve(**new_kwargs, **kwargs)

        self.addItem(grid)
        self.curves.append(grid)
        return grid

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

    def xlim(self):
        """
        Returns current xlim
        """
        return tuple(self.getViewBox().viewRange()[0])

    def ylim(self):
        """"
        Returns current ylim
        """
        return tuple(self.getViewBox().viewRange()[1])

    def enable_autoscale(self, axis=None, enable=True, x=None, y=None):
        """
        Enable (or disable) auto-range for *axis*, which may be "x", "y", or "xy" for both (if *axis* is omitted, both
        axes will be changed).
        When enabled, the axis will automatically rescale when items are added/removed or change their shape.
        The argument *enable* may optionally be a float (0.0-1.0) which indicates the fraction of the data that should
        be visible.
        Also allows setting `x` and or `y` to `True` for simpler interface.

        :param axis: Axis to autoscale. Can be "x", "y", or "xy", or `None` for both. Defaults to `None`.
        :type axis: str
        :param enable: Whether to enable or disable. Defaults to `True`.
        :type enable: bool
        :param x: optional simpler interface. Setting this to `True` enables autoscaling in the x-direction. Defaults
        to `None`.
        :type x: bool
        :param y: optional simpler interface. Setting this to `True` enables autoscaling in the y-direction. Defaults
        to `None`.
        :type y: bool
        """
        self.enableAutoRange(axis, enable, x, y)

    def disable_autoscale(self, axis=None, x=None, y=None):
        """Disables auto-scale. (See `enable_autoscale`)"""
        self.enableAutoRange(axis, False, x, y)

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

    # def clear(self):          # pyqtgraph implementation is probably better
    #     for curve in self.curves:
    #         curve.clear()

    def remove_curve(self, curve):
        self.removeItem(curve)


class PlotCurve(PlotDataItem):
    kwarg_mapping = {
        "c": "color", "colour": "color", "w": "width", "downsample_method": "downsampleMethod",
        "skip_finite_check": "skipFiniteCheck", "auto_downsample": "autoDownsample",
        "s": "symbolSize", "size": "symbolSize", "symbol_size": "symbolSize", "pixel_mode": "pxMode",
        "clip_to_view": "clipToView", "symbol_colour": "symbol_color", "symbol_lc": "symbol_line_color",
        "symbol_lw": "symbol_line_width", "gradient": "color", "symbol_edge_color": "symbol_line_color",
        "symbol_edge_width": "symbol_line_width", "sec": "symbol_line_color", "sew": "symbol_line_width",
        "dm": "downsample_method", "sfc": "skipFiniteCheck", "ad": "autoDownsample", "pm": "pxMode",
        "ss": "symbolSize", "ctv": "clipToView", "sc": "symbol_color", "slc": "symbol_line_color",
        "slw": "symbol_line_width", "xerr": "x_err", "yerr": "y_err", "bs": "beam_size", "beamsize": "beam_size",
        "errorbar_colour": "errorbar_color", "ec": "errorbar_color", "ew": "errorbar_width"
    }   # last line is the ones for scatter only, downsample for both, rest for line. (not completely sure)
    all_pen_kwargs = ["line_color", "width", "dashed", "dash_pattern"]
    all_symbol_kwargs = ["symbol_color", "symbol_line_width",  "symbol_line_color"]
    all_errorbar_kwargs = ["x_err", "y_err", "beam_size", "errorbar_color", "errorbar_width"]

    all_other_kwargs = [
        "symbolSize", "symbolBrush", "symbol", "connect", "pxMode", "antialias", "skipFiniteCheck", "downsample",
        "downsampleMethod", "autoDownsample", "clipToView", "symbolPen"
    ]

    def __init__(self, parent, curve_type="plot", *args, **kwargs):
        super().__init__()
        self.curve_type = curve_type
        self.parent = parent
        self.errorbar_curve = None

        if curve_type == "plot":
            self.pen = mkPen(color="y")
            self.pen.stored_dash_pattern = None
            self.pen.setCosmetic(True)
            self.setPen(self.pen)
            self.set_data(downsample_method="subsample")                    # defaults are overwritten later
        elif curve_type == "scatter":
            self.pen = None
            self.setPen(self.pen)
            self.set_data(symbol='o', s=6, downsample_method="subsample")   # defaults are overwritten later
            self.setSymbolPen(None)
            self.setSymbolBrush(get_single_color("y"))
        else:
            raise ValueError(f"curve_type {curve_type} is not a valid type of curve.")  # error #1000

        self.symbol_lw = 0
        self.symbol_lc = "white"
        self.gradient = None
        self.errorbar_curve = None

        self.set_data(*args, **kwargs)

    # def setData(self, suppress_warnings=False, *args, **kwargs):
    #     if not suppress_warnings:     # temporarily disabled warning
    #         print("warning")
    #         warnings.warn("Method setData deprecated for usage in squap.")
    #     else:
    #         print("not warning")
        # super(PlotCurve, self).setData(*args, **kwargs)

    # def clear(self):          # clear is already implemented (better than this)
    #     self.setData()

    def set_data(self, x=None, y=None, **kwargs):
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
            - `line_color`: Changes the color of the line. It can either be a single color name, an RGB tuple,
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
            - `symbol_color`: Changes the color of the symbols. It can be a single color name, an RGB tuple (with values
                between 0 and 1), one float between 0.0 (black) and 1.0 (white), an integer (where each integer
                corresponds to a different color already), or a hex code, or it can be multiple colors of the
                previous types. If multiple colors are provided, there should be as many colors as there are points.
            - `symbol_size` (int): The size (in pixels) of each symbol. Can also be a list or array.
                `s` and `size` are also allowed instead of `symbol_size`.
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
            xy_changed = False
        else:
            if y is None:
                y = self.getData()[1]
                if y is None:
                    y = np.zeros(len(x))
            if x is None:
                x = self.getData()[0]
                if x is None:
                    x = np.zeros(len(y))
            xy_changed = True

        other_kwargs = {}           # `setData` needs to be done in one command, so other kwargs that need to be passed
        # to it are added to this dict. If the data is updated, this is also passed as the kwargs.
        if kwargs:      # if anything else is changed, run this bit
            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)

            if "color" in new_kwargs:
                if self.curve_type == "scatter":
                    new_kwargs["symbol_color"] = new_kwargs["color"]
                else:
                    new_kwargs["line_color"] = new_kwargs["color"]

                # changes color if color of the line is changed using the color kwarg.
                if self.errorbar_curve is not None and "errorbar_color" not in new_kwargs:
                    new_kwargs["errorbar_color"] = new_kwargs["color"]

            errorbar_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_errorbar_kwargs if kwarg in new_kwargs}
            if errorbar_kwargs:         # self.errorbar_curve needs to be set before "color" is handled
                if self.errorbar_curve is None:
                    self.errorbar_curve = ErrorbarCurve(self)
                    self.parent.addItem(self.errorbar_curve)
                    self.parent.curves.append(self.errorbar_curve)
                    if "errorbar_color" not in new_kwargs:
                        errorbar_kwargs["color"] = self.pen.color()

                self.errorbar_curve.set_data(x=x, y=y, **errorbar_kwargs)
            elif self.errorbar_curve is not None and xy_changed:
                self.errorbar_curve.set_data(x=x, y=y)

            pen_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_pen_kwargs if kwarg in new_kwargs}
            if pen_kwargs:
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

                        cmap_to_gradient(self.gradient.cmap, self.gradient)
                    pen_kwargs["color"] = pen_kwargs["line_color"]      # handled by update_pen
                if self.pen is None:
                    self.pen = mkPen()
                    self.pen.stored_dash_pattern = None

                update_pen(self.pen, **pen_kwargs)
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


class ErrorbarCurve(ErrorBarItem):
    """Will be added to PlotCurve as attribute. User probably will not interact with this object."""
    kwarg_mapping = {"xe": "x_err", "xerr": "x_err", "yerr": "y_err", "beamsize": "beam_size",
                     "bs": "beam_size", "c": "color", "colour": "color", "w": "width", "errorbar_color": "color",
                     "errorbar_width": "width"}

    def __init__(self, parent, x_err: None | Number | Iterable = None, y_err: None | Number | Iterable = None,
                 beam_size: Number = 0.0, color: ColorType = "white", width: int = 1):
        super().__init__()
        self.parent = parent        # for giving just one value for x_err or y_err
        self.pen = None
        self.old_x_err = None
        self.old_y_err = None
        self.set_data(x_err=x_err, y_err=y_err, beam_size=beam_size, color=color, width=width)

    def set_data(self, *args, **kwargs):
        print(list(kwargs.keys()))

        if args:
            if len(args) == 1:
                kwargs["y"] = args[0]
            elif len(args) == 2:
                kwargs["x"] = args[0]
                kwargs["y"] = args[1]
            else:
                raise ValueError(f"Too many args provided. Can be 2 maximum, but is now {len(args)}.")

        if kwargs:
            if "x_err" in kwargs or "y_err" in kwargs:
                if "x_err" not in kwargs:
                    if self.old_x_err is None:
                        raise ValueError("`x_err` must be defined at the start.")
                    kwargs["x_err"] = self.old_x_err
                else:
                    x_err = kwargs["x_err"]
                    self.old_x_err = x_err
                if "y_err" not in kwargs:
                    if self.old_y_err is None:
                        raise ValueError("`y_err` must be defined at the start.")
                    kwargs["y_err"] = self.old_y_err
                else:
                    y_err = kwargs["y_err"]
                    self.old_y_err = y_err

            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
            errorbar_kwargs = {}

            # repeat the same thing for x and y
            for arg_strings in [["x_err", "left", "right"], ["y_err", "bottom", "top"]]:
                kwarg_name = arg_strings[0]
                errorbar_kwarg1 = arg_strings[1]
                errorbar_kwarg2 = arg_strings[2]

                # is a little vague right now, fill in arg_strings for x to get clearer code.
                if kwarg_name in new_kwargs:
                    if isinstance(new_kwargs[kwarg_name], Number):
                        if self.old_y_err is None or len(self.old_y_err) == 0:
                            errorbar_kwargs[errorbar_kwarg1] = None
                            errorbar_kwargs[errorbar_kwarg2] = None
                        else:
                            errorbar_kwargs[errorbar_kwarg1] = np.full(len(self.old_y_err), new_kwargs[kwarg_name])
                            errorbar_kwargs[errorbar_kwarg2] = np.full(len(self.old_y_err), new_kwargs[kwarg_name])
                    elif isinstance(new_kwargs[kwarg_name], Iterable):
                        kwarg_shape = np.shape(new_kwargs[kwarg_name])
                        if len(kwarg_shape) == 1 or kwarg_shape[1] == 1:       # if it has only one dimension
                            errorbar_kwargs[errorbar_kwarg1] = new_kwargs[kwarg_name]
                            errorbar_kwargs[errorbar_kwarg2] = new_kwargs[kwarg_name]
                        elif kwarg_shape[1] == 2:
                            errorbar_kwargs[errorbar_kwarg1] = new_kwargs[kwarg_name][0]
                            errorbar_kwargs[errorbar_kwarg2] = new_kwargs[kwarg_name][1]

            if "beam_size" in new_kwargs:
                errorbar_kwargs["beam"] = new_kwargs["beam_size"]
            if "x" in new_kwargs:
                errorbar_kwargs["x"] = new_kwargs["x"]
            if "y" in new_kwargs:
                errorbar_kwargs["y"] = new_kwargs["y"]

            pen_kwargs = {}
            if "color" in new_kwargs:
                pen_kwargs["color"] = new_kwargs["color"]
            if "width" in new_kwargs:
                pen_kwargs["width"] = new_kwargs["width"]
            if pen_kwargs != {}:
                if self.pen is None:
                    self.pen = mkPen()
                update_pen(self.pen, **pen_kwargs)
                errorbar_kwargs["pen"] = self.pen

            self.setData(**errorbar_kwargs)


class TextWidget(TextItem):
    kwarg_mapping = {
        "c": "color", "colour": "color", "text_color": "color", "fill": "fill_color", "fc": "fill_color",
        "tw": "text_width"
    }

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.set_data(*args, **kwargs)

    def set_data(self, *args, **kwargs):
        if args:
            self.setText(str(args[0]))
            if is_iter(args[1]):
                self.setPos(*args[1])
            elif len(args) > 2:
                self.setPos(args[1], args[2])

        if kwargs:
            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
            if "text" in new_kwargs:
                self.setText(new_kwargs["text"])
            if "color" in new_kwargs:
                self.setColor(get_single_color(new_kwargs["color"]).toTuple())
            if "angle" in new_kwargs:
                self.setAngle(new_kwargs["angle"])
            if "font" in new_kwargs:
                self.setFont(new_kwargs["font"])
            if "html" in new_kwargs:
                self.setHtml(new_kwargs["html"])
            if "text_width" in new_kwargs:
                self.setTextWidth(new_kwargs["text_width"])
            if "fill_color" in new_kwargs:
                # if isinstance(new_kwargs["fill_color"], QGradient):
                #     gradient = new_kwargs["fill_color"]
                #     cmap_to_gradient(gradient.cmap, gradient)
                self.fill = QBrush(get_single_color(new_kwargs["fill_color"]))
            border_pen_kwargs = {}
            if "border_color" in new_kwargs:
                border_pen_kwargs["color"] = new_kwargs["border_color"]
            if "border_width" in new_kwargs:
                border_pen_kwargs["width"] = new_kwargs["border_width"]
            if border_pen_kwargs:
                if self.border.style() == Qt.PenStyle.NoPen:     # self.border is automatically the pen that is used to draw the border
                    self.border = mkPen(**border_pen_kwargs)
                else:
                    update_pen(self.border, **border_pen_kwargs)
                    self.getViewBox().update()
                    # is not properly updated when only width changes so needs to done manually

    def set_font(self, *args, **kwargs):
        if "font" in kwargs:
            font = kwargs["font"]
            if isinstance(font, QFont):
                self.setFont(font)
                return
        if args:
            if isinstance(args[0], QFont):
                self.setFont(args[0])
                return

        self.setFont(Font(*args, **kwargs))

    def font(self):
        return self.textItem.font()


class InfLine(InfiniteLine):
    kwarg_mapping = {
        "c": "color", "colour": "color", "w": "width", "ls": "line_style", "hc": "hover_color",
        "hw": "hover_width", "gradient": "color"
    }
    all_pen_kwargs = ["color", "width", "dashed", "dash_pattern", "line_style"]
    all_label_kwargs = ["label", "label_text", "movable", "label_movable", "label_position", "label_anchors"]

    def __init__(self, pos, angle, bounds=None, **kwargs):
        super().__init__(pos=pos, angle=angle, bounds=bounds)
        self.pen = mkPen(color="y")
        self.pen.stored_dash_pattern = None
        self.hover_color = None
        self.hover_width = None
        self.movable = False
        self.label_movable = None
        self.label_text = "{value}"
        self.label_position = 0.5
        self.label_anchors = None
        self.line_movable = None
        self.label = None
        self.set_data(**kwargs)

    def set_data(self, pos=None, **kwargs):
        """
        This function updates the data of an infinite line.

        :param pos: The new x-value for a vertical line, the new y-value for horizontal line, otherwise it must be a
            tuple of a position on the line. Defaults to `None`, meaning the position is not changed
        :type pos: float or tuple

        :param kwargs: Can contain any argument accepted by `squap.inf_dline`, meaning the following arguments are
            accepted: `angle`, `color`, `width`, `dashed`, `dash_pattern`, `line_style`, `bounds`, `span`, `movable`,
            `line_movable`, `label`, `label_text`, `label_movable`, `label_position`, `label_anchors`,
            `hover_color`, `hover_width` and `name`. For information
            on these see `squap.inf_dline` documentation.
        """
        if pos is not None:
            self.setValue(pos)

        if kwargs:
            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)

            if "angle" in new_kwargs:
                self.setAngle(new_kwargs["angle"])
                vb = self.getViewBox()
                vb._matrixNeedsUpdate = True
                vb.update()
            if "bounds" in new_kwargs:
                self.setBounds(new_kwargs["bounds"])
            if "span" in new_kwargs:
                self.setSpan(*new_kwargs["span"])
                vb = self.getViewBox()
                if vb:
                    vb._matrixNeedsUpdate = True
                    vb.update()
            if "name" in new_kwargs:
                self.setName(new_kwargs["name"])
            if "movable" in new_kwargs or "line_movable" in new_kwargs:
                self.setMovable(self.movable if self.line_movable is None else self.line_movable)

            for attr in ["movable", "label_movable", "label_text", "label_position", "label_anchors", "line_movable",
                         "hover_color", "hover_width", "label"]:
                if attr in new_kwargs:  # updates all self.attr
                    setattr(self, attr, new_kwargs[attr])

            pen_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_pen_kwargs if kwarg in new_kwargs}
            if pen_kwargs:
                if "color" in pen_kwargs:
                    if isinstance(pen_kwargs["color"], QGradient):
                        gradient = pen_kwargs["color"]
                        if gradient.autoscale:     # todo: autoscale to min and max when span is given or when bounds is given
                            raise ValueError("`gradient` can not autoscale for infinite lines. Provide `position` to "
                                             "`get_gradient`")
                        cmap_to_gradient(gradient.cmap, gradient)
                    pen_kwargs["color"] = pen_kwargs["color"]      # handled by update_pen
                update_pen(self.pen, **pen_kwargs)
                self.setPen(self.pen)

            hover_pen_kwargs = {}
            if (self.line_movable is None and self.movable) or self.line_movable == True:
                if self.hover_color is not None:
                    hover_pen_kwargs["color"] = self.hover_color
                if self.hover_width is not None:
                    hover_pen_kwargs["width"] = self.hover_width
            if hover_pen_kwargs or pen_kwargs:
                hover_pen = copy(self.pen)          # makes sure eg. dashing is consistent with normal line
                update_pen(hover_pen, **hover_pen_kwargs)
                self.setHoverPen(hover_pen)

            label_kwargs = {kwarg: new_kwargs[kwarg] for kwarg in self.all_label_kwargs if kwarg in new_kwargs}
            if label_kwargs and self.label:
                if isinstance(self.label, InfLineLabel):
                    if "movable" in new_kwargs or "label_movable" in new_kwargs:
                        self.label.setMovable(self.movable if self.label_movable is None else self.label_movable)
                    if "label_position" in label_kwargs:
                        self.label.setPosition(new_kwargs["position"])
                    if "label_text" in label_kwargs:
                        self.label.setFormat(new_kwargs["text"])
                    if "label_anchors" in label_kwargs:
                        if label_kwargs["label_anchors"]:
                            self.label.anchors = label_kwargs["label_anchors"]
                else:
                    self.label = InfLineLabel(
                        self, self.label_text,
                        self.movable if self.label_movable is None else self.label_movable,
                        self.label_position, self.label_anchors
                    )


class ImageCurve(ImageItem):
    kwarg_mapping = {
        "loc": "location", "z": "data", "image": "data", "bc": "border_color", "border": "border_color"
    }

    def __init__(self, data=None, location=None, cmap=None, auto_levels=False, levels=None, axis_order="row-major",
                 border_color=None, **kwargs):        # **kwargs for aliases
        super().__init__(axisOrder="row-major")
        self.auto_levels = None         # will be updated before first usage, initial value is irrelevant.
        self.rect = None
        self.data_shape = data.shape if data is not None else None
        self.data = data            # for when cmap is given and data is not changed.
        self.cmap = None            # for when data is given and cmap is not changed
        self.set_data(data=data, location=location, cmap=cmap, auto_levels=auto_levels, levels=levels,
                      axis_order=axis_order, border_color=border_color, **kwargs)

    def set_data(self, data=None, **kwargs):
        """
        This function updates the data of an image.

        :param data: New data. Behaviour depends on other kwargs. For more information see `squap.imshow` documentation.

        :param kwargs: Can contain any argument accepted by `squap.imshow`, meaning the following arguments are
            accepted: `data`, `location`, `cmap`, `auto_levels`, `levels`, `axis_order`, `border_color` and some
            aliases. For information on these see `squap.imshow` documentation.
        """
        kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
        final_kwargs = {}
        if data is not None:
            if self.cmap is not None:
                final_kwargs["image"] = self.cmap(data)/255
            else:
                final_kwargs["image"] = data

            if data.shape != self.data_shape:
                self.data_shape = data.shape if data is not None else None
                if "location" not in kwargs:
                    final_kwargs["rect"] = self.rect
            self.data = data
            # test_print(final_kwargs["image"])

        if "location" in kwargs:
            if kwargs["location"] is None:
                final_kwargs["rect"] = (0, 0, 1, 1)
            else:
                if len(kwargs["location"]) != 4:
                    raise TypeError(f"`location` must be a length 4-iterable")
                else:
                    loc = kwargs["location"]
                    final_kwargs["rect"] = (loc[0], loc[1], loc[2]-loc[0], loc[3]-loc[1])
            self.rect = final_kwargs["rect"]
        if "cmap" in kwargs:
            cmap = get_cmap(kwargs["cmap"])
            self.cmap = cmap
            if data is not None:
                final_kwargs["image"] = cmap(data)/255      # image want values between 0 and 1
            # print(cmap(data).shape)

        if "auto_levels" in kwargs:
            self.auto_levels = kwargs["auto_levels"]    # updates self.auto_levels to most recent value
            final_kwargs["autoLevels"] = self.auto_levels
        # if "levels" in kwargs:
        #     final_kwargs["levels"] = kwargs["levels"]
        if not self.auto_levels:
            if self.data_shape is not None:
                final_kwargs["levels"] = [0, 1]

        if "axis_order" in kwargs:
            final_kwargs["axisOrder"] = kwargs["axis_order"]
            self.setOpts(kwargs["axis_order"])
        if "border_color" in kwargs:
            final_kwargs["border"] = kwargs["border_color"]

        self.setImage(**final_kwargs)


class GridCurve(GridItem):
    kwarg_mapping = {
        "grid_spacing": "tick_spacing", "gs": "tick_spacing", "spacing": "tick_spacing", "ts": "tick_spacing",
        "c": "color", "colour": "color", "w": "width"
    }
    all_pen_kwargs = ["color", "width"]

    def __init__(self, **kwargs):
        super().__init__()
        self.pen = mkPen(getConfigOption('foreground'))
        self.setTextPen(None)
        self.set_data(**kwargs)

    def set_data(self, **kwargs):
        kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
        if "tick_spacing" in kwargs:
            tick_spacing = kwargs["tick_spacing"]
            if is_iter(tick_spacing):
                if len(tick_spacing) != 2:
                    raise TypeError(f"`tick_spacing` must be a length 2-iterable, or a single value")
                if is_iter(tick_spacing[0]):
                    self.setTickSpacing(*tick_spacing)
                else:
                    self.setTickSpacing([tick_spacing[0]], [tick_spacing[1]])
            else:
                self.setTickSpacing([tick_spacing, tick_spacing])

        pen_kwargs = {kwarg: kwargs[kwarg] for kwarg in self.all_pen_kwargs if kwarg in kwargs}
        if pen_kwargs:
            if "color" in pen_kwargs:
                if isinstance(pen_kwargs["color"], QGradient):
                    gradient = pen_kwargs["color"]
                    if gradient.autoscale:  # todo: autoscale to min and max when span is given or when bounds is given
                        raise ValueError("`gradient` can not autoscale for grids. Provide `position` to "
                                         "`get_gradient`")
                    cmap_to_gradient(gradient.cmap, gradient)
                pen_kwargs["color"] = pen_kwargs["color"]  # handled by update_pen
            update_pen(self.pen, **pen_kwargs)
            self.setPen(self.pen)


def test_print(*args, **kwargs):
    print(f"filename={os.path.basename(__file__)}: ", end="")
    print(*args, **kwargs)
