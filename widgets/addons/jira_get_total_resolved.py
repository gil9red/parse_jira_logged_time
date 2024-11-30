#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from PyQt5.QtWidgets import (
    QTextBrowser,
    QVBoxLayout,
)

from api.jira_get_total_resolved import (
    JQL_TOTAL,
    JQL_LAST_YEAR,
    JQL_LAST_MONTH,
    JQL_LAST_WEEK,
    Stats,
    get_stats,
)
from config import JIRA_HOST
from widgets.addons import AddonWidget


class AddonGetTotalResolvedWidget(AddonWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Jira. Статистика закрытых задач")

        self.html_viewer = QTextBrowser()
        self.html_viewer.setOpenExternalLinks(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.html_viewer)

    def get_data(self) -> Stats:
        return get_stats()

    def process(self, data: Stats):
        def _get_tag_a(title: str, url: str) -> str:
            return f'<a href="{url}">{title}</a>'

        def _get_tr(title: str, number: int, jql: str) -> str:
            url: str = f"{JIRA_HOST}/issues/?jql={jql} ORDER BY resolved ASC"
            return f"""
            <tr>
                <td class="key"><b>{title}</b>:</td>
                <td>{_get_tag_a(str(number), url)}</td>
            </tr>
            """

        style = """
            <style>
                a {
                    color: inherit;
                }
                td.key {
                    padding-right: 10px;
                }
            </style>
        """
        html = f"""
            {style}
            <table>
                {_get_tr("Неделя", data.last_7_days, JQL_LAST_WEEK)}
                {_get_tr("Месяц", data.last_month, JQL_LAST_MONTH)}
                {_get_tr("Год", data.last_year, JQL_LAST_YEAR)}
                {_get_tr("Всего", data.total, JQL_TOTAL)}
            </table>
        """

        self.html_viewer.setHtml(html)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    w = AddonGetTotalResolvedWidget()
    w.show()
    w.refresh()

    app.exec()
