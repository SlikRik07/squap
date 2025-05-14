import ast

import numpy as np
from PySide6.QtWidgets import QTableWidgetItem
from pyqtgraph import mkPen, mkColor
import json


# def map_color(color_name):
#     translator = str.maketrans({'_': '', ' ': ''})
#
#     color_name = color_name.translate(translator).lower()
#     col_dict = {
#         "w": "white", "r": "red", "g": "green", "b": "blue", "y": "yellow", "c": "cyan", "m": "magenta",
#         "darkgray": "darkGray", "lightgray": "lightGray", "darkred": "darkRed", "darkgreen": "darkGreen",
#         "darkblue": "darkBlue", "darkcyan": "darkCyan", "darkmagenta": "darkMagenta", "darkyellow": "darkYellow",
#     }
#
#     if color_name in col_dict:
#         color_name = col_dict[color_name]
#     return color_name


# def construct_color(color):   # accepts color name (see map_color), tuple of 3 or 4 ints between 0 and 255
#     # tuple of 3 or 4 floats between 0 and 1, or hex string starting with #
#     if isinstance(color, str):
#         color = map_color(color)
#         return QColor(color)
#     elif isinstance(color, tuple):
#         return QColor(*color)
#     # elif isinstance(color, list) or isinstance(color, np.ndarray):
#     #     colors = []
#     #     for col in color:
#     #         colors.append(construct_color(col))
#     #     return colors
#     elif isinstance(color, QColor):
#         return QColor(color)
#     else:
#         return QColor(color)
#         raise TypeError(
#         f"Not sure how to make a color from {color} with type {type(color)}. If this is a mistake send me a message"
#         )   # error #1007


def get_pen(old_pen, **kwargs):
    if "width" in kwargs:
        width = kwargs["width"]
    elif "w" in kwargs:
        width = kwargs["w"]
    else:
        width = 1

    if "colour" in kwargs:
        color = kwargs["colour"]
    elif "c" in kwargs:
        color = kwargs["c"]
    elif "color" in kwargs:
        color = kwargs["color"]
    else:
        color = 'y'

    if is_iter(color):
        color = np.array(color)*255

    pen = mkPen(
        color, width=width, **kwargs
    )  # pen are all the things to do with how the curve is drawn
    return pen


def qvect_to_arr(qvect):    # turns any type of QVector into an array
    return np.array(qvect.toTuple())


def textify(value):         # consistent value layout. If it is too large or small, it will be represented in e notation
    if 0.001 < value <= 1e5:
        text = str(round(value, 12))
    else:
        text = f"{value:.9e}"
    return text


def is_iter(arg):
    if hasattr(arg, "__iter__") and not isinstance(arg, str):
        return True
    else:
        return False


def is_multiple_colors(arg):
    if is_iter(arg):
        if is_iter(arg[0]):
            return True
        elif len(arg) == 3 and (isinstance(arg[0], int) or isinstance(arg[0], float)):
            return False
        else:
            return True
    else:
        return False


def get_single_color(input_col):
    if is_iter(input_col):
        if isinstance(input_col[0], int) or isinstance(input_col[0], float):
            if len(input_col) == 3 or len(input_col) == 4:
                if max(input_col) <= 1:
                    return mkColor(np.array(input_col)*255)
                else:
                    return mkColor(np.array(input_col))
            else:
                raise ValueError(f"Expected tuple of lenght 3 or 4  , but got length {len(input_col)} (Note that a "
                                 f"line can only be one color).")
        else:
            raise TypeError(f"When an iterable is provided, it should have elements that are integers or floats. "
                            f"Got {type(input_col)} (Note that a line can only be one color).")
    else:
        return mkColor(input_col)


# <editor-fold desc="functions that convert string to specified type, for inputbox input validation.">
# def stringify(string):          # turning 'banana' into string "banana" instead of "'banana'"
#     return string.strip(r'"\'')


# def str_to_bool(string: str):
#     if string == "False":
#         return False
#     else:
#         return True


# def str_to_tuple_func(sub_func):
#     def func(string: str):
#         return (sub_func(i) for i in map(str.strip, string.strip(" ()").split(","))) if string.strip(" ()") else ()
#
#     return func


# def str_to_list_func(sub_func):
#     def func(string: str):
#         return [sub_func(i) for i in map(str.strip, string.strip(" []").split(","))] if string.strip(" []") else []
#
#     return func


# def str_to_set_func(sub_func):
#     def func(string: str):
#         return {sub_func(i) for i in map(str.strip, string.strip(" {}").split(","))} if string.strip(" {}") else set()
#
#     return func


# def str_to_dict_func(sub_func1, sub_func2):
#     def func(string: str):
#         if string.strip(" {}"):
#             result = {}
#             for i in map(str.strip, string.strip(" {}").split(",")):
#                 key, value = i.split(":")
#                 result[sub_func1(key)] = sub_func2(value)
#             return result
#         else:
#             return {}
#
#     return func

# </editor-fold>


def get_type_func(value, parent, col):
    for instance in [int, str, float, complex, bool, list, dict, tuple, set, range, np.ndarray]:
        if isinstance(value, instance):  # checks a bunch of instances, and if it is one of them,
            if instance in [int, str, float, complex, bool, list, dict, tuple, set]:
                type_func = ast.literal_eval

            elif instance is range:
                type_func = lambda string: range(*(
                    int(i) for i in string.replace(" ", "").replace(")", "").split("(")[1].split(",")))

            elif instance is np.ndarray:
                parent.setItem(parent.current_row, col, QTableWidgetItem(
                    json.dumps(value.tolist())))
                type_func = lambda string: np.array(json.loads(string))
            break
    else:
        if value is None:
            type_func = ast.literal_eval
        else:
            raise NotImplementedError(
                "the instance you are using (the type of the variable provided) is currently not supported"
                "do you think it should be? send me an e-mail at rikmulder7@gmail.com, and mention the "
                f"type was probably: {type(value)}")

    return type_func
