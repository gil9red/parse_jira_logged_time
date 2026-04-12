#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import html
import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCharFormat
from PyQt6.QtWidgets import QMainWindow, QPlainTextEdit, QToolBar


def get_exception_traceback(e: Exception) -> str:
    return "".join(traceback.format_exception(e)).strip()


class LogsWidget(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.logs = QPlainTextEdit()
        self.logs.setObjectName("logs")
        self.logs.setMaximumBlockCount(1_000)
        self.logs.setReadOnly(True)

        # TODO:
        # from PyQt6.QtGui import QTextOption
        # self.logs.setWordWrapMode(QTextOption.NoWrap)

        tool_bar = QToolBar()
        tool_bar.setMovable(False)

        action_clear = tool_bar.addAction("🗑️")
        action_clear.setToolTip("Очистить всё")
        action_clear.triggered.connect(self.logs.clear)

        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, tool_bar)

        self.setCentralWidget(self.logs)

    def append(self, text: str) -> None:
        self.logs.setCurrentCharFormat(QTextCharFormat())
        self.logs.appendPlainText(text)

    def append_error(self, text: str) -> None:
        text: str = html.escape(text)
        text = f"<p style='color: red'>{text}</p>"
        text = text.replace("\n", "<br/>")

        self.logs.setCurrentCharFormat(QTextCharFormat())
        self.logs.appendHtml(text)

    def append_exception(self, e: Exception) -> None:
        error: str = get_exception_traceback(e)
        self.append_error(error)


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication([])

    w = LogsWidget()
    w.show()

    w.append("123")
    w.append_error("RED TEXT")
    w.append("Hello World!")
    w.append_exception(Exception("ERROR"))

    app.exec()
