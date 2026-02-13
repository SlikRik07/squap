# starts off by creating an instance of main_window, containing a plot widget.
import time
from typing import Iterable, Callable
from numbers import Number
import os.path

from .main_window import MainWindow
from .plot_widget import PlotWidget
from .helper_funcs import get_single_color, get_cmap, Font, ColorType
from .input_widget import InputTable, Box            # only for type hinting

from time import perf_counter as current_time
import os.path
import numpy as np
import cv2  # doesn't work with numpy2 yet
from argparse import Namespace, ArgumentError
from inspect import signature
from matplotlib import colors

from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from pyqtgraph import setConfigOption
from PySide6.QtGui import QLinearGradient, QRadialGradient, QConicalGradient, QGradient, QCursor, QGuiApplication
from PySide6.QtCore import QPointF, QTimer
from PySide6.QtWidgets import QWidget           # QWidget only for type hinting
from PySide6.QtCore import Qt

__all__ = [
    "var", "plot", "scatter", "errorbar", "set_xlim", "set_ylim", "xlim", "ylim", "legend", "set_title", "lock_zoom", "subplots",
    "remove_item", "get_gradient", "get_cmap", "inf_dline", "inf_hline", "inf_vline", "grid", "plot_text", "merge", "set_interval",
    "on_refresh", "on_mouse_click", "add_slider", "add_checkbox", "add_inputbox", "add_button",
    "add_dropdown", "add_rate_slider", "add_input_table", "get_boxes", "display_fps", "resize",
    "set_input_partition", "is_alive", "refresh", "show_window", "show", "clear", "export", "export_video"
]

window = MainWindow()
var = window.variables

plot = window.plot_widget.plot
scatter = window.plot_widget.scatter
errorbar = window.plot_widget.errorbar
inf_dline = window.plot_widget.inf_dline
inf_hline = window.plot_widget.inf_hline
inf_vline = window.plot_widget.inf_vline
grid = window.plot_widget.grid
plot_text = window.plot_widget.plot_text
imshow = window.plot_widget.imshow
set_xlim = window.plot_widget.set_xlim
set_ylim = window.plot_widget.set_ylim
xlim = window.plot_widget.xlim
ylim = window.plot_widget.ylim
enable_autoscale = window.plot_widget.enable_autoscale
disable_autoscale = window.plot_widget.disable_autoscale
legend = window.plot_widget.legend
set_title = window.plot_widget.set_title
lock_zoom = window.plot_widget.lock_zoom
subplots = window.create_subplots


# def surface_plot(*args, color=None, **kwargs):
#     """
#     Create a surface plot. Only works in 3D mode.
#
#     :param args:
#     :param color:
#     :return:
#     """
#     assert window.is3D
#     all_kwargs = [
#         "color"
#     ]
#
#     for index, kwarg in enumerate([
#         color
#     ]):
#         if kwarg is not None:
#             kwargs[all_kwargs[index]] = kwarg       # only adds the ones who are not None to kwargs,
#             # so that the user can still see the optional parameters, while they don't need to be passed to set_data()
#     return window.plot_widget.base_plot("surface", *args, **kwargs)


# def mesh_plot(*args, color=None, **kwargs):
#     """
#     Create a surface plot. Only works in 3D mode.
#
#     :param args:
#     :param color:
#     :return:
#     """
#     assert window.is3D
#     all_kwargs = [
#         "color"
#     ]
#
#     for index, kwarg in enumerate([
#         color
#     ]):
#         if kwarg is not None:
#             kwargs[all_kwargs[index]] = kwarg       # only adds the ones who are not None to kwargs,
#             # so that the user can still see the optional parameters, while they don't need to be passed to set_data()
#     return window.plot_widget.base_plot("mesh", *args, **kwargs)
def enable_numba(enable: bool = True):
    """Enable numba. Can be a little faster, but takes longer to initialize. """
    setConfigOption('useNumba', enable)


def remove_item(item: GraphicsObject):
    """
    Remove item `item` from the plot widget. Item can be anything that can be added to the plot view.
    """
    if isinstance(window.axs, np.ndarray):
        for pw in window.axs.flatten():
            if item in pw.curves:
                pw.removeItem(item)
        return
    else:
        if item in window.axs.curves:
            window.axs.removeItem(item)
            return
    raise ValueError("Item has not been found")


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


def merge(plots: Iterable[PlotWidget]) -> PlotWidget:  # not optimised, but fast enough (& not sure if it works)
    """Merge multiple plots into a single plot. This is used for unevenly spaced grids of subplots.

    Args:
        plots (Iterable[PlotWidget]): list of plots to merge.

    Returns:
        PlotWidget: One plot object that is the merged plot.

    """
    # hrs = list(np.cumsum(window.heightratios))
    # wrs = list(np.cumsum(window.widthratios))

    coordinates = []  # coordinates of plots, integer starting from 0, not accounting width and heights.
    for index, plt in enumerate(plots):
        coordinates.append((plt.row, plt.col))

    co_arr = np.array(coordinates)
    min_x, max_x = min(co_arr[:, 0]), max(co_arr[:, 0])
    min_y, max_y = min(co_arr[:, 1]), max(co_arr[:, 1])
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            if (x, y) not in coordinates:
                raise ValueError("The plots should form a rectangle")

    for index, plt in enumerate(plots):
        window.fig_widget.removeItem(plt)
        del plt

    height = max_x - min_x+1
    width = max_y - min_y+1

    # new_plot = PlotWidget(hrs[min_x], wrs[min_y])
    new_plot = PlotWidget(min_x, min_y)

    window.fig_widget.addItem(new_plot, min_x, min_y, height, width)
    return new_plot
    # check whether rectangle
    # remove all but first plot
    # change colspan and rowspan of first plot


def set_interval(interval: Number):
    """Set interval between frames.

    Args:
        interval (Number): The time interval (in seconds) to set for updating the plot.
    """
    window.interval = interval * 1000
    if is_alive():
        window.timer.setTimeout(window.interval)        # not tested


def on_refresh(func: Callable, disconnect: bool = False):
    """Adds or removes a function on refresh.

    If you try to disconnect a function that cannot be disconnected, nothing happes.
    Args:
        func (Callable): The function that will be called on refresh.
        disconnect (bool, optional): Whether the function should be connected (False) or disconnected (True).
            Defaults to False.
    """
    if not disconnect:
        if window.timer:
            window.timer.timeout.connect(func)
        window.update_funcs.append(func)
    else:
        if func in window.update_funcs:
            window.update_funcs.append(func)
            if window.timer:
                window.timer.timeout.disconnect(func)


def on_next_refresh(func: Callable):          # todo: only works in eventloop, not in show_window style.
    QTimer.singleShot(0, func)


def on_mouse_click(func: Callable, pixel_mode: bool = False, ax: PlotWidget = window.plot_widget):
    """
    Bind function to run on mouse click. As arguments it gets the position of the mouse, in pixels if `pixel_mode` is
    set to `True`, in coordinates if set to `True`. Second argument that is passed is which mouse button is clicked. If
    `pixel_mode` is False, ax should specify which plot you clicked.

    Args:
        func (Callable): The function that is called when the mouse is clicked. The function can take up to 2 arguments:
            the first is the mouse position, the second is the pyqtgraph internal event for more advanced usage.
        pixel_mode (bool, optional): whether to return pixels from the top left (`True`), or coordinates (`False`).
            Defaults to `False`.
        ax (PlotWidget, optional): Axes on which to count the coordinate. Defaults to the first plot.
    todo: check all MouseClickEvent options, and check with middle mouse button
    todo: automatically determine which ax.
    """
    params = signature(func).parameters
    has_var_args = any(
        param.kind == param.VAR_POSITIONAL
        for param in params.values()
    )
    n_args = 2 if has_var_args else len(params)
    print(ax)

    if len(params) > 2:
        raise ArgumentError(func, f"func should take one or two arguments, but currently takes "
                                  f"{len(signature(func).parameters)} arguments.")

    if pixel_mode:
        def mouse_func(event):
            pos = event.scenePos().toTuple()
            args = ([pos, event][i] for i in range(n_args))     # handles 0, 1 or 2 n_args
            func(*args)

    else:
        def mouse_func(event):
            pos = event.scenePos()
            plot_pos = ax.getViewBox().mapSceneToView(pos).toTuple()
            print(event, pos, plot_pos)
            args = ([plot_pos, event][i] for i in range(n_args))     # handles 0, 1 or 2 n_args
            func(*args)

    window.fig_widget.scene().sigMouseClicked.connect(mouse_func)


def on_mouse_move(func: Callable, pixel_mode=False, ax: PlotWidget = window.plot_widget):
    """Bind a function to mouse move.

    Args:
        func (Callable): The function that is called when the mouse is moved. The function can take 1 argument: the
            mouse position.
        pixel_mode (bool, optional): whether to return pixels from the top left (`True`), or coordinates (`False`).
            Defaults to `False`.
        ax (PlotWidget, optional): Axes on which to count the coordinate. Defaults to the first plot.
    """
    params = signature(func).parameters
    has_var_args = any(
        param.kind == param.VAR_POSITIONAL
        for param in params.values()
    )
    n_args = 1 if has_var_args else len(params)

    if len(params) > 1:
        raise ArgumentError(func, f"func should take one or two arguments, but currently takes "
                                  f"{len(signature(func).parameters)} arguments.")

    if pixel_mode:
        def mouse_func(pos_pixel):
            pos = pos_pixel.toTuple()
            if n_args == 0:
                func()
            else:
                func(pos)
    else:
        def mouse_func(pos_pixel):
            plot_pos = ax.getViewBox().mapSceneToView(pos_pixel).toTuple()
            if n_args == 0:
                func()
            else:
                func(plot_pos)

    window.fig_widget.scene().sigMouseMoved.connect(mouse_func)


def get_mouse_pos(pixel_mode=False, ax: PlotWidget = window.plot_widget) -> tuple:
    """Get the position of the mouse cursor on the plot, either as pixels from the top left, or as coordinates.

    Args:
        pixel_mode (bool, optional): whether to return pixels from the top left (`True`), or coordinates (`False`).
            Defaults to `False`.
        ax (PlotWidget, optional): Axes on which to count the coordinate. Defaults to the first plot.

    Returns:
        tuple: The coordinates of the mouse cursor on the plot.
    """
    pos = window.fig_widget.mapFromGlobal(QCursor.pos())
    if pixel_mode:
        return pos.toTuple()
    else:
        return ax.getViewBox().mapSceneToView(pos).toTuple()


def on_key_press(func: Callable, accept_modifier: bool = False, modifier_arg: bool = False,
                 event_arg: bool = False) -> Callable:
    """Bind `func` to keypress. `func` takes as argument which key is pressed. Is not great yet but good enough for
    simple stuff.

    Args:
        func (Callable): The function that is called when the key is pressed.
        accept_modifier (bool, optional): Whether to call the function when the input is a modifier, such as shift or
            alt. Defaults to `False`.
        modifier_arg (bool, optional): Whether to call the function with the modifier as an extra argument. Defaults to
            `False`.
        event_arg (bool, optional): Whether to call the function with just the event as an argument. Is more complex
            to deal with but much more versatile. Defaults to `False`.
        """
    if window.keyboardGrabber() is None:
        window.grabKeyboard()

    if event_arg:       # needs no changes, func takes as argument the event.
        edited_func = func
    else:
        def edited_func(event):     # edited_func takes in event, while func takes in func
            key = event.key()
            print(key)
            if not key & (1 << 24):
                key = chr(key)
            if event.modifiers() == Qt.NoModifier:
                if modifier_arg:
                    func(key, None)
                else:
                    func(key)
            else:
                if modifier_arg:
                    func(key, event.modifiers())
                else:
                    if accept_modifier:
                        func(event.modifiers())

    window.on_key_press_funcs.append(edited_func)
    return edited_func


def add_slider(
        name: str, init_value: Number = 1.0, min_value: Number = 0.0, max_value: Number = 10.0, n_ticks: int = 51,
        tick_interval: Number | None = None, only_ints: bool = False, logscale: bool = False,
        custom_arr: Iterable | None = None, var_name: str | None = None, print_value: bool = False,
        row: int | None = None) -> InputTable.Slider:
    """Create a slider with the given parameters, and add it to window.first_input_table.

    Args:
        name (str): The name in front of the slider.
        init_value (Number, optional): The initial value of the slider.
        min_value (Number, optional): The minimum value of the slider.
        max_value (Number, optional): The maximum value of the slider.
        n_ticks (int, optional): The number of ticks on the slider. Defaults to 51.
        tick_interval (Number, optional): The interval between ticks. If provided, overwrites `n_ticks`.
        only_ints (bool, optional): Whether to use whole numbers as ticks. If set to True, `tick_interval` is used as
            spacing between the ticks and `n_ticks` is ignored. If `tick_interval` is not specified, it defaults to 1.
            Rounds `tick_interval` to an integer and changes the variable to always be an integer. Not allowed
            in combination with `logscale`. Defaults to False
        logscale (bool, optional): Whether to use a logarithmic scale. When `tick_interval` is given it serves as a
            multiplication factor between a point and the previous point (it is rounded to fit min_value and
            max_value. Not allowed in combination with `only_ints`. Defaults to False.
        custom_arr (Iterable, optional): Array or list of values, where `custom_arr[i]` will be the value (can be
            any type) of the slider when it is set to position `i`. Overwrites all other parameters (except
            `init_value`). Defaults to None.
        var_name (str, optional): The name of the created variable. If var_name is not provided, the variable will be
            named name.
        print_value (bool, optional): Whether to print the value of the slider when it changes. Defaults to False.
        row (int, optional): Row to which the widget is added. Defaults to first empty row.

    Returns:
        The slider widget.
    """

    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.Slider(
        window.first_input_table, name, init_value, min_value, max_value, n_ticks, tick_interval, only_ints, logscale,
        custom_arr, var_name, print_value, row
    )


def add_checkbox(name: str, init_value: bool = False, var_name: str| None = None, print_value: bool = False,
                 row: int | None = None) -> InputTable.CheckBox:
    """Create a checkbox with the given parameters, and add it to window.first_input_table.

    Args:
        name (str): The name in front of the checkbox.
        init_value (bool, optional): The initial value of the checkbox. Defaults to `False` (not ticked).
        var_name (str, optional): The name of the created variable. If var_name is not provided, the variable will be
            named name.
        print_value (bool, optional): Whether to print the value of the checkbox when it changes. Defaults to False.
        row (int, optional): Row to which the widget is added. Defaults to first empty row.

    Returns:
        The checkbox widget.
    """

    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.CheckBox(window.first_input_table, name, init_value, var_name, print_value, row)


def add_inputbox(name: str, init_value=1.0, type_func: Callable | None = None, var_name: str| None = None,
                 print_value: bool = False, row: int | None = None) -> InputTable.InputBox:
    """Create an inputbox with the given parameters, and add it to window.first_input_table.

    Args:
        name (str): The name in front of the inputbox.
        init_value (optional): The initial value of the inputbox. Can be any object that can be turned into
            a string.
        type_func (Callable, optional): The function that takes in a string and returns the value as the
            correct type. Usually, this will default to `ast.literal_eval`, which works for a lot of data
            types: str, float, complex, bool, tuple, list, dict, set and None. If `type_func` is set to
            None (default value), then it will be set to `ast.literal_eval` if `init_value` is one of the
            mentioned data types. If init_value is a `np.array` or a range object, this is also handled, but
            it needs to be explicitly changed to ast.literal_eval if the data type is changed during runtime.
            If you have a different data type that doesn't work with the automatic behavior, a function can be
            passed to this argument that takes in a string and returns the desired value. Note that
            `ast.literal_eval` is a lot slower than, for example, `float`, so if you are sure the input is
            a float, a minor speedup can be achieved by explicitly setting `type_func=float`.

            `type_func` can also be set to `int`, so that each value is turned into an int. If `type_func` is not
            given, it is automatically determined, which works for the following instances: str, float, complex,
            bool, range, and the following iterables: tuple, list, dict, set, np.ndarray.
        var_name (str, optional): The name of the created variable. If var_name is not provided, the variable will
            be named name.
        print_value (bool, optional): Whether to print the value of the inputbox when it changes. Defaults to False.
        row (int, optional): Row to which the widget is added. Defaults to first empty row.

    Returns:
        The inputbox widget.
    """

    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.InputBox(window.first_input_table, name, init_value, type_func, var_name,
                                             print_value, row)
    # current_row + 1 because this parameter is updated inside the function


def add_button(name: str, func: Callable | None = None, row: int | None = None) -> InputTable.Button:
    """Create a button with name `name` and bound function `func`, and add it to window.first_input_table.

    Args:
        name (str): The name in front of the button.
        func (Callable, optional): The function which is run on button press.
        row (int, optional): Row to which the widget is added. Defaults to first empty row.

    Returns:
        The button widget.
    """
    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.Button(window.first_input_table, name, func, row)


def add_dropdown(name: str, options: Iterable, init_index: int = 0, option_names: Iterable[str] | None = None,
                 var_name: str| None = None, print_value: bool = False, row: int | None = None) -> InputTable.Dropdown:
    """Create a dropdown widget with the given parameters, and add it to window.first_input_table.

    Args:
        name (str): The name in front of the dropdown.
        options (Iterable): A list of all options shown in the dropdown menu.
        init_index (int, optional): The index that the dropdown is initially set to.
        option_names (Iterable[str], optional): A list of all options the created variable can be, where
            option_names[index] is the value given to the variable, if the dropdown is set to index. If option_names
            is not provided it will be set to `options`.
        var_name (str, optional): The name of the created variable. If var_name is not provided, the variable will be
            named name.
        print_value (bool, optional): Whether to print the value of the dropdown when it changes. Defaults to False.
        row (int, optional): Row to which the widget is added. Defaults to first empty row.

    Returns: 
        The dropdown widget.
    """

    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.Dropdown(window.first_input_table, name, options, init_index, option_names,
                                             var_name, print_value, row)


def add_rate_slider(
        name: str, init_value: Number = 1.0, change_rate: Number = 10.0, absolute: bool = False,
        time_var: None | str = None, custom_func: Callable | None = None, var_name: str| None = None,
        print_value: bool = False, row: int | None = None) -> InputTable.RateSlider:
    """Create a RateSlider with the given parameters, and add it to window.first_input_table.
    
    Args:
        name (str): The name in front of the rate slider.
        init_value (Number, optional): The initial value of the rate slider.
        change_rate (Number, optional): Change to the value of the variable per second (how it changes depends
            on `absolute`), multiplied by the current rate_slider position (value between -1 and 1).
        absolute (bool, optional): How the value of the variable is changed. If absolute is True, changerate will be
            added every second. If it is set to False, the variable will be multiplied be changerate every second.
        time_var (str, optional): If set to None (default), actual time will be used. It can also be set to the name of
            a variable in `squap.var` as a string. Then that variable will be regarded as time: if it increases by 1,
            the created variable will be changed by changerate.
        custom_func (Callable, optional): the function that changes the created variable. Overrides `absolute`. It must
            take three arguments: `old_value`, `dt` and `slider_value` and must return the new value. `old_value` is
            the value of the variable the previous time the function was run, dt is the change in time since then (takes
            `time_var` into account). `slider_value` is a value between -1 and 1, dependent on the slider position.
        var_name (str, optional): The name of the created variable. If var_name is not provided, the variable will be
            named name.
        print_value (bool, optional): Whether to print the value of the slider when it changes. Defaults to False.
        row (int, optional): Row to which the widget is added. Defaults to first empty row.

    Returns: 
        The rate_slider widget.
    """
    if not window.first_input_table:
        window.init_first_tab()

    return window.first_input_table.RateSlider(
        window.first_input_table, name, init_value, change_rate,
        absolute, time_var, custom_func, var_name, print_value, row
    )


def add_color_picker(
        name: str, init_value: ColorType = (255, 255, 255), var_name: str| None = None, print_value: bool = False,
        row: int | None = None) -> InputTable.ColorPicker:
    """Create a ColorPicker with the gives parameters, and add it to window.first_input_table.
    
    Args:
        name (str): The name in front of the slider.
        init_value (ColorType, optional): The initial value of the slider.
        var_name (str, optional): The name of the created variable. If var_name is not provided, the variable will be
            named name.
        print_value (bool, optional): Whether to print the value of the color picker when it changes. Defaults to False.
        row (int, optional): Row to which the widget is added. Defaults to first empty row.

    Returns: 
        The color_picker widget.
    """
    if not window.first_input_table:
        window.init_first_tab()

    return window.first_input_table.ColorPicker(
        window.first_input_table, name, init_value, var_name, print_value, row
    )


def add_input_table(name: str | None = None) -> InputTable:
    """Return a newly created input table on the left with name `name`.

    If one already exists, it is added as a tab to a QTabWidget. Note that an input table is automatically created when
    another function is called that implies the existence of an input table, so call this function before that to name
    the first input table.

    Args:
        name (str, optional): Name of the tab, only visible when multiple input tables are added. Defaults to tab{i}
        where i is the ith tab.
    """
    if not window.first_input_table:
        return window.init_first_tab(name=name)
    else:
        return window.add_table(name=name)


def rename_tab(name: str, index: int = 0, old_name: str | None = None):
    """Rename tab with index `ìndex` or old name `old_name` to `name`.

    Args:
        name (str): new name.
        index (int, optional): index of the tab to rename. Defaults to 0.
        old_name (str, optional): old name of the tab to rename. Overwrites index if provided.
    """
    window.rename_tab(name, index, old_name)


def set_active_tab(*args: int | InputTable | str, index: int | None = None, tab: InputTable | None = None, name: str | None = None) -> InputTable:
    """Set active tab using one of the possible arguments. Use exactly one.

    Args:
        *args (int | InputTable | str, optional): One of the possible arguments, automatically determined which it is by
            given type.
        index (int, optional): Index of the tab to select. Defaults to None.
        tab (InputTable, optional): The tab to select. Defaults to None.
        name (str, optional): Name of the tab to select. Defaults to None.

    Returns:
        The InputTable belonging to the selected tab.
    """
    if window.tab_widget is None:
        if window.first_input_table is None:
            raise ValueError("Could not find any tabs. Create tabs before selecting an active tab.")
        else:
            return window.first_input_table

    if args:
        if isinstance(args[0], int):
            index = args[0]
        elif isinstance(args[0], InputTable):
            tab = args[0]
        elif isinstance(args[0], str):
            name = args[0]
        else:
            raise ValueError("Type of arg not recognised. Must be `int` or `InputTable` or `str`, but"
                                f" is {type(args[0])}.")

    if index is not None:
        window.tab_widget.setCurrentIndex(index)
    elif tab is not None:
        window.tab_widget.setCurrentWidget(tab)
    elif name is not None:
        for i in range(window.tab_widget.count()):
            if window.tab_widget.widget(i).name == name:
                window.tab_widget.setCurrentIndex(i)
                break
    else:
        raise ValueError("`set_active_tab` needs an argument. ")
    return window.tab_widget.currentWidget()


def get_all_tabs() -> list[InputTable]:
    result = []
    for i in range(window.tab_widget.count()):
        result.append(window.tab_widget.widget(i))
    return result


def get_boxes() -> list[Box]:
    """Return a list containing all boxes that exist at this point. """
    result = []
    for table in window.input_tables:
        result.extend(table.get_boxes())
    return result


def get_current_row() -> int:
    """Return row of the latest placed widget"""
    return window.first_input_table.current_row


def link_boxes(boxes: Iterable[Box | int], only_update_boxes: list | None = None):
    """Link all boxes in the list `boxes`.
    
    Boxes added to only_update_boxes are only updated when a box in boxes is
    changed but do not cause the other boxes to update when they are changed.
    `link_boxes(box1, box2); link_boxes(box2, box3)` can be used to link box1 to box2 and box2 to box3 without linking
    box1 to box3.

    Args:
        boxes (Iterable[Box | int]): list of boxes or row numbers of the boxes to link
        only_update_boxes (list, optional): todo: I forgot what this does...
    """
    window.link_boxes(boxes, only_update_boxes)


def display_fps(update_speed: Number = 0.2, get_fps: bool = False, optimized: bool = False,
                plot_window: PlotWidget | None = None):
    """
    Display frames per second(fps) at the top of the plot widget.

    Args:
        update_speed (float, optional): The update speed for fps calculation. Defaults to 0.2 second.
        get_fps (bool, optional): Whether to store fps. If set to True, the fps will be saved to var.fps every time it
            is updated. Defaults to False
        optimized (bool, optional): Whether to use an optimized calculation method. If set to True, it is a bit
            quicker, but less consistent for variable fps. Defaults to False.
        plot_window (squap.PlotWidget, optional): Which window to set the title to the fps. Defaults to top-left.

    Returns:
        Callable: function that is needed to update the fps. If the program is run in refresh mode, this function
            needs to be run each loop

    Raises:
        NotImplementedError: If the function is called in 3D plot style, which is not supported yet.
    """
    if plot_window is None:
        plot_window = window.plot_widget

    window.fps_timer = current_time()
    skip = Namespace(total=0, count=0)  # Namespace used for function variables that need to carry over
    # the fps is updated

    if optimized:
        def func():
            if skip.count == 0:
                now = current_time()
                elapsed = now - window.fps_timer
                if elapsed:
                    window.fps_timer = now
                    fps = (skip.total + 1) / elapsed
                    fps = round(fps, -int(np.floor(np.log10(fps))) + (5 - 1))
                    if get_fps:
                        setattr(var, "fps", fps)
                    if window.is3D:
                        print(f"{fps = }")
                    else:
                        plot_window.set_title(f"fps = {fps}")

                    skip.total = int(update_speed * fps)
                    skip.count = skip.total
            else:
                skip.count -= 1
    else:
        def func():
            elapsed = current_time() - window.fps_timer
            skip.count += 1
            if elapsed > update_speed:
                window.fps_timer = current_time()
                fps = skip.count / elapsed
                fps = round(fps, -int(np.floor(np.log10(fps))) + (5 - 1))
                if window.is3D:
                    print(f"{fps = }")
                else:
                    plot_window.set_title(f"fps = {fps}")
                skip.count = 0

    window.update_funcs.append(func)  # both so that it works for both styles


def stable_fps():
    """
    Deze is handig te maken als ik hem kan testen met een barplot van de fps, dus die laat ik nog even

    """


def benchmark(n_frames: int | None = None, duration: Number | None = None):
    """Run the program until it is closed and then report the total frames and fps. 
    
    If n_frames or duration are specified, the program will quit when either has passed.
    
    Args:
        n_frames (int, optional): Number of frames to run the program for
        duration (Number, optional): Total time to run the program for in seconds.
    """
    local_vars = Namespace(time=current_time(), count=0)
    # Namespace used for function variables that need to carry over

    if n_frames is None and duration is None:
        def func():
            local_vars.count += 1

    elif n_frames is None:
        def func():
            local_vars.count += 1
            if current_time() - local_vars.time > duration:
                window.close()

    elif duration is None:
        def func():
            local_vars.count += 1
            if local_vars.count >= n_frames:
                window.close()

    else:
        def func():
            local_vars.count += 1
            if current_time() - local_vars.time > duration or local_vars.count >= n_frames:
                window.close()

    def final_func():
        elapsed = current_time() - local_vars.time
        print(f"{local_vars.count} frames have passed in {elapsed} seconds, "
              f"which gives an fps of {local_vars.count / elapsed}")

    window.update_funcs.append(func)
    window.close_funcs.append(final_func)


# def init_3D():
#     window.init_3D()


# def add_grid(diagonal):
#     """
#     :param diagonal: A tuple of two points that span the diagonal of a rectangle that lies on or parallel to the
#         xy, yz, or zx plane.
#     :return:
#     """
#     if window.is3D:
#         window.plot_widget.add_grid(diagonal)
#     else:
#         raise RuntimeError("This function only works in 3D. 3D mode needs to be initialised first. (1003)")


# def add_grids(size=(0.0, 5.0)):
#     """
#     Adds square grids on the xy, yz and zx planes, spanning from size[0] to size[1].
#
#     :param size: the size of each grid.
#     """
#     if window.is3D:
#         window.plot_widget.add_grids(size)
#     else:
#         raise RuntimeError("This function only works in 3D. 3D mode needs to be initialised first. (1003)")


# def align_camera():
#     window.plot_widget.animated = True
#     current_params = window.plot_widget.cameraParams()
#     add_rate_slider("distance", current_params["distance"], changerate=2)
#     row_js_1 = get_current_row()
#     slider_1 = add_slider("azimuth", current_params["azimuth"], 0, 360, n_ticks=72)
#     slider_2 = add_slider("elevation", current_params["elevation"], -90, 90, n_ticks=180)
#     slider_3 = add_slider("fov", current_params["fov"], 0, 180, n_ticks=180)
#     add_rate_slider("x", 0, absolute=True, changerate=5)       # todo: change init_value to current_params.center.x
#     row_js_x = get_current_row()
#     add_rate_slider("y", 0, absolute=True, changerate=5)
#     row_js_y = get_current_row()
#     add_rate_slider("z", 0, absolute=True, changerate=5)
#     row_js_z = get_current_row()
#
#     def update_cam_params():
#         window.plot_widget.setCameraParams(
#             distance=var.distance,
#             azimuth=var.azimuth,
#             elevation=var.elevation,
#             fov=var.fov
#         )
#
#     def rate_slider_update(row):
#         if row == row_js_1:
#             update_cam_params()
#
#     def update_cam_pos():
#         vector = QtGui.QVector3D(
#             var.x,
#             var.y,
#             var.z
#         )
#         window.plot_widget.setCameraPosition(
#             vector
#         )
#
#     def rate_slider_pos_update(row):
#         if row == row_js_x or row == row_js_y or row == row_js_z:
#             update_cam_pos()
#
#     slider_1.valueChanged.connect(update_cam_params)
#     slider_2.valueChanged.connect(update_cam_params)
#     slider_3.valueChanged.connect(update_cam_params)
#     window.input_widget.cellChanged.connect(rate_slider_update)
#     window.input_widget.cellChanged.connect(rate_slider_pos_update)
#     update_cam_params()
#
#     def get_params():
#         print(
#             f"The following function would get you this camera postition: \n"
#             f"squap.set_camera(\n"
#             f"    x={var.x}, y={var.y}, z={var.z}, \n"
#             f"    distance={var.distance}, azimuth={var.azimuth}, "
#             f"elevation={var.elevation}, fov={var.fov}\n)"
#         )
#
#     add_button("print camera parameters", get_params)


# def set_camera(x=None, y=None, z=None, distance=None, azimuth=None, elevation=None, fov=None):
#     """
#     Sets the camera position, rotation and fov using the given arguments.
#
#     :param x:
#     :type x: float
#     :param fov: field of view of the camera
#
#     """
#     cam_params_kwargs = {}
#
#     if distance is not None:
#         cam_params_kwargs["distance"] = distance
#     if azimuth is not None:
#         cam_params_kwargs["azimuth"] = azimuth
#     if elevation is not None:
#         cam_params_kwargs["elevation"] = elevation
#     if fov is not None:
#         cam_params_kwargs["fov"] = fov
#
#     window.plot_widget.setCameraParams(**cam_params_kwargs)
#     if x is not None or y is not None or z is not None:     # todo: fix this. When only z is given there is an error.
#         window.plot_widget.setCameraPosition(
#             QtGui.QVector3D(x, y, z)
#         )


def resize(width: int, height: int):
    """
    Resize the window.

    Args:
        width (int): Number of pixels wide it is changed to. Starts off at 640, or 965 if inputs are present (the 5 is
            for the border between the input_widget and the plot_widget).
        height (int): New height in pixels. Starts off at 480.
    """
    window.resize(width, height)
    window.resized = True
    # if window.input_widget is None and not window.isVisible():
    #     window.fig_widget.resize(width, height)

    if window.main_input_widget:
        ratio = window.splitter.width_ratio
        window.main_input_widget.resize(int(ratio * width / (ratio + 1)), height)
        window.fig_widget.resize(int(width / (ratio + 1)), height)
        window.splitter.resize(width, height)
        window.main_input_widget.resized = True


def size() -> tuple:
    """Return the size of the window as a tuple. Can be unreliable when called before the window is shown. """
    return window.size().toTuple()


def set_input_partition(fraction: float = 1/3):
    """Set the position of the partition between the 2 columns of the input_widget.

    Args:
        fraction (float, optional): value between 0 and 1, specifying the portion of the window taken up by the
            partition. Starts off at 1/3
    """
    if not window.first_input_table:
        window.init_first_tab()
    window.first_input_table.set_partition(fraction)


def set_input_width_ratio(fraction: float = 1/2):
    """
    Set the relative size of the input window compared to the plot window. A fraction of 1/2 (default value) means that
    the plot window is 2 times wider than the input window.

    Args:
        fraction (float, optional): value between 0 and 1, specifying the portion of the window taken up by the
            input window. Starts off at 1/2
    """
    if not window.first_input_table:
        window.init_first_tab(width_ratio=fraction)
    else:
        width, height = window.size().toTuple()
        window.splitter.width_ratio = fraction
        window.main_input_widget.resize(int(fraction * width / (fraction + 1)), height)
        window.fig_widget.resize(int(width / (fraction + 1)), height)
        window.splitter.resize(width, height)


def is_alive() -> bool:
    """Whether the window is visible. """
    return window.isVisible()


def refresh(wait_interval: bool = True, call_update_funcs: bool = True):
    """Refresh everything shown on screen, and wait according to interval (set with squap.set_interval)

    Args:
        wait_interval (bool, optional): If set to `False`, doesn't wait for time set by `squap.set_interval`.
        call_update_funcs (bool, optional): If set to `True`, calls all functions bound by `squap.on_refresh` when
            this function is called.
    """
    if wait_interval and window.interval:
        now = current_time()
        to_wait = window.interval/1000 - (now - window.refresh_timer)
        if to_wait > 0:
            time.sleep(to_wait)
        window.refresh_timer = current_time()
        QGuiApplication.processEvents()
    else:
        QGuiApplication.processEvents()
    if call_update_funcs:
        for func in window.update_funcs:
            func()
    # timer.start(0)


def show_window():
    """Shows the window and refreshes it. Use in combination with `squap.refresh`"""
    window.refresh_timer = current_time()

    if window.main_input_widget:
        if window.resized:
            if not window.main_input_widget.resized:
                x = window.splitter.width_ratio              # calculates width of the input_widget given x and total w
                fig_width = window.size().width()/(1+x)
                window.input_width = fig_width*x
            else:
                fig_width = window.width()-window.input_width-4
            window.splitter.setSizes([window.input_width, fig_width])
        else:
            if not window.main_input_widget.resized:
                window.resize(window.size().width() + window.input_width + 4, window.height())
            # +4 extra for space between plot_widget and input_widget
            window.splitter.setSizes([window.input_width, window.fig_widget.width()])

    window.show()

    refresh()
    if window.interval:
        var.hidden_variables["start"] = time.time()

        def interval_func():
            time_left = window.interval / 1000 - (time.time() - var.hidden_variables["start"])
            print(f"{time_left = }")
            # the time it should still wait
            if time_left > 0:
                time.sleep(time_left)
            var.hidden_variables["start"] = time.time()

        window.update_funcs.append(interval_func)


def show():
    """Show window and starts loop. Use in combination with `Box.bind`, `squap.on_refresh` or for static plots. """

    timer = QTimer()            # timer is required for running functions on refresh and executing pyqtgraph programs
    if len(window.update_funcs):
        for func in window.update_funcs:
            timer.timeout.connect(func)

    if window.interval:
        timer.start(window.interval)
    else:
        timer.start()
    window.timer = timer

    if window.main_input_widget:
        if window.resized:
            if not window.main_input_widget.resized:
                x = window.splitter.width_ratio              # calculates width of the input_widget given x and total w
                fig_width = window.size().width()/(1+x)
                window.input_width = fig_width*x
            else:
                fig_width = window.width()-window.input_width-4
            window.splitter.setSizes([window.input_width, fig_width])
        else:
            if not window.main_input_widget.resized:
                window.resize(window.size().width() + window.input_width + 4, window.height())
            # +4 extra for space between plot_widget and input_widget
            window.splitter.setSizes([window.input_width, window.fig_widget.width()])

        # pos = window.pos().toTuple()          # don't know why but this is suddenly not necessary anymore
        # window.move(pos[0]-0.5*(window.input_widget.width() + 4), pos[1])

    window.show()

    window.app.exec()


def close_window():
    """Close the window. The program continues after `squap.show()`. """
    window.close()


def clear():
    """Clear everything. Todo: check"""
    for update_func in window.update_funcs:
        window.timer.timeout.disconnect(update_func)
    if isinstance(window.axs, np.ndarray):
        for pw in window.axs.flatten():
            for curve in pw.curves:
                pw.removeItem(curve)
    else:
        for curve in window.axs.curves:
            window.axs.removeItem(curve)

    window.update_funcs = []
    set_xlim(0, 1)
    set_ylim(0, 1)


def export(filename: str, full_window: bool = False):
    """Save the current window as an image to file `filename`.

    Args:
        filename (str): Name of the file to which the image must be saved. Extension can be png, jpg, jpeg, bmp, pbm,
            pgm, ppm, xbm and xpm. Defaults to png if no extension is provided.
        full_window (bool, optional): Whether to include the input window as well.
    """
    if full_window:
        pixmap = window.grab()
    else:
        pixmap = window.fig_widget.grab()

    basename, extension = os.path.splitext(filename)
    if extension:
        success = pixmap.toImage().save(filename)
    else:
        success = pixmap.toImage().save(f"{filename}.png")
        extension = ".png"
    if success:
        print(f"Exported current plot window to {basename}{extension}")
    else:
        raise RuntimeError(f"Saving failed, extension {extension} is not an allowed extension")


def export_video(
        filename: str, fps: Number = 30.0, n_frames: int | None = None, duration: Number = None,
        stop_func: Callable | None = None, skip_frames: int = 0, display_window: bool = False,
        widget: QWidget = window.fig_widget, save_on_close: bool = True
):
    """Saves a video to file `filename` with the specified parameters.

    Out of `n_frames`, `duration` and `stop_func` at most one can be provided. If none of these are given, the video
    will be indefinite, and will be stopped and saved as soon as the window is closed, or when KeyboardInterrupt is
    raised (when the user attempts to manually stop the program). If the window is closed before the stop condition is
    met, the video will still be saved by default.

    Args:
        filename (str): Name of the file to which the video is exported.
        fps (Number, optional): Frames per second of the video. Defaults to 30.
        n_frames (int, optional): Number of frames before the video stops and saves.
        duration (Number, optional): Duration in seconds before the video stops and saves. It will save the last frame
            after the time is up as well.
        stop_func (Callable, optional): This function will be run after every iteration. If it returns True, the video
            stops and saves.
        skip_frames (int, optional): number of frames to not save after a frame is saved.
        display_window (bool, optional): Whether to display the window or not. Defaults to False.
        widget (QWidget, optional): which widget to record. Can be eg. a single plot, the entire window, or only
            the plot window. Defaults to only the plot window.
        save_on_close (bool, optional): Whether to save the video if the window is closed prematurely. Defaults to True.
    """
    if len([None for arg in [n_frames, duration, stop_func] if arg is None]) < 2:
        raise ValueError("Only one of n_frames, duration or stop_func can be provided, error code 1009.")

    # this bit creates the loop condition, which can be the stop_func given by the user, or
    if duration is not None:
        n_frames = int(duration * fps)
    if stop_func is not None:
        def condition():
            return stop_func()
    elif n_frames is None:
        def condition():
            return False
    else:
        n_frames = int(n_frames)  # shouldn't do anything, but just incase it prevents an infinite loop

        def condition():
            return frame_counter == n_frames

    frame_counter = 0
    pixmaps = []
    if display_window:
        show_window()

    try:
        while not condition():
            for update_func in window.update_funcs:
                update_func()

            if display_window:
                refresh()

            if not frame_counter % (skip_frames + 1):
                pixmaps.append(widget.grab())

            frame_counter += 1

    except KeyboardInterrupt:
        if save_on_close:
            print("The program is interupted, the recording is now being save.")
        else:
            print("The program is interupted, the video will not be saved.")
            return

    basename, extension = os.path.splitext(filename)
    print(f"started saving {len(pixmaps)} frames to file {basename}.mp4 at {fps} fps")  # maybe other file-extension
    if extension and extension != '.mp4':
        print("you can only save to mp4, if you want other filenames, you can request them")

    arrs = []

    for index, pixmap in enumerate(pixmaps):  # see chatgpt once it works again
        qimg = pixmap.toImage()

        img_size = qimg.size()
        buffer = qimg.constBits()

        arr = np.ndarray(
            shape=(img_size.height(), img_size.width(), qimg.depth() // 8),
            buffer=buffer,
            dtype=np.uint8
        )
        arrs.append(arr[:, :, :3])  # only include RGB, not A

    try:
        width, height, _ = arr.shape
    except NameError:
        raise NameError("No frames were captured, error code 1006.")
    out = cv2.VideoWriter(f"{basename}.mp4", cv2.VideoWriter_fourcc(*'mp4v'), fps, (height, width))

    for index, arr in enumerate(arrs):
        out.write(arr)
        if not (index % 1000) and index:
            print(f"{index} frames have been saved.")

    out.release()
    print("Saving finished.")


def start_recording(filename: str, fps: Number = 30.0, skip_frames: int = 0,
                    widget: QWidget = window.fig_widget) -> Callable:
    """Start recording to file `filename` with the specified parameters. Use function returned by this function to stop
    the recording.

    Args:
        filename (str): Name of the file to which the video will be exported.
        fps (Number, optional): Frames per second of the video. Defaults to 30.
        widget (QWidget, optional): which widget to record. Can be eg. a single plot, the entire window, or only
            the plot window. Defaults to only the plot window.

    Returns:
        Callable: Call this function to stop the recording and save the video.
    """

    pixmaps = []
    frame_counter = {"i": 0}

    def record_func():
        if not frame_counter["i"] % (skip_frames + 1):
            pixmaps.append(widget.grab())
        frame_counter["i"] += 1

    def stop_func():
        basename, extension = os.path.splitext(filename)
        print(f"started saving {len(pixmaps)} frames to file {basename}.mp4 at {fps} fps")  # maybe other file-extension
        if extension and extension != '.mp4':
            print("you can only save to mp4, if you want other filenames, you can request them")

        arrs = []

        for index, pixmap in enumerate(pixmaps):  # see chatgpt once it works again
            qimg = pixmap.toImage()

            img_size = qimg.size()
            buffer = qimg.constBits()

            arr = np.ndarray(
                shape=(img_size.height(), img_size.width(), qimg.depth() // 8),
                buffer=buffer,
                dtype=np.uint8
            )
            arrs.append(arr[:, :, :3])  # only include RGB, not A

        try:
            width, height, _ = arr.shape
        except NameError:
            raise NameError("No frames were captured, error code 1006.")
        out = cv2.VideoWriter(f"{basename}.mp4", cv2.VideoWriter_fourcc(*'mp4v'), fps, (height, width))

        for index, arr in enumerate(arrs):
            out.write(arr)
            if not (index % 1000) and index:
                print(f"{index} frames have been saved.")

        out.release()
        print("Saving finished.")

        window.update_funcs.remove(record_func)

    window.update_funcs.append(record_func)

    return stop_func


def test_print(*args, **kwargs):
    print(f"filename={os.path.basename(__file__)}: ", end="")
    print(*args, **kwargs)
