#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from typing import Any

from PyQt5.QtWidgets import QVBoxLayout, QPlainTextEdit, QFormLayout, QCheckBox

from api.job_report.get_hours_worked import (
    get_user_and_deviation_hours,
    get_quarter_user_and_deviation_hours,
    NotFoundReport,
)
from api.job_report.utils import URL
from third_party.get_quarter import get_quarter_roman
from widgets.addons import AddonWidget, AddonDockWidget


class AddonGetHoursWorkedWidget(AddonWidget):
    def __init__(self, addon_dock_widget: AddonDockWidget):
        super().__init__(addon_dock_widget)

        self.setWindowTitle("Рабочие часы")

        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)

        self.cb_is_colorized = QCheckBox()
        self.cb_is_colorized.setObjectName("is_colorized")
        self.cb_is_colorized.setChecked(True)
        self.cb_is_colorized.toggled.connect(self._update_is_colorized)

        self.color: str | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.info)

    @property
    def url(self) -> str:
        return URL

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

        return ok, text.strip()

    def process(self, data: tuple[bool, str]):
        ok, text = data

        self.color = "#29AB87" if ok else "#80ff0000"
        self._update_is_colorized()

        self.info.setPlainText(text)

    def _update_is_colorized(self):
        self.info.setStyleSheet(
            f"background: {self.color};"
            if self.color and self.cb_is_colorized.isChecked()
            else None
        )

    def init_settings(self, settings_layout: QFormLayout):
        settings_layout.addRow("Раскрашивать:", self.cb_is_colorized)

    def read_settings(self, settings: dict[str, Any] | None):
        if settings is None:
            settings: dict[str, Any] = dict()

        value: bool = settings.get(self.cb_is_colorized.objectName(), True)
        self.cb_is_colorized.setChecked(value)

    def write_settings(self, settings: dict[str, Any]):
        settings[self.cb_is_colorized.objectName()] = self.cb_is_colorized.isChecked()
