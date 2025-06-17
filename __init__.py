# starts off by creating an instance of main_window, containing a plot widget.
import time
import typing
import os.path

from .main_window import MainWindow
from .plot_widget import PlotWidget

from time import perf_counter as current_time
import os.path
import numpy as np
import cv2  # doesn't work with numpy2 yet
from argparse import Namespace

from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph import mkQApp
from PySide6.QtGui import QLinearGradient, QRadialGradient, QConicalGradient, QGradient
from PySide6.QtCore import QPointF

__all__ = [
    "var", "plot", "scatter", "set_xlim", "set_ylim", "legend", "set_title", "lock_zoom", "subplots", "get_gradient",
    "merge", "set_interval", "on_refresh", "on_mouse_click", "add_slider", "add_checkbox", "add_inputbox", "add_button",
    "add_dropdown", "add_rate_slider", "add_input_table", "get_boxes", "add_text", "display_fps", "resize",
    "set_input_partition", "is_alive", "refresh", "show_window", "show", "clear", "export", "export_video"
]

window = MainWindow(mkQApp("squap"))
var = window.variables

plot = window.plot_widget.plot
scatter = window.plot_widget.scatter
imshow = window.plot_widget.imshow
add_text = window.plot_widget.add_text
set_xlim = window.plot_widget.set_xlim
set_ylim = window.plot_widget.set_ylim
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

def remove_curve(curve):
    if isinstance(window.axs, np.ndarray):
        for pw in window.axs.flatten():
            if curve in pw.curves:
                pw.removeItem(curve)
                return
    else:
        if curve in window.axs.curves:
            window.axs.removeItem(curve)
            return
    raise ValueError("Curve has not been found")



def get_gradient(cmap, style="horizontal", position=None, extend="pad", resolution=256):
    """
    The gradient can be seen as a 2D image of a gradient which appears at each pixel that lies on the line. When `style`
    of the gradient is set to "horizontal" or "vertical", or "radial" without providing `position`, the bounds of the
    gradient will be automatically determined when set_data is called, which can decrease performance. So, specify
    `position` for optimal performance. Default is None.

    :param cmap: The colormap used as gradient. Can either be a string, a dictionary, a list
        of colors or an instance of `matplotlib.colors.Colormap`.
        When a string is passed, it is any string accepted by matplotlib or cmasher. When a colormap exists for both
        matplotlib and cmasher, matplotlib will be used. Use "mpl_ocean" and "cmasher_ocean" to explicitly select
        matplotlib or cmasher.
        When a dictionary is passed, it specifies the color for different inputs. The color corresponding to
        0 is indicated by cmap[0], and cmap[1] is the end. The rest of the dictionary entries are other points at which
        the color is specified. The gradient is a linear interpolation between each of these points.
        When a list of colors is passed, the colormap is a linear interpolation between the colors, equally spaced
        between 0 and 1.
        When a `matplotlib.colors.Colormap` instance is passed, it is used as cmap with the specified resolution.
    :type cmap: str, dict
    :param style: The style of the gradient. Can be "horizontal" or "vertical" for a simple horizontal or vertical
        gradient. Can be "linear", which forms a gradient from `position[0]` (tuple) to `position[1]` (tuple). Can be
        "radial", which forms a radial gradient with centre `position[0]` (tuple) and radius `position[1]` (float). If
        `position` is not specified, this is automatically determined. Can be "conical", which forms a conical gradient
        (a gradient that is constant along the radius and varies along as the angle varies). `position[0]` (tuple)
        specifies the centre, and `postion[1]` (float) the starting angle (in degrees from the positive y-axis). If
        `position` is not provided, it is automatically determined, with starting angle set to 0. Defaults to
        "horizontal".
    :type style: str
    :param position: See style.
    :type position: tuple
    :param extend: How the gradient behaves outside the range specified in `position`. Can be "pad", "repeat" or
        "reflect" (only applies when style is "linear" or "radial" and `position` is specified). Defaults to "pad".
    :type extend: str
    :param resolution: The resolution of the gradient, when it is a matplotlib (or cmasher) cmap. Does not do anything
        when the cmap is a dict or a list. Defaults to 256.
    :type resolution: int

    :return:
    """
    style = style.lower()
    extend = extend.lower()
    if style in ["horizontal", "vertical"]:
        if position is not None:
            raise ValueError(f"If gradient has style {style}, position must not be specified.")
        else:
            gradient = QLinearGradient()
            gradient.autoscale = True

    elif style in ["linear"]:
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


def merge(plots):  # not optimised, but fast enough (& not sure if it works)
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


def set_interval(interval):
    """
    :param interval: The time interval (in seconds) to set for updating the plot.
    """
    window.interval = interval * 1000


def on_refresh(func):
    if window.timer:
        window.timer.timeout.connect(func)
    window.update_funcs.append(func)


def on_next_refresh(func):          # todo: only works in eventloop, not in show_window style.
    QtCore.QTimer.singleShot(0, func)


def on_mouse_click(func):
    window.fig_widget.scene().sigMouseClicked.connect(func)


def add_slider(
        name: str, init_value=1.0, min_value=0.0, max_value=10.0, n_ticks=51,
        tick_interval=None, only_ints=False, logscale=False, custom_arr=None, var_name=None,
        print_value=False, row=None):
    """
    Creates a slider with the given parameters, and adds it to the input_widget.

    :param name: The name in front of the slider.
    :type name: str
    :param init_value: The initial value of the slider.
    :type init_value: float
    :param min_value: The minimum value of the slider.
    :type min_value: float
    :param max_value: The maximum value of the slider.
    :type max_value: float
    :param n_ticks: The number of ticks on the slider. Defaults to 51.
    :type n_ticks: int
    :param tick_interval: The interval between ticks. If provided, overwrites `n_ticks`.
    :param only_ints: Whether to use whole numbers as ticks. If set to True, `tick_interval` is used as spacing
        between the ticks and `n_ticks` is ignored. If `tick_interval` is not specified, it defaults to 1.
        Rounds `tick_interval` to an integer and changes the variable to always be an integer. Not allowed
        in combination with `logscale`. Defaults to False
    :type only_ints: bool
    :param logscale: Whether to use a logarithmic scale. When `tick_interval` is given it serves as a
        multiplication factor between a point and the previous point (it is rounded to fit min_value and
        max_value. Not allowed in combination with `only_ints`. Defaults to False.
    :type logscale: bool
    :param custom_arr: Array or list of values, where `custom_arr[i]` will be the value of the slider when it
        is set to position `i`. Overwrites all other parameters (except `init_value`). Defaults to None.
    :param var_name: The name of the created variable. If `var_name` is not provided, the variable will be
        named `name`.
    :type var_name: str
    :param print_value: Whether to print the value of the slider when it changes. Defaults to False.
    :type print_value: bool
    :param row: Row to which the widget is added. Defaults to
    :type row: int
    :return: The slider widget.
    """

    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.Slider(
        window.first_input_table, name, init_value, min_value, max_value, n_ticks, tick_interval, only_ints, logscale,
        custom_arr, var_name, print_value, row
    )


def add_checkbox(name: str, init_value=False, var_name=None, print_value=False, row=None):
    """
    Adds a checkbox with the given parameters.

    :param name: The name in front of the checkbox.
    :type name: str
    :param init_value: The initial value of the checkbox.
    :type init_value: bool
    :param var_name: The name of the created variable. If var_name is not provided, the variable will be named name.
    :type var_name: str
    :param print_value: Whether to print the value of the slider when it changes. Defaults to False.
    :type print_value: bool
    :param row: Row to which the widget is added. Defaults to
    :type row: int
    :return: The checkbox widget.
    """

    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.Checkbox(window.first_input_table, name, init_value, var_name, print_value, row)


def add_inputbox(name: str, init_value=1.0, type_func=None, var_name=None, print_value=False, row=None):
    """
    Adds an inputbox with the given parameters.

    :param name: The name in front of the inputbox.
    :type name: str
    :param init_value: The initial value of the inputbox.
    :param type_func: The function that takes in a string and returns the value as the correct type. Usually,
        this will default to `ast.literal_eval`, which works for a lot of data types: str, float, complex, bool,
        tuple, list, dict, set and None. If `type_func` is set to None (default value), then it will be set to
        `ast.literal_eval` if `init_value` is one of the mentioned data types. If init_value is a `np.array` or
        a range object, this is also handled, but it needs to be explicitly changed to ast.literal_eval if the
        data type is changed during runtime. If you have a different data type that doesn't work with automatic
        handling a function can be passed to this argument that takes in a string and returns the desired value.
        Note that `ast.literal_eval` is a lot slower than for example `float`, so if you are sure the input is
        a float, a minor speedup can be achieved by explicitly setting `type_func=float`.

        For example
        `type_func` can be `int`. So that each value is turned into an int. If it is not given it is
        automatically determined, which works for the following instances: str, float, complex, bool, range, and
        the following iterables: tuple, list, dict, set. It is assumed that each of their elements is one of the
        previously mentioned instances, and they are not nested. Only np.ndarrays allow nesting.
        Can be refreshed by passing a value of the new type to refresh_type_func.
        Note: if you aren't sure if the type will be a list or a value, you can use type_func=json.loads
    :param var_name: The name of the created variable. If `var_name` is not provided, the variable will be
        named name.
    :type var_name: str
    :param print_value: Whether to print the value of the slider when it changes. Defaults to False.
    :type print_value: bool
    :param row: Row to which the widget is added. Defaults to
    :type row: int
    """

    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.InputBox(window.first_input_table, name, init_value, type_func, var_name,
                                             print_value, row)
    # current_row + 1 because this parameter is updated inside the function


def add_button(name: str, func=None, row=None):
    """
    Creates a button with name `name` and bound function `func`, and adds it to the input_widget.

    :param name: The name in front of the button.
    :type name: str
    :param func: The function which is run on button press
    :param row: Row to which the widget is added. Defaults to
    :type row: int
    """
    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.Button(window.first_input_table, name, func, row)


def add_dropdown(name: str, options: list, init_index=0, option_names=None, var_name=None, print_value=False, row=None):
    """
    Creates a dropdown widget with the given parameters.

    :param name: The name in front of the dropdown.
    :type name: str
    :param options: A list of all options shown in the dropdown menu.
    :param init_index: The index that the dropdown is initially set to.
    :type init_index: int
    :param option_names: A list of all options the created variable can be, where option_names[index] is
        the value given to the variable, if the dropdown is set to index. If option_names is not provided
        it will be set to `options`.
    :param var_name: The name of the variable. If var_name is not provided, the variable will be named name.
    :type var_name: str
    :param print_value: Whether to print the value of the slider when it changes. Defaults to False.
    :type print_value: bool
    :param row: Row to which the widget is added. Defaults to
    :type row: int
    :return: The dropdown widget.
    """

    if not window.first_input_table:
        window.init_first_tab()
    return window.first_input_table.Dropdown(window.first_input_table, name, options, init_index, option_names,
                                             var_name, print_value, row)


def add_rate_slider(
        name: str, init_value=1.0, change_rate=10.0, absolute=False, time_var=None,
        custom_func=None, var_name=None, print_value=False, row=None
):
    """
    Creates a RateSlider with the given parameters.

    :param name: The name in front of the rate_slider.
    :type name: str
    :param init_value: The initial value of the rate_slider.
    :type init_value: float
    :param change_rate: Change to the value of the variable per second (how it changes depends on `absolute`),
        multiplied by the current rate_slider position (value between -1 and 1).
    :type change_rate: float
    :param absolute: How the value of the variable is changed. If absolute is True, changerate will be added
        every second. If it is set to False, the variable will be multiplied be changerate every second.
    :type absolute: bool
    :param time_var: If set to None (default), actual time will be used. It can also be set to the name of a
        variable in `squap.var` as a string. Then that variable will be regarded as time: if it increases by 1,
        the created variable will be changed by changerate.
    :param custom_func: the function that changes the created variable. Overrides `absolute`. It must take three
        arguments: `old_value`, `dt` and `slider_value` and must return the new value. `old_value` is the value
        of the variable the previous time the function was run, dt is the change in time since then (takes
        `time_var` into account). `slider_value` is a value between -1 and 1, dependent on the slider position.
    :param var_name: The name of the created variable. If var_name is not provided, the variable will be named name.
    :type var_name: str
    :param print_value: Whether to print the value of the slider when it changes. Defaults to False.
    :type print_value: bool
    :param row: Row to which the widget is added. Defaults to
    :type row: int
    :return: The rate_slider widget.
    """
    if not window.first_input_table:
        window.init_first_tab()

    return window.first_input_table.RateSlider(
        window.first_input_table, name, init_value, change_rate,
        absolute, time_var, custom_func, var_name, print_value, row
    )


def add_input_table(name=None):
    """
    Returns a newly created input table on the left. If one already exists, it is added as a tab to a QTabWidget. Note
    that an input table is automatically created when another function is called that implies the existence of an
    input table, so call this function before that to name the first input table.

    :param name: Name of the tab, only visible when multiple input tables are added. Defaults to tab{i} where i is the
        ith tab.
    :type name: str
    """
    if not window.first_input_table:
        return window.init_first_tab(name=name)
    else:
        return window.add_table(name=name)


def rename_tab(name, index=0, old_name=None):
    """
    Renames tab with index `ìndex` or old name `old_name` to `name`.
    """
    window.rename_tab(name, index, old_name)


def get_boxes():
    """
    Returns a list containing all boxes that exist at this point.
    """
    result = []
    for table in window.input_tables:
        result.extend(table.get_boxes())
    return result


def get_current_row():
    """
    returns row of latest placed widget
    """
    return window.first_input_table.current_row


def link_boxes(boxes: typing.List, only_update_boxes=None):
    """
    Links all boxes in the list `boxes`. Boxes added to only_update_boxes are only updated when a box in boxes is
    changed but do not cause the other boxes to update when they are changed.
    `link_boxes(box1, box2); link_boxes(box2, box3)` can be used to link box1 to box2 and box2 to box3 without linking
    box1 to box3.
    """
    window.link_boxes(boxes, only_update_boxes)


def display_fps(update_speed=0.2, get_fps=False, optimised=False, plot_window=None):
    """
    Displays frames per second(fps) at the top of the plot widget.

    Parameters:
        update_speed (float, optional): The update speed for fps calculation. Defaults to 0.2 second.
        get_fps (bool, optional): Whether to store fps. If set to True, the fps will be saved to var.fps every time it
            is updated. Defaults to False
        optimised (bool, optional): Whether to use an optimised calculation method. If set to True, it is a bit
            quicker, but less consistent for variable fps. Defaults to False.
        plot_window (pyqtgraph.PlotItem, optional): Which window to set the title to the fps. Defaults to top-left.

    :return func: function that is needed to update the fps. If the program is run in refresh mode, this function
        needs to be run each loop

    Raises:
        NotImplementedError: If the function is called in 3D plot style, which is not supported yet.
    """
    if plot_window is None:
        plot_window = window.axs
        while isinstance(plot_window, list):
            plot_window = plot_window[0]

    window.fps_timer = current_time()
    skip = Namespace(total=0, count=0)  # Namespace used for function variables that need to carry over
    # the fps is updated

    if optimised:
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


def benchmark(n_frames=None, total_seconds=None):
    """
    Run the program until it is closed and then report the total frames and fps. If n_frames or total_seconds are
    specified, the program will quit when either has passed.

    :param n_frames: Number of frames to run the program for
    :type n_frames: int
    :param total_seconds: Total time to run the program for.
    :type total_seconds: float
    """
    local_vars = Namespace(time=current_time(), count=0)
    # Namespace used for function variables that need to carry over

    if n_frames is None and total_seconds is None:
        def func():
            local_vars.count += 1

    elif n_frames is None:
        def func():
            local_vars.count += 1
            if current_time() - local_vars.time > total_seconds:
                window.close()

    elif total_seconds is None:
        def func():
            local_vars.count += 1
            if local_vars.count >= n_frames:
                window.close()

    else:
        def func():
            local_vars.count += 1
            if current_time() - local_vars.time > total_seconds or local_vars.count >= n_frames:
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


def resize(width, height):
    """
    Resizes the window.

    :param width: Number of pixels wide it is changed to. Starts off at 640, or 965 if inputs are present (the 5 is for
        the border between the input_widget and the plot_widget).
    :type width: int
    :param height: Number of pixels high it is changed to. Starts off at 480.
    :type height: int
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


def size():
    """
    Returns the size of the window. Can be unreliable when called before the window is shown.
    """
    return window.size().toTuple()


def set_input_partition(fraction=1/3):
    """
    Sets the position of the partition between the 2 columns of the input_widget.

    :param fraction: float between 0 and 1, specifying the portion of the window taken up by the partition. Starts off
        as 1/3
    :type fraction: float
    """
    if not window.first_input_table:
        window.init_first_tab()
    window.first_input_table.set_partition(fraction)


def set_input_width_ratio(fraction=1/2):
    """
    Sets the relative size of the input window compared to the plot window. A fraction of 1/2 (default value) means that
    the plot window is 2 times wider than the input window.
    """
    if not window.first_input_table:
        window.init_first_tab(width_ratio=fraction)
    else:
        width, height = window.size().toTuple()
        window.splitter.width_ratio = fraction
        window.main_input_widget.resize(int(fraction * width / (fraction + 1)), height)
        window.fig_widget.resize(int(width / (fraction + 1)), height)
        window.splitter.resize(width, height)


def is_alive():
    return window.isVisible()


def refresh(wait_interval=True, call_update_funcs=True):
    """
    Refreshes everything that is shown on screen, and waits according to interval (set with squap.set_interval)

    :param wait_interval: If set to `False`, doesn't wait for
    """
    if wait_interval and window.interval:
        now = current_time()
        to_wait = window.interval/1000 - (now - window.refresh_timer)
        if to_wait > 0:
            time.sleep(to_wait)
        window.refresh_timer = current_time()
        QtGui.QGuiApplication.processEvents()
    else:
        QtGui.QGuiApplication.processEvents()
    if call_update_funcs:
        for func in window.update_funcs:
            func()
    # timer.start(0)


def show_window():
    """
    shows the window and refreshes it
    """
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
    """
    shows window and starts updating it if update funcs are provided
    """

    timer = QtCore.QTimer()
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

    window.app.exec_()


def close_window():
    window.close()


def clear():
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


def export(filename, full_window=False):
    """
    saves the current window as an image to file `filename`

    :param filename: Name of the file to which the image must be saved. Extension can be png, jpg, jpeg, bmp, pbm,
        pgm, ppm, xbm and xpm. Defaults to png if no extension is provided
    :param full_window: whether to include the input window as well.
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
        print(f"exported current plot window to {basename}{extension}")
    else:
        print(f"saving failed, extension {extension} is not an allowed extension")


def export_video(
        filename: str, fps=30.0, n_frames=None, duration=None, stop_func=None, skip_frames=0, display_window=False
):
    """
    Saves a video to file `filename` with the specified parameters. Out of n_frames, duration and stop_func at most
    one can be provided. If none of these are given the video will be indefinite, and will be stopped and saved as
    soon as the window is closed, or when KeyboardInterrupt is raissed (when the user attempts to manually
    stop the program). If the window is closed before the stop condition is met, the video will still be saved.

    :param filename: Name of the file to which the video is exported.
    :type filename: str
    :param fps: Frames per second of the video. Defaults to 30.
    :type fps: float
    :param n_frames: Number of frames before the video stops and saves.
    :type n_frames: int
    :param duration: Duration in seconds before the video stops and saves. It will save the last frame after the time is
        up as well.
    :type duration: float
    :param stop_func: This function will be run after every iteration. If it returns True, the video stops and saves.
    :type stop_func: function
    :param skip_frames: number of frames to not save after a frame is saved.
    :type skip_frames: int
    :param display_window: Whether to display the window or not. Defaults to False.
    :type display_window: bool
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
                pixmaps.append(window.fig_widget.grab())

            frame_counter += 1

    except KeyboardInterrupt:
        print("The program is interupted, the recording is now being save.")

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


def start_recording(filename: str, fps=30.0, skip_frames=0, widget=window.fig_widget):
    """
    Saves a video to file `filename` with the specified parameters. Out of n_frames, duration and stop_func at most
    one can be provided. If none of these are given the video will be indefinite, and will be stopped and saved as
    soon as the window is closed, or when KeyboardInterrupt is raissed (when the user attempts to manually
    stop the program). If the window is closed before the stop condition is met, the video will still be saved.

    :param filename: Name of the file to which the video is exported.
    :type filename: str
    :param fps: Frames per second of the video. Defaults to 30.
    :type fps: float
   :param skip_frames: number of frames to not save after a frame has been saved.
    :type skip_frames: int
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
