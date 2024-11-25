#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import date

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QHeaderView,
    QSplitter,
    QVBoxLayout,
    QTableWidgetItem,
)

from api import get_human_date, get_human_time
from api.jira_rss import Activity, get_logged_total_seconds
from widgets import (
    create_table,
    create_table_item,
    add_table_row,
    clear_table,
    open_jira,
    block_signals,
)
from third_party.seconds_to_str import seconds_to_str


class LoggedWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.table_logged = create_table(
            header_labels=["ДАТА", "ЗАЛОГИРОВАНО"],
        )
        self.table_logged.itemSelectionChanged.connect(
            lambda: self._on_table_logged_item_clicked(self.table_logged.currentItem())
        )

        self.table_logged_info = create_table(
            header_labels=["ВРЕМЯ", "ЗАЛОГИРОВАНО", "ЗАДАЧА", "НАЗВАНИЕ", "ОПИСАНИЕ"],
        )

        # Первые 3 колонки (кроме названия) имеют размер под содержимое
        for j in range(3):
            self.table_logged_info.horizontalHeader().setSectionResizeMode(
                j, QHeaderView.ResizeToContents
            )
        self.table_logged_info.itemDoubleClicked.connect(
            self._on_table_logged_info_item_double_clicked
        )

        splitter_main = QSplitter(Qt.Horizontal)
        splitter_main.setObjectName("splitter_main")
        splitter_main.addWidget(self.table_logged)
        splitter_main.addWidget(self.table_logged_info)
        splitter_main.setSizes([300, 600])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter_main)

        self.setLayout(layout)

    def set_date_by_activities(self, date_by_activities: dict[date, list[Activity]]):
        with block_signals(self.table_logged):
            clear_table(self.table_logged)

            for entry_date, activities in sorted(
                date_by_activities.items(), key=lambda x: x[0], reverse=True
            ):
                activities: list[Activity] = [
                    obj for obj in reversed(activities) if obj.logged
                ]

                total_seconds: int = get_logged_total_seconds(activities)
                total_seconds_str: str = seconds_to_str(total_seconds)

                date_str: str = get_human_date(entry_date)
                is_odd_week: int = entry_date.isocalendar().week % 2 == 1

                # Не показывать даты, в которых не было залогировано
                if not total_seconds:
                    continue

                items = [
                    create_table_item(date_str, data=activities),
                    create_table_item(
                        total_seconds_str,
                        tool_tip=f"Всего секунд: {total_seconds}",
                    ),
                ]
                for item in items:
                    if is_odd_week:
                        item.setBackground(Qt.lightGray)

                add_table_row(self.table_logged, items)

        self.table_logged.setCurrentCell(0, 0)
        self.table_logged.setFocus()
        self._on_table_logged_item_clicked(self.table_logged.currentItem())

    def _on_table_logged_item_clicked(self, item: QTableWidgetItem | None):
        with block_signals(self.table_logged_info):
            clear_table(self.table_logged_info)

            if not item:
                return

            row = item.row()
            item1 = item.tableWidget().item(row, 0)

            activities: list[Activity] = item1.data(Qt.UserRole)
            if not activities:
                return

            for activity in activities:
                if activity.logged:
                    logged_human_time = activity.logged.human_time
                    logged_description = activity.logged.description
                else:
                    logged_human_time = logged_description = None

                items = [
                    create_table_item(
                        get_human_time(activity.entry_dt),
                        data=activity,
                    ),
                    create_table_item(logged_human_time),
                    create_table_item(activity.jira_id),
                    create_table_item(
                        activity.jira_title, tool_tip=activity.jira_title
                    ),
                    create_table_item(logged_description, tool_tip=logged_description),
                ]
                add_table_row(self.table_logged_info, items)

    def _on_table_logged_info_item_double_clicked(self, item: QTableWidgetItem):
        row = item.row()
        jira_id = item.tableWidget().item(row, 2).text()
        open_jira(jira_id)
