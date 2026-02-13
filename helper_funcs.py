import ast
import os.path
import json
from argparse import ArgumentError
from typing import TypeAlias, Union, Tuple, Iterable

import numpy as np
from numbers import Number
from PySide6.QtGui import QGradient, Qt, QFont, QColor, QPen

from PySide6.QtWidgets import QTableWidgetItem
from pyqtgraph import mkPen, mkColor, colormap


ColorType: TypeAlias = Union[QColor, mkColor, str, Iterable[int], float]
# ColorsType: TypeAlias = Union[Iterable[ColorType], Iterable[Iterable[ColorType]]]

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

class Font(QFont):
    """Class for generating font. Based on PySide6.QtGui.QFont. """
    kwarg_mapping = {           # aliases
        "font": "font_name", "fn": "font_name", "size": "font_size", "fs": "font_size", "strikethrough": "strikeout",
        "ls": "letter_spacing", "ws": "word_spacing"
    }

    def __init__(self, font_name: str = "Segoe UI", font_size: int | None = None, bold: bool = False,
                 italic: bool = False, underline: bool = False, strikeout: bool = False, overline: bool = False,
                 kerning: bool = False, stretch: int = 100, letter_spacing: float = .0, word_spacing: float = .0,
                 **kwargs):
        """
        Args:
            font_name (str): Name of the font. Can be any font on your computer. Defaults to "Segoe UI".
                Aliases: `font`, `fn`.
            font_size (int): Font size. Defaults to None. This usually means the font_size is 12 todo: check
                Aliases: `size`, `fs`.
            bold (bool): Whether to make the font bold. Defaults to `False`.
            italic (bool): Whether to make the font italic. Defaults to `False`.
            underline (bool): Whether to give the font underline. Defaults to `False`.
            strikethrough (bool): Whether to make the font strikethrough. Defaults to `False`. Alias: `strikeout`.
            overline (bool): Whether to give the font overline. Defaults to `False`.
            kerning (bool): Whether to draw the font with kerning. If kerning is enabled the text is drawn a bit more
                compactly. Defaults to `False`.
            stretch (int): Stretch factor as percentage. Eg. 100 is normal, 200 is twice as wide. Default is 100.
            letter_spacing (float): Extra spacing between letters in pixels. Defaults to `0.0`. Alias: `ls`.
            word_spacing (float): Extra spacing between words in pixels. Defaults to `0.0`. Alias: `ws`.
            **kwargs: Aliases. See argument description for allowed aliases.
        setFixedPitch?
        setLetterSpacing?
        setWordSpacing?
        """
        if font_size is None:
            super().__init__(font_name)
        else:
            super().__init__(font_name, font_size)

        self.set_data(bold=bold, italic=italic, underline=underline, strikeout=strikeout, overline=overline,
                      kerning=kerning, stretch=stretch, letter_spacing=letter_spacing, word_spacing=word_spacing,
                      **kwargs)

    def set_data(self, *args, **kwargs):
        """Changes Font after creation. Accepts all arguments appearing in `__init__`, so see that docstring
        for descriptions."""
        if len(args) > 2:
            raise ValueError("Too many positional arguments provided, only two are allowed, the first being font_size"
                             " and the second font_name")
        elif len(args):
            self.setPointSize(args[0])
            if len(args) == 2:
                self.setFamily(args[1])

        if kwargs:
            new_kwargs = transform_kwargs(kwargs, self.kwarg_mapping)
            if "font_name" in new_kwargs:
                self.setFamily(new_kwargs["font_name"])
            if "font_size" in new_kwargs:
                self.setPointSize(new_kwargs["font_size"])
            if "bold" in new_kwargs:
                bold = new_kwargs["bold"]
                if isinstance(bold, bool):
                    if bold:
                        self.setBold(bold)
                elif isinstance(bold, Number):
                    self.setWeight(Font.Weight(int(bold*1000)))
            if "italic" in new_kwargs:
                self.setItalic(new_kwargs["italic"])
            if "underline" in new_kwargs:
                self.setUnderline(new_kwargs["underline"])
            if "strikeout" in new_kwargs:
                self.setStrikeOut(new_kwargs["strikeout"])
            if "overline" in new_kwargs:
                self.setOverline(new_kwargs["overline"])
            if "kerning" in new_kwargs:
                self.setKerning(new_kwargs["kerning"])
            if "stretch" in new_kwargs:
                self.setStretch(new_kwargs["stretch"])
            if "letter_spacing" in new_kwargs:
                self.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, new_kwargs["letter_spacing"])
            if "word_spacing" in new_kwargs:
                self.setWordSpacing(new_kwargs["word_spacing"])


def update_pen(pen: QPen, **kwargs) -> QPen:
    """Update existing pen `pen` using kwargs.

    Note that changing the pen won't affect plots that already exist. The pen needs to be reassigned.

    Args:
        pen (mkPen): Pen to update.
        **kwargs: Can contain the following:
            "color": new color or gradient
            "width" (int): new width
            "dashed" (bool): draw dashed
            "dash_pattern" (List[int]): list of integers representing dash, gap sizes consecutively. Can be any even
                length and the pattern is repeated.

    Returns:
        QPen: The changed pen (old pen has also been changed).
    """
    if "color" in kwargs:
        if kwargs["color"] is not None:
            if isinstance(kwargs["color"], QGradient):
                pen.setBrush(kwargs["color"])
            else:
                pen.setBrush(get_single_color(kwargs["color"]))

    if "width" in kwargs:
        if kwargs["width"] is not None:
            pen.setWidth(kwargs["width"])

    if "dashed" in kwargs:
        if kwargs["dashed"]:
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([16, 16])
        else:
            pen.setStyle(Qt.PenStyle.SolidLine)

    if "dash_pattern" in kwargs:
        pen.setDashPattern(kwargs["dash_pattern"])
        # pen.stored_dash_pattern = None

    return pen


def get_cmap(data: str | dict[float | int, ColorType] | Iterable[ColorType], source: str = "matplotlib"):
    """Tool for getting cmap from different sources.

    If `data` is of type `str`, `source` decides from which library the cmap is obtained.

    Args:
        data (str, Iterable or dict): Has different behaviour depending on type:
            str: Name of the cmap. `source` specifies from which library the cmap is obtained.
            dict: `data[x]` is the cmap color at `x`, where the cmap is defined from x=0 to x=1. Every value not in
                `data` is interpolated. So e.g. `data` can be {0.0: "green", 0.25: "red", 1.0: "blue"}, which would
                mean a cmap going from green to red rather quickly, and then slowly turning blue.
            Iterable: `data[i]` should be colors, and the cmap becomes those colors equally spaced and interpolated
                between them.
        source (str): Library to obtain cmap from if it is a string. Currently you can choose from matplotlib and
            colorcet. Feel free to request me more.
    Returns:
        Callable:
    """
    if callable(data):  # probably catches too much, todo: check
        return data

    if isinstance(data, list):  # turns data into dict with equal spacing
        data = {index / (len(data) - 1): np.array(get_single_color(col).toTuple()) for index, col in enumerate(data)}

    if isinstance(data, str):
        def cmap_func(i):
            return colormap.get(data, source).map(i)

    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = np.array(get_single_color(value).toTuple())
        keys, values = map(np.array, zip(*sorted(data.items())))

        def cmap_func(i):
            """
            Interpolates to find the best approximation of the color at location `i`.
            A cmap generated from a dictionary defines color values at different positions on the interval [0, 1]. This
            function finds the closest two colors to `i`, and interpolates appropriately. If `i` is smaller than the
            lowest point at which a color is defined (usually 0), then this function returns the color at that lowest
            point, and similarly for the highest point.
            Works for scalar and array input.
            """
            i_arr = np.asarray(i)  # turns i into 1D array if it is just a number.
            is_scalar = i_arr.ndim == 0
            original_shape = i_arr.shape
            i_arr = i_arr.ravel()
            indices = np.array(np.searchsorted(keys, i_arr))  # index of first item that is bigger than i.

            lower_bound = indices == 0
            upper_bound = indices == max(keys)

            result = np.zeros((len(i_arr), 4))
            result[lower_bound] = values[0]
            result[upper_bound] = values[-1]

            interior = ~(lower_bound | upper_bound)

            if np.any(interior):
                interior_indices = indices[interior]
                interior_i = i_arr[interior]

                v_1, v_2 = values[interior_indices - 1], values[interior_indices]
                x_1, x_2 = keys[interior_indices - 1], keys[interior_indices]

                result[interior] = v_1 + (v_2 - v_1) * ((interior_i - x_1) / (x_2 - x_1))[:, np.newaxis]

            if is_scalar:
                return result[0]
            else:
                return result.reshape(original_shape + (4,))

            # Simplified slower version with iteration instead of array calculations below. Does not include dealing with bounds.
            # result = np.zeros((len(i), 4))
            # for ii, index in enumerate(indices):
            #     v_1, v_2, x_1, x_2 = values[index - 1], values[index], keys[index - 1], keys[index]
            #     result[ii] = v_1 + (v_2 - v_1) / (x_2 - x_1) * (i[ii] - x_1)
    else:
        raise TypeError("cmap is of incorrect type. Must be str, list or dict.")

    cmap_func.data = data

    return cmap_func


def cmap_to_gradient(cmap, gradient):
    """
    cmap must be from get_cmap, or accepted by get_cmap, and the gradient must be from get_gradient
    """
    cmap = get_cmap(cmap)
    if isinstance(cmap.data, str):
        for i in range(gradient.resolution):
            value = cmap(i / (gradient.resolution - 1))
            gradient.setColorAt(i / (gradient.resolution - 1), get_single_color(value))
    else:
        for key, value in cmap.data.items():
            gradient.setColorAt(key, get_single_color(value))
    return gradient


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
        elif len(arg) == 3 and isinstance(arg[0], Number):
            return False
        else:
            return True
    else:
        return False


def get_single_color(input_col):
    if is_iter(input_col):
        if isinstance(input_col[0], Number):
            if len(input_col) == 3 or len(input_col) == 4:
                if max(input_col) <= 1:
                    return mkColor(np.array(input_col)*255)
                else:
                    return mkColor(np.array(input_col))
            else:
                raise ValueError(f"Expected tuple of lenght 3 or 4, but got length {len(input_col)} (Note that a "
                                 f"line can only be one color).")
        else:
            raise TypeError(f"When an iterable is provided, it should have elements that are integers or floats. "
                            f"Got {type(input_col)} (Note that a line can only be one color).")
    else:
        return mkColor(input_col)


def normalise_arr(arr):
    arr = np.array(arr)
    arr -= np.min(arr)
    arr /= np.max(arr)
    return arr


def get_type_func(value, parent, col):
    # this for-loop is essentially get_instance(value) and then assigns type_func
    if value is None:
        type_func = ast.literal_eval
        return type_func
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
            else:
                raise AssertionError("This should never run.")

            return type_func
    else:
        raise NotImplementedError(
            "the instance you are using (the type of the variable provided) is currently not supported"
            "do you think it should be? send me an e-mail at rikmulder7@proton.me, and mention the "
            f"type was probably: {type(value)}")


def get_new_kwargs(current_locals, none_kwargs, exclude_args):
    """
    makes new kwargs exluding some kwargs and excluding some kwargs only if they are left at None.

    current_locals: pass locals()
    none_kwargs: kwargs to skip if they are None
    exclude_args: kwargs to always exclude. Stuff like "self", "args", "kwargs"
    """
    new_kwargs = {}
    for k, v in current_locals.items():
        if k not in exclude_args and not (k in none_kwargs and v is None):
            new_kwargs[k] = v

    return new_kwargs


def transform_kwargs(kwargs, mapping):
    result = {}
    for k, v in kwargs.items():
        if k not in result:
            result[mapping.get(k, k)] = v

    return result


def test_print(*args, **kwargs):
    print(f"filename={os.path.basename(__file__)}: ", end="")
    print(*args, **kwargs)
