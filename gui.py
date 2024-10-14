#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import io
import json
import sys
import traceback

from contextlib import redirect_stdout
from datetime import datetime, date
from typing import Any

from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QCheckBox,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSplitter,
    QSystemTrayIcon,
    QProgressBar,
    QSizePolicy,
    QToolTip,
    QTabWidget,
)
from PyQt5.QtCore import (
    QEvent,
    QTimer,
    QByteArray,
)
from PyQt5.QtGui import QTextOption, QIcon

from api import RunFuncThread
from config import VERSION, PATH_FAVICON, PATH_CONFIG, CONFIG
from console import (
    URL,
    USERNAME,  # В модуле его значение может быть переопределено
    Activity,
    get_rss_jira_log,
    seconds_to_str,
    parse_date_by_activities,
    get_logged_total_seconds,
)
from widgets import get_class_name
from widgets.activities_widget import ActivitiesWidget
from widgets.logged_widget import LoggedWidget


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = f"{ex_cls.__name__}: {ex}:\n"
    text += "".join(traceback.format_tb(tb))

    print(text)
    QMessageBox.critical(None, "Error", text)
    sys.exit(1)


sys.excepthook = log_uncaught_exceptions


WINDOW_TITLE: str = f"parse_jira_logged_time v{VERSION}. username={USERNAME}"


def from_base64(state: str) -> QByteArray:
    return QByteArray.fromBase64(state.encode("utf-8"))


def to_base64(state: QByteArray) -> str:
    return state.toBase64().data().decode("utf-8")


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

        self.setWindowTitle(WINDOW_TITLE)

        icon = QIcon(str(PATH_FAVICON))

        self.setWindowIcon(icon)

        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip(self.windowTitle())
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        self.pb_refresh = QPushButton("🔄 REFRESH")
        self.pb_refresh.setObjectName("pb_refresh")
        self.pb_refresh.setShortcut("F5")
        self.pb_refresh.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.pb_refresh.clicked.connect(self.refresh)

        self.progress_refresh = QProgressBar()
        self.progress_refresh.setObjectName("progress_refresh")
        self.progress_refresh.setRange(0, 0)
        self.progress_refresh.setTextVisible(False)
        self.progress_refresh.hide()

        self.cb_show_log = QCheckBox()
        self.cb_show_log.setText("Show log")
        self.cb_show_log.setChecked(False)

        self.timer_auto_refresh = QTimer()
        self.timer_auto_refresh.setInterval(60 * 60 * 1000)  # 1 hour
        self.timer_auto_refresh.timeout.connect(self.refresh)

        self.cb_auto_refresh = QCheckBox()
        self.cb_auto_refresh.setText("Auto")
        self.cb_auto_refresh.setToolTip("Every 1 hour")
        self.cb_auto_refresh.setChecked(True)

        self.cb_auto_refresh.clicked.connect(self.set_auto_refresh)
        if self.cb_auto_refresh.isChecked():
            self.timer_auto_refresh.start()

        self.log = QPlainTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setWordWrapMode(QTextOption.NoWrap)

        self.cb_show_log.clicked.connect(self.log.setVisible)
        self.log.setVisible(self.cb_show_log.isChecked())

        self.thread_get_data = RunFuncThread(func=get_rss_jira_log)
        self.thread_get_data.started.connect(self._before_refresh)
        self.thread_get_data.about_error.connect(self._set_error_log)
        self.thread_get_data.run_finished.connect(self._fill_tables)
        self.thread_get_data.finished.connect(self._after_refresh)

        self.logged_widget = LoggedWidget()
        self.activities_widget = ActivitiesWidget()

        tab_widget = QTabWidget()
        tab_widget.addTab(self.logged_widget, "LOGGED")
        tab_widget.addTab(self.activities_widget, "ACTIVITIES")

        layout_log = QVBoxLayout()
        layout_log.addWidget(self.log)
        layout_log.addWidget(self.cb_show_log)

        layout_content = QVBoxLayout()
        layout_content.addWidget(tab_widget)
        layout_content.addLayout(layout_log)

        layout_refresh = QHBoxLayout()
        layout_refresh.addWidget(self.pb_refresh)
        layout_refresh.addWidget(self.cb_auto_refresh)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_refresh)
        layout_main.addWidget(self.progress_refresh)
        layout_main.addLayout(layout_content)

        central_widget = QWidget()
        central_widget.setLayout(layout_main)

        self.setCentralWidget(central_widget)

        self.setStyleSheet(
            """
            * {
                font-size: 16px;
            }
            #pb_refresh {
                font-size: 18px;
            }
            #progress_refresh {
                min-height: 14px;
                max-height: 14px;
            }
            #log {
                font-family: Courier New;
            }
            """
        )

    def set_auto_refresh(self, checked: bool):
        if checked:
            self.timer_auto_refresh.start()
        else:
            self.timer_auto_refresh.stop()

        pos = self.cb_auto_refresh.geometry().topRight()
        pos = self.mapToGlobal(pos)
        QToolTip.showText(pos, f"Timer {'started' if checked else 'stopped'}")

    def _set_error_log(self, text: str):
        self.log.setPlainText(text)

        # Отображение лога
        self.cb_show_log.setChecked(False)
        self.cb_show_log.click()

    def _fill_tables(self, xml_data: bytes):
        buffer_io = io.StringIO()
        try:
            with redirect_stdout(buffer_io):
                print(f"{URL}\n")
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
                table_header: tuple = ("DATE", "LOGGED", "SECONDS", "ACTIVITIES")
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

                    date_str: str = entry_date.strftime("%d/%m/%Y")
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
            self.log.setPlainText(text)

            print(text)

    def _before_refresh(self):
        self.pb_refresh.setEnabled(False)
        self.progress_refresh.show()

    def _after_refresh(self):
        self.pb_refresh.setEnabled(True)
        self.progress_refresh.hide()

        self.setWindowTitle(
            f"{WINDOW_TITLE}. Last refresh date: {datetime.now():%d/%m/%Y %H:%M:%S}"
        )
        self.tray.setToolTip(self.windowTitle())

    def refresh(self):
        # Если обновление уже запущено
        if self.thread_get_data.isRunning():
            return

        self.thread_get_data.start()

    def read_settings(self):
        config_gui: dict[str, Any] | None = CONFIG.get("gui")
        if config_gui:
            geometry = from_base64(config_gui["MainWindow"]["geometry"])
            self.restoreGeometry(geometry)

            state = from_base64(config_gui["MainWindow"]["state"])
            self.restoreState(state)

            for child in [self.logged_widget, self.activities_widget]:
                child_name = get_class_name(child)
                read_settings_children(
                    child,
                    config_gui.get(child_name),
                )

    def write_settings(self):
        with open(PATH_CONFIG, "w") as f:
            CONFIG["gui"] = {
                "MainWindow": {
                    "state": to_base64(self.saveState()),
                    "geometry": to_base64(self.saveGeometry()),
                },
            }

            for child in [self.logged_widget, self.activities_widget]:
                child_config: dict[str, Any] = dict()
                write_settings_children(child, child_config)

                child_name = get_class_name(child)
                CONFIG["gui"][child_name] = child_config

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
        reply = QMessageBox.question(
            self,
            "Quit",
            "Are you sure you want to quit?",
            QMessageBox.Yes,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            event.ignore()
            return

        self.write_settings()


if __name__ == "__main__":
    app = QApplication([])

    mw = MainWindow()
    mw.resize(1200, 800)
    mw.read_settings()
    mw.show()

    mw.refresh()

    app.exec()
