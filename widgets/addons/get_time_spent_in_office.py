#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit

from api.job_report.get_time_spent_in_office import (
    get_time_spent_in_office,
    TimeSpent,
    NotFoundReport,
)
from widgets.addons import AddonWidget


class AddonGetTimeSpentInOfficeWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Проведенное время в офисе")

        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.info)

    def get_data(self) -> TimeSpent | None:
        try:
            return get_time_spent_in_office()
        except NotFoundReport:
            return

    def process(self, data: TimeSpent | None):
        if data:
            text = f"""
Первый вход: {data.first_enter}
Отработано: {data.today}
            """.strip()
        else:
            text = "Отчет на сегодня еще не готов"

        self.info.setPlainText(text)
