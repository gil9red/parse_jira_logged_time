#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import html
import importlib

from datetime import datetime
from typing import Type, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QDockWidget,
    QToolButton,
    QProgressBar,
    QPlainTextEdit,
    QTabWidget,
    QStackedWidget,
    QLabel,
)

from api import RunFuncThread, get_human_datetime, get_ago
from widgets import get_class_name


class AddonWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.__is_active: bool = True

        self.thread_process = RunFuncThread(func=self.get_data)
        self.thread_process.run_finished.connect(self.process)

    @property
    def name(self) -> str:
        return get_class_name(self)

    @property
    def title(self) -> str:
        return self.windowTitle()

    # TODO:
    @property
    def is_active(self) -> bool:
        return self.__is_active

    # TODO:
    @is_active.setter
    def is_active(self, value: bool):
        self.__is_active = value

    def get_data(self) -> Any:
        raise NotImplementedError()

    def process(self, data: Any):
        raise NotImplementedError()

    def refresh(self):
        if not self.isEnabled() or self.thread_process.isRunning():
            return

        self.thread_process.start()


class AddonDockWidget(QDockWidget):
    def __init__(self, addon_cls: Type[AddonWidget]):
        super().__init__()

        self.progress_refresh = QProgressBar()
        self.progress_refresh.setObjectName("progress_refresh")
        self.progress_refresh.setRange(0, 0)
        self.progress_refresh.setTextVisible(False)

        self.label_ago = QLabel()
        self.label_ago.setObjectName("ago")

        self.addon: AddonWidget = addon_cls()
        self.addon.thread_process.started.connect(self._process_started)
        self.addon.thread_process.run_finished.connect(self._process_run_finished)
        self.addon.thread_process.about_error.connect(self._process_set_error_log)
        self.addon.thread_process.finished.connect(self._process_finished)

        self.setWindowTitle(self.addon.title)

        # Для работы saveState/restoreState
        self.setObjectName(f"{self.addon.name}_DockWidget")

        # TODO: Общая инфа, а не только ошибки
        # TODO: Кнопку очищения бы добавить
        self.logs = QPlainTextEdit()
        self.logs.setMaximumBlockCount(1_000)
        self.logs.setObjectName("logs")
        self.logs.setReadOnly(True)

        self.button_refresh = QToolButton()
        self.button_refresh.setObjectName("button_refresh")
        self.button_refresh.setText("🔄")
        self.button_refresh.clicked.connect(self.addon.refresh)

        self._last_refresh_datetime: datetime | None = None

        self.stacked_ago_progress = QStackedWidget()
        self.stacked_ago_progress.setObjectName("ago_progress")
        self.stacked_ago_progress.addWidget(self.progress_refresh)
        self.stacked_ago_progress.addWidget(self.label_ago)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tabs")
        self.tab_widget.addTab(self.addon, "🏛️")
        self.tab_widget.addTab(self.logs, "📝")
        # self.tab_widget.addTab(self.settings, "⚙️")  # TODO: На будущее

        self.tab_widget.setCornerWidget(self.button_refresh, Qt.TopLeftCorner)
        self.tab_widget.setCornerWidget(self.stacked_ago_progress, Qt.TopRightCorner)

        self.setWidget(self.tab_widget)

    def update_last_refresh_datetime(self):
        self.label_ago.setText(
            get_ago(self._last_refresh_datetime) if self._last_refresh_datetime else ""
        )

    def refresh(self):
        self.addon.refresh()

    def _run_finished(self, data: Any):
        self.stacked_layout.setCurrentIndex(self.INDEX_MAIN)
        self.process(data)

    def _set_error_log(self, error: str):
        self.stacked_layout.setCurrentIndex(self.INDEX_ERROR)

        error = html.escape(error).replace("\n", "<br/>")
        self.logs.appendHtml(f"<span style='color: red'>{error}</span>")

    def _process_started(self):
        self._last_refresh_datetime = None
        self.button_refresh.setEnabled(False)
        self.addon.setEnabled(False)
        self.stacked_ago_progress.setCurrentWidget(self.progress_refresh)

        self.logs.appendPlainText(f"Refresh at {get_human_datetime()}")

    def _process_run_finished(self, _: Any):
        self.tab_widget.setCurrentWidget(self.addon)

    def _process_set_error_log(self, text: str):
        self.logs.setPlainText(text)
        self.tab_widget.setCurrentWidget(self.logs)

    def _process_finished(self):
        self.button_refresh.setEnabled(True)
        self.addon.setEnabled(True)
        self.stacked_ago_progress.setCurrentWidget(self.label_ago)

        self._last_refresh_datetime = datetime.now()
        self.update_last_refresh_datetime()

    # TODO: Методы сохранения/считывания из конфига


# TODO:
from pathlib import Path
FILE = Path(__file__).resolve()
DIR = FILE.parent

# TODO: добавить вариант с возвратом AddonDockWidget?

def import_all_addons() -> list[type[AddonWidget]]:
    items = []

    for f in DIR.glob("*.py"):
        if f == FILE:
            continue

        module = importlib.import_module(f".{f.stem}", package=__name__)

        from inspect import isclass  # TODO:

        # Перебираем список объектов в модуле
        for name in dir(module):
            obj = getattr(module, name)
            if (
                    not isclass(obj)
                    or obj is AddonWidget
                    or not issubclass(obj, AddonWidget)
            ):
                continue

            # items.append(obj())
            items.append(obj)

    return items