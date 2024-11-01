#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import sys
import os
import platform
import re

from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

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
    QScrollArea,
)

from api import get_human_datetime, get_ago
from config import PROGRAM_NAME, VERSION, DIR, GITHUB_PROJECT, PATH_README, PATH_CHANGELOG
from widgets.markdown_viewer import MarkdownViewer


# SOURCE: https://stackoverflow.com/a/78205823/5909792
PATTERN_EMAIL: re.Pattern = re.compile(
    r"[A-Za-z0-9!#%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#%&'*+/=?^_`{|}~-]+)*"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
)


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

        self.changelog = MarkdownViewer(
            title="Журнал изменений",
            path=PATH_CHANGELOG,
            parent=self,
        )
        self._started: datetime = datetime.now()

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

        le_version = get_ext_line_edit(VERSION)
        icon = le_version.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        action_changelog = le_version.addAction(icon, QLineEdit.TrailingPosition)
        action_changelog.setToolTip("Посмотреть журнал изменений")
        action_changelog.triggered.connect(self.changelog.exec)

        fields_layout.addRow(
            "Версия:",
            le_version,
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

        self._label_started = get_ext_label("")
        fields_layout.addRow(
            "Запущено:",
            self._label_started,
        )

        if emails := PATTERN_EMAIL.findall(PATH_README.read_text(encoding="utf-8")):
            fields_layout.addRow(
                "Контактная информация:",
                get_ext_label(
                    "\n".join(
                        f"<a href='mailto:{email}?subject={PROGRAM_NAME}'>{email}</a>"
                        for email in emails
                    )
                ),
            )

        if psutil:
            fields_layout.addRow(
                "PID:",
                get_ext_label(str(os.getpid())),
            )

            self._label_memory = get_ext_label("")
            fields_layout.addRow(
                "Потребление памяти:",
                self._label_memory,
            )

        fields_widget = QWidget()
        fields_layout.setContentsMargins(0, 0, 0, 0)
        fields_widget.setLayout(fields_layout)

        scroll_area = QScrollArea()
        scroll_area.setFrameStyle(QScrollArea.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(fields_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel(f"<h1>{PROGRAM_NAME}</h1>"))
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(button_box)

        self.refresh()

        self.resize(800, 500)

    def refresh(self):
        self._label_started.setText(
            f"{get_human_datetime(self._started)} ({get_ago(self._started)})"
        )

        if psutil:
            # SOURCE: https://github.com/gil9red/SimplePyScripts/blob/fec522a6d931b0e353ed9e1025fe0a1c2d7c4ae6/human_byte_size.py#L7
            def sizeof_fmt(num: int | float) -> str:
                for x in ["bytes", "KB", "MB", "GB"]:
                    if num < 1024.0:
                        return "%.1f %s" % (num, x)

                    num /= 1024.0

                return "%.1f %s" % (num, "TB")

            def _get_tr(pid: int, value: int) -> str:
                return f"<tr><td>{pid}</td><td>{sizeof_fmt(value)}</td></tr>"

            current_process = psutil.Process(os.getpid())
            mem = current_process.memory_info().rss
            lines = [_get_tr(current_process.pid, mem)]
            for child in current_process.children(recursive=True):
                try:
                    child_mem = child.memory_info().rss
                    mem += child_mem
                    lines.append(_get_tr(child.pid, child_mem))
                except psutil.NoSuchProcess:
                    pass

            self._label_memory.setText(
                f"""
                <style>
                    .total {{
                        text-align: right;
                    }}
                    
                    table {{
                        border-collapse: collapse;
                    }}
                    
                    th, td {{
                        border: 1px solid black;
                        padding: 10px;
                    }}
                    th {{
                        background: lightgray;
                    }}
                </style>
                
                <table>
                    <thead>
                        <tr>
                            <th>Pid</th>
                            <th>Память</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(lines)}
                    </tbody>
                    <tfoot>
                        <tr>
                            <th class="total">Всего:</th>
                            <th>{sizeof_fmt(mem)}</td>
                        </tr>
                    </tfoot>
                </table>
                """
            )


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    w = About()
    w.show()

    sys.exit(app.exec())
