#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
import webbrowser

from contextlib import contextmanager
from typing import Any, Callable

from PyQt5.QtCore import Qt, QObject, QPoint, QModelIndex
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

from config import JIRA_HOST


@contextmanager
def block_signals(obj: QObject):
    obj.blockSignals(True)
    try:
        yield
    finally:
        obj.blockSignals(False)


def open_context_menu(
    table: QTableView,
    p: QPoint,
    get_additional_actions_func: Callable[[QTableView, int], list[QAction]] = None,
):
    index: QModelIndex = table.indexAt(p)
    if not index.isValid():
        return

    menu = QMenu(table)

    row: int = index.row()
    model = table.model()

    for column in range(model.columnCount()):
        title = model.headerData(column, Qt.Horizontal)

        idx: QModelIndex = model.index(row, column)
        value: str = str(model.data(idx))

        action = menu.addAction(
            f'Скопировать из "{title}"',
            lambda value=value: QApplication.clipboard().setText(value),
        )
        action.setEnabled(bool(value))

    if get_additional_actions_func:
        if actions := get_additional_actions_func(table, row):
            menu.addSeparator()
            menu.addActions(actions)

    menu.exec(table.viewport().mapToGlobal(p))


def create_table(header_labels: list[str]) -> QTableWidget:
    table_widget = QTableWidget()
    table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
    table_widget.setSelectionBehavior(QTableWidget.SelectRows)
    table_widget.setSelectionMode(QTableWidget.SingleSelection)
    table_widget.setColumnCount(len(header_labels))
    table_widget.setHorizontalHeaderLabels(header_labels)
    table_widget.horizontalHeader().setStretchLastSection(True)

    table_widget.setContextMenuPolicy(Qt.CustomContextMenu)

    def _get_additional_actions(table: QTableView, row: int) -> list[QAction]:
        model = table.model()

        actions = []
        for column in range(model.columnCount()):
            idx = model.index(row, column)
            value: str = str(model.data(idx))

            # NOTE: Поиск строки вида "FOO-123"
            m = re.search(r"^\w+-\d+", value)
            if not m:
                continue

            jira_key: str = m.group(0)

            action_open_jira = QAction(f'Открыть "{jira_key}"')
            action_open_jira.triggered.connect(lambda: open_jira(jira_key))

            actions.append(action_open_jira)

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
    webbrowser.open(url)


def get_scroll_area(widget: QWidget) -> QScrollArea:
    scroll_area = QScrollArea()
    scroll_area.setFrameStyle(QScrollArea.NoFrame)
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(widget)

    return scroll_area


def get_class_name(obj: Any) -> str:
    return obj.__class__.__name__
