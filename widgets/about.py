#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import sys
import os
import platform

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QFormLayout,
    QLabel,
    QDialogButtonBox,
    QGroupBox,
    QLineEdit,
    QStyle,
    QVBoxLayout,
)

from config import PROGRAM_NAME, VERSION, DIR, GITHUB_PROJECT


def get_ext_label(text: str) -> QLabel:
    label = QLabel(text)

    flags = label.textInteractionFlags()
    flags |= Qt.TextSelectableByMouse
    flags |= Qt.LinksAccessibleByMouse
    label.setTextInteractionFlags(flags)

    label.setOpenExternalLinks(True)

    return label


def get_ext_line_edit(text: str, is_path: bool = False) -> QLineEdit:
    line_edit = QLineEdit(text)
    line_edit.setPlaceholderText("<не задано>")
    line_edit.setReadOnly(True)

    if is_path:
        path = Path(text)
        if path.is_file():
            path = path.parent

        icon = line_edit.style().standardIcon(QStyle.SP_DirOpenIcon)
        action = line_edit.addAction(icon, QLineEdit.TrailingPosition)
        action.setToolTip("Открыть папку")

        action.triggered.connect(lambda: os.startfile(str(path)))

    return line_edit


class About(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("О программе")

        gb_python = QGroupBox("Python:")
        gb_python_layout = QFormLayout(gb_python)
        gb_python_layout.addRow(
            "Версия:",
            get_ext_line_edit(sys.version),
        )
        gb_python_layout.addRow(
            "Реализация:",
            get_ext_line_edit(platform.python_implementation()),
        )
        gb_python_layout.addRow(
            "Путь:", get_ext_line_edit(sys.executable, is_path=True)
        )

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        fields_layout = QFormLayout()
        fields_layout.addRow(
            "Версия:",
            get_ext_line_edit(VERSION),
        )
        fields_layout.addRow(
            "Проект:",
            get_ext_label(f"<a href='{GITHUB_PROJECT}'>{GITHUB_PROJECT}</a>"),
        )
        fields_layout.addRow(
            "Папка:",
            get_ext_line_edit(str(DIR), is_path=True),
        )
        fields_layout.addRow(
            "Аргументы:",
            get_ext_line_edit(" ".join(sys.argv[1:])),
        )
        fields_layout.addRow(gb_python)
        fields_layout.addRow(
            "ОС:",
            get_ext_line_edit(platform.platform()),
        )

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel(f"<h1>{PROGRAM_NAME}</h1>"))
        main_layout.addLayout(fields_layout)
        main_layout.addStretch()
        main_layout.addWidget(button_box)

        self.resize(800, 400)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = About()
    w.show()

    app.exec()
