#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import json
import shutil

from pathlib import Path
from typing import Any


VERSION: str = "1.3.0"
PROGRAM_NAME: str = "parse_jira_logged_time"

GITHUB_PROJECT: str = "https://github.com/gil9red/parse_jira_logged_time"

# Текущая папка со скриптом
DIR: Path = Path(__file__).resolve().parent

PATH_RESOURCES: Path = DIR / "resources"
PATH_FAVICON: Path = PATH_RESOURCES / "favicon.png"
PATH_STYLE_SHEET: Path = PATH_RESOURCES / "style.qss"
PATH_EXAMPLES_CONFIG: Path = PATH_RESOURCES / "examples" / "config.json"

PATH_CHANGELOG: Path = DIR / "CHANGELOG.md"
PATH_README: Path = DIR / "README.md"

PATH_CONFIG: Path = DIR / "config.json"
if not PATH_CONFIG.exists():
    print(f"Не найден файл конфига {PATH_CONFIG}")

    if not PATH_EXAMPLES_CONFIG.exists():
        raise FileNotFoundError(PATH_EXAMPLES_CONFIG)

    print(f"Файл конфига скопирован из примера {PATH_EXAMPLES_CONFIG}")
    shutil.copy(PATH_EXAMPLES_CONFIG, PATH_CONFIG)

CONFIG: dict[str, Any] = json.loads(PATH_CONFIG.read_text("utf-8"))
USERNAME: str | None = CONFIG.get("username")
MAX_RESULTS: int = CONFIG["max_results"]
JIRA_HOST: str = CONFIG["jira_host"]
NAME_CERT: str = CONFIG["name_cert"]  # NOTE: Получение описано в README.md

PATH_CERT = DIR / NAME_CERT
if not PATH_CERT.exists():
    raise Exception(f"File {PATH_CERT} not found!")
