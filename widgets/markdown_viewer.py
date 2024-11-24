#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
from pathlib import Path

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QTextBrowser,
    QVBoxLayout,
)


class MarkdownViewer(QDialog):
    def __init__(
        self,
        title: str,
        path: Path,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.path = path

        self.setWindowTitle(f"{title} ({self.path.name})")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.content = QTextBrowser()
        self.content.setReadOnly(True)
        self.content.setOpenLinks(False)
        self.content.anchorClicked.connect(self._anchor_clicked)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.content)

        text: str = self.path.read_text(encoding="utf-8")
        self.content.setMarkdown(text)

        self.resize(800, 500)

    def _anchor_clicked(self, url: QUrl):
        url: str = url.toString()

        path = self.path.parent / url
        if path.exists():  # Если это путь к файлу или папке
            os.startfile(path)
        else:
            os.startfile(url)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from config import PATH_CHANGELOG

    app = QApplication([])

    w = MarkdownViewer(title="Информация", path=PATH_CHANGELOG)
    w.exec()
