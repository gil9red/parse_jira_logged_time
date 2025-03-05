#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QWidget,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
)

from api import RunFuncThread
from api import requirements
from widgets.addons import AddonWidget, AddonDockWidget, Defaults


REQUIRED_MODULE_NAME: str = "psutil"
IS_INSTALLED_PSUTIL: bool = requirements.is_installed(REQUIRED_MODULE_NAME)

# NOTE: Использует psutil
if IS_INSTALLED_PSUTIL:
    from widgets.addons.busy_ports.get_info_html import open_html_file
else:

    def open_html_file():
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
    def __init__(self, addon_dock_widget: AddonDockWidget):
        super().__init__(addon_dock_widget)

        self.setWindowTitle("Занятые порты")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        if IS_INSTALLED_PSUTIL:
            thread_func = RunFuncThread(func=open_html_file)
            thread_func.setParent(self)

            pb_open_report = create_push_button_with_word_wrap(
                "📝 Собрать отчет по занятым портам локальных серверов"
            )
            pb_open_report.clicked.connect(thread_func.start)

            thread_func.started.connect(lambda: pb_open_report.setEnabled(False))
            thread_func.finished.connect(lambda: pb_open_report.setEnabled(True))

            main_layout.addWidget(pb_open_report)
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
