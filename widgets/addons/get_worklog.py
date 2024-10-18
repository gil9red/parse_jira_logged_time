#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from api.job_report.get_worklog import get_worklog, Worklog, NotFoundReport
from widgets.addons import AddonWidget

from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit


class AddonGetWorklogWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Рабочий журнал")

        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.info)

    def get_data(self) -> Worklog | None:
        try:
            return get_worklog()
        except NotFoundReport:
            return

    def process(self, data: Worklog | None):
        if data:
            text = f"""
Залогировано: {data.logged} ({data.logged_percent}%)
Всего отработано: {data.actually}
            """.strip()
        else:
            text = "Отчет на сегодня еще не готов"

        self.info.setPlainText(text)
