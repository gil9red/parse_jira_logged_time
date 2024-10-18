#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from api.job_report.get_hours_worked import (
    get_user_and_deviation_hours,
    get_quarter_user_and_deviation_hours,
    NotFoundReport,
)
from third_party.get_quarter import get_quarter_roman
from widgets.addons import AddonWidget

from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit


class AddonGetHoursWorkedWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Рабочие часы")

        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.info)

    def get_data(self) -> tuple[bool, str]:
        def _get_title(deviation_hours: str):
            ok = deviation_hours[0] != "-"
            return "Переработка" if ok else "Недоработка"

        deviation_hours = None
        quarter_deviation_hours = None

        text = ""
        try:
            _, deviation_hours = get_user_and_deviation_hours()
            ok = deviation_hours[0] != "-"
            text += _get_title(deviation_hours) + " " + deviation_hours

            _, quarter_deviation_hours = get_quarter_user_and_deviation_hours()
            if quarter_deviation_hours.count(":") == 1:
                quarter_deviation_hours += ":00"

            text += f"\n{_get_title(quarter_deviation_hours)} за квартал {get_quarter_roman()} {quarter_deviation_hours}"

        except NotFoundReport:
            text += "\nОтчет на сегодня еще не готов."
            ok = True

        # Если часы за месяц не готовы, но часы за квартал есть
        if not deviation_hours and quarter_deviation_hours:
            ok = True

        return ok, text

    def process(self, data: tuple[bool, str]):
        ok, text = data

        # TODO: А вот это можно настроить - раскрашивать ли. Или мб только текст закрашивать?
        color = "#29AB87" if ok else "#80ff0000"
        self.info.setStyleSheet(f"background: {color};")

        self.info.setPlainText(text)
