#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QTextBrowser,
    QVBoxLayout,
)

from config import PATH_CHANGELOG


class Changelog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("Журнал изменений")

        self.content = QTextBrowser()
        self.content.setReadOnly(True)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.content)

        self.content.setMarkdown(PATH_CHANGELOG.read_text(encoding="utf-8"))

        self.resize(800, 500)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = Changelog()
    w.exec()
