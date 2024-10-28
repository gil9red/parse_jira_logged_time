#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import io
import json
import multiprocessing as mp
import sys
import traceback

from contextlib import redirect_stdout
from datetime import datetime, date
from typing import Any

from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QMainWindow,
    QToolButton,
    QCheckBox,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QSystemTrayIcon,
    QProgressBar,
    QToolTip,
    QTabWidget,
)
from PyQt5.QtCore import (
    QEvent,
    QTimer,
    QByteArray,
    Qt,
    QTranslator,
    QLibraryInfo,
)
from PyQt5.QtGui import QIcon

import api
from api import (
    RunFuncThread,
    get_human_datetime,
    get_human_date,
    get_ago,
)
from api.jira import get_jira_current_username
from api.jira_rss import (
    Activity,
    get_rss_jira_log,
    seconds_to_str,
    parse_date_by_activities,
    get_logged_total_seconds,
)
from config import (
    VERSION,
    PROGRAM_NAME,
    PATH_STYLE_SHEET,
    PATH_FAVICON,
    PATH_CONFIG,
    CONFIG,
    USERNAME,
)
from widgets.addons import AddonDockWidget, import_all_addons
from widgets.about import About
from widgets.activities_widget import ActivitiesWidget
from widgets.logged_widget import LoggedWidget
from widgets.logs_widget import LogsWidget


MAIN_WINDOW: "MainWindow" = None


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = f"{ex_cls.__name__}: {ex}\n"
    text += "".join(traceback.format_tb(tb))
    print(text)

    if isinstance(ex, KeyboardInterrupt):
        if MAIN_WINDOW:
            MAIN_WINDOW.write_settings()
            QApplication.instance().quit()
        return

    if QApplication.instance():
        msg_box = QMessageBox(
            QMessageBox.Critical,
            "Ошибка",
            f"Ошибка: {ex}",
            parent=MAIN_WINDOW,
        )
        msg_box.setDetailedText(text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()


sys.excepthook = log_uncaught_exceptions


WINDOW_TITLE_BASE: str = f"{PROGRAM_NAME} v{VERSION}"
TEMPLATE_WINDOW_TITLE_WITH_USERNAME: str = (
    f"{PROGRAM_NAME} v{VERSION}. username={{username}}"
)
TEMPLATE_WINDOW_TITLE_WITH_REFRESH: str = (
    f"{TEMPLATE_WINDOW_TITLE_WITH_USERNAME}. Последнее обновление: {{dt}} ({{ago}})"
)


def from_base64(state: str) -> QByteArray:
    return QByteArray.fromBase64(state.encode("utf-8"))


def to_base64(state: QByteArray) -> str:
    return state.toBase64().data().decode("utf-8")


def get_class_name(obj: Any) -> str:
    return obj.__class__.__name__


def read_settings_children(widget, config: dict[str, Any] | None):
    if not config:
        return

    for child in widget.findChildren(QSplitter):
        object_name: str = child.objectName()
        if not object_name:
            print(f"[WARN] {child} does not have an objectName")
            continue

        state: str | None = config.get(object_name)
        if not state:
            continue

        child.restoreState(from_base64(state))


def write_settings_children(widget, config: dict[str, Any]):
    for child in widget.findChildren(QSplitter):
        object_name: str = child.objectName()
        if not object_name:
            print(f"[WARN] {child} does not have an objectName")
            continue

        config[object_name] = to_base64(child.saveState())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(WINDOW_TITLE_BASE)

        icon = QIcon(str(PATH_FAVICON))

        self.setWindowIcon(icon)

        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip(self.windowTitle())
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        self.windowTitleChanged.connect(self.tray.setToolTip)

        self.button_refresh = QToolButton()
        self.button_refresh.setObjectName("button_refresh")
        self.button_refresh.setText("🔄")
        self.button_refresh.setToolTip("Обновить")
        self.button_refresh.setShortcut("F5")
        self.button_refresh.clicked.connect(self.refresh)

        self.cb_auto_refresh = QCheckBox()
        self.cb_auto_refresh.setObjectName("cb_auto_refresh")
        self.cb_auto_refresh.setText("Авто-обновление")
        self.cb_auto_refresh.setToolTip("Каждый 1 час")
        self.cb_auto_refresh.setChecked(True)
        self.cb_auto_refresh.toggled.connect(self.set_auto_refresh)

        self.logs = LogsWidget()

        self.cb_show_log = QCheckBox()
        self.cb_show_log.setText("Логи")
        self.cb_show_log.setChecked(False)
        self.cb_show_log.clicked.connect(self.logs.setVisible)
        self.logs.setVisible(self.cb_show_log.isChecked())

        tool_bar_general = self.addToolBar("&Общее")
        tool_bar_general.setObjectName("tool_bar_general")
        tool_bar_general.addWidget(self.button_refresh)
        tool_bar_general.addWidget(self.cb_auto_refresh)
        tool_bar_general.addSeparator()
        tool_bar_general.addWidget(self.cb_show_log)

        self.progress_refresh = QProgressBar()
        self.progress_refresh.setObjectName("progress_refresh")
        self.progress_refresh.setRange(0, 0)
        self.progress_refresh.setTextVisible(False)
        self.progress_refresh.hide()

        self.timer_auto_refresh = QTimer()
        self.timer_auto_refresh.setInterval(60 * 60 * 1000)  # 1 hour
        self.timer_auto_refresh.timeout.connect(self.refresh)

        self.timer_update_window_title = QTimer()
        self.timer_update_window_title.setInterval(5 * 1000)  # 5 seconds
        self.timer_update_window_title.timeout.connect(self._update_window_title)

        self.username: str | None = USERNAME

        self.thread_get_data = RunFuncThread(
            func=lambda: get_rss_jira_log(self.username)
        )
        self.thread_get_data.started.connect(self._before_refresh)
        self.thread_get_data.about_error.connect(self._set_error_log)
        self.thread_get_data.run_finished.connect(self._fill_tables)
        self.thread_get_data.finished.connect(self._after_refresh)

        self.logged_widget = LoggedWidget()
        self.activities_widget = ActivitiesWidget()

        self.menu_file = self.menuBar().addMenu("&Файл")
        action_exit = self.menu_file.addAction("&Выйти")
        action_exit.triggered.connect(self.close)

        self._last_refresh_datetime: datetime | None = None

        menu_view = self.menuBar().addMenu("&Вид")

        menu_tool_bar = menu_view.addMenu("&Панель инструментов")
        menu_tool_bar.addAction(tool_bar_general.toggleViewAction())

        menu_addons = menu_view.addMenu("&Аддоны")
        self.addons: list[AddonDockWidget] = []
        for addon_dock in import_all_addons():
            self.addons.append(addon_dock)

            self.addDockWidget(Qt.RightDockWidgetArea, addon_dock)
            menu_addons.addAction(addon_dock.toggleViewAction())

        self.menu_help = self.menuBar().addMenu("&Помощь")

        self.about = About(self)
        self.menu_help.addAction("О &программе", self.about.exec)

        self.menu_help.addAction("О &Qt", QApplication.aboutQt)

        tab_widget = QTabWidget()
        tab_widget.addTab(self.logged_widget, "ЗАЛОГИРОВАНО")
        tab_widget.addTab(self.activities_widget, "АКТИВНОСТИ")

        layout_content = QVBoxLayout()
        layout_content.addWidget(tab_widget)
        layout_content.addWidget(self.logs)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.progress_refresh)
        layout_main.addLayout(layout_content)

        central_widget = QWidget()
        central_widget.setLayout(layout_main)

        self.setCentralWidget(central_widget)

        self._quit_dont_ask_again: bool = False

        # Запуск таймеров после инициализации GUI
        self.timer_update_window_title.start()

        if self.cb_auto_refresh.isChecked():
            self.timer_auto_refresh.start()

    def set_auto_refresh(self, checked: bool):
        if checked:
            self.timer_auto_refresh.start()
        else:
            self.timer_auto_refresh.stop()

        pos = self.cb_auto_refresh.geometry().topRight()
        pos = self.mapToGlobal(pos)
        QToolTip.showText(pos, f"Таймер {'запущен' if checked else 'остановлен'}")

    def _set_error_log(self, e: Exception):
        self.logs.append_exception(e)

        # Отображение лога
        self.cb_show_log.setChecked(False)
        self.cb_show_log.click()

    def _fill_tables(self, xml_data: bytes):
        buffer_io = io.StringIO()
        try:
            with redirect_stdout(buffer_io):
                print(
                    f"Xml data ({len(xml_data)} bytes):\n"
                    f"{xml_data[:150] + b'...' if len(xml_data) > 150 else xml_data!r}"
                )

                date_by_activities: dict[
                    date, list[Activity]
                ] = parse_date_by_activities(xml_data)
                if not date_by_activities:
                    return

                self.logged_widget.set_date_by_activities(date_by_activities)
                self.activities_widget.set_date_by_activities(date_by_activities)

                # Для красоты выводим результат в табличном виде
                table_header: tuple = (
                    "ДАТА",
                    "ЗАЛОГИРОВАНО",
                    "СЕКУНД(Ы)",
                    "АКТИВНОСТИ",
                )
                table_lines: list[tuple[str, str, int, int]] = []

                for entry_date, activities in sorted(
                    date_by_activities.items(), key=lambda x: x[0], reverse=True
                ):
                    activities_number = len(activities)

                    activities: list[Activity] = [
                        obj for obj in reversed(activities) if obj.logged
                    ]

                    total_seconds: int = get_logged_total_seconds(activities)
                    total_seconds_str: str = seconds_to_str(total_seconds)

                    date_str: str = get_human_date(entry_date)
                    table_lines.append(
                        (date_str, total_seconds_str, total_seconds, activities_number)
                    )

                print()

                # Список строк станет списком столбцов, у каждого столбца подсчитается максимальная длина
                table: list = [table_header] + table_lines
                max_len_columns = [max(map(len, map(str, col))) for col in zip(*table)]

                # Создание строки форматирования: [30, 14, 5] -> "{:<30} | {:<14} | {:<5}"
                my_table_format = " | ".join(
                    "{:<%s}" % max_len for max_len in max_len_columns
                )
                for line in table:
                    print(my_table_format.format(*line))

        finally:
            text = buffer_io.getvalue()
            self.logs.append(text)

            print(text)

    def _before_refresh(self):
        self.button_refresh.setEnabled(False)
        self.progress_refresh.show()

        for addon_dock in self.addons:
            if addon_dock.addon.is_active and addon_dock.is_auto_refresh():
                addon_dock.refresh()

    def _update_window_title(self):
        for addon_dock in self.addons:
            # NOTE: Обновление времени последнего обновления будет и для отключенных
            addon_dock.update_last_refresh_datetime()

        if not self._last_refresh_datetime:
            return

        self.setWindowTitle(
            TEMPLATE_WINDOW_TITLE_WITH_REFRESH.format(
                username=self.username,
                dt=get_human_datetime(self._last_refresh_datetime),
                ago=get_ago(self._last_refresh_datetime),
            )
        )

    def _after_refresh(self):
        self.button_refresh.setEnabled(True)
        self.progress_refresh.hide()

        self._last_refresh_datetime = datetime.now()

        self._update_window_title()

    def refresh(self):
        if not self.username:

            def _set_username(value: str):
                self.username = value

            thread = RunFuncThread(func=get_jira_current_username)
            thread.run_finished.connect(_set_username)
            # TODO: Отображение проблем получения текущего имени юзера
            # thread.about_error.connect(lambda e: raise e)
            thread.start()

            while not self.username:
                QApplication.instance().processEvents()

        self.setWindowTitle(
            TEMPLATE_WINDOW_TITLE_WITH_USERNAME.format(username=self.username)
        )

        self.thread_get_data.start()

    def read_settings(self):
        config_gui: dict[str, Any] | None = CONFIG.get("gui")
        if not config_gui:
            return

        if config_main_window := config_gui.get("MainWindow"):
            geometry = from_base64(config_main_window["geometry"])
            self.restoreGeometry(geometry)

            state = from_base64(config_main_window["state"])
            self.restoreState(state)

            value: bool = config_main_window.get("auto_refresh", True)
            self.cb_auto_refresh.setChecked(value)

            value: bool = config_main_window.get("quit_dont_ask_again", False)
            self._quit_dont_ask_again = value

        for child in [self.logged_widget, self.activities_widget]:
            child_name = get_class_name(child)
            read_settings_children(
                child,
                config_gui.get(child_name),
            )

        for name, settings in config_gui.get("Addons", dict()).items():
            for addon_dock in self.addons:
                if addon_dock.addon.name == name:
                    addon_dock.read_settings(settings)
                    break

    def write_settings(self):
        with open(PATH_CONFIG, "w") as f:
            CONFIG["gui"] = {
                "MainWindow": {
                    "state": to_base64(self.saveState()),
                    "geometry": to_base64(self.saveGeometry()),
                    "auto_refresh": self.cb_auto_refresh.isChecked(),
                    "quit_dont_ask_again": self._quit_dont_ask_again,
                },
            }

            for child in [self.logged_widget, self.activities_widget]:
                child_config: dict[str, Any] = dict()
                write_settings_children(child, child_config)

                child_name = get_class_name(child)
                CONFIG["gui"][child_name] = child_config

            addons: dict[str, Any] = dict()
            for addon_dock in self.addons:
                settings: dict[str, Any] = dict()
                addon_dock.write_settings(settings)
                addons[addon_dock.addon.name] = settings

            CONFIG["gui"]["Addons"] = addons

            json.dump(CONFIG, f, indent=4, ensure_ascii=False)

    def _on_tray_activated(self, _: QSystemTrayIcon.ActivationReason):
        self.setVisible(not self.isVisible())

        if self.isVisible():
            self.showNormal()
            self.activateWindow()

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.WindowStateChange:
            # Если окно свернули
            if self.isMinimized():
                # Прячем окно с панели задач
                QTimer.singleShot(0, self.hide)

    def closeEvent(self, event):
        if not self._quit_dont_ask_again:
            cb_dont_ask_again = QCheckBox("Не спрашивать")
            cb_dont_ask_again.setChecked(False)

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Выйти")
            msg_box.setText("Вы уверены, что хотите выйти?")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            msg_box.setCheckBox(cb_dont_ask_again)

            reply = msg_box.exec()
            if reply != QMessageBox.Yes:
                event.ignore()
                return

            self._quit_dont_ask_again = cb_dont_ask_again.isChecked()

        self.write_settings()


if __name__ == "__main__":
    with mp.Pool(processes=5) as pool:
        api.POOL = pool

        app = QApplication([])

        # Использование локали на русском в стандартных виджетах
        translator = QTranslator()
        translations_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        if translator.load("qtbase_ru", directory=translations_path):
            app.installTranslator(translator)

        app.setStyleSheet(PATH_STYLE_SHEET.read_text(encoding="utf-8"))

        mw = MainWindow()
        MAIN_WINDOW = mw

        mw.resize(1200, 800)
        mw.show()

        mw.read_settings()
        mw.refresh()

        app.exec()
