from pyqtgraph import GraphicsLayoutWidget
from .plot_widget import PlotWidget
import numpy as np
from typing import Optional, List, Iterable
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from time import perf_counter as current_time


class PlotManager:
    """Stores the plots and GraphicsLayoutWidget so that not everything is located inside the main window. The main
    window is only a window. """
    def __init__(self):
        self.fig_widget = GraphicsLayoutWidget()

        self.plot_style_3D = False

        self.plot_widget = PlotWidget(0, 0)
        self.axs = self.plot_widget                     # when there are no subplots, axs is the main plot widget
        self.shape = (1, 1)
        self.fig_widget.addItem(self.plot_widget, 0, 0)  # addItem takes what is added, row, col, rowspan, colspan

        self.widthratios = None                 # for subplots
        self.heightratios = None

    def clear(self):
        if isinstance(self.axs, np.ndarray):
            for pw in self.axs.flatten():
                for curve in pw.curves:
                    pw.removeItem(curve)
        else:
            for curve in self.axs.curves:
                self.axs.removeItem(curve)

        self.plot_style_3D = False
        self.axs = PlotWidget(0, 0)
        self.shape = (1, 1)
        self.fig_widget.addItem(self.axs, 0, 0)  # addItem takes what is added, row, col, rowspan, colspan
        self.plot_widget = self.axs

        self.widthratios = None                 # for subplots
        self.heightratios = None

    def update_size(self, event):
        if self.heightratios:
            pwidth = (self.fig_widget.width() - 18 - 6*(self.shape[1]-1))/sum(self.widthratios)
            for index, width in enumerate(self.widthratios):
                self.fig_widget.ci.layout.setColumnMinimumWidth(index, pwidth * width)
        if self.widthratios:
            pheight = (self.fig_widget.height() - 18 - 6*(self.shape[0]-1))/sum(self.heightratios)
            for index, height in enumerate(self.heightratios):
                self.fig_widget.ci.layout.setRowMinimumHeight(index, height * pheight)

        if event:
            event.accept()

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

    def remove_item(self, item: GraphicsObject):
        """
        Remove item `item` from the window. Item can be anything that can be added to a plot widget.
        """
        if isinstance(self.axs, np.ndarray):
            for pw in self.axs.flatten():
                if item in pw.curves:
                    pw.removeItem(item)
            return
        else:
            if item in self.axs.curves:
                self.axs.removeItem(item)
                return
        raise ValueError("Item has not been found")

    def merge_plots(self, plots: Iterable[PlotWidget]) -> PlotWidget:  # not optimised, but fast enough (& not sure if it works)
        """Merge multiple subplots into a single plot. This is used for unevenly spaced grids of subplots.

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
            self.fig_widget.removeItem(plt)
            del plt

        height = max_x - min_x + 1
        width = max_y - min_y + 1

        # new_plot = PlotWidget(hrs[min_x], wrs[min_y])
        new_plot = PlotWidget(min_x, min_y)

        self.fig_widget.addItem(new_plot, min_x, min_y, height, width)
        return new_plot



