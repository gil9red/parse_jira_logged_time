#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import ssl
import traceback
from datetime import datetime, date

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from config import PATH_CERT, JIRA_HOST
from third_party.ago import ago, L10N, UnitSeconds


L10N_RU = L10N(
    singular={
        UnitSeconds.SECOND: "{value} секунда назад",
        UnitSeconds.MINUTE: "{value} минута назад",
        UnitSeconds.HOUR: "{value} час назад",
        UnitSeconds.DAY: "{value} день назад",
        UnitSeconds.WEEK: "{value} неделя назад",
        UnitSeconds.MONTH: "{value} месяц назад",
        UnitSeconds.YEAR: "{value} год назад",
    },
    plural={
        UnitSeconds.SECOND: "{value} секунды назад",
        UnitSeconds.MINUTE: "{value} минуты назад",
        UnitSeconds.HOUR: "{value} часа назад",
        UnitSeconds.DAY: "{value} дня назад",
        UnitSeconds.WEEK: "{value} недели назад",
        UnitSeconds.MONTH: "{value} месяца назад",
        UnitSeconds.YEAR: "{value} года назад",
    },
)


def get_exception_traceback(e: Exception) -> str:
    return "".join(traceback.format_exception(e)).strip()


class RunFuncThread(QThread):
    run_finished = pyqtSignal(object)
    about_error = pyqtSignal(Exception)

    def __init__(self, func):
        super().__init__()

        self.func = func

    def run(self):
        try:
            self.run_finished.emit(self.func())
        except Exception as e:
            self.about_error.emit(e)


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

    def send(self, *args, **kwargs):
        # Установка таймаута в 60 секунд, если оно не было задано
        if not kwargs.get("timeout"):
            kwargs["timeout"] = 60
        return super().send(*args, **kwargs)


DATE_FORMAT: str = "%d.%m.%Y"
TIME_FORMAT: str = "%H:%M:%S"


def get_human_datetime(dt: datetime | None = None) -> str:
    if not dt:
        dt = datetime.now()
    return dt.strftime(f"{DATE_FORMAT} {TIME_FORMAT}")


def get_human_date(d: datetime | date | None = None) -> str:
    if not d:
        d = date.today()
    return d.strftime(DATE_FORMAT)


def get_human_time(dt: datetime | None = None) -> str:
    if not dt:
        dt = datetime.now()
    return dt.strftime(TIME_FORMAT)


def get_ago(dt1: datetime | None = None, dt2: datetime | None = None) -> str:
    if not dt1:
        dt1 = datetime.now()

    if not dt2:
        dt2 = datetime.now()

    return ago(dt2 - dt1, L10N_RU)


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0"
)
session = requests.session()

session.cert = str(PATH_CERT)
session.mount("https://", TLSAdapter())
session.headers["User-Agent"] = USER_AGENT


if __name__ == "__main__":
    # Check
    rs = session.get(f"{JIRA_HOST}/pa-reports/")
    print(rs)
    rs.raise_for_status()

    rs = session.get(f"{JIRA_HOST}/secure/ViewProfile.jspa")
    print(rs)
    rs.raise_for_status()
