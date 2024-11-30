#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time
from typing import Any

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (
    QFormLayout,
    QTextBrowser,
    QVBoxLayout,
)

from api.jira_show_last_issue import get_last_issue_key
from third_party.advanced_list_widget import AdvancedListWidget
from widgets import open_jira, open_jira_project
from widgets.addons import AddonWidget


class AddonGetLastIssueKeyWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Jira. Последние задачи в проектах")

        self.html_viewer = QTextBrowser()
        self.html_viewer.setOpenLinks(False)
        self.html_viewer.anchorClicked.connect(self._anchor_clicked)

        self.list_widget_projects = AdvancedListWidget()
        self.list_widget_projects.setObjectName("projects")
        self.list_widget_projects.set_items(["RADIX", "FLORA"])

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.html_viewer)

    def _anchor_clicked(self, url: QUrl):
        url: str = url.toString()
        if "-" in url:
            open_jira(url)
        else:
            open_jira_project(url)

    def get_data(self) -> list[tuple[str, str | None]]:
        items = []
        for project in self.list_widget_projects.items():
            last_key: str | None = get_last_issue_key(project)
            items.append((project, last_key))
            time.sleep(0.5)

        return items

    def process(self, data: list[tuple[str, str | None]]):
        lines = []

        if data:
            lines.append(
                """
                <style>
                    a {
                        color: inherit;
                    }
                    td.key {
                        padding-right: 10px;
                    }
                </style>
                """
            )
            lines.append("<table>")

            def _get_tag_a(value: str) -> str:
                return f'<a href="{value}">{value}</a>'

            for project, last_key in data:
                lines.append(
                    f"""
                    <tr>
                        <td class="key"><b>{_get_tag_a(project)}</b>:</td>
                        <td>{_get_tag_a(last_key) if last_key else "-"}</td>
                    </tr>
                    """
                )

            lines.append("</table>")

        self.html_viewer.setHtml(
            "".join(lines) if lines else "<b>Проекты не заданы</b>"
        )

    def init_settings(self, settings_layout: QFormLayout):
        settings_layout.addRow("Проекты:", None)
        settings_layout.addRow(self.list_widget_projects)

    def read_settings(self, settings: dict[str, Any] | None):
        if settings is None:
            settings: dict[str, Any] = dict()

        key: str = self.list_widget_projects.objectName()
        items: list[str] = settings.get(key, [])
        self.list_widget_projects.set_items(items)

    def write_settings(self, settings: dict[str, Any]):
        key: str = self.list_widget_projects.objectName()
        settings[key] = self.list_widget_projects.items()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = AddonGetLastIssueKeyWidget()
    w.show()
    w.list_widget_projects.set_items(["RADIX", "FLORA"])
    w.refresh()

    app.exec()
