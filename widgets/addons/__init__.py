#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import html
import importlib

from datetime import datetime
from inspect import isclass
from typing import Type, Any
from pathlib import Path

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
    QFormLayout,
    QCheckBox,
)

from api import RunFuncThread, get_human_datetime, get_ago, get_exception_traceback
from widgets import get_class_name


FILE = Path(__file__).resolve()
DIR = FILE.parent


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

    @property
    def is_active(self) -> bool:
        return self.__is_active

    @is_active.setter
    def is_active(self, value: bool):
        self.__is_active = value

    def get_data(self) -> Any:
        raise NotImplementedError()

    def process(self, data: Any):
        raise NotImplementedError()

    def refresh(self):
        if not self.isEnabled() or not self.__is_active:
            return

        self.thread_process.start()

    def init_settings(self, settings_layout: QFormLayout):
        pass

    def read_settings(self, settings: dict[str, Any] | None):
        pass

    def write_settings(self, settings: dict[str, Any]):
        pass


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

        # Для работы saveState/restoreState
        self.setObjectName(f"{self.addon.name}_DockWidget")

        # TODO: Общая инфа, а не только ошибки
        # TODO: Кнопку очищения бы добавить
        self.logs = QPlainTextEdit()
        self.logs.setMaximumBlockCount(1_000)
        self.logs.setObjectName("logs")
        self.logs.setReadOnly(True)

        self.cb_is_active = QCheckBox()
        self.cb_is_active.setObjectName("is_active")
        self.cb_is_active.setChecked(True)
        self.cb_is_active.toggled.connect(self._set_is_active)

        self.cb_is_auto_refresh = QCheckBox()
        self.cb_is_auto_refresh.setObjectName("is_auto_refresh")
        self.cb_is_auto_refresh.setChecked(True)

        self.settings = QWidget()

        self.button_refresh = QToolButton()
        self.button_refresh.setObjectName("button_refresh")
        self.button_refresh.setText("🔄")
        self.button_refresh.clicked.connect(self.addon.refresh)

        self._last_refresh_datetime: datetime | None = None

        self.stacked_ago_progress = QStackedWidget()
        self.stacked_ago_progress.setObjectName("ago_progress")
        self.stacked_ago_progress.addWidget(self.label_ago)
        self.stacked_ago_progress.addWidget(self.progress_refresh)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tabs")
        self.tab_widget.addTab(self.addon, "🏛️")
        self.tab_widget.addTab(self.logs, "📝")
        self.tab_widget.addTab(self.settings, "⚙️")

        self.tab_widget.setCornerWidget(self.button_refresh, Qt.TopLeftCorner)
        self.tab_widget.setCornerWidget(self.stacked_ago_progress, Qt.TopRightCorner)

        self.setWidget(self.tab_widget)

        self._update_window_title()
        self._init_settings()

    def _init_settings(self):
        settings_layout = QFormLayout()
        settings_layout.addRow("Активный:", self.cb_is_active)
        settings_layout.addRow("Авто-обновление:", self.cb_is_auto_refresh)

        self.settings.setLayout(settings_layout)

        self.addon.init_settings(settings_layout)

    def _update_window_title(self):
        title = self.addon.title
        if not self.addon.is_active:
            title = f"{title} (отключено)"

        self.setWindowTitle(title)

    def _set_is_active(self, is_active: bool):
        # Зачеркивание текста действия у отключенного аддона
        action = self.toggleViewAction()
        font = action.font()
        font.setStrikeOut(not is_active)
        action.setFont(font)

        self.addon.is_active = is_active
        self.button_refresh.setEnabled(is_active)
        self._update_window_title()

    def update_last_refresh_datetime(self):
        self.label_ago.setText(
            get_ago(self._last_refresh_datetime) if self._last_refresh_datetime else ""
        )

    def is_auto_refresh(self) -> bool:
        return self.cb_is_auto_refresh.isChecked()

    def refresh(self):
        self.addon.refresh()

    def _process_started(self):
        self._last_refresh_datetime = None
        self.button_refresh.setEnabled(False)
        self.addon.setEnabled(False)
        self.stacked_ago_progress.setCurrentWidget(self.progress_refresh)

        self.logs.appendPlainText(f"Обновление в {get_human_datetime()}")

    def _process_run_finished(self, _: Any):
        self.tab_widget.setCurrentWidget(self.addon)

    def _process_set_error_log(self, e: Exception):
        error: str = get_exception_traceback(e)

        error = html.escape(error).replace("\n", "<br/>")
        self.logs.appendHtml(f"<span style='color: red'>{error}</span>")

        self.tab_widget.setCurrentWidget(self.logs)

    def _process_finished(self):
        self.button_refresh.setEnabled(True)
        self.addon.setEnabled(True)
        self.stacked_ago_progress.setCurrentWidget(self.label_ago)

        self._last_refresh_datetime = datetime.now()
        self.update_last_refresh_datetime()

    def read_settings(self, settings: dict[str, Any] | None):
        if not settings:
            return

        value: bool = settings.get(self.cb_is_active.objectName(), True)
        self.cb_is_active.setChecked(value)

        value: bool = settings.get(self.cb_is_auto_refresh.objectName(), True)
        self.cb_is_auto_refresh.setChecked(value)

        self.addon.read_settings(settings)

    def write_settings(self, settings: dict[str, Any]):
        settings[self.cb_is_active.objectName()] = self.cb_is_active.isChecked()
        settings[self.cb_is_auto_refresh.objectName()] = self.cb_is_auto_refresh.isChecked()

        self.addon.write_settings(settings)


def import_all_addons() -> list[AddonDockWidget]:
    items = []

    for f in DIR.glob("*.py"):
        if f == FILE:
            continue

        module = importlib.import_module(f".{f.stem}", package=__name__)

        # Перебираем список объектов в модуле
        for name in dir(module):
            obj = getattr(module, name)
            if (
                not isclass(obj)
                or obj is AddonWidget
                or not issubclass(obj, AddonWidget)
            ):
                continue

            items.append(AddonDockWidget(addon_cls=obj))

    return items
