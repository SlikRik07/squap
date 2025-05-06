import numpy as np
import typing
from collections.abc import Callable
from time import time as current_time
import json

from .helper_funcs import (is_iter, textify, stringify, str_to_bool, str_to_tuple_func, str_to_list_func,
                           str_to_set_func, str_to_dict_func)

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem,
    QLabel, QSlider, QCheckBox, QPushButton, QComboBox
)
from PySide6.QtCore import Qt


class Box:                              # I am not sure if this is required, but I feel like it helps the IDE
    def __init__(self, parent):         # parent will be the InputWidget
        self.parent = parent
        self.change_funcs = []  # this is so that they can be reordered later if necessary

    def change_params(self, **kwargs):
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def bind(self, func):       # For a user to add a function that runs when the value is changed
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def on_change(self, *args):        # Function that updates the var.var_name value upon value change
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")

    def print_val(self):
        raise NotImplementedError("Subclasses should implement this! Users should not see this.")


class InputWidget(QTableWidget):    # table for all inputs
    def __init__(self, variables, width, height):
        super().__init__()

        self.resize(width, height)
        self.resized = False            # if window is resized with existing input_widget but not yet shown, this is
        # set to True, so that showing doesn't correct for input_widget as normal

        self.setRowCount(0)
        self.setColumnCount(3)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.col_partition = 1/3                # where is the partition between col 0 & col 1, should be between 0&1
        self.throttle_space = 60                # pixels of space a throttle gets

        self.setColumnWidth(0, int(width * self.col_partition))
        self.setColumnWidth(1, int(self.throttle_space))
        self.setColumnWidth(2, int(width * (1-self.col_partition))-self.throttle_space)

        # this cell is split in 2 for the throttle

        self.current_row = -1
        self.variables = variables
        self.input_varnames = []     # the names of every variable indexed by row for stuff like linking and throttle

    def resizeEvent(self, event) -> None:       # event is not used since every necessary parameter is in self
        width = self.width()
        height = self.height()

        self.setGeometry(0, 0, width, height)

        if self.rowHeight(0)*(self.current_row+1)+26 <= height:
            width -= 2
        else:
            width -= 18

        self.setColumnWidth(0, int(width * self.col_partition))
        self.setColumnWidth(1, int(self.throttle_space))
        self.setColumnWidth(2, int(width * (1-self.col_partition))-self.throttle_space)

    def add_widget(self):
        self.current_row += 1
        self.setRowCount(self.current_row + 1)
        table_height = self.rowHeight(0)*(self.current_row+1)+26
        if table_height >= self.height():
            # noinspection PyTypeChecker
            self.resizeEvent(None)

    def link_cells(self, row1, row2):
        rows = [row1, row2]
        cols = []
        for row in rows:
            for col in (1, 2):
                if self.item(row, col) is not None:
                    cols.append(col)
                    break
            else:
                print(f"row number {row} doesn't contain any cells that can be linked")
                exit(1005)
        skip_cell = {rows[0]: False, rows[1]: False}        # prevents recursion when a cell is changed

        def on_change(row_arg, col_arg):
            for i in range(len(rows)):
                if row_arg == rows[i] and col_arg == cols[i]:
                    j = -i + 1              # turns 1 into 0 and other way around
                    # this bit prevents recursion by skipping next time the other is called. This doesn't feel to sturdy
                    if not skip_cell[rows[i]]:     # so might crash later, not sure though.
                        skip_cell[rows[j]] = True
                        self.setItem(rows[j], cols[j], QTableWidgetItem(self.item(rows[i], cols[i]).text()))
                    else:
                        skip_cell[rows[i]] = False

        self.cellChanged.connect(on_change)

    class Slider(Box, QSlider):
        def __init__(self, parent, name: str, init_value: float, min_value: float, max_value: float, n_ticks=50,
                     tick_interval=None, only_ints=False, logscale=False, var_name=None, print_value=False,
                     custom_arr=None):
            """
            Creates a slider with the given parameters, and adds it to the input_widget.

            :param name: The name in front of the slider.
            :param init_value: The initial value of the slider.
            :param min_value: The minimum value of the slider.
            :param max_value: The maximum value of the slider.
            :param n_ticks: The number of ticks on the slider. Defaults to 50.
            :param tick_interval: The interval between ticks. If provided, overwrites `n_ticks`.
            :param only_ints: Whether to use whole numbers as ticks. If set to True, `tick_interval` is used as spacing
                between the ticks and `n_ticks` is ignored. If `tick_interval` is not specified, it defaults to 1.
                Rounds `tick_interval` to an integer and changes the variable to always be an integer. Not allowed
                in combination with `logscale`. Defaults to False
            :type only_ints: bool
            :param logscale: Whether to use a logarithmic scale. When `tick_interval` is given it serves as a
                multiplication factor between a point and the previous point (it is rounded to fit min_value and
                max_value. Not allowed in combination with `only_ints`. Defaults to False.
            :type only_ints: bool
            :param var_name: The name of the created variable. If `var_name` is not provided, the variable will be
                named `name`.
            :param print_value: Whether to print the value of the slider when it changes. Defaults to False.
            :param custom_arr: Array or list of values, where `custom_arr[i]` will be the value of the slider when it
                is set to position `i`. Overwrites all other parameters (except `init_value`). Defaults to None.
            :return: The slider widget.
            """
            Box.__init__(self, parent=parent)
            QSlider.__init__(self, parent=parent, orientation=Qt.Orientation.Horizontal)

            (self.min_value, self.max_value, self.var_name, self.only_ints, self.logscale, self.custom_arr,
             self.n_ticks, self.tick_interval) = (min_value, max_value, var_name, only_ints, logscale, custom_arr,
                                                  n_ticks, tick_interval)
            # this bit is the same for most widgets:
            # <editor-fold desc="add_widget and init name&var_name">
            parent.add_widget()
            # is set before so that the given value is remembered not the calculated one

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                col = 0
                parent.setSpan(parent.current_row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                col = 1
                parent.setSpan(parent.current_row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(parent.current_row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            parent.setCellWidget(parent.current_row, col, self)
            # </editor-fold>

            self.setMinimum(0)

            self.current_name = var_name
            self.printing_val = False

            if custom_arr is not None:
                self.arr = custom_arr
            elif logscale:
                if min_value*max_value <= 0:
                    raise ValueError("`min_value` and `max_value` must have the same sign when `logscale` is enabled.")
                if not tick_interval:
                    self.arr = np.logspace(np.log10(min_value), np.log10(max_value), int(n_ticks))
                else:
                    n_ticks = round(np.emath.logn(tick_interval, max_value/min_value))
                    self.arr = np.logspace(np.log10(min_value), np.log10(max_value), n_ticks)
            elif only_ints:
                if tick_interval is None:
                    tick_interval = 1
                else:
                    tick_interval = int(tick_interval)
                # max_value = max_value - (max_value - min_value) % tick_interval
                self.arr = np.arange(min_value, max_value+tick_interval, tick_interval)
                # n = int((max_value - min_value) / tick_interval)
            else:
                if not tick_interval:
                    self.arr = np.linspace(min_value, max_value, int(n_ticks))
                else:
                    self.arr = np.arange(min_value, max_value+tick_interval, tick_interval)

            # slider.setStyleSheet("QSlider {height: 20px; width: 200px;}")     # makes sliders nicer
            n = len(self.arr)-1
            self.setMaximum(n)
            self.setSingleStep(1)  # increment between values
            self.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.setTickInterval(1)  # distance between ticks
            if n > 50:      # remove ticks after n=50 to not make it too cluttered
                self.setTickPosition(QSlider.NoTicks)
            else:
                self.setTickPosition(QSlider.TickPosition.TicksBelow)

            if logscale:
                slider_val = np.argmin(np.abs(np.log10(np.array(self.arr)) - np.log10(init_value)))
            else:
                slider_val = np.argmin(np.abs(np.array(self.arr) - init_value))

            setattr(parent.variables, self.current_name, slider_val)
            self.setValue(slider_val)
            self.valueChanged.connect(self.on_change)

            if print_value:
                self.valueChanged.connect(self.print_val)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the slider. Only keyword arguments are accepted, and takes all arguments that
            `add_slider` accepts, except `init_value`.
            """
            turn_on_print_func = False
            update_arr = False                  # if any parameters are changed such that self.arr changes
            arr_kwargs = ["min_value", "max_value", "n_ticks", "tick_interval", "only_ints", "logscale", "custom_arr"]

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]

            print(f"{self.printing_val = }")
            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.valueChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True

            if "n_ticks" in kwargs and "tick_interval" not in kwargs:
                self.tick_interval = None

            for kwarg in arr_kwargs:
                if kwarg in kwargs:
                    update_arr = True
                    setattr(self, kwarg, kwargs[kwarg])

            if update_arr:
                old_arr = self.arr.copy()
                if "custom_arr" not in kwargs:      # if custom_arr is not provided but other arguments that change self.arr are
                    self.custom_arr = None

                if self.custom_arr is not None:
                    self.arr = self.custom_arr
                elif self.logscale:
                    if self.min_value * self.max_value <= 0:
                        raise ValueError("min_value and max_value must have the same sign when logscale is enabled.")
                    if not self.tick_interval:
                        self.arr = np.logspace(np.log10(self.min_value), np.log10(self.max_value), self.n_ticks)
                    else:
                        n_ticks = round(np.emath.logn(self.tick_interval, self.max_value / self.min_value))
                        self.arr = np.logspace(np.log10(self.min_value), np.log10(self.max_value), n_ticks)
                elif self.only_ints:
                    if self.tick_interval is None:
                        tick_interval = 1
                    else:
                        tick_interval = int(self.tick_interval)

                    self.arr = np.arange(self.min_value, self.max_value + tick_interval, tick_interval)
                    # self.max_value = self.max_value - (self.max_value-self.min_value) % tick_interval
                    # n = int((self.max_value-self.min_value)/tick_interval)
                else:
                    # print(not float(self.tick_i?nterval))
                    if self.tick_interval is None:
                        if "n_ticks" in kwargs.keys():
                            n_ticks = int(kwargs["n_ticks"])
                        else:
                            n_ticks = len(self.arr)
                        self.arr = np.linspace(self.min_value, self.max_value, n_ticks)
                    else:
                        self.arr = np.arange(self.min_value, self.max_value+self.tick_interval, self.tick_interval)

                if len(self.arr) == 0:
                    self.arr = old_arr
                    raise ValueError("Current parameters give an empty array")

                n = len(self.arr) - 1
                self.setMaximum(n)
                if n > 50:
                    self.setTickPosition(QSlider.NoTicks)
                else:
                    self.setTickPosition(QSlider.TickPosition.TicksBelow)

                current_val = getattr(self.parent.variables, self.current_name)
                if self.logscale:
                    slider_val = np.argmin(np.abs(np.log10(np.array(self.arr)) - np.log10(current_val)))
                else:
                    slider_val = np.argmin(np.abs(np.array(self.arr) - current_val))

                self.setValue(slider_val)       # also automatically calls on_change

            if turn_on_print_func:
                self.valueChanged.connect(self.print_val)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.valueChanged.disconnect(func)
                    self.valueChanged.connect(func)

        def bind(self, func):
            self.change_funcs.append(func)
            self.valueChanged.connect(func)
            return self

        def on_change(self, val):
            setattr(self.parent.variables, self.current_name, self.arr[val])

        def print_val(self):
            print(f"{self.current_name} = {self.arr[self.value()]}")

    class Checkbox(Box, QCheckBox):
        def __init__(self, parent, name: str, init_value: bool, var_name=None, print_value=False):
            """
            Adds a checkbox with the given parameters.

            :param name: The name in front of the checkbox.
            :param init_value: The initial value of the checkbox.
            :param var_name: The name of the created variable. If var_name is not provided, the variable will be named name.
            :param print_value: Whether to print the value of the checkbox when it changes. Defaults to False.
            :return: The checkbox widget.
            """
            Box.__init__(self, parent=parent)
            QCheckBox.__init__(self)

            self.var_name = var_name

            # <editor-fold desc="add_widget and init name&var_name">
            parent.add_widget()
            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                col = 0
                parent.setSpan(parent.current_row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                col = 1
                parent.setSpan(parent.current_row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(parent.current_row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            parent.setCellWidget(parent.current_row, col, self)
            # </editor-fold>
            self.current_name = var_name
            self.printing_val = False

            setattr(parent.variables, self.current_name, init_value)

            self.setChecked(init_value)
            self.stateChanged.connect(self.on_change)

            if print_value:
                self.stateChanged.connect(self.print_val)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the checkbox. Only keyword arguments are accepted, and takes all arguments that
            `add_checkbox` accepts, except `init_value`.
            """
            turn_on_print_func = False

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.stateChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True

            if turn_on_print_func:
                self.stateChanged.connect(self.print_val)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.stateChanged.disconnect(func)
                    self.stateChanged.connect(func)

        def val(self):  # turns checkbox state into tf value    (val because value is already used by some boxes)
            if self.checkState() == Qt.CheckState.Checked:
                return True
            else:
                return False

        def bind(self, func):
            self.change_funcs.append(func)
            self.stateChanged.connect(func)
            return self

        def on_change(self):
            setattr(self.parent.variables, self.current_name, self.val())

        def print_val(self):
            print(f"{self.current_name} = {self.val()}")

    class InputBox(Box):
        def __init__(self, parent, name: str, init_value: float, type_func=None, var_name=None, print_value=False):
            """
            Adds an inputbox with the given parameters.

            :param name: The name in front of the inputbox.
            :param init_value: The initial value of the inputbox.
            :param var_name: The name of the created variable. If `var_name` is not provided, the variable will be
                named name.
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
            :param print_value: Whether to print the value of the inputbox when it changes. Defaults to False.

            """
            Box.__init__(self, parent=parent)

            self.row = parent.current_row + 1
            self.var_name = var_name

            # <editor-fold desc="add_widget and init name&var_name">
            parent.add_widget()

            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                self.col = 0
                parent.setSpan(parent.current_row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                self.col = 1
                parent.setSpan(parent.current_row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(parent.current_row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            # </editor-fold>
            if isinstance(init_value, str):
                parent.setItem(parent.current_row, self.col, QTableWidgetItem('"' + init_value + '"'))
            else:
                parent.setItem(parent.current_row, self.col, QTableWidgetItem(str(init_value)))

            self.current_name = var_name
            self.printing_val = False

            if type_func is None:
                self.type_func = get_type_func(init_value, parent, self.col)
            else:
                self.type_func = type_func

            setattr(parent.variables, self.current_name, init_value)
            self.parent.cellChanged.connect(self.on_change)

            if print_value:
                def print_func(row):
                    if row == self.row:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the checkbox. Only keyword arguments are accepted, and takes all arguments that
            `add_checkbox` accepts, except `init_value`.
            """
            turn_on_print_func = False

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.parent.cellChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True
            if turn_on_print_func:
                def print_func(row):
                    if row == self.row:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.parent.cellChanged.disconnect(func)
                    self.parent.cellChanged.connect(func)

        def val(self):
            return self.type_func(self.parent.item(self.row, self.col).text())

        def bind(self, func):
            def actual_func(row):
                if row == self.row:
                    func()

            self.change_funcs.append(actual_func)
            self.parent.cellChanged.connect(actual_func)
            return self

        def on_change(self, row):
            if row == self.row:
                setattr(self.parent.variables, self.current_name, self.type_func(self.parent.item(self.row, self.col).text()))

        def print_val(self):
            print(f"{self.current_name} = {self.val()}")

    class Button(Box, QPushButton):
        def __init__(self, parent, name: str, func=None):
            """
            Creates a button with name `name` and bound function `func`, and adds it to the input_widget.

            :param name: The name in front of the button.
            :param func: The function which is run on button press
            """
            Box.__init__(self, parent=parent)
            QPushButton.__init__(self, parent=parent, name=name)

            parent.add_widget()
            parent.setSpan(parent.current_row, 0, 1, 3)
            parent.input_varnames.append(None)        # so that indexing still works
            parent.setCellWidget(parent.current_row, 0, self)

            if func is not None:
                self.bind(func)         # is a user provided function, so now we can use bind

        def change_params(self, **kwargs):
            pass

        def bind(self, func):
            self.change_funcs.append(func)
            self.clicked.connect(func)
            return self

        def on_change(self):
            raise ValueError("This function is not defined for a Button")

        def print_val(self):
            raise ValueError("This function is not defined for a Button")

    class Dropdown(Box, QComboBox):
        def __init__(self, parent, name: str, options: typing.List, init_index=0, option_names=None, var_name=None,
                     print_value=False):
            Box.__init__(self, parent=parent)
            QComboBox.__init__(self)

            self.var_name, self.options, self.option_names = var_name, options, option_names
            if option_names is None:        # for change_params we need the original value, for this function not.
                for option in options:
                    if not isinstance(option, str):
                        option_names = [str(option) for option in options]
                        break
                else:
                    option_names = options

            # <editor-fold desc="add_widget and init name&var_name">
            parent.add_widget()
            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                col = 0
                parent.setSpan(parent.current_row, 0, 1, 3)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                col = 1
                parent.setSpan(parent.current_row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(parent.current_row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)
            parent.setCellWidget(parent.current_row, col, self)
            # </editor-fold>
            self.current_name = var_name
            self.printing_val = False

            self.addItems(option_names)
            self.setCurrentIndex(init_index)

            setattr(parent.variables, self.current_name, options[init_index])

            self.currentTextChanged.connect(self.on_change)

            if print_value:
                self.currentTextChanged.connect(self.print_val)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the checkbox. Only keyword arguments are accepted, and takes all arguments that
            `add_dropdown` accepts, except `init_value`.
            """
            turn_on_print_func = False
            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.currentTextChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True

            if "option_names" in kwargs:
                self.option_names = kwargs["option_names"]
                for _ in range(len(self.options)):
                    self.removeItem(0)
                self.addItems(self.option_names)

            if "options" in kwargs:
                if self.option_names is None:
                    for _ in range(len(self.options)):
                        self.removeItem(0)
                    for option in kwargs["options"]:
                        if not isinstance(option, str):
                            option_names = [str(option) for option in kwargs["options"]]
                            break
                    else:
                        option_names = kwargs["options"]
                    self.addItems(option_names)
                self.options = kwargs["options"]

            if turn_on_print_func:
                self.currentTextChanged.connect(self.print_val)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.currentTextChanged.disconnect(func)
                    self.currentTextChanged.connect(func)

        def bind(self, func):
            self.change_funcs.append(func)
            self.currentTextChanged.connect(func)

        def on_change(self):
            setattr(self.parent.variables, self.current_name, self.options[self.currentIndex()])

        def print_val(self):
            print(f"{self.current_name} = {self.options[self.currentIndex()]}")

    class Throttle(Box, QSlider):
        def __init__(self, parent, update_funcs, name: str, init_value: float, change_rate=10.0, absolute=False,
                     time_var=None, custom_func=None, var_name=None, print_value=False):
            """
            Creates a RateSlider with the given parameters.
    
            :param parent: The parent of the box, set to `squap.window.input_widget`.
            :param update_funcs: This is needed for updating the throttle while holding it, provide
                squap.window.update_funcs
            :param name: The name in front of the throttle.
            :param init_value: The initial value of the throttle.
            :param change_rate: Change to the value of the variable per second (how it changes depends on `absolute`),
                multiplied by the current throttle position (value between -1 and 1).
            :param absolute: How the value of the variable is changed. If absolute is True, changerate will be added
                every second. If it is set to False, the variable will be multiplied be changerate every second.
            :param time_var: If set to None (default), actual time will be used. It can also be set to the name of a
                variable in `squap.var` as a string. Then that variable will be regarded as time: if it increases by 1,
                the created variable will be changed by changerate.
            :param custom_func: the function that changes the created variable. Overrides `absolute`. It must take three
                arguments: `old_value`, `dt` and `slider_value` and must return the new value. `old_value` is the value
                of the variable the previous time the function was run, dt is the change in time since then (takes
                `time_var` into account). `slider_value` is a value between -1 and 1, dependent on the slider position.
            :param var_name: The name of the created variable. If var_name is not provided, the variable will be named name.
            :param print_value: Whether to print the value of the inputbox when it changes. Defaults to False.
            :return: The throttle widget.
            """
            Box.__init__(self, parent=parent)
            QSlider.__init__(self)

            (self.var_name, self.change_rate, self.absolute, self.time_var,
             self.custom_func) = var_name, change_rate, absolute, time_var, custom_func
            self.row = parent.current_row + 1
            # this bit is a bit different for the throttle \/\/
            # <editor-fold desc="add_widget and init name&var_name">
            parent.add_widget()
            if name == "":  # if no name the first two columns are merged for one cell, but does require var_name
                throttle_col = 0
                self.col = 1
                parent.setSpan(parent.current_row, 0, 1, 2)

                if var_name is None:
                    raise ValueError("name can only be empty if var_name is specified")  # #1004
            else:
                throttle_col = 1
                self.col = 2
                # parent.setSpan(parent.current_row, 1, 1, 2)
                self.textbox = QLabel(name)
                parent.setCellWidget(parent.current_row, 0, self.textbox)

                if var_name is None:
                    var_name = name

            parent.input_varnames.append(var_name)

            # </editor-fold>
            self.current_name = var_name
            self.printing_val = False

            setattr(parent.variables, self.current_name, init_value)

            self.slider = QSlider(Qt.Orientation.Horizontal, parent)
            parent.setCellWidget(parent.current_row, throttle_col, self.slider)
            self.slider.setRange(0, 200)
            self.slider.setValue(100)
            self.slider.setStyleSheet("""
                    QSlider::groove:horizontal {
                        border: 1px solid #aaa;
                        width: 50px;
                        height: 8px;
                        border-radius: 4px;
                    }

                    QSlider::handle:horizontal {
                        background: #000;
                        border: 1px solid #000;
                        width: 14px;
                        height: 16px;
                        border-radius: 8px;
                        margin: -4px 0;
                    }
                """)
            self.slider.in_middle = True        # if the throttle is set to the middle, nothing needs to happen
            # so if this is set to False, it doesn't run the stuff, so when the throttle is released, the impact on
            # performance is minimal

            def release_func():  # resets throttle to 0 when released
                self.slider.setValue(100)
                self.slider.in_middle = True

            def press_func():
                self.timer = get_t()
                self.slider.in_middle = False

            self.slider.sliderReleased.connect(release_func)
            self.slider.sliderPressed.connect(press_func)

            parent.setItem(self.row, self.col, QTableWidgetItem(str(textify(init_value))))
            setattr(parent.variables, self.current_name, init_value)
            self.parent.cellChanged.connect(self.on_change)

            # <editor-fold desc="create throttle update func">
            if time_var is None:
                self.timer = current_time()
                
                def get_t():
                    return current_time()
                
            else:
                def get_t():
                    return getattr(parent.variables, time_var)

            self.get_t = get_t

            if custom_func is None:
                if absolute:
                    def new_calc(dt,
                                 slider_value):  # slider_value is a value between -1 & 1 depending on slider position
                        setattr(parent.variables, self.current_name,
                                getattr(parent.variables, self.current_name) + self.change_rate * slider_value * dt)

                else:
                    # scales logarithmically, so every dt*slider_value = 1 var gets multiplied by changerate
                    def new_calc(dt, slider_value):
                        setattr(parent.variables, self.current_name,
                                getattr(parent.variables, self.current_name) * self.change_rate ** (dt * slider_value))
            else:
                def new_calc(dt, slider_value):
                    setattr(parent.variables, self.current_name,
                            custom_func(getattr(parent.variables, self.current_name), dt, slider_value))

            self.new_calc = new_calc

            def update_func():
                if not self.slider.in_middle:
                    old_t = self.timer
                    self.timer = self.get_t()
                    dt = self.timer - old_t
                    slider_value = (self.slider.sliderPosition() - 100) / 100
                    # 6 is arbitrary, it's how changerate scales with slider_val, linear sucks
                    self.new_calc(dt, np.sign(slider_value) * (np.exp(np.abs(slider_value) * 6) - 1) / np.exp(6))
                    val = getattr(parent.variables, var_name)
                    parent.setItem(self.row, self.col, QTableWidgetItem(textify(val)))
            # </editor-fold>

            update_funcs.append(update_func)

            if print_value:
                def print_func(row, col):
                    if row == self.row and col == self.col:
                        self.print_val()

                self.parent.cellChanged.connect(print_func)
                self.printing_val = True

        def change_params(self, **kwargs):
            """
            Changes the parameters of the rate-slider. Only keyword arguments are accepted, and takes all arguments that
            `add_throttle` accepts, except `init_value`.
            """
            turn_on_print_func = False
            update_new_calc = False

            if "name" in kwargs:
                self.textbox.setText(kwargs["name"])
            if "var_name" in kwargs:
                self.current_name = kwargs["var_name"]
            elif self.var_name is not None:
                self.current_name = self.var_name
            elif "name" in kwargs:
                self.current_name = kwargs["name"]

            if "print_value" in kwargs:
                if not kwargs["print_value"]:  # if print_value=False is passed as kwarg
                    if self.printing_val:
                        # if print_func already exists (and is not None), remove it and set it to None
                        self.parent.cellChanged.disconnect(self.print_val)
                        self.printing_val = False
                elif not self.printing_val:  # or if it does exist but is set to None at the moment
                    turn_on_print_func = True

            if "time_var" in kwargs:
                if kwargs["time_var"] != self.time_var:
                    if kwargs["time_var"] is None and self.time_var is not None:
                        self.timer = current_time()

                        def get_t():
                            return current_time()

                        self.get_t = get_t
                    elif kwargs["time_var"] is not None and self.time_var is None:
                        def get_t():
                            return getattr(self.parent.variables, self.time_var)

                        self.get_t = get_t
                    self.time_var = kwargs["time_var"]

            if "change_rate" in kwargs:
                self.change_rate = kwargs["change_rate"]

            if "absolute" in kwargs:
                self.absolute = kwargs["absolute"]
                update_new_calc = True

            if "custom_func" in kwargs:
                self.custom_func = kwargs["custom_func"]
                update_new_calc = True

            if update_new_calc:
                if self.custom_func is None:
                    if self.absolute:
                        def new_calc(dt,
                                     slider_value):  # slider_value is a value between -1 & 1 depending on slider position
                            setattr(self.parent.variables, self.current_name,
                                    getattr(self.parent.variables, self.current_name)
                                    + self.change_rate * slider_value * dt)

                    else:
                        # scales logarithmically, so every dt*slider_value = 1 var gets multiplied by changerate
                        def new_calc(dt, slider_value):
                            setattr(self.parent.variables, self.current_name,
                                    getattr(self.parent.variables, self.current_name) * self.change_rate ** (
                                                dt * slider_value))
                else:
                    def new_calc(dt, slider_value):
                        setattr(self.parent.variables, self.current_name,
                                self.custom_func(getattr(self.parent.variables, self.current_name), dt, slider_value))

                self.new_calc = new_calc

            if turn_on_print_func:
                self.parent.cellChanged.connect(self.print_val)
                self.printing_val = True

                for func in self.change_funcs:      # reorders change_funcs so that print_val is first
                    self.parent.cellChanged.disconnect(func)
                    self.parent.cellChanged.connect(func)

        def val(self):
            return float(self.parent.item(self.row, self.col).text())

        def bind(self, func):
            def actual_func(row, col):
                if row == self.row and col == self.col:
                    func()

            self.change_funcs.append(actual_func)
            self.parent.cellChanged.connect(actual_func)
            return self

        def on_change(self, row, col):
            if row == self.row and col == self.col:
                setattr(self.parent.variables, self.current_name, float(self.parent.item(self.row, self.col).text()))

        def print_val(self):
            print(f"{self.current_name} = {self.val()}")

