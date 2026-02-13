import sys
import os.path
import numpy as np
from typing import Optional, List

from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QVBoxLayout, QTabWidget, QApplication
from pyqtgraph import GraphicsLayoutWidget

from .plot_widget import PlotWidget
from .input_widget import InputTable
from .variables import Variables
# from .plot_widget_3d import PlotWidget3D


class MainWindow(QMainWindow):
    def __init__(self):
        self.app = QApplication()       # app must be created before QMainWindow initialisation.
        self.app.setStyle("Fusion")

        super().__init__()

        self.variables = Variables()
        self.update_funcs = []

        self.fig_widget = GraphicsLayoutWidget()
        self.setCentralWidget(self.fig_widget)

        self.plot_style_3D = False
        self.interval = None                    # for timer when animated
        self.fps_timer = None
        self.refresh_timer = None
        self.timer = None                       # for disconnecting update_funcs

        self.axs = PlotWidget(0, 0)
        self.shape = (1, 1)
        self.fig_widget.addItem(self.axs, 0, 0)  # addItem takes what is added, row, col, rowspan, colspan
        self.plot_widget = self.axs

        self.widthratios = None                 # for subplots
        self.heightratios = None

        self.extra_width = 0
        self.input_width = 0                # width of the input_table
        self.resized = False                # if it has been resized already, the input_widget mustn't make it bigger
        self.input_tables = []
        self.main_input_widget = None       # the input_widget, or the QTabWidget if multiple tabs are added
        self.first_input_table = None       # the input_table that was added first
        self.splitter = None                # stuff that can be initialised later is set to None
        self.tab_widget = None
        self.table_container = None
        self.exit_when_closed = False
        self.close_funcs = []
        self.on_key_press_funcs = []

        self.is3D = False

        self.resize(640, 480)

        self.n_links = 0            # number of links between boxes

    def closeEvent(self, event):
        # Window is being closed
        for func in self.close_funcs:
            func()
        if self.exit_when_closed:       # not sure if there should be an else
            sys.exit("Application has been closed (code 1008)")

    def resizeEvent(self, event):
        if self.heightratios:
            pwidth = (self.fig_widget.width() - 18 - 6*(self.shape[1]-1))/sum(self.widthratios)
            for index, width in enumerate(self.widthratios):
                self.fig_widget.ci.layout.setColumnMinimumWidth(index, pwidth * width)
        if self.widthratios:
            pheight = (self.fig_widget.height() - 18 - 6*(self.shape[0]-1))/sum(self.heightratios)
            for index, height in enumerate(self.heightratios):
                self.fig_widget.ci.layout.setRowMinimumHeight(index, height * pheight)

        if event:
            event.accept()      # for testing purposes

    def keyPressEvent(self, event):
        for func in self.on_key_press_funcs:
            func(event)

        if event:
            event.accept()

    def link_boxes(self, boxes, only_update_boxes=None):
        """
        box1, box2 are either both boxes or both rows, which can be linked. The boxes that can be linked are:
        rate_slider, slider, or inputbox. Linking means that when one value changes, the other changes too.
        """
        self.n_links += 1
        if only_update_boxes is None:
            only_update_boxes = []

        for i, box_ in enumerate(boxes):
            if box_ in only_update_boxes:
                def func():
                    return

            else:
                def func(*args, box=box_, n_links=self.n_links):
                    val = box.value()
                    for other_box in boxes:
                        if other_box != box and n_links in other_box.link_funcs.keys():
                            for link_fuc in other_box.link_funcs.values():
                                other_box.unbind(link_fuc)
                            other_box.set_value(val)
                            for link_fuc in other_box.link_funcs.values():
                                other_box.bind(link_fuc)

            box_.link_funcs[self.n_links] = func     # enables linking box1 and box2 and box2 and box3 without
            # linking box1 and box3
            box_.bind(func)

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
        if self.first_input_table is not None:
            raise RuntimeError("Can not create a first table when one already exists, use `add_tab()` instead.")

        self.splitter = QSplitter()
        self.splitter.width_ratio = width_ratio
        self.input_width = int(self.size().width()*width_ratio)
        input_table = self.new_table(name)
        self.first_input_table = input_table        # with one table, the first table is both the first table and the
        self.main_input_widget = input_table        # widget that needs to be resized.

        # First added table is added to a widget so that it can be moved into a QTabWidget later.
        self.table_container = QWidget()
        layout = QVBoxLayout(self.table_container)  # Set layout on the container
        layout.setContentsMargins(0, 0, 0, 0)       # Optional: Remove margins if needed
        layout.addWidget(input_table)               # Add table to the layout

        self.splitter.addWidget(self.table_container)
        self.splitter.addWidget(self.fig_widget)
        self.setCentralWidget(self.splitter)

        height = self.size().height()
        if self.isVisible():
            self.resize(self.size().width() + self.input_width + 4, height)
            # +4 extra for space between plot_widget and input_widget

            pos = self.pos().toTuple()
            self.move(pos[0] - 0.5 * (self.input_width+4), pos[1])

        return input_table

    def init_tab_widget(self):
        self.tab_widget = QTabWidget()
        if self.main_input_widget.resized:
            # print(self.size())
            width, height = self.size().toTuple()
            # copied from resize in __init__.py (when input_widget has been resized, the new QTabWidget is also resized)
            ratio = self.splitter.width_ratio
            self.tab_widget.resize(int(ratio * width / (ratio + 1)), height)
            self.fig_widget.resize(int(width / (ratio + 1)), height)
            self.splitter.resize(width, height)
            self.tab_widget.resized = True
        else:
            self.tab_widget.resize(self.input_width, self.height())
            self.tab_widget.resized = False

        self.main_input_widget = self.tab_widget
        self.table_container.deleteLater()
        self.splitter.replaceWidget(0, self.tab_widget)

        self.tab_widget.addTab(self.first_input_table, self.first_input_table.name)

    def add_table(self, name=None):
        """
        Returns a newly created input table and adds it to a tab_widget.

        :param name: Name of the tab, only visible when multiple input tables are added.
        :type name: str
        """
        if self.tab_widget is None:
            self.init_tab_widget()

        new_table = self.new_table(name)
        self.tab_widget.addTab(new_table, new_table.name)
        return new_table

    def new_table(self, name=None):
        """
        Returns a newly created input table and adds it to self.input_tables.

        :param name: Name of the tab, only visible when multiple input tables are added.
        :type name: str
        """
        if name is None:
            name = f"tab{len(self.input_tables)+1}"

        height = self.size().height()
        input_table = InputTable(self.input_width, height, name, self)
        self.input_tables.append(input_table)

        return input_table

    def rename_tab(self, name, index=0, old_name=None):
        if self.first_input_table is None:
            self.init_first_tab(name=name)
            return self.first_input_table
        if self.tab_widget is None:
            if index == 0 or old_name == self.first_input_table.name:
                self.first_input_table.name = name
            else:
                if old_name is not None:
                    raise ValueError(f"{old_name} is not the current name of a tab.")
                else:
                    raise ValueError(f"`index` is too high. It can be at most {len(self.input_tables)-1}.")
            return self.first_input_table

        if old_name is not None:
            for i, table in enumerate(self.input_tables):
                if table.name == old_name:
                    self.tab_widget.setTabText(i, name)
                    table.name = name
                    return table
            else:
                raise ValueError(f"{old_name} is not the current name of a tab.")
        else:
            self.input_tables[index].name = name
            self.tab_widget.setTabText(index, name)
            return self.input_tables[index]

    # def init_3D(self):
    #     self.is3D = True
    #     self.plot_widget = PlotWidget3D(
    #         self.plot_widget.variables, self.plot_widget.update_funcs
    #     )
    #     self.setCentralWidget(self.plot_widget)

    def create_subplots(
            self, nrows=1, ncols=1, heightratios: Optional[List[int]] = None, widthratios: Optional[List[int]] = None):
        """

        :param nrows: number of rows.
        :param ncols: number of columns.
        :param heightratios: ratios between the heights of the rows. Defaults to all ones. Only integer values allowed.
            Not working yet!
        :param widthratios: ratios between the widths of the columns. Defaults to all ones. Only integer values allowed.
            Not working yet!
        :return: nested list of plot_windows on which the plots can be drawn.
        """
        if nrows == 1 and ncols == 1 and heightratios is None and widthratios is None:
            return self.axs

        self.shape = (nrows, ncols)
        if widthratios is None:
            widthratios = [1]*ncols
        else:
            ncols = len(widthratios)
        if heightratios is None:
            heightratios = [1]*nrows
        else:
            nrows = len(heightratios)

        self.fig_widget.clear()            # removes all existing plots
        self.widthratios = widthratios
        self.heightratios = heightratios

        # pwidth = (self.width()-12)/sum(widthratios)-6
        # pheight = (self.height()-12)/sum(heightratios)-6
        pwidth = (self.fig_widget.width() - 18 - 6*ncols)/sum(widthratios)
        pheight = (self.fig_widget.height() - 18 - 6*nrows)/sum(heightratios)

        self.axs = []
        if nrows == 1:
            for col in range(ncols):
                pw = PlotWidget(0, col)
                self.axs.append(pw)
                self.fig_widget.addItem(pw, 0, col)
        elif ncols == 1:
            for row in range(nrows):
                pw = PlotWidget(row, 0)
                self.axs.append(pw)
                self.fig_widget.addItem(pw, row, 0)
        else:
            for row in range(nrows):
                axs_row = []
                for col in range(ncols):
                    pw = PlotWidget(row, col)
                    axs_row.append(pw)
                    self.fig_widget.addItem(pw, row, col)
                self.axs.append(axs_row)

        if heightratios:
            for index, width in enumerate(widthratios):
                # self.fig_widget.ci.layout.setColumnStretchFactor(index, height)
                # self.fig_widget.ci.layout.setColumnPreferredWidth(index, width*pwidth+6*(width-1))
                self.fig_widget.ci.layout.setColumnMinimumWidth(index, pwidth*width)
        if widthratios:
            for index, height in enumerate(heightratios):
                # self.fig_widget.ci.layout.setRowPreferredHeight(index, height*pheight+6*(height-1))
                self.fig_widget.ci.layout.setRowMinimumHeight(index, height*pheight)
                # self.fig_widget.ci.layout.setRowStretchFactor(index, width)

        self.axs = np.array(self.axs)
        return self.axs


def test_print(*args, **kwargs):
    print(f"filename={os.path.basename(__file__)}: ", end="")
    print(*args, **kwargs)
