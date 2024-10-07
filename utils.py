#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import ssl
import requests
from config import PATH_CERT, JIRA_HOST


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0"
)


session = requests.session()
session.cert = str(PATH_CERT)
session.mount("https://", TLSAdapter())
session.headers["User-Agent"] = USER_AGENT


def get_jira_current_username() -> str:
    rs = session.get(f"{JIRA_HOST}/rest/api/latest/myself")
    rs.raise_for_status()

    return rs.json()["name"]


if __name__ == "__main__":
    # Check
    rs = session.get(f"{JIRA_HOST}/pa-reports/")
    print(rs)
    rs.raise_for_status()

    rs = session.get(f"{JIRA_HOST}/secure/ViewProfile.jspa")
    print(rs)
    rs.raise_for_status()

    print()
    print(get_jira_current_username())
