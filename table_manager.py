from typing import Iterable
from .input_widget import InputTable, Box            # only for type hinting
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget


class TableManager:
    """Stores the table/tab widgets so that not everything is located inside the main window. The main
    window is only a window. """
    def __init__(self, height):
        self.width = 0
        self.height = height

        self.input_tables = []              # the input_widget, or all input tables in the QTabWidget if multiple tabs
        # are added
        self.main_input_widget = None       # the input_widget, or the QTabWidget if multiple tabs are added
        self.first_input_table = None       # the input_table that was added first
        self.resized = False                # if window is resized with existing input_widget but not yet shown, this is
        # set to True, so that showing doesn't correct for input_widget as normal

        self.tab_widget = None              # stuff that can be initialised later is set to None
        self.table_container = None

        self.n_links = 0            # number of links between boxes

    def set_input_partition(self, fraction: float = 1 / 3):
        """Set the position of the partition between the 2 columns of the input_widget.

        Args:
            fraction (float, optional): value between 0 and 1, specifying the portion of the window taken up by the
                partition. Starts off at 1/3
        """
        self.first_input_table.set_partition(fraction)

    def create_first_table(self, input_table):
        self.input_tables.append(input_table)

        self.first_input_table = input_table        # with one table, the first table is both the first table and the
        self.main_input_widget = input_table        # widget that needs to be resized.

        # First added table is added to a widget so that it can be moved into a QTabWidget later.
        self.table_container = QWidget()

        layout = QVBoxLayout(self.table_container)  # Set layout on the container
        layout.setContentsMargins(0, 0, 0, 0)       # Optional: Remove margins if needed
        layout.addWidget(input_table)               # Add table to the layout

        return input_table, self.table_container

    def init_tab_widget(self):
        self.tab_widget = QTabWidget()
        self.main_input_widget = self.tab_widget
        self.table_container.deleteLater()
        self.tab_widget.addTab(self.first_input_table, self.first_input_table.name)
        self.input_tables.append(self.first_input_table)

        return

    def add_table(self, new_table) -> InputTable:
        self.input_tables.append(new_table)
        self.tab_widget.addTab(new_table, new_table.name)
        return new_table

    def rename_tab(self, name, index=0, old_name=None):
        if self.tab_widget is None:
            if index == 0 or old_name == self.first_input_table.name:
                self.first_input_table.name = name
            else:
                if old_name is not None:
                    raise ValueError(f"{old_name} is not the current name of a tab.")
                else:
                    raise ValueError(f"`index` is too high. It can be at most 0.")
            return self.first_input_table
        else:
            if old_name is not None:
                for i, table in enumerate(self.input_tables):
                    if table.name == old_name:
                        self.tab_widget.setTabText(i, name)
                        table.name = name
                        return table
                else:
                    raise ValueError(f"{old_name} is not the current name of a tab.")
            else:
                if index > len(self.input_tables):
                    raise ValueError(f"{index} is too high. It can be at most {len(self.input_tables)-1}.")
                self.input_tables[index].name = name
                self.tab_widget.setTabText(index, name)
                return self.input_tables[index]

    def set_active_tab(self, *args: int | InputTable | str, index: int | None = None, tab: InputTable | None = None,
                       name: str | None = None) -> InputTable:
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
        if self.tab_widget is None:
            if self.first_input_table is None:
                raise ValueError("Could not find any tabs. Create tabs before selecting an active tab.")
            else:
                return self.first_input_table

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
            self.tab_widget.setCurrentIndex(index)
        elif tab is not None:
            self.tab_widget.setCurrentWidget(tab)
        elif name is not None:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i).name == name:
                    self.tab_widget.setCurrentIndex(i)
                    break
        else:
            raise ValueError("`set_active_tab` needs an argument. ")
        return self.tab_widget.currentWidget()

    def get_current_row(self) -> int:
        """Return row of the latest placed widget"""
        return self.tab_widget.currentWidget().current_row

    def get_all_tabs(self) -> list[InputTable]:
        return self.input_tables

    def get_all_boxes(self) -> list[Box]:
        """Return a list containing all boxes that exist at this point. """
        result = []
        for table in self.input_tables:
            result.extend(table.get_boxes())
        return result

    def link_boxes(self, boxes: Iterable[Box | int], only_update_boxes: list | None = None):
        """Link all boxes in the list `boxes`.

        Boxes added to only_update_boxes are only updated when a box in boxes is
        changed but do not cause the other boxes to update when they are changed.
        `link_boxes(box1, box2); link_boxes(box2, box3)` can be used to link box1 to box2 and box2 to box3 without linking
        box1 to box3.

        Args:
            boxes (Iterable[Box | int]): list of boxes or row numbers of the boxes to link
            only_update_boxes (list, optional): todo: I forgot what this does...
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
