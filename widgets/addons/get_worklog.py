#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit

from api.job_report.get_worklog import get_worklog, Worklog, NotFoundReport
from api.job_report.utils import URL
from widgets.addons import AddonWidget, AddonDockWidget


class AddonGetWorklogWidget(AddonWidget):
    def __init__(self, addon_dock_widget: AddonDockWidget):
        super().__init__(addon_dock_widget)

        self.setWindowTitle("Рабочий журнал")

        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.info)

    @property
    def url(self) -> str:
        return URL

    def get_data(self) -> Worklog | None:
        try:
            return get_worklog()
        except NotFoundReport:
            return

    def process(self, data: Worklog | None):
        if data:
            logged: str = data.logged

            # "hh:mm" -> "hh:mm:ss"
            if logged.count(":") == 1:
                logged = f"{logged}:00"

            text = f"""
Залогировано: {logged} ({data.logged_percent}%)
Всего отработано: {data.actually}
            """.strip()
        else:
            text = "Отчет на сегодня еще не готов"

        self.info.setPlainText(text)
