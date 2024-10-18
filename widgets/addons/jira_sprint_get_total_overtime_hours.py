#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from api import get_human_date
from api.jira_sprint_get_total_overtime_hours import (
    get_sprints_with_overtime_hours,
    Sprint,
)
from widgets import (
    open_jira,
    create_table,
    create_table_item,
    add_table_row,
    clear_table,
)
from widgets.addons import AddonWidget

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHeaderView,
    QFormLayout,
    QLabel,
    QStackedLayout,
    QWidget,
    QTableWidgetItem,
)


class AddonSprintsWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Спринты. Сверхурочные часы")

        self.label_not_found = QLabel("Спринты не найдены")

        self.label_number = QLabel()
        self.label_total_hours = QLabel()

        self.table = create_table(header_labels=["Задача", "Дата", "Часы"])
        self.table.itemDoubleClicked.connect(self._on_table_item_double_clicked)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )

        self.main_widget = QWidget()

        main_widget_layout = QFormLayout(self.main_widget)
        main_widget_layout.addRow("Всего задач:", self.label_number)
        main_widget_layout.addRow("Всего часов:", self.label_total_hours)
        main_widget_layout.addRow(self.table)

        self.main_layout = QStackedLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(QWidget())  # Empty
        self.main_layout.addWidget(self.label_not_found)
        self.main_layout.addWidget(self.main_widget)

    def _on_table_item_double_clicked(self, item: QTableWidgetItem):
        row = item.row()
        item1 = item.tableWidget().item(row, 0)

        sprint: Sprint = item1.data(Qt.UserRole)
        if not sprint:
            return

        open_jira(sprint.key)

    def get_data(self) -> list[Sprint]:
        return get_sprints_with_overtime_hours()

    def process(self, data: list[Sprint]):
        sprints: list[Sprint] = get_sprints_with_overtime_hours()
        if not sprints:
            self.main_layout.setCurrentWidget(self.label_not_found)
            return

        self.main_layout.setCurrentWidget(self.main_widget)

        clear_table(self.table)

        total_overtime_hours = 0
        for sprint in sprints:
            total_overtime_hours += sprint.overtime_hours

            add_table_row(
                self.table,
                [
                    create_table_item(
                        text=sprint.key,
                        data=sprint,
                    ),
                    create_table_item(
                        text=get_human_date(sprint.created),
                    ),
                    create_table_item(
                        text=str(sprint.overtime_hours),
                    ),
                ],
            )

        self.label_number.setText(str(len(sprints)))
        self.label_total_hours.setText(str(total_overtime_hours))


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = AddonSprintsWidget()
    w.show()
    w.refresh()

    app.exec()
