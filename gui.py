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

from PyQt5.QtCore import (
    QEvent,
    QTimer,
    QByteArray,
    Qt,
    QTranslator,
    QLibraryInfo,
    QEventLoop,
)
from PyQt5.QtGui import QIcon, QCloseEvent
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
    QTabWidget,
    QDockWidget,
    QMenu,
)

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

        icon = QIcon(str(PATH_FAVICON))
        self.setWindowIcon(icon)

        self.setDockNestingEnabled(True)

        self.button_refresh = QToolButton()
        self.button_refresh.setObjectName("button_refresh")
        self.button_refresh.setText("🔄")
        self.button_refresh.setToolTip("Обновить")
        self.button_refresh.setShortcut("F5")
        self.button_refresh.clicked.connect(self.refresh)

        self.cb_auto_refresh_rss = QCheckBox()
        self.cb_auto_refresh_rss.setObjectName("cb_auto_refresh")
        self.cb_auto_refresh_rss.setText("Авто-обновление")
        self.cb_auto_refresh_rss.setChecked(True)

        self.logs = LogsWidget()
        self.dock_widget_logs = QDockWidget("Логи")
        self.dock_widget_logs.setObjectName(f"{get_class_name(self.logs)}_DockWidget")
        self.dock_widget_logs.setWidget(self.logs)
        self.dock_widget_logs.hide()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_widget_logs)

        tool_bar_general = self.addToolBar("&Общее")
        tool_bar_general.setObjectName("tool_bar_general")
        tool_bar_general.addWidget(self.button_refresh)
        tool_bar_general.addSeparator()
        tool_bar_general.addAction(self.dock_widget_logs.toggleViewAction())

        self.progress_refresh = QProgressBar()
        self.progress_refresh.setObjectName("progress_refresh")
        self.progress_refresh.setRange(0, 0)
        self.progress_refresh.setTextVisible(False)
        self.progress_refresh.hide()

        self.timer_auto_refresh = QTimer()
        self.timer_auto_refresh.setInterval(60 * 60 * 1000)  # 1 hour
        self.timer_auto_refresh.timeout.connect(self.refresh)

        self.timer_update_states = QTimer()
        self.timer_update_states.setInterval(5 * 1000)  # 5 seconds
        self.timer_update_states.timeout.connect(self._update_states)

        self.username: str | None = USERNAME
        self._last_refresh_is_forced: bool = False
        self._skip_get_data: bool = False

        self.thread_get_data = RunFuncThread(func=self._get_data)
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
        action_about = self.menu_help.addAction("О &программе", self.about.exec)

        self.menu_help.addAction("О &Qt", QApplication.aboutQt)

        tab_widget = QTabWidget()
        tab_widget.addTab(self.logged_widget, "ЗАЛОГИРОВАНО")
        tab_widget.addTab(self.activities_widget, "АКТИВНОСТИ")
        tab_widget.setCornerWidget(self.cb_auto_refresh_rss, Qt.TopRightCorner)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.progress_refresh)
        layout_main.addWidget(tab_widget)

        central_widget = QWidget()
        central_widget.setLayout(layout_main)

        self.setCentralWidget(central_widget)

        menu_tray = QMenu()
        menu_tray.addAction(action_about)
        menu_tray.addSeparator()
        menu_tray.addAction(action_exit)

        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip(self.windowTitle())
        self.tray.setContextMenu(menu_tray)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        self.windowTitleChanged.connect(self.tray.setToolTip)

        self._update_window_title()

        self._quit_dont_ask_again: bool = False

        self._last_is_maximized: bool = self.isMaximized()

        # Запуск таймера обновления состояния после инициализации GUI
        self.timer_update_states.start()

    # Функция вызывается в отдельном потоке RunFuncThread
    def _get_data(self) -> bytes | None:
        if self._skip_get_data:
            return

        return get_rss_jira_log(self.username)

    def _update_window_title(self):
        username: str | None = self.username
        if not username:
            username = "<не задано>"

        if self._last_refresh_datetime:
            title = TEMPLATE_WINDOW_TITLE_WITH_REFRESH.format(
                username=username,
                dt=get_human_datetime(self._last_refresh_datetime),
                ago=get_ago(self._last_refresh_datetime),
            )
        else:
            title = TEMPLATE_WINDOW_TITLE_WITH_USERNAME.format(
                username=username,
            )

        self.setWindowTitle(title)

    def _set_error_log(self, e: Exception):
        self.logs.append_exception(e)

    def _fill_tables(self, xml_data: bytes | None):
        if not xml_data:
            return

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

    def _block_ui(self, block: bool):
        self.button_refresh.setEnabled(not block)
        self.progress_refresh.setVisible(block)

    def _before_refresh(self):
        self._block_ui(True)

        for addon_dock in self.addons:
            if addon_dock.addon.is_active and addon_dock.is_auto_refresh():
                addon_dock.refresh()

    def _update_states(self):
        self._update_window_title()

        for addon_dock in self.addons:
            # NOTE: Обновление времени последнего обновления будет и для отключенных
            addon_dock.update_last_refresh_datetime()

        self.about.refresh()

    def _after_refresh(self):
        self._block_ui(False)

        self._last_refresh_datetime = datetime.now()

        self._update_states()

        try:
            self.write_settings()
        except Exception as e:
            self.logs.append_error(f"Ошибка при сохранении конфига: {e}")

    def refresh(self):
        if not self.timer_auto_refresh.isActive():
            self.timer_auto_refresh.start()

        self.logs.append(f"Обновление в {get_human_datetime()}")

        if not self.username:
            loop = QEventLoop()

            def _on_started():
                self._block_ui(True)
                self.logs.append("Имя пользователя не задано. Выполнение запроса к API")

            def _on_finished():
                self._block_ui(False)
                loop.quit()

            def _set_username(value: str):
                self.username = value

                # Сохранение в конфиге, чтобы при следующем запуске не запрашивать его
                CONFIG["username"] = self.username

            thread = RunFuncThread(func=get_jira_current_username)
            thread.started.connect(_on_started)
            thread.run_finished.connect(_set_username)
            thread.about_error.connect(self._set_error_log)
            thread.finished.connect(_on_finished)
            thread.start()

            loop.exec()

        self._update_window_title()

        self._last_refresh_is_forced = (
            # Не ручной вызов метода
            self.sender() is not None
            and self.sender() != self.timer_auto_refresh
        )

        self._skip_get_data = False

        if not self.username:
            self.logs.append("Имя пользователя не задано. Запрос RSS не будет выполнен")
            self._skip_get_data = True

        # Если обновление не было вызвано напрямую и не стоит флаг авто-обновления
        if (
            not self._last_refresh_is_forced
            and not self.cb_auto_refresh_rss.isChecked()
        ):
            self.logs.append(
                f'Флаг "{self.cb_auto_refresh_rss.text()}" отключен. Запрос RSS не будет выполнен'
            )
            self._skip_get_data = True

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
            self.cb_auto_refresh_rss.setChecked(value)

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
                    "auto_refresh": self.cb_auto_refresh_rss.isChecked(),
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

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Context:
            return

        self.setVisible(not self.isVisible())

        if self.isVisible():
            if self._last_is_maximized:
                self.showMaximized()
            else:
                self.showNormal()

            self.activateWindow()

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.WindowStateChange:
            self._last_is_maximized = self.isMaximized()

            # Если окно свернули
            if self.isMinimized():
                # Прячем окно с панели задач
                QTimer.singleShot(0, self.hide)

    def closeEvent(self, event: QCloseEvent):
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
            if reply == QMessageBox.No:
                event.ignore()
                return

            self._quit_dont_ask_again = cb_dont_ask_again.isChecked()

        self.write_settings()

        QApplication.instance().quit()


if __name__ == "__main__":
    with mp.Pool(processes=5) as pool:
        api.POOL = pool

        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # Использование локали на русском в стандартных виджетах
        translator = QTranslator()
        translations_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        if translator.load("qtbase_ru", directory=translations_path):
            app.installTranslator(translator)

        # Использование qss из ресурсов, если он не был задан в аргументах
        if not app.styleSheet():
            app.setStyleSheet(f"file:///{PATH_STYLE_SHEET}")

        mw = MainWindow()
        MAIN_WINDOW = mw

        app.setWindowIcon(mw.windowIcon())

        mw.resize(1200, 800)
        mw.show()

        mw.read_settings()
        mw.refresh()

        sys.exit(app.exec())
