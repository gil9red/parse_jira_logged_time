#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout

from widgets.addons import AddonWidget, Defaults
from widgets.addons.eyes.eyes.eyes_widget import EyesWidget


class AddonEyesWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Глаза 👀")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(EyesWidget())

    def defaults(self) -> Defaults:
        return Defaults(
            is_visible=False,
            is_active=True,
            area=Qt.DockWidgetArea.LeftDockWidgetArea,
        )

    def refresh(self):
        return

    def get_data(self) -> None:
        return

    def process(self, data: None):
        return


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = AddonEyesWidget()
    w.resize(300, 300)
    w.show()

    app.exec()
