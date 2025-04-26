import sys

from PySide6.QtWidgets import QMainWindow, QSplitter, QApplication
from pyqtgraph import GraphicsLayoutWidget

from .plot_widget import PlotWidget
from .input_widget import InputWidget
from .variables import Variables
# from .plot_widget_3d import PlotWidget3D
from typing import Optional, List
import numpy as np


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.app = app
        app.setStyle("Fusion")

        self.variables = Variables()
        self.update_funcs = []

        self.fig_widget = GraphicsLayoutWidget()
        self.setCentralWidget(self.fig_widget)

        self.plot_style_3D = False
        self.interval = None                    # for timer when animated
        self.fps_timer = None
        self.refresh_timer = None

        self.axs = PlotWidget(0, 0)
        self.shape = (1, 1)
        self.fig_widget.addItem(self.axs, 0, 0)  # addItem takes what is added, row, col, rowspan, colspan
        self.plot_widget = self.axs

        self.widthratios = None             # for subplots
        self.heightratios = None

        self.extra_width = 0
        self.input_widget = None            # stuff that can be initialised later is set to None
        self.splitter = None
        self.exit_when_closed = False
        self.close_funcs = []

        self.is3D = False

        self.resize(640, 480)

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

    def init_input(self, width_ratio=0.5):
        """
        initialises the input window (a table), with width_ratio: width_ratio*fig_widget.width.
        By default, width_ratio=0.5, probably meaning that fig_widget will be width 640,
        input_widget width 320, and window width 964
        """
        height = self.size().height()

        self.splitter = QSplitter()
        self.splitter.widthratio = width_ratio

        input_width = int(self.size().width()*width_ratio)
        self.input_widget = InputWidget(self.variables, input_width, height)

        self.splitter.addWidget(self.input_widget)
        self.splitter.addWidget(self.fig_widget)

        self.setCentralWidget(self.splitter)
        if self.isVisible():
            self.resize(self.size().width() + input_width + 4, height)
            # +4 extra for space between plot_widget and input_widget

            pos = self.pos().toTuple()
            self.move(pos[0] - 0.5 * (input_width+4), pos[1])

    def construct_update_func(self, extra_funcs=None):    # constructs the function used to update the plot
        if extra_funcs is None:
            extra_funcs = []        # we don't want mutable default arguments

        def final_func():
            for func in self.update_funcs:
                func()
            for func in extra_funcs:
                func()

        return final_func


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

