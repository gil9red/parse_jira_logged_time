#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import ssl
import traceback

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from config import PATH_CERT, JIRA_HOST


class RunFuncThread(QThread):
    run_finished = pyqtSignal(object)
    about_error = pyqtSignal(str)

    def __init__(self, func):
        super().__init__()

        self.func = func

    def run(self):
        try:
            self.run_finished.emit(self.func())
        except Exception as e:
            print(f"Error: {e}")
            self.about_error.emit(traceback.format_exc())


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
