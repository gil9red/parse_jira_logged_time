#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import importlib
import sys

from pathlib import Path

from PyQt5.QtWidgets import QTextBrowser

from config import DIR


PATH_REQUIREMENTS_DEV: Path = DIR / "requirements-dev.txt"


def is_installed(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ModuleNotFoundError:
        return False


def get_module_from_requirements(module_name: str) -> str | None:
    if not PATH_REQUIREMENTS_DEV.exists():
        return

    for line in PATH_REQUIREMENTS_DEV.read_text("utf-8").splitlines():
        if line.startswith(module_name):
            return line


def get_not_module_widget(
    module_name: str,
    text_template: str = "Для работы аддона нужно установить {name} и перезапустить приложение",
) -> QTextBrowser:
    name: str | None = get_module_from_requirements(module_name)
    if not name:
        name = module_name

    html_text = f"""
        <p>
            <b><font color="red">
            {text_template.format(name=name)}
            </font></b>
        </p>
        <p>Команда:</p>
        <p>{sys.executable} -m pip install {name}</p>
    """

    text_browser = QTextBrowser()
    text_browser.setHtml(html_text)

    return text_browser


if __name__ == "__main__":
    print(is_installed("psutil"))
    # False

    print(get_module_from_requirements("psutil"))
    # psutil==6.1.0
