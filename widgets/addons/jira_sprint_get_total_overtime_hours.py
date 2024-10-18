#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from api.jira_sprint_get_total_overtime_hours import get_total_overtime_hours
from widgets.addons import AddonWidget

from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit


class AddonSprintGetTotalOvertimeHoursWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Спринты. Переработка по часам")

        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.info)

    def get_data(self) -> int:
        return get_total_overtime_hours()

    def process(self, data: int):
        self.info.setPlainText(f"Отработано часов за текущий месяц: {data}")
