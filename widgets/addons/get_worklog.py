#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from api.job_report.get_worklog import get_worklog, Worklog
from widgets.addons import AddonWidget

from PyQt5.QtWidgets import QVBoxLayout, QLabel


class AddonGetWorklogWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        # TODO:
        self.setWindowTitle("Get Worklog")

        self.info = QLabel()
        self.info.setWordWrap(True)
        self.info.setFrameStyle(QLabel.Box)  # TODO:

        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # TODO:
        main_layout.addWidget(self.info)

    def get_data(self) -> Worklog:
        return get_worklog()

    def process(self, data: Worklog):
        self.info.setText(str(data))
