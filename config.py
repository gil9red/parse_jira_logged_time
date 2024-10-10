#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import json
import shutil

from pathlib import Path


VERSION: str = "1.0.0"

# Текущая папка со скриптом
DIR = Path(__file__).resolve().parent

PATH_FAVICON = DIR / "favicon.png"

PATH_ETC_EXAMPLES_CONFIG = DIR / "etc" / "examples" / "config.json"
PATH_CONFIG = DIR / "config.json"
if not PATH_CONFIG.exists():
    print(f"Не найден файл конфига {PATH_CONFIG}")

    if not PATH_ETC_EXAMPLES_CONFIG.exists():
        raise FileNotFoundError(PATH_ETC_EXAMPLES_CONFIG)

    print(f"Файл конфига скопирован из примера {PATH_ETC_EXAMPLES_CONFIG}")
    shutil.copy(PATH_ETC_EXAMPLES_CONFIG, PATH_CONFIG)

CONFIG: dict[str, str | int] = json.loads(PATH_CONFIG.read_text("utf-8"))
USERNAME: str | None = CONFIG["username"]
MAX_RESULTS: int = CONFIG["max_results"]
JIRA_HOST: str = CONFIG["jira_host"]
NAME_CERT: str = CONFIG["name_cert"]  # NOTE: Получение описано в README.md

PATH_CERT = DIR / NAME_CERT
if not PATH_CERT.exists():
    raise Exception(f"File {PATH_CERT} not found!")
