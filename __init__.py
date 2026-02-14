# starts off by creating an instance of main_window, containing a plot widget.
from typing import Callable

from .main_window import MainWindow
from .plot_widget import PlotWidget
from .helper_funcs import get_single_color, get_cmap, ColorType
from .input_widget import InputTable, Box            # only for type hinting
from .variables import Variables
from .plot_manager import PlotManager
from .custimisation import get_font, get_gradient, cmap_to_colors

from functools import wraps

from pyqtgraph import setConfigOption
from PySide6.QtCore import QTimer

__all__ = [
    "var", "plot", "scatter", "errorbar", "set_xlim", "set_ylim", "xlim", "ylim", "legend", "set_title", "lock_zoom", "subplots",
    "remove_item", "get_gradient", "get_cmap", "inf_dline", "inf_hline", "inf_vline", "grid", "plot_text", "merge_plots", "set_interval",
    "on_refresh", "on_mouse_click", "on_mouse_move", "get_mouse_pos", "on_key_press", "add_slider", "add_checkbox", "add_inputbox", "add_button", "get_font",
    "add_dropdown", "add_rate_slider", "add_input_table", "get_boxes", "display_fps", "resize", "benchmark", "set_input_width_ratio",
    "set_input_partition", "is_alive", "refresh", "show_window", "show", "clear", "export", "export_video", "start_recording"
]

_window = None
_input_table = None
var = Variables()


def get_window():
    global _window
    if _window is None:
        _window = MainWindow(var)
    return _window


def get_input_table():
    global _input_table
    if _input_table is None:
        _input_table = get_window().init_first_tab()
    return _input_table


# <editor-fold desc="wrapped functions">
@wraps(PlotWidget.plot)
def plot(*args, **kwargs):
    return get_window().plot_manager.plot_widget.plot(*args, **kwargs)


@wraps(PlotWidget.scatter)
def scatter(*args, **kwargs):
    return get_window().plot_manager.plot_widget.scatter(*args, **kwargs)


@wraps(PlotWidget.errorbar)
def errorbar(*args, **kwargs):
    return get_window().plot_manager.plot_widget.errorbar(*args, **kwargs)


@wraps(PlotWidget.inf_dline)
def inf_dline(*args, **kwargs):
    return get_window().plot_manager.plot_widget.inf_dline(*args, **kwargs)


@wraps(PlotWidget.inf_hline)
def inf_hline(*args, **kwargs):
    return get_window().plot_manager.plot_widget.inf_hline(*args, **kwargs)


@wraps(PlotWidget.inf_vline)
def inf_vline(*args, **kwargs):
    return get_window().plot_manager.plot_widget.inf_vline(*args, **kwargs)


@wraps(PlotWidget.grid)
def grid(*args, **kwargs):
    return get_window().plot_manager.plot_widget.grid(*args, **kwargs)


@wraps(PlotWidget.plot_text)
def plot_text(*args, **kwargs):
    return get_window().plot_manager.plot_widget.plot_text(*args, **kwargs)


@wraps(PlotWidget.imshow)
def imshow(*args, **kwargs):
    return get_window().plot_manager.plot_widget.imshow(*args, **kwargs)


@wraps(PlotWidget.set_xlim)
def set_xlim(*args, **kwargs):
    return get_window().plot_manager.plot_widget.set_xlim(*args, **kwargs)


@wraps(PlotWidget.set_ylim)
def set_ylim(*args, **kwargs):
    return get_window().plot_manager.plot_widget.set_ylim(*args, **kwargs)


@wraps(PlotWidget.xlim)
def xlim(*args, **kwargs):
    return get_window().plot_manager.plot_widget.xlim(*args, **kwargs)


@wraps(PlotWidget.ylim)
def ylim(*args, **kwargs):
    return get_window().plot_manager.plot_widget.ylim(*args, **kwargs)


@wraps(PlotWidget.enable_autoscale)
def enable_autoscale(*args, **kwargs):
    return get_window().plot_manager.plot_widget.enable_autoscale(*args, **kwargs)


@wraps(PlotWidget.disable_autoscale)
def disable_autoscale(*args, **kwargs):
    return get_window().plot_manager.plot_widget.disable_autoscale(*args, **kwargs)


@wraps(PlotWidget.legend)
def legend(*args, **kwargs):
    return get_window().plot_manager.plot_widget.legend(*args, **kwargs)


@wraps(PlotWidget.set_title)
def set_title(*args, **kwargs):
    return get_window().plot_manager.plot_widget.set_title(*args, **kwargs)


@wraps(PlotWidget.lock_zoom)
def lock_zoom(*args, **kwargs):
    return get_window().plot_manager.plot_widget.lock_zoom(*args, **kwargs)


@wraps(PlotManager.create_subplots)
def subplots(*args, **kwargs):
    return get_window().plot_manager.create_subplots(*args, **kwargs)


@wraps(PlotManager.remove_item)
def remove_item(*args, **kwargs):
    return get_window().plot_manager.remove_item(*args, **kwargs)


@wraps(PlotManager.merge_plots)
def merge_plots(*args, **kwargs):
    return get_window().plot_manager.merge_plots(*args, **kwargs)


@wraps(MainWindow.set_interval)
def set_interval(*args, **kwargs):
    return get_window().set_interval(*args, **kwargs)


@wraps(MainWindow.is_alive)
def is_alive():
    return get_window().is_alive()


@wraps(InputTable.add_slider)
def add_slider(*args, **kwargs):
    return get_input_table().add_slider(*args, **kwargs)


@wraps(InputTable.add_checkbox)
def add_checkbox(*args, **kwargs):
    return get_input_table().add_checkbox(*args, **kwargs)


@wraps(InputTable.add_inputbox)
def add_inputbox(*args, **kwargs):
    return get_input_table().add_inputbox(*args, **kwargs)


@wraps(InputTable.add_button)
def add_button(*args, **kwargs):
    return get_input_table().add_button(*args, **kwargs)


@wraps(InputTable.add_dropdown)
def add_dropdown(*args, **kwargs):
    return get_input_table().add_dropdown(*args, **kwargs)


@wraps(InputTable.add_rate_slider)
def add_rate_slider(*args, **kwargs):
    return get_input_table().add_rate_slider(*args, **kwargs)


@wraps(InputTable.add_color_picker)
def add_color_picker(*args, **kwargs):
    return get_input_table().add_color_picker(*args, **kwargs)


@wraps(MainWindow.add_table)
def add_input_table(*args, **kwargs):
    return get_window().add_table(*args, **kwargs)


@wraps(MainWindow.on_mouse_click)
def on_mouse_click(*args, **kwargs):
    return get_window().on_mouse_click(*args, **kwargs)


@wraps(MainWindow.on_mouse_move)
def on_mouse_move(*args, **kwargs):
    return get_window().on_mouse_move(*args, **kwargs)


@wraps(MainWindow.get_mouse_pos)
def get_mouse_pos(*args, **kwargs):
    return get_window().get_mouse_pos(*args, **kwargs)


@wraps(MainWindow.on_key_press)
def on_key_press(*args, **kwargs):
    return get_window().on_key_press(*args, **kwargs)


@wraps(MainWindow.rename_tab)
def rename_tab(*args, **kwargs):
    return get_window().rename_tab(*args, **kwargs)


@wraps(MainWindow.set_active_tab)
def set_active_tab(*args, **kwargs):
    return get_window().set_active_tab(*args, **kwargs)


@wraps(MainWindow.get_all_tabs)
def get_all_tabs():
    return get_window().get_all_tabs()


@wraps(MainWindow.get_boxes)
def get_boxes():
    return get_window().get_boxes()


@wraps(MainWindow.get_current_row)
def get_current_row():
    return get_window().get_current_row()


@wraps(MainWindow.link_boxes)
def link_boxes(*args, **kwargs):
    return get_window().link_boxes(*args, **kwargs)


@wraps(MainWindow.resize)
def resize(*args, **kwargs):
    return get_window().resize(*args, **kwargs)


@wraps(MainWindow.window_size)
def size():
    return get_window().window_size()


@wraps(MainWindow.set_input_partition)
def set_input_partition(*args, **kwargs):
    return get_window().set_input_partition(*args, **kwargs)


@wraps(MainWindow.set_input_width_ratio)
def set_input_width_ratio(*args, **kwargs):
    return get_window().set_input_width_ratio(*args, **kwargs)


@wraps(MainWindow.display_fps)
def display_fps(*args, **kwargs):
    return get_window().display_fps(*args, **kwargs)


@wraps(MainWindow.benchmark)
def benchmark(*args, **kwargs):
    return get_window().benchmark(*args, **kwargs)


@wraps(MainWindow.refresh)
def refresh(*args, **kwargs):
    return get_window().refresh(*args, **kwargs)


@wraps(MainWindow.show_window)
def show_window():
    return get_window().show_window()


@wraps(MainWindow.on_refresh)
def on_refresh(*args, **kwargs):
    return get_window().on_refresh(*args, **kwargs)


@wraps(MainWindow.show)
def show():
    return get_window().show()


@wraps(MainWindow.close)
def close_window():
    return get_window().close()


@wraps(MainWindow.clear)
def clear():
    return get_window().clear()


@wraps(MainWindow.export)
def export(*args, **kwargs):
    return get_window().export(*args, **kwargs)


@wraps(MainWindow.export_video)
def export_video(*args, **kwargs):
    return get_window().export_video(*args, **kwargs)


@wraps(MainWindow.start_recording)
def start_recording(*args, **kwargs):
    return get_window().start_recording(*args, **kwargs)
# </editor-fold>


def enable_numba(enable: bool = True):
    """Enable numba. Can be a little faster, but takes longer to initialize. """
    setConfigOption('useNumba', enable)


def on_next_refresh(func: Callable):          # todo: only works in eventloop, not in show_window style.
    """Calls a function upon next refresh only. """
    QTimer.singleShot(0, func)


# def init_3D():
#     window.init_3D()
#
#
# def add_grid(diagonal):
#     """
#     :param diagonal: A tuple of two points that span the diagonal of a rectangle that lies on or parallel to the
#         xy, yz, or zx plane.
#     :return:
#     """
#     if window.plot_style_3D:
#         window.plot_widget.add_grid(diagonal)
#     else:
#         raise RuntimeError("This function only works in 3D. 3D mode needs to be initialised first. (1003)")
#
#
# def add_grids(size=(0.0, 5.0)):
#     """
#     Adds square grids on the xy, yz and zx planes, spanning from size[0] to size[1].
#
#     :param size: the size of each grid.
#     """
#     if window.plot_style_3D:
#         window.plot_widget.add_grids(size)
#     else:
#         raise RuntimeError("This function only works in 3D. 3D mode needs to be initialised first. (1003)")
#
#
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
#
#
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

