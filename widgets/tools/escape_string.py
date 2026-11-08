#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from third_party.tools.EscapeString.main import MainWindow
from widgets.tools import ToolWidget


class EscapeStringToolWidget(MainWindow, ToolWidget):
    @property
    def title(self) -> str:
        return "Escape String"
