#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from collections import defaultdict
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
from api.jira_rss import ActivityActionEnum, Activity, get_logged_total_seconds
from widgets import (
    create_table,
    create_table_item,
    add_table_row,
    clear_table,
    open_jira,
    block_signals,
)
from third_party.seconds_to_str import seconds_to_str


class ActivitiesWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.table_date = create_table(
            header_labels=["ДАТА", "ЗАЛОГИРОВАНО", "АКТИВНОСТИ"],
        )
        self.table_date.itemSelectionChanged.connect(
            lambda: self._on_table_date_item_clicked(self.table_date.currentItem())
        )

        self.table_date_by_jira = create_table(
            header_labels=["ЗАЛОГИРОВАНО", "АКТИВНОСТИ", "ЗАДАЧА", "НАЗВАНИЕ"],
        )
        self.table_date_by_jira.itemSelectionChanged.connect(
            lambda: self._on_table_date_by_jira_item_clicked(
                self.table_date_by_jira.currentItem()
            )
        )
        self.table_date_by_jira.itemDoubleClicked.connect(
            self._on_table_date_by_jira_item_double_clicked
        )
        for j in [0, 1, 2]:
            self.table_date_by_jira.horizontalHeader().setSectionResizeMode(
                j, QHeaderView.ResizeToContents
            )

        self.table_jira_by_activities = create_table(
            header_labels=["ВРЕМЯ", "ЗАЛОГИРОВАНО", "ДЕЙСТВИЕ", "ОПИСАНИЕ", "ТЕКСТ"],
        )
        for j in [0, 1, 2]:
            self.table_jira_by_activities.horizontalHeader().setSectionResizeMode(
                j, QHeaderView.ResizeToContents
            )

        splitter_table_activities = QSplitter(Qt.Vertical)
        splitter_table_activities.setObjectName("splitter_table_activities")
        splitter_table_activities.addWidget(self.table_date_by_jira)
        splitter_table_activities.addWidget(self.table_jira_by_activities)

        splitter_main = QSplitter(Qt.Horizontal)
        splitter_main.setObjectName("splitter_main")
        splitter_main.addWidget(self.table_date)
        splitter_main.addWidget(splitter_table_activities)
        splitter_main.setSizes([400, 600])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter_main)

        self.setLayout(layout)

    def set_date_by_activities(self, date_by_activities: dict[date, list[Activity]]):
        with block_signals(self.table_date):
            clear_table(self.table_date)

            for entry_date, activities in sorted(
                date_by_activities.items(), key=lambda x: x[0], reverse=True
            ):
                activities_number = len(activities)

                total_seconds: int = get_logged_total_seconds(activities)
                total_seconds_str: str = seconds_to_str(total_seconds)

                date_str: str = get_human_date(entry_date)
                is_odd_week: int = entry_date.isocalendar().week % 2 == 1

                items = [
                    create_table_item(date_str, data=activities),
                    create_table_item(
                        total_seconds_str,
                        tool_tip=f"Всего секунд: {total_seconds}",
                    ),
                    create_table_item(
                        f"{activities_number}",
                    ),
                ]
                for item in items:
                    if is_odd_week:
                        item.setBackground(Qt.lightGray)

                add_table_row(self.table_date, items)

        self.table_date.setCurrentCell(0, 0)
        self.table_date.setFocus()
        self._on_table_date_item_clicked(self.table_date.currentItem())

    def _on_table_date_item_clicked(self, item: QTableWidgetItem | None):
        with block_signals(self.table_date_by_jira):
            clear_table(self.table_date_by_jira)

            if not item:
                return

            row = item.row()
            item1 = item.tableWidget().item(row, 0)

            activities: list[Activity] = item1.data(Qt.UserRole)
            if not activities:
                return

            jira_by_activity: dict[str, list[Activity]] = defaultdict(list)
            for activity in activities:
                jira_by_activity[activity.jira_id].append(activity)

            for activities in sorted(
                jira_by_activity.values(), key=get_logged_total_seconds, reverse=True
            ):
                # Группировка была по джире
                activity = activities[0]
                jira_id = activity.jira_id
                jira_title = activity.jira_title

                total_logged_seconds = get_logged_total_seconds(activities)
                total_logged_human = (
                    seconds_to_str(total_logged_seconds) if total_logged_seconds else ""
                )

                items = [
                    create_table_item(total_logged_human),
                    create_table_item(f"{len(activities)}"),
                    create_table_item(jira_id),
                    create_table_item(jira_title, tool_tip=jira_title),
                ]
                items[0].setData(Qt.UserRole, activities)

                add_table_row(self.table_date_by_jira, items)

        self.table_date_by_jira.setCurrentCell(0, 0)
        self._on_table_date_by_jira_item_clicked(self.table_date_by_jira.currentItem())

    def _on_table_date_by_jira_item_clicked(self, item: QTableWidgetItem | None):
        with block_signals(self.table_jira_by_activities):
            clear_table(self.table_jira_by_activities)

            if not item:
                return

            row = item.row()
            item1 = item.tableWidget().item(row, 0)

            activities: list[Activity] = item1.data(Qt.UserRole)
            if not activities:
                return

            activities.sort(key=lambda x: x.entry_dt)

            for activity in activities:
                if activity.logged:
                    logged_human_time = activity.logged.human_time
                    logged_description = activity.logged.description
                else:
                    logged_human_time = logged_description = None

                action_name = activity.action.name
                action_tooltip = None
                if activity.action == ActivityActionEnum.UNKNOWN:
                    action_name = f"⚠️ {action_name}"
                    action_tooltip = "Неизвестное действие. Оповестите мейнтейнера, отправив текст активности"

                items = [
                    create_table_item(get_human_time(activity.entry_dt)),
                    create_table_item(logged_human_time),
                    create_table_item(action_name, tool_tip=action_tooltip),
                    create_table_item(logged_description, tool_tip=logged_description),
                    create_table_item(
                        activity.action_text, tool_tip=activity.action_text
                    ),
                ]
                add_table_row(self.table_jira_by_activities, items)

    def _on_table_date_by_jira_item_double_clicked(self, item: QTableWidgetItem):
        row = item.row()
        item1 = item.tableWidget().item(row, 0)

        activities: list[Activity] = item1.data(Qt.UserRole)
        if not activities:
            return

        activity: Activity = activities[0]
        open_jira(activity.jira_id)
