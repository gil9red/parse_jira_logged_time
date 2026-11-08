#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from third_party.tools.hex2str.gui import Widget
from widgets.tools import ToolWidget


class Hex2StrToolWidget(Widget, ToolWidget):
    @property
    def title(self) -> str:
        return "Hex -> Str"
