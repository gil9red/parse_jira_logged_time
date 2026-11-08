#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from third_party.tools.gui_base64 import MainWindow
from widgets.tools import ToolWidget


class Base64ToolWidget(MainWindow, ToolWidget):
    @property
    def title(self) -> str:
        return "Base64"
