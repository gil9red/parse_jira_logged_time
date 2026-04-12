#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import subprocess
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QCheckBox,
    QWidget,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
)

from api import RunFuncThread, requirements
from widgets.addons import AddonWidget, AddonDockWidget, Defaults

from third_party.is_user_admin import is_user_admin, is_windows


REQUIRED_MODULE_NAME: str = "psutil"
IS_INSTALLED_PSUTIL: bool = requirements.is_installed(REQUIRED_MODULE_NAME)

# NOTE: Использует psutil
if IS_INSTALLED_PSUTIL:
    from widgets.addons.busy_ports import get_info_html

    def open_html_file(run_as_admin: bool = False) -> None:
        try:
            # Если нужно запустить как админ и текущий процесс не запущен от имени админа
            if run_as_admin and not is_user_admin():
                path_py_exe: str = sys.executable
                path_script: str = get_info_html.__file__

                if is_windows():
                    args: list[str] = [
                        "powershell",
                        "-Command",
                        f"&{{Start-Process -FilePath '{path_py_exe}' '{path_script}' -Wait -Verb RunAs}}",
                    ]
                else:
                    # TODO: Не тестировалось
                    if sys.platform == "darwin":
                        # TODO:
                        args: list[str] = [
                            "osascript",
                            "-e",
                            f'tell app "Terminal" to do script "python3 {path_py_exe} {path_script}"',
                        ]
                    else:
                        # TODO: open_new_terminal_linux
                        # TODO: open_new_terminal_macos
                        args: list[str] = ["sudo", path_py_exe, path_script]

                print("Run command:", args)
                subprocess.check_output(args)
                return

            # Выполнение кода от текущего процесса
            get_info_html.open_html_file()

        except Exception:
            pass

else:

    def open_html_file(*args, **kwargs) -> None:
        pass


def create_push_button_with_word_wrap(
    text: str,
    parent: QWidget | None = None,
) -> QPushButton:
    btn = QPushButton(parent)
    btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    label = QLabel(text, btn)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.NoTextInteraction)
    label.setMouseTracking(False)

    layout = QHBoxLayout(btn)
    layout.addWidget(label, Qt.AlignCenter)

    return btn


class AddonBusyPortsWidget(AddonWidget):
    def __init__(self, addon_dock_widget: AddonDockWidget) -> None:
        super().__init__(addon_dock_widget)

        self.setWindowTitle("Занятые порты")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        if IS_INSTALLED_PSUTIL:
            cb_as_admin = QCheckBox("Запустить как админ")
            cb_as_admin.setChecked(True)
            # NOTE: Если запущен от имени админа, то не показывать чекбокс
            if is_user_admin():
                cb_as_admin.setVisible(False)
                cb_as_admin.setChecked(False)

            thread_func = RunFuncThread(
                func=lambda: open_html_file(cb_as_admin.isChecked())
            )
            thread_func.setParent(self)

            pb_open_report = create_push_button_with_word_wrap(
                "📝 Собрать отчет по занятым портам локальных серверов"
            )
            pb_open_report.clicked.connect(thread_func.start)

            thread_func.started.connect(lambda: pb_open_report.setEnabled(False))
            thread_func.finished.connect(lambda: pb_open_report.setEnabled(True))

            main_layout.addWidget(pb_open_report)

            layout_settings = QHBoxLayout()
            layout_settings.setContentsMargins(5, 0, 0, 0)  # Left = 5
            layout_settings.addWidget(cb_as_admin)
            main_layout.addLayout(layout_settings)

            return

        not_module_widget = requirements.get_not_module_widget(REQUIRED_MODULE_NAME)
        main_layout.addWidget(not_module_widget)

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


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = AddonDockWidget(AddonBusyPortsWidget)
    w.resize(300, 300)
    w.show()

    app.exec()
