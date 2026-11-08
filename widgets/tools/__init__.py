#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import traceback

from inspect import isclass
from typing import Type

from PyQt6.QtGui import QAction, QCloseEvent, QShowEvent
from PyQt6.QtWidgets import QWidget, QMessageBox

from widgets import get_class_name, import_submodules


class ToolWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._toggle_view_action: QAction | None = None

    @property
    def name(self) -> str:
        return get_class_name(self)

    @property
    def title(self) -> str:
        return self.windowTitle()

    def toggleViewAction(self) -> QAction:
        if self._toggle_view_action is None:
            self._toggle_view_action = QAction(self.title, self)
            self._toggle_view_action.setCheckable(True)
            self._toggle_view_action.setChecked(self.isVisible())
            self._toggle_view_action.triggered.connect(self._on_toggle_triggered)

        return self._toggle_view_action

    def _on_toggle_triggered(self, checked: bool) -> None:
        if checked:
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.hide()

    def _update_action_state(self, is_visible: bool) -> None:
        if self._toggle_view_action is not None:
            self._toggle_view_action.blockSignals(True)
            self._toggle_view_action.setChecked(is_visible)
            self._toggle_view_action.blockSignals(False)

    def showEvent(self, event: QShowEvent | None) -> None:
        super().showEvent(event)
        self._update_action_state(True)

    def closeEvent(self, event: QCloseEvent | None) -> None:
        super().closeEvent(event)
        self._update_action_state(False)


def import_all_tool_classes(package: str = __name__) -> list[Type[ToolWidget]]:
    items = []

    for module in import_submodules(package).values():
        # Перебор списка объектов в модуле
        for name in dir(module):
            obj = getattr(module, name)
            if not isclass(obj) or obj is ToolWidget or not issubclass(obj, ToolWidget):
                continue

            try:
                items.append(obj)
            except Exception as e:
                msg_box = QMessageBox(
                    QMessageBox.Icon.Warning,
                    "Ошибка при загрузке инструмента",
                    f"Ошибка при загрузке инструмента {name}: {e}",
                )
                msg_box.setDetailedText(traceback.format_exc())
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()

    return items
