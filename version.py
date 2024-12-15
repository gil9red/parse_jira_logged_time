#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from config import PATH_CHANGELOG


PATTERN_VERSION: re.Pattern = re.compile(r"^## \[(\d+)\.(\d+)\.(\d+)] - (.+)$")


# Получение версии из CHANGELOG.md
def get_version() -> str:
    is_dev: bool = False

    # NOTE: Перебор строк вида "## [Unreleased]" и "## [1.7.0] - 2024-12-09"
    with open(PATH_CHANGELOG, encoding="UTF-8") as f:
        for line in f:
            if not line.startswith("## ["):
                continue

            if "UNRELEASED" in line.upper():
                is_dev = True
                continue

            m = PATTERN_VERSION.match(line)
            if not m:
                continue

            groups: tuple[str, ...] = m.groups()
            major, minor, patch = map(int, groups[:3])
            date_str = groups[3]

            if is_dev:
                minor += 1

            return f"{major}.{minor}.{patch}{'-dev' if is_dev else ''}+{date_str}"

    raise Exception(f"Не удалось найти версию в {PATH_CHANGELOG}")


# NOTE: "1.8.0-dev+2024-12-09" и "1.7.0+2024-12-09"
VERSION: str = get_version()


if __name__ == "__main__":
    print(VERSION)
