#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from config import JIRA_HOST
from api import session


def get_jira_current_username() -> str:
    rs = session.get(f"{JIRA_HOST}/rest/api/latest/myself")
    rs.raise_for_status()

    return rs.json()["name"]


if __name__ == "__main__":
    print(get_jira_current_username())
