import sys
import os.path
from time import perf_counter as current_time
import time
from argparse import Namespace

import cv2
import numpy as np

from typing import Callable
from numbers import Number
from inspect import signature
from argparse import ArgumentError

from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QApplication
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt

from .plot_manager import PlotManager
from .table_manager import TableManager
from .plot_widget import PlotWidget
# from .plot_widget_3d import PlotWidget3D


class MainWindow(QMainWindow):
    def __init__(self, variables, width=640, height=480):
        self.app = QApplication()       # app must be created before QMainWindow initialisation.
        self.app.setStyle("Fusion")

        super().__init__()

        self.variables = variables
        self.update_funcs = []

        self.plot_manager = PlotManager()
        self.setCentralWidget(self.plot_manager.fig_widget)

        self.table_manager = TableManager(height)

        self.interval = None                # for timer when animated
        self.fps_timer = None
        self.refresh_timer = None
        self.timer = None                   # for disconnecting update_funcs

        self.resized = False                # if it has been resized already, the input_widget mustn't make it bigger
        self.splitter = None                # stuff that can be initialised later is set to None
        self.exit_when_closed = False       # whether to exit the entire program when window is closed
        # (above is mainly useful for `while True: squap.refresh`)
        self.close_funcs = []
        self.on_key_press_funcs = []

        self.resize(width, height)

    def closeEvent(self, event):
        # Window is being closed
        for func in self.close_funcs:
            func()
        if self.exit_when_closed:       # not sure if there should be an else
            sys.exit("Application has been closed (code 1008)")

    def resizeEvent(self, event):
        self.plot_manager.update_size(event)
        self.table_manager.height = self.height()

    def keyPressEvent(self, event):
        self.plot_manager.key_pressed(event)

    def init_first_tab(self, width_ratio=0.5, name="tab1"):
        """
        Initialises the first tab and adds it to a widget so that it can be moved into a QTabWidget later. This first
        tab is a standalone and a QTabWidget is not created yet.

        :param width_ratio: width=width_ratio*fig_widget.width. By default, width_ratio=0.5, probably meaning that
            fig_widget will be width 640, input_widget width 320, and window width 964. Note that width_ratio is a
            ratio not a fraction.
        :type width_ratio: float
        :param name: Name of the tab, only visible when multiple input tables are added.
        :type name: str
        """
        if self.table_manager.first_input_table is not None:
            raise RuntimeError("Can not create a first table when one already exists, use `add_tab()` instead.")

        self.splitter = QSplitter()
        self.splitter.width_ratio = width_ratio

        self.table_manager.width = int(self.size().width()*width_ratio)
        table, table_container = self.table_manager.create_first_table(name)

        self.splitter.addWidget(table_container)
        self.splitter.addWidget(self.plot_manager.fig_widget)
        self.setCentralWidget(self.splitter)

        height = self.size().height()
        if self.isVisible():
            self.resize(self.size().width() + self.table_manager.width + 4, height)
            # +4 extra for space between plot_widget and input_widget

            pos = self.pos().toTuple()
            self.move(int(pos[0] - 0.5 * (self.table_manager.width+4)), pos[1])

        return table

    def init_tab_widget(self):
        # size initialisation must be different depending on whether has been resized with existing input_widget
        # but not yet shown
        if self.table_manager.resized:
            # print(self.size())
            width, height = self.size().toTuple()
            # copied from resize in __init__.py (when input_widget has been resized, the new QTabWidget is also resized)
            ratio = self.splitter.width_ratio
            self.table_manager.main_input_widget.resize(int(ratio * width / (ratio + 1)), height)
            self.plot_manager.fig_widget.resize(int(width / (ratio + 1)), height)
            self.splitter.resize(width, height)
            self.table_manager.resized = True
        else:
            self.table_manager.main_input_widget.resize(self.table_manager.width, self.height())
            self.table_manager.resized = False

        tab_widget = self.table_manager.init_tab_widget()
        self.splitter.replaceWidget(0, tab_widget)

    # def init_3D(self):
    #     self.plot_style_3D = True
    #     self.plot_widget = PlotWidget3D(
    #         self.plot_widget.variables, self.plot_widget.update_funcs
    #     )
    #     self.setCentralWidget(self.plot_widget)

    def set_interval(self, interval: float):
        """Set interval between frames.

        Args:
            interval (Number): The time interval (in seconds) to set for updating the plot.
        """
        self.interval = interval * 1000
        if self.is_alive():
            self.timer.setTimeout(self.interval)        # not tested

    def is_alive(self) -> bool:
        """Whether the window is visible. """
        return self.isVisible()

    def on_refresh(self, func: Callable, disconnect: bool = False):
        """Adds or removes a function that will be called on window refresh.

        If you try to disconnect a function that cannot be disconnected, nothing happes.
        Args:
            func (Callable): The function that will be called on refresh.
            disconnect (bool, optional): Whether the function should be connected (False) or disconnected (True).
                Defaults to False.
        """
        if not disconnect:
            if self.timer:
                self.timer.timeout.connect(func)
            self.update_funcs.append(func)
        else:
            if func in self.update_funcs:
                self.update_funcs.append(func)
                if self.timer:
                    self.timer.timeout.disconnect(func)

    def benchmark(self, n_frames: int | None = None, duration: float | None = None):
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
                    self.close()

        elif duration is None:
            def func():
                local_vars.count += 1
                if local_vars.count >= n_frames:
                    self.close()

        else:
            def func():
                local_vars.count += 1
                if current_time() - local_vars.time > duration or local_vars.count >= n_frames:
                    self.close()

        def final_func():
            elapsed = current_time() - local_vars.time
            print(f"{local_vars.count} frames have passed in {elapsed} seconds, "
                  f"which gives an fps of {local_vars.count / elapsed}")

        self.update_funcs.append(func)
        self.close_funcs.append(final_func)

    def resize_window(self, width: int, height: int):
        """
        Resize the window.

        Args:
            width (int): Number of pixels wide it is changed to. Starts off at 640, or 965 if inputs are present (the 5 is
                for the border between the input_widget and the plot_widget).
            height (int): New height in pixels. Starts off at 480.
        """
        self.resize(width, height)
        self.resized = True
        # if window.input_widget is None and not window.isVisible():
        #     window.fig_widget.resize(width, height)

        if self.table_manager.main_input_widget:
            ratio = self.splitter.width_ratio
            self.table_manager.main_input_widget.resize(int(ratio * width / (ratio + 1)), height)
            self.plot_manager.fig_widget.resize(int(width / (ratio + 1)), height)
            self.splitter.resize(width, height)
            self.table_manager.resized = True

    def window_size(self) -> tuple:
        """Return the size of the window as a tuple. Can be unreliable when called before the window is shown. """
        return self.size().toTuple()

    def set_input_width_ratio(self, fraction: float = 1 / 2):
        """
        Set the relative size of the input window compared to the plot window. A fraction of 1/2 (default value) means that
        the plot window is 2 times wider than the input window.

        Args:
            fraction (float, optional): value between 0 and 1, specifying the portion of the window taken up by the
                input window. Starts off at 1/2
        """
        if not self.table_manager.first_input_table:
            self.init_first_tab(width_ratio=fraction)
        else:
            width, height = self.window_size()
            self.splitter.width_ratio = fraction
            self.table_manager.main_input_widget.resize(int(fraction * width / (fraction + 1)), height)
            self.plot_manager.fig_widget.resize(int(width / (fraction + 1)), height)
            self.splitter.resize(width, height)

    def refresh(self, wait_interval: bool = True, call_update_funcs: bool = True):
        """Refresh everything shown on screen, and wait according to interval (set with squap.set_interval)

        Args:
            wait_interval (bool, optional): If set to `False`, doesn't wait for time set by `squap.set_interval`.
            call_update_funcs (bool, optional): If set to `True`, calls all functions bound by `squap.on_refresh` when
                this function is called.
        """
        if wait_interval and self.interval:
            now = current_time()
            to_wait = self.interval / 1000 - (now - self.refresh_timer)
            if to_wait > 0:
                time.sleep(to_wait)
            self.refresh_timer = current_time()
            QGuiApplication.processEvents()
        else:
            QGuiApplication.processEvents()
        if call_update_funcs:
            for func in self.update_funcs:
                func()
        # timer.start(0)

    def show_window(self):
        """Shows the window and refreshes it. Use in combination with `squap.refresh`"""
        self.refresh_timer = current_time()

        if self.table_manager.main_input_widget:
            if self.resized:
                if not self.table_manager.resized:
                    x = self.splitter.width_ratio  # calculates width of the input_widget given x and total w
                    fig_width = self.size().width() / (1 + x)
                    self.table_manager.width = fig_width * x
                else:
                    fig_width = self.width() - self.table_manager.width - 4
                self.splitter.setSizes([self.table_manager.width, fig_width])
            else:
                if not self.table_manager.resized:
                    self.resize(self.size().width() + self.table_manager.width + 4, self.height())
                # +4 extra for space between plot_widget and input_widget
                self.splitter.setSizes([self.table_manager.width, self.plot_manager.fig_widget.width()])

        self.show()

        self.refresh()
        if self.interval:
            self.variables.hidden_variables["start"] = time.time()

            def interval_func():
                time_left = self.interval / 1000 - (time.time() - self.variables.hidden_variables["start"])
                print(f"{time_left = }")
                # the time it should still wait
                if time_left > 0:
                    time.sleep(time_left)
                self.variables.hidden_variables["start"] = time.time()

            self.update_funcs.append(interval_func)

    def show(self):
        """Show window and starts loop. Use in combination with `Box.bind`, `squap.on_refresh` or for static plots. """

        timer = QTimer()  # timer is required for running functions on refresh and executing pyqtgraph programs
        if len(self.update_funcs):
            for func in self.update_funcs:
                timer.timeout.connect(func)

        if self.interval:
            timer.start(self.interval)
        else:
            timer.start()
        self.timer = timer

        if self.table_manager.main_input_widget:
            if self.resized:
                if not self.table_manager.resized:
                    x = self.splitter.width_ratio  # calculates width of the input_widget given x and total w
                    fig_width = self.size().width() / (1 + x)
                    self.table_manager.width = fig_width * x
                else:
                    fig_width = self.width() - self.table_manager.width - 4
                self.splitter.setSizes([self.table_manager.width, fig_width])
            else:
                if not self.table_manager.resized:
                    self.resize(self.size().width() + self.table_manager.width + 4, self.height())
                # +4 extra for space between plot_widget and input_widget
                self.splitter.setSizes([self.table_manager.width, self.plot_manager.fig_widget.width()])

            # pos = window.pos().toTuple()          # don't know why but this is suddenly not necessary anymore
            # window.move(pos[0]-0.5*(window.input_widget.width() + 4), pos[1])

        self.show()

        self.app.exec()

    def clear(self):
        """Clear everything. Todo: check"""
        for update_func in self.update_funcs:
            self.timer.timeout.disconnect(update_func)

        self.update_funcs = []
        self.plot_manager.clear()

    def export(self, filename: str, widget: QWidget | None = None):
        """Save the current window as an image to file `filename`.

        Args:
            filename (str): Name of the file to which the image must be saved. Extension can be png, jpg, jpeg, bmp, pbm,
                pgm, ppm, xbm and xpm. Defaults to png if no extension is provided.
            widget (bool, optional): The widget to export.
        """
        if widget is None:
            pixmap = self.grab()
        else:
            pixmap = widget.grab()

        basename, extension = os.path.splitext(filename)
        if extension:
            success = pixmap.toImage().save(filename)
        else:
            success = pixmap.toImage().save(f"{filename}.png")
            extension = ".png"
        if success:
            print(f"Exported current plot window to {basename}{extension}")
        else:
            raise RuntimeError(f"Saving failed, probably because extension {extension} is not an allowed extension")

    def export_video(
            self, filename: str, fps: float | int = 30.0, n_frames: int | None = None, duration: float | None = None,
            stop_func: Callable | None = None, skip_frames: int = 0, display_window: bool = False,
            widget: QWidget | None = None, save_on_close: bool = True
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
            duration (float, optional): Duration in seconds before the video stops and saves. It will save the last frame
                after the time is up as well.
            stop_func (Callable, optional): This function will be run after every iteration. If it returns True, the video
                stops and saves.
            skip_frames (int, optional): number of frames to not save after a frame is saved.
            display_window (bool, optional): Whether to display the window or not. Defaults to False.
            widget (QWidget, optional): which widget to record. Can be eg. a single plot, the entire window, or only
                the plot window. Defaults to only the plot window.
            save_on_close (bool, optional): Whether to save the video if the window is closed prematurely. Defaults to True.
        """
        if widget is None:
            widget = self

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
            self.show_window()

        try:
            while not condition():
                for update_func in self.update_funcs:
                    update_func()

                if display_window:
                    self.refresh()

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

    def start_recording(self, filename: str, fps: Number = 30.0, skip_frames: int = 0,
                        widget: QWidget | None = None) -> Callable:
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
        if widget is None:
            widget = self

        pixmaps = []
        frame_counter = {"i": 0}

        def record_func():
            if not frame_counter["i"] % (skip_frames + 1):
                pixmaps.append(widget.grab())
            frame_counter["i"] += 1

        def stop_func():
            basename, extension = os.path.splitext(filename)
            print(
                f"started saving {len(pixmaps)} frames to file {basename}.mp4 at {fps} fps")  # maybe other file-extension
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

            self.update_funcs.remove(record_func)

        self.update_funcs.append(record_func)

        return stop_func

    def display_fps(self, update_speed: float = 0.2, get_fps: bool = False, optimized: bool = False,
                    ax: PlotWidget | None = None):
        """
        Display frames per second(fps) at the top of the plot widget.

        Args:
            update_speed (float, optional): The update speed for fps calculation. Defaults to 0.2 second.
            get_fps (bool, optional): Whether to store fps. If set to True, the fps will be saved to var.fps every time it
                is updated. Defaults to False
            optimized (bool, optional): Whether to use an optimized calculation method. If set to True, it is a bit
                quicker, but less consistent for variable fps. Defaults to False.
            ax (squap.PlotWidget, optional): Which window to set the title to the fps. Defaults to top-left.

        Returns:
            Callable: function that is needed to update the fps. If the program is run in refresh mode, this function
                needs to be run each loop

        Raises:
            NotImplementedError: If the function is called in 3D plot style, which is not supported yet.
        """
        if ax is None:
            ax = self.plot_manager.plot_widget

        self.fps_timer = current_time()
        skip = Namespace(total=0, count=0)  # Namespace used for function variables that need to carry over
        # the fps is updated

        if optimized:
            def func():
                if skip.count == 0:
                    now = current_time()
                    elapsed = now - self.fps_timer
                    if elapsed:
                        self.fps_timer = now
                        fps = (skip.total + 1) / elapsed
                        fps = round(fps, -int(np.floor(np.log10(fps))) + (5 - 1))
                        if get_fps:
                            setattr(self.variables, "fps", fps)
                        if self.plot_manager.plot_style_3D:
                            print(f"{fps = }")
                        else:
                            ax.set_title(f"fps = {fps}")

                        skip.total = int(update_speed * fps)
                        skip.count = skip.total
                else:
                    skip.count -= 1
        else:
            def func():
                elapsed = current_time() - self.fps_timer
                skip.count += 1
                if elapsed > update_speed:
                    self.fps_timer = current_time()
                    fps = skip.count / elapsed
                    fps = round(fps, -int(np.floor(np.log10(fps))) + (5 - 1))
                    if self.plot_manager.plot_style_3D:
                        print(f"{fps = }")
                    else:
                        ax.set_title(f"fps = {fps}")
                    skip.count = 0

        self.update_funcs.append(func)  # both so that it works for both styles

    def on_mouse_click(self, func: Callable, pixel_mode: bool = False, ax: PlotWidget | None = None):
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
        if ax is None:
            ax = self.plot_manager.plot_widget

        params = signature(func).parameters
        has_var_args = any(
            param.kind == param.VAR_POSITIONAL
            for param in params.values()
        )
        n_args = 2 if has_var_args else len(params)

        if len(params) > 2:
            raise ArgumentError(func, f"func should take one or two arguments, but currently takes "
                                      f"{len(signature(func).parameters)} arguments.")

        if pixel_mode:
            def mouse_func(event):
                pos = event.scenePos().toTuple()
                args = ([pos, event][i] for i in range(n_args))  # handles 0, 1 or 2 n_args
                func(*args)

        else:
            def mouse_func(event):
                pos = event.scenePos()
                plot_pos = ax.getViewBox().mapSceneToView(pos).toTuple()
                print(event, pos, plot_pos)
                args = ([plot_pos, event][i] for i in range(n_args))  # handles 0, 1 or 2 n_args
                func(*args)

        self.plot_manager.fig_widget.scene().sigMouseClicked.connect(mouse_func)

    def on_mouse_move(self, func: Callable, pixel_mode=False, ax: PlotWidget | None = None):
        """Bind a function to mouse move.

        Args:
            func (Callable): The function that is called when the mouse is moved. The function can take 1 argument: the
                mouse position.
            pixel_mode (bool, optional): whether to return pixels from the top left (`True`), or coordinates (`False`).
                Defaults to `False`.
            ax (PlotWidget, optional): Axes on which to count the coordinate. Defaults to the first plot.
        """
        if ax is None:
            ax = self.plot_manager.plot_widget

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

        self.plot_manager.fig_widget.scene().sigMouseMoved.connect(mouse_func)

    def get_mouse_pos(self, pixel_mode=False, ax: PlotWidget | None = None) -> tuple:
        """Get the position of the mouse cursor on the plot, either as pixels from the top left, or as coordinates.

        Args:
            pixel_mode (bool, optional): whether to return pixels from the top left (`True`), or coordinates (`False`).
                Defaults to `False`.
            ax (PlotWidget, optional): Axes on which to count the coordinate. Only matters when `pixel_mode` is `False`.
                Defaults to the first plot.

        Returns:
            tuple: The coordinates of the mouse cursor on the plot.
        """
        if ax is None:
            ax = self.plot_manager.plot_widget

        pos = self.plot_manager.fig_widget.mapFromGlobal(QCursor.pos())
        if pixel_mode:
            return pos.toTuple()
        else:
            return ax.getViewBox().mapSceneToView(pos).toTuple()

    def on_key_press(self, func: Callable, accept_modifier: bool = False, modifier_arg: bool = False,
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
        if self.keyboardGrabber() is None:
            self.grabKeyboard()

        if event_arg:  # needs no changes, func takes as argument the event.
            edited_func = func
        else:
            def edited_func(event):  # edited_func takes in event, while func takes in func
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

        self.on_key_press_funcs.append(edited_func)
        return edited_func


def test_print(*args, **kwargs):
    print(f"filename={os.path.basename(__file__)}: ", end="")
    print(*args, **kwargs)
