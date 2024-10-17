#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from api.job_report.get_time_spent_in_office import get_time_spent_in_office, TimeSpent
from widgets.addons import AddonWidget

from PyQt5.QtWidgets import QVBoxLayout, QLabel


class AddonGetTimeSpentNnOfficeWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Time spent in office")

        self.info = QLabel()
        self.info.setWordWrap(True)
        self.info.setFrameStyle(QLabel.Box)  # TODO:

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # TODO:
        main_layout.addWidget(self.info)

    def get_data(self) -> TimeSpent:
        return get_time_spent_in_office()

    def process(self, data: TimeSpent):
        self.info.setText(str(data))
