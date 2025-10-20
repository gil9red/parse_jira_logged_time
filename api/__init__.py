#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
import subprocess
import sys

from datetime import datetime, date
from multiprocessing.pool import Pool
from pathlib import Path

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from config import PATH_CERT, JIRA_HOST, PATH_README
from third_party.ago import ago, L10N_RU


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


POOL: Pool | None = None


class CustomAdapter(requests.adapters.HTTPAdapter):
    timeout: int = 60
    max_attempts: int = 3

    def send(self, *args, **kwargs) -> requests.Response:
        # Установка таймаута, если оно не было задано
        if not kwargs.get("timeout"):
            kwargs["timeout"] = self.timeout

        # В дочернем процессе будет None
        if POOL:
            last_error: Exception | None = None
            for _ in range(self.max_attempts):
                try:
                    apply = POOL.apply_async(super().send, args=args, kwds=kwargs)
                    return apply.get(timeout=self.timeout)

                except Exception as e:
                    last_error = e

            raise last_error

        return super().send(*args, **kwargs)


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0"
)

session = requests.session()
session.cert = str(PATH_CERT)
session.mount("https://", CustomAdapter())
session.mount("http://", CustomAdapter())
session.headers["User-Agent"] = USER_AGENT


# Проверка сертификата
# TODO: Добавить бы проверку в CustomAdapter.send - по-крайней мере, при запущенном приложении,
#       сертификат может устареть и будут 400 ошибки
try:
    rs = session.get(JIRA_HOST)
    rs.raise_for_status()

except requests.exceptions.HTTPError as e:
    # Ошибка "400 Client Error: Bad Request" на GET-запрос по базовому адресу
    # похожа на проблему устаревшего сертификата
    if e.response.status_code == 400:
        print(
            f'[#] HTTP Error. Вероятно, используется устаревший сертификат в "{PATH_CERT}"\n'
            f'Инструкция по сертификату есть в "{PATH_README}"'
        )

    raise e

except requests.exceptions.SSLError as e:
    print(
        f'[#] SSL Error. Вероятно, используется невалидный или устаревший сертификат в "{PATH_CERT}"\n'
        f'Инструкция по сертификату есть в "{PATH_README}"'
    )
    raise e


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

    return ago(dt2 - dt1, l10n=L10N_RU())


def start_file(file_name: Path | str):
    if isinstance(file_name, Path):
        file_name = str(file_name)

    if sys.platform == "win32":
        os.startfile(file_name)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, file_name])


if __name__ == "__main__":
    # Check
    rs = session.get(f"{JIRA_HOST}/pa-reports/")
    print(rs)
    rs.raise_for_status()

    rs = session.get(f"{JIRA_HOST}/secure/ViewProfile.jspa")
    print(rs)
    rs.raise_for_status()
