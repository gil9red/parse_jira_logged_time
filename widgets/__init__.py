#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import webbrowser

from contextlib import contextmanager
from typing import Any

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

from config import JIRA_HOST


@contextmanager
def block_signals(obj: QObject):
    obj.blockSignals(True)
    try:
        yield
    finally:
        obj.blockSignals(False)


def create_table(header_labels: list[str]) -> QTableWidget:
    table_widget = QTableWidget()
    table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
    table_widget.setSelectionBehavior(QTableWidget.SelectRows)
    table_widget.setSelectionMode(QTableWidget.SingleSelection)
    table_widget.setColumnCount(len(header_labels))
    table_widget.setHorizontalHeaderLabels(header_labels)
    table_widget.horizontalHeader().setStretchLastSection(True)

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


def get_class_name(obj: Any) -> str:
    return obj.__class__.__name__
