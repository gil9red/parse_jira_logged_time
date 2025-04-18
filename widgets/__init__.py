#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
import textwrap
import webbrowser

from contextlib import contextmanager
from typing import Any, Callable

from PyQt5.QtCore import Qt, QObject, QPoint, QModelIndex, QAbstractItemModel
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (
    QApplication,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
    QWidget,
    QAction,
    QTableView,
    QMenu,
)

from api.jira_rss import Activity
from config import JIRA_HOST


@contextmanager
def block_signals(obj: QObject):
    obj.blockSignals(True)
    try:
        yield
    finally:
        obj.blockSignals(False)


def get_cell_value(model: QAbstractItemModel, row: int, column: int) -> str:
    idx: QModelIndex = model.index(row, column)
    return str(model.data(idx, role=Qt.ItemDataRole.EditRole))


def open_context_menu(
    table: QTableView,
    p: QPoint,
    get_additional_actions_func: Callable[[QTableView, int], list[QAction]] = None,
):
    index: QModelIndex = table.indexAt(p)
    if not index.isValid():
        return

    menu = QMenu(table)

    current_row: int = index.row()

    model = table.model()
    column_count: int = model.columnCount()

    def _copy_to_clipboard(value: str):
        QApplication.clipboard().setText(value)

    def _shorten(text: str) -> str:
        return textwrap.shorten(text, width=50)

    def _get_row_as_str(row: int) -> str:
        return "\t".join(
            get_cell_value(model, row, column) for column in range(column_count)
        )

    def _get_table_as_str() -> str:
        return "\n".join(_get_row_as_str(row) for row in range(model.rowCount()))

    value: str = get_cell_value(model, current_row, index.column())
    if value:
        menu.addAction(
            f'Скопировать "{_shorten(value)}"',
            lambda value=value: _copy_to_clipboard(value),
        )

    menu_copy_from = menu.addMenu("Скопировать из")

    for column in range(column_count):
        value: str = get_cell_value(model, current_row, column)

        action = menu_copy_from.addAction(
            model.headerData(column, Qt.Horizontal),
            lambda value=value: _copy_to_clipboard(value),
        )
        action.setEnabled(bool(value))

    menu_copy_from.addSeparator()
    menu_copy_from.addAction(
        "<Текущая строка>",
        lambda: _copy_to_clipboard(_get_row_as_str(current_row)),
    )
    menu_copy_from.addAction(
        "<Все строки>",
        lambda: _copy_to_clipboard(_get_table_as_str()),
    )

    if get_additional_actions_func:
        if actions := get_additional_actions_func(table, current_row):
            menu.addSeparator()
            menu.addActions(actions)

    menu.exec(table.viewport().mapToGlobal(p))


def web_browser_open(url: str):
    webbrowser.open(url)


def create_table(header_labels: list[str]) -> QTableWidget:
    table_widget = QTableWidget()
    table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
    table_widget.setSelectionBehavior(QTableWidget.SelectRows)
    table_widget.setSelectionMode(QTableWidget.SingleSelection)
    table_widget.setColumnCount(len(header_labels))
    table_widget.setHorizontalHeaderLabels(header_labels)
    table_widget.horizontalHeader().setStretchLastSection(True)

    p = table_widget.palette()
    p.setColor(
        QPalette.Inactive,
        QPalette.Highlight,
        p.color(QPalette.Active, QPalette.Highlight),
    )
    table_widget.setPalette(p)

    table_widget.setContextMenuPolicy(Qt.CustomContextMenu)

    def _get_additional_actions(table: QTableView, row: int) -> list[QAction]:
        model = table.model()

        actions = []
        for column in range(model.columnCount()):
            value: str = get_cell_value(model, row, column)

            # NOTE: Поиск строки вида "FOO-123"
            m = re.search(r"^(\w+)-\d+", value)
            if not m:
                continue

            jira_key: str = m.group(0)
            project: str = m.group(1)

            action_open_jira = QAction(f'Открыть "{jira_key}"')
            action_open_jira.triggered.connect(lambda: open_jira(jira_key))
            actions.append(action_open_jira)

            action_open_jira_project = QAction(f'Открыть "{project}"')
            action_open_jira_project.triggered.connect(
                lambda: open_jira_project(project)
            )
            actions.append(action_open_jira_project)

        activity: Activity | None = get_activity_from_row(table.model(), row)
        if activity and activity.link_to_comment:
            action_open_comment = QAction("Открыть комментарий")
            action_open_comment.triggered.connect(
                lambda: web_browser_open(activity.link_to_comment)
            )
            actions.append(action_open_comment)

        return actions

    table_widget.customContextMenuRequested.connect(
        lambda p: open_context_menu(table_widget, p, _get_additional_actions)
    )

    return table_widget


def create_table_item(
    text: str,
    tool_tip: str | None = None,
    data: Any = None,
) -> QTableWidgetItem:
    item = QTableWidgetItem(text)

    if tool_tip:
        item.setToolTip(tool_tip)

    if data:
        item.setData(Qt.UserRole, data)

    return item


def get_activity_from_row(model: QAbstractItemModel, row: int) -> Activity | None:
    idx = model.index(row, 0)
    value = model.data(idx, role=Qt.UserRole)

    return value if isinstance(value, Activity) else None


def add_table_row(table: QTableWidget, items: list[QTableWidgetItem]):
    row = table.rowCount()
    table.setRowCount(row + 1)
    for j, item in enumerate(items):
        table.setItem(row, j, item)


def clear_table(table_widget: QTableWidget):
    # Удаление строк таблицы
    while table_widget.rowCount():
        table_widget.removeRow(0)


def open_jira(jira_id: str):
    url = f"{JIRA_HOST}/browse/{jira_id}"
    web_browser_open(url)


def open_jira_project(project: str):
    url = f"{JIRA_HOST}/projects/{project}"
    web_browser_open(url)


def get_scroll_area(widget: QWidget) -> QScrollArea:
    scroll_area = QScrollArea()
    scroll_area.setFrameStyle(QScrollArea.NoFrame)
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(widget)

    return scroll_area


def get_class_name(obj: Any) -> str:
    return obj.__class__.__name__
