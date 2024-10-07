#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import json
from pathlib import Path


DIR = Path(__file__).resolve().parent
ROOT_DIR = DIR.parent

PATH_FAVICON = DIR / "favicon.png"
PATH_CONFIG = DIR / "config.json"

CONFIG: dict[str, str | int] = json.loads(PATH_CONFIG.read_text("utf-8"))
USERNAME: str = CONFIG["username"]
MAX_RESULTS: int = CONFIG["max_results"]
JIRA_HOST: str = CONFIG["jira_host"]
NAME_CERT: str = CONFIG["name_cert"]  # NOTE: Получение описано в README.md

PATH_CERT = ROOT_DIR / NAME_CERT
if not PATH_CERT.exists():
    raise Exception(f"File {PATH_CERT} not found!")
