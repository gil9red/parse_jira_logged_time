#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"

import re
import sys
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QTextEdit

from widgets.addons import AddonWidget, AddonDockWidget, Defaults
from widgets import block_signals

# NOTE: Обход проблемы импорта "from seconds_to_str import seconds_to_str"
DIR: Path = Path(__file__).resolve().parent
PATH_THIRD_PARTY: str = str(DIR.parent.parent.parent / "third_party")
sys.path.insert(0, PATH_THIRD_PARTY)
from widgets.addons.time_calc.eval_expr_total_time import eval_expr_with_time


EXAMPLE: str = """
08:53:11 - 07:15:00
+ 08:56:12
+ 03:10:00
- 00:00:23
""".strip()
SEP: str = "="


class AddonTimeCalcWidget(AddonWidget):
    def __init__(self, addon_dock_widget: AddonDockWidget):
        super().__init__(addon_dock_widget)

        self.setWindowTitle("Калькулятор времени")

        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.setPlainText(EXAMPLE)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.text_edit)

    def defaults(self) -> Defaults:
        return Defaults(
            is_visible=False,
            is_active=True,
            area=Qt.DockWidgetArea.RightDockWidgetArea,
        )

    def is_supported_refresh(self) -> bool:
        return False

    def is_supported_logs(self) -> bool:
        return False

    def is_supported_settings(self) -> bool:
        return False

    def read_settings(self, settings: dict[str, Any] | None):
        if settings is None:
            settings: dict[str, Any] = dict()

        text: str | None = settings.get("text")
        if text is None:
            text = EXAMPLE

        self.text_edit.setPlainText(text)

    def write_settings(self, settings: dict[str, Any]):
        settings["text"] = self.text_edit.toPlainText()

    def _on_text_changed(self):
        text: str = self.text_edit.toPlainText()
        input_text: str = text.split(SEP)[0]

        try:
            result: str = eval_expr_with_time(input_text)
        except Exception:
            result: str = "⚠️"

        input_text = re.sub("\n{2,}$", "\n", input_text)
        input_text = input_text.replace("\n", "<br/>")

        new_text = f"{input_text}<p>{SEP}</p><p><b>{result}</b></p>"

        # Сохранение позиции курсора
        text_cursor = self.text_edit.textCursor()
        position: int = text_cursor.position()

        # Для блокирования сигнала textChanged, чтобы не было рекурсии
        with block_signals(self.text_edit):
            self.text_edit.setHtml(new_text)

        # Восстановление позиции курсора
        text_cursor.setPosition(position)
        self.text_edit.setTextCursor(text_cursor)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = AddonDockWidget(AddonTimeCalcWidget)
    w.resize(300, 300)
    w.show()

    app.exec()
