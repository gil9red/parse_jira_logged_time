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
)

from api import get_human_datetime, get_ago
from api import requirements
from config import (
    PROGRAM_NAME,
    DIR,
    GITHUB_PROJECT,
    PATH_README,
    PATH_CHANGELOG,
    CONFIG,
)
from version import VERSION
from third_party.column_resizer import ColumnResizer
from third_party.human_byte_size import sizeof_fmt
from widgets import get_scroll_area
from widgets.markdown_viewer import MarkdownViewer


# SOURCE: https://stackoverflow.com/a/78205823/5909792
PATTERN_EMAIL: re.Pattern = re.compile(
    r"[A-Za-z0-9!#%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#%&'*+/=?^_`{|}~-]+)*"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
)

PATTERN_MARKDOWN_HTTP_LINK: re.Pattern = re.compile(r"\[(.+?)]\((https?.+?)\)")

try:
    SHOW_USED_MEMORY: bool = CONFIG["gui"]["About"]["show_used_memory"] is True
except Exception:
    SHOW_USED_MEMORY: bool = False


def get_ext_label(text: str) -> QLabel:
    label = QLabel(text)

    label.setWordWrap(True)

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
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.changelog = MarkdownViewer(
            title="Журнал изменений",
            path=PATH_CHANGELOG,
            parent=self,
        )

        self.readme = MarkdownViewer(
            title="Информация",
            path=PATH_README,
            parent=self,
        )

        self._started: datetime = datetime.now()

        gb_python = QGroupBox("Python:")
        gb_python_layout = QFormLayout(gb_python)

        margins = gb_python_layout.contentsMargins()
        margins.setRight(0)
        gb_python_layout.setContentsMargins(margins)

        gb_python_layout.addRow(
            "Версия:",
            get_ext_label(sys.version),
        )
        gb_python_layout.addRow(
            "Реализация:",
            get_ext_label(platform.python_implementation()),
        )
        gb_python_layout.addRow(
            "Путь:", get_ext_line_edit(sys.executable, is_path=True)
        )

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        fields_layout = QFormLayout()

        le_version = get_ext_line_edit(VERSION)

        icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
        action_readme = le_version.addAction(icon, QLineEdit.TrailingPosition)
        action_readme.setToolTip("Посмотреть README.md")
        action_readme.triggered.connect(self.readme.exec)

        icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        action_changelog = le_version.addAction(icon, QLineEdit.TrailingPosition)
        action_changelog.setToolTip("Посмотреть журнал изменений (CHANGELOG.md)")
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
            get_ext_label(platform.platform()),
        )

        self._label_started = get_ext_label("")
        fields_layout.addRow(
            "Запущено:",
            self._label_started,
        )

        # NOTE: В текущем README.md может не присутствовать, но есть в
        #       поставляемой версией
        readme: str = PATH_README.read_text(encoding="utf-8")
        links: list[str] = []

        for email in PATTERN_EMAIL.findall(readme):
            links.append(f"<a href='mailto:{email}?subject={PROGRAM_NAME}'>{email}</a>")

        for title, url in PATTERN_MARKDOWN_HTTP_LINK.findall(readme):
            if "zoom" not in url.lower():  # Белый список
                continue

            links.append(f"<a href='{url}'>{title}</a>")

        if links:
            fields_layout.addRow(
                "Контактная информация:",
                get_ext_label("<br/>".join(links)),
            )

        if SHOW_USED_MEMORY:
            if psutil:
                fields_layout.addRow(
                    "PID:",
                    get_ext_label(str(os.getpid())),
                )

                self._label_memory = get_ext_label("")
                fields_layout.addRow(
                    "Память:",
                    self._label_memory,
                )
            else:
                not_module_widget = requirements.get_not_module_widget(
                    module_name="psutil",
                    text_template=(
                        "Для отображения используемой памяти нужно установить {name} и перезапустить приложение"
                    ),
                )
                fields_layout.addRow(not_module_widget)

        fields_widget = QWidget()
        fields_layout.setContentsMargins(0, 0, 0, 0)
        fields_widget.setLayout(fields_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel(f"<h1>{PROGRAM_NAME}</h1>"))
        main_layout.addWidget(get_scroll_area(fields_widget))
        main_layout.addWidget(button_box)

        resizer = ColumnResizer(self)
        resizer.addWidgetsFromLayout(fields_layout, 0)
        resizer.addWidgetsFromLayout(gb_python_layout, 0)

        self.refresh()

        self.resize(800, 500)

    def refresh(self):
        self._label_started.setText(
            f"{get_human_datetime(self._started)} ({get_ago(self._started)})"
        )

        if SHOW_USED_MEMORY and psutil:

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
                except psutil.Error:
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
