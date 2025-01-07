#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import sys
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QVBoxLayout

from widgets.addons import AddonWidget, AddonDockWidget, Defaults

# NOTE: Обход проблемы импорта из-за "from src ..."
DIR: Path = Path(__file__).resolve().parent
PATH_TETRIS: str = str(DIR / "tetris")
sys.path.insert(0, PATH_TETRIS)
from widgets.addons.tetris.tetris.main_gui import MainWindow, HighScore

sys.path.remove(PATH_TETRIS)


class TetrisWindow(MainWindow):
    def save_high_scores(self):
        pass

    def load_high_scores(self):
        pass


class AddonTetrisWidget(AddonWidget):
    def __init__(self, addon_dock_widget: AddonDockWidget):
        super().__init__(addon_dock_widget)

        self.setWindowTitle("Тетрис")

        self.tetris_window = TetrisWindow()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.tetris_window)

        # Для проброса клика от док-виджета
        self.addon_dock_widget.installEventFilter(self)

    def read_settings(self, settings: dict[str, Any] | None):
        if settings is None:
            settings: dict[str, Any] = dict()

        items: list[dict[str, Any]] = settings.get("scores", [])
        self.tetris_window.set_raw_high_scores(items)

    def write_settings(self, settings: dict[str, Any]):
        settings["scores"] = self.tetris_window.get_raw_high_scores()

    def defaults(self) -> Defaults:
        return Defaults(
            is_visible=False,
            is_active=True,
            area=Qt.DockWidgetArea.LeftDockWidgetArea,
        )

    def is_supported_refresh(self) -> bool:
        return False

    def is_supported_logs(self) -> bool:
        return False

    def is_supported_settings(self) -> bool:
        return False

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:
        if self.addon_dock_widget == watched and event.type() == QEvent.Type.KeyRelease:
            self.tetris_window.keyReleaseEvent(event)
            return True

        return False


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = AddonDockWidget(AddonTetrisWidget)
    w.resize(400, 600)
    w.show()

    app.exec()
