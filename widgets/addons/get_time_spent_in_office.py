#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit

from api.job_report.get_time_spent_in_office import (
    get_time_spent_in_office,
    TimeSpent,
    URL,
    NotFoundReport,
)
from widgets.addons import AddonWidget, AddonDockWidget


class AddonGetTimeSpentInOfficeWidget(AddonWidget):
    def __init__(self, addon_dock_widget: AddonDockWidget):
        super().__init__(addon_dock_widget)

        self.setWindowTitle("Проведенное время в офисе")

        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.info)

    @property
    def url(self) -> str:
        return URL

    def get_data(self) -> TimeSpent | NotFoundReport:
        try:
            return get_time_spent_in_office()
        except NotFoundReport as e:
            return e

    def process(self, data: TimeSpent | NotFoundReport):
        if isinstance(data, TimeSpent):
            text = f"""
Первый вход: {data.first_enter}
Отработано: {data.today}
            """.strip()
        else:
            text = f"Отчет на сегодня еще не готов:\n{data}"

        self.info.setPlainText(text)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = AddonDockWidget(AddonGetTimeSpentInOfficeWidget)
    w.show()
    w.refresh()

    app.exec()
