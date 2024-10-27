#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import html
import traceback

from PyQt5.QtCore import Qt
# TODO:
# from PyQt5.QtGui import QTextOption
from PyQt5.QtWidgets import QMainWindow, QPlainTextEdit, QToolButton, QToolBar


def get_exception_traceback(e: Exception) -> str:
    return "".join(traceback.format_exception(e)).strip()


class LogsWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.logs = QPlainTextEdit()
        self.logs.setObjectName("logs")
        self.logs.setMaximumBlockCount(1_000)
        self.logs.setReadOnly(True)

        # TODO:
        # self.logs.setWordWrapMode(QTextOption.NoWrap)

        tool_bar = QToolBar()
        tool_bar.setMovable(False)

        action_clear = tool_bar.addAction("🗑️")
        action_clear.setToolTip("Очистить всё")
        action_clear.triggered.connect(self.logs.clear)

        self.addToolBar(Qt.LeftToolBarArea, tool_bar)

        self.setCentralWidget(self.logs)

    def append(self, text: str):
        self.logs.appendPlainText(text)

    def append_error(self, text: str):
        text = html.escape(text).replace("\n", "<br/>")
        self.logs.appendHtml(f"<span style='color: red'>{text}</span>")

    def append_exception(self, e: Exception):
        error: str = get_exception_traceback(e)
        self.append_error(error)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = LogsWidget()
    w.show()

    w.append("123")
    w.append("Hello World!")

    app.exec()
