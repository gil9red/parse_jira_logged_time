#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from typing import Type, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QDockWidget,
    QToolButton,
    QHBoxLayout,
    QVBoxLayout,
    QProgressBar,
    QStackedLayout,
    QPlainTextEdit,
)

from api import RunFuncThread


class AddonWidget(QWidget):
    INDEX_MAIN = 0
    INDEX_ERROR = 1

    def __init__(self):
        super().__init__()

        self.main_widget = QWidget()

        self.error_info = QPlainTextEdit()
        self.error_info.setReadOnly(True)
        self.error_info.setStyleSheet("color: red;")

        self.thread_process = RunFuncThread(func=self.get_data)
        self.thread_process.run_finished.connect(self._run_finished)
        self.thread_process.about_error.connect(self._set_error_log)

        self.stacked_layout = QStackedLayout(self)
        self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_layout.addWidget(self.main_widget)
        self.stacked_layout.addWidget(self.error_info)

    def _run_finished(self, data: Any):
        self.stacked_layout.setCurrentIndex(self.INDEX_MAIN)
        self.process(data)

    def _set_error_log(self, error: str):
        self.stacked_layout.setCurrentIndex(self.INDEX_ERROR)
        self.error_info.setPlainText(error)

    # TODO: В AddonDockWidget
    def refresh(self):
        if not self.isEnabled() or self.thread_process.isRunning():
            return

        self.thread_process.start()

    def get_data(self) -> Any:
        raise NotImplementedError()

    def process(self, data: Any):
        raise NotImplementedError()


class AddonDockWidget(QDockWidget):
    def __init__(self, addon_cls: Type[AddonWidget]):
        super().__init__()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()

        self.addon: AddonWidget = addon_cls()
        self.addon.thread_process.started.connect(self._process_started)
        self.addon.thread_process.finished.connect(self._process_finished)

        self.setWindowTitle(self.addon.windowTitle())

        self.button_refresh = QToolButton()
        self.button_refresh.setText("🔄")
        self.button_refresh.clicked.connect(self.addon.refresh)

        central_widget = QWidget()

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.button_refresh, alignment=Qt.AlignLeft)
        buttons_layout.addWidget(self.progress_bar)

        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.addon)

        self.setWidget(central_widget)

    def _process_started(self):
        self.setEnabled(False)
        self.progress_bar.show()

    def _process_finished(self):
        self.setEnabled(True)
        self.progress_bar.hide()
