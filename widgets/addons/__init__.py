#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import importlib
import traceback
import pkgutil
import sys

from dataclasses import dataclass
from datetime import datetime
from inspect import isclass
from typing import Type, Any
from types import ModuleType
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QDockWidget,
    QToolButton,
    QProgressBar,
    QTabWidget,
    QStackedWidget,
    QLabel,
    QFormLayout,
    QCheckBox,
    QHBoxLayout,
    QMessageBox,
)

from api import RunFuncThread, get_human_datetime, get_ago
from widgets import get_class_name, get_scroll_area, web_browser_open
from widgets.logs_widget import LogsWidget


FILE: Path = Path(__file__).resolve()
DIR: Path = FILE.parent


@dataclass
class Defaults:
    is_active: bool
    is_visible: bool
    area: Qt.DockWidgetArea


class AddonWidget(QWidget):
    def __init__(self, addon_dock_widget: "AddonDockWidget"):
        super().__init__()

        self.addon_dock_widget = addon_dock_widget

        self.__is_active: bool = True
        self.context: Any = None

        self.thread_process = RunFuncThread(func=self.get_data)
        self.thread_process.run_finished.connect(self.do_process)

    def set_context(self, context: Any):
        self.context = context

    def defaults(self) -> Defaults:
        return Defaults(
            is_active=True,
            is_visible=True,
            area=Qt.DockWidgetArea.RightDockWidgetArea,
        )

    def is_supported_refresh(self) -> bool:
        return True

    def is_supported_logs(self) -> bool:
        return True

    def is_supported_settings(self) -> bool:
        return True

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

    @property
    def url(self) -> str:
        return ""

    def get_data(self) -> Any:
        raise NotImplementedError()

    def process(self, data: Any):
        raise NotImplementedError()

    def do_process(self, data: Any):
        try:
            self.process(data)
        except Exception as e:
            self.thread_process.about_error.emit(e)

    def refresh(self):
        if (
            not self.isEnabled()
            or not self.__is_active
            or not self.is_supported_refresh()
        ):
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

        self._last_error: Exception | None = None

        self.addon: AddonWidget = addon_cls(self)
        self.addon.thread_process.started.connect(self._process_started)
        self.addon.thread_process.run_finished.connect(self._process_run_finished)
        self.addon.thread_process.about_error.connect(self._process_set_error_log)
        self.addon.thread_process.finished.connect(self._process_finished)

        # Для работы saveState/restoreState
        self.setObjectName(f"{self.addon.name}_DockWidget")

        self.logs = LogsWidget()

        self.cb_is_active = QCheckBox()
        self.cb_is_active.setObjectName("is_active")
        self.cb_is_active.setChecked(True)
        self.cb_is_active.toggled.connect(self._set_is_active)

        self.cb_is_auto_refresh = QCheckBox()
        self.cb_is_auto_refresh.setObjectName("is_auto_refresh")
        self.cb_is_auto_refresh.setChecked(True)
        self.cb_is_auto_refresh.toggled.connect(self._update_window_title)

        self.settings = QWidget()

        self.button_refresh = QToolButton()
        self.button_refresh.setObjectName("button_refresh")
        self.button_refresh.setAutoRaise(True)
        self.button_refresh.setText("🔄")
        self.button_refresh.clicked.connect(self.addon.refresh)

        self.button_url = QToolButton()
        self.button_url.setObjectName("button_url")
        self.button_url.setAutoRaise(True)
        self.button_url.setText("🌍")
        self.button_url.setToolTip("Открыть ссылку")
        self.button_url.clicked.connect(lambda: web_browser_open(self.addon.url))

        self._last_refresh_datetime: datetime | None = None

        self.stacked_ago_progress = QStackedWidget()
        self.stacked_ago_progress.setObjectName("ago_progress")
        self.stacked_ago_progress.addWidget(self.label_ago)
        self.stacked_ago_progress.addWidget(self.progress_refresh)

        right_corner_widget = QWidget()
        right_corner_widget_layout = QHBoxLayout(right_corner_widget)
        right_corner_widget_layout.setContentsMargins(0, 0, 0, 0)

        if self.addon.url:
            right_corner_widget_layout.addWidget(self.button_url)

        if self.addon.is_supported_refresh():
            right_corner_widget_layout.addWidget(self.stacked_ago_progress)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBarAutoHide(True)
        self.tab_widget.setObjectName("tabs")

        self._idx_tab_addon = self.tab_widget.addTab(
            get_scroll_area(self.addon),
            "🏛️",
        )

        if self.addon.is_supported_logs():
            self._idx_tab_logs = self.tab_widget.addTab(
                self.logs,  # NOTE: Тут get_scroll_area не нужен
                "📝",
            )
        else:
            self._idx_tab_logs = -1

        if self.addon.is_supported_settings():
            self.tab_widget.addTab(
                get_scroll_area(self.settings),
                "⚙️",
            )

        if self.addon.is_supported_refresh():
            self.tab_widget.setCornerWidget(self.button_refresh, Qt.TopLeftCorner)

        self.tab_widget.setCornerWidget(right_corner_widget, Qt.TopRightCorner)

        self.setWidget(self.tab_widget)

        self._update_window_title()
        self._init_settings()

    def _init_settings(self):
        settings_layout = QFormLayout()
        settings_layout.addRow("Активный:", self.cb_is_active)

        if self.addon.is_supported_refresh():
            settings_layout.addRow(
                "Авто-обновление (общее):",
                self.cb_is_auto_refresh,
            )

        self.settings.setLayout(settings_layout)

        self.addon.init_settings(settings_layout)

    def _update_window_title(self):
        title = self.addon.title
        if not self.addon.is_active:
            title = f"{title} (отключено)"

        if not self.is_auto_refresh():
            title = f"❌ {title}"

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
        if not self.addon.is_supported_refresh():
            return

        self.logs.append(f"Обновление в {get_human_datetime()}")
        self.addon.refresh()

    def _process_started(self):
        self._last_error = None
        self._last_refresh_datetime = None

        self.button_refresh.setEnabled(False)
        self.addon.setEnabled(False)
        self.stacked_ago_progress.setCurrentWidget(self.progress_refresh)

    def _process_run_finished(self, _: Any):
        # Это код может быть выполнен сразу после _process_set_error_log
        if self._last_error and self._idx_tab_logs != -1:
            self.tab_widget.setCurrentIndex(self._idx_tab_logs)
            return

        self.tab_widget.setCurrentIndex(self._idx_tab_addon)

    def _process_set_error_log(self, e: Exception):
        self._last_error = e

        self.logs.append_exception(e)

        if self._idx_tab_logs != -1:
            self.tab_widget.setCurrentIndex(self._idx_tab_logs)

    def _process_finished(self):
        self.button_refresh.setEnabled(True)
        self.addon.setEnabled(True)
        self.stacked_ago_progress.setCurrentWidget(self.label_ago)

        self._last_refresh_datetime = datetime.now()
        self.update_last_refresh_datetime()

    def read_settings(self, settings: dict[str, Any] | None):
        defaults: Defaults = self.addon.defaults()

        if not settings:
            settings: dict[str, Any] = dict()

            self.setVisible(defaults.is_visible)

        is_active: bool = settings.get(
            self.cb_is_active.objectName(),
            defaults.is_active,
        )
        self.cb_is_active.setChecked(is_active)

        is_auto_refresh: bool = settings.get(
            self.cb_is_auto_refresh.objectName(),
            True,
        )
        self.cb_is_auto_refresh.setChecked(is_auto_refresh)

        self.addon.read_settings(settings)

    def write_settings(self, settings: dict[str, Any]):
        is_active = self.cb_is_active.objectName()
        settings[is_active] = self.cb_is_active.isChecked()

        is_auto_refresh = self.cb_is_auto_refresh.objectName()
        settings[is_auto_refresh] = self.cb_is_auto_refresh.isChecked()

        self.addon.write_settings(settings)


# SOURCE: https://stackoverflow.com/a/25083161/5909792
def import_submodules(package_name: str) -> dict[str, ModuleType]:
    """
    Import all submodules of a module, recursively
    """

    package = sys.modules[package_name]
    return {
        name: importlib.import_module(package_name + "." + name)
        for _, name, _ in pkgutil.walk_packages(package.__path__)
    }


def import_all_addons(package: str = __name__) -> list[AddonDockWidget]:
    items = []

    for module in import_submodules(package).values():
        # Перебираем список объектов в модуле
        for name in dir(module):
            obj = getattr(module, name)
            if (
                not isclass(obj)
                or obj is AddonWidget
                or not issubclass(obj, AddonWidget)
            ):
                continue

            try:
                items.append(AddonDockWidget(addon_cls=obj))
            except Exception as e:
                msg_box = QMessageBox(
                    QMessageBox.Warning,
                    "Ошибка при загрузке аддона",
                    f"Ошибка при загрузке аддона {name}: {e}",
                )
                msg_box.setDetailedText(traceback.format_exc())
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()

    return items
