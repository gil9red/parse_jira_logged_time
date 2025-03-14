#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import re
import xml.etree.ElementTree as ET

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date, timezone

from config import USERNAME, MAX_RESULTS, JIRA_HOST
from api import session, get_human_date
from api.jira import get_jira_current_username
from third_party.decode_escapes_telegram_bot.utils import decode
from third_party.jira_logged_human_time_to_seconds import logged_human_time_to_seconds
from third_party.seconds_to_str import seconds_to_str


PATTERN_TAGS: re.Pattern = re.compile("<.*?>")
PATTERN_SPACES: re.Pattern = re.compile(r"\s{2,}")


def get_clean_html(raw_html: str) -> str:
    text = PATTERN_TAGS.sub("", raw_html)
    text = PATTERN_SPACES.sub(" ", text).strip()
    return decode(text)


class ActivityActionEnum(enum.Enum):
    COMMENTED = enum.auto()
    UPDATED = enum.auto()
    CHANGED = enum.auto()
    ADDED = enum.auto()
    REMOVED = enum.auto()
    STARTED_PROGRESS = enum.auto()
    STOPPED_PROGRESS = enum.auto()
    ATTACHED = enum.auto()
    LOGGED = enum.auto()
    LINKED = enum.auto()
    RESOLVED = enum.auto()
    CREATED = enum.auto()
    REDUCED = enum.auto()
    REOPENED = enum.auto()
    UNKNOWN = enum.auto()


@dataclass
class Logged:
    human_time: str
    seconds: int
    description: str | None = None


@dataclass
class Activity:
    id: str
    entry_dt: datetime
    action: ActivityActionEnum
    action_text: str
    jira_id: str
    jira_title: str
    logged: Logged | None = None
    link_to_comment: str | None = None

    def is_logged(self) -> bool:
        return self.logged is not None


# SOURCE: https://stackoverflow.com/a/13287083/5909792
def utc_to_local(utc_dt: datetime) -> datetime:
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

MAX_RESULTS = 250

def get_rss_jira_log(username: str | None = USERNAME) -> bytes:
    if not username:
        username = get_jira_current_username()

    url: str = (
        f"{JIRA_HOST}/activity?maxResults={MAX_RESULTS}"
        f"&streams=user+IS+{username}&os_authType=basic&title=undefined"
    )
    print(url)

    rs = session.get(url)
    rs.raise_for_status()
    return rs.content


def get_rss_jira_log_v2(dt1, dt2, username: str | None = USERNAME) -> bytes:
    if not username:
        username = get_jira_current_username()

    url: str = (
        f"{JIRA_HOST}/activity?maxResults={MAX_RESULTS}&streams=user+IS+{username}"
        f"&streams=update-date+BETWEEN+{to_ms(dt1)}+{to_ms(dt2)}"
        "&os_authType=basic&title=undefined"
    )
    print(url)

    rs = session.get(url)
    rs.raise_for_status()

    from pathlib import Path
    Path(f"{dt1.date().isoformat()}-{dt2.date().isoformat()}.xml").write_bytes(rs.content)

    return rs.content


def get_date_by_activities(root) -> dict[date, list[Activity]]:
    ns = {
        "": "http://www.w3.org/2005/Atom",
        "activity": "http://activitystrea.ms/spec/1.0/",
    }

    def _get_text(el, xpath: str) -> str:
        return el.find(xpath, namespaces=ns).text.strip()

    def _get_activity_action(text: str) -> ActivityActionEnum:
        text = text.lower()
        for action in ActivityActionEnum:
            if action == ActivityActionEnum.UNKNOWN:
                continue

            if re.search(f" {action.name.lower().replace('_', ' ')} ", text):
                return action

        return ActivityActionEnum.UNKNOWN

    result: dict[date, list[Activity]] = defaultdict(list)

    pattern_logged = re.compile("logged '(.+?)'", flags=re.IGNORECASE)

    for entry in root.findall("./entry", namespaces=ns):
        id: str = _get_text(entry, "./id")

        title: str = _get_text(entry, "./title")

        # Удаление тегов HTML, лишних пробелов
        title = get_clean_html(title)

        action: ActivityActionEnum = _get_activity_action(title)

        # Ищем в <entry> строку с логированием
        if m := pattern_logged.search(
            # Не всегда у title есть строка с логами
            # Если несколько полей менялось, то инфа по залогированному будет в другом теге
            "".join(entry.itertext())
        ):
            logged_human_time = m.group(1)
            logged_seconds = logged_human_time_to_seconds(logged_human_time)
        else:
            logged_human_time = logged_seconds = None

        logged_description = None
        if action == ActivityActionEnum.LOGGED:
            content_el = entry.find("./content", namespaces=ns)
            if content_el is not None:
                logged_description = get_clean_html(content_el.text)

        if logged_seconds:
            logged = Logged(
                human_time=logged_human_time,
                seconds=logged_seconds,
                description=logged_description,
            )
        else:
            logged = None

        try:
            jira_id = _get_text(entry, "./activity:object/title")
            jira_title = _get_text(entry, "./activity:object/summary")
        except:
            jira_id = _get_text(entry, "./activity:target/title")
            jira_title = _get_text(entry, "./activity:target/summary")

        link_to_comment: str | None = None
        for el in entry.findall("./link[@href]", namespaces=ns):
            href = el.attrib["href"]
            if "focusedCommentId=" in href:
                link_to_comment = href
                break

        # Переменная entry_dt имеет время в UTC, и желательно его привести в локальное время
        entry_dt = datetime.strptime(
            _get_text(entry, "./published"),
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
        entry_dt = utc_to_local(entry_dt)
        entry_date = entry_dt.date()

        result[entry_date].append(
            Activity(
                id=id,
                entry_dt=entry_dt,
                action=action,
                action_text=title,
                jira_id=jira_id,
                jira_title=jira_title,
                logged=logged,
                link_to_comment=link_to_comment,
            )
        )
        # print(result[entry_date][-1])

    return result


def parse_date_by_activities(xml_data: bytes) -> dict[date, list[Activity]]:
    root = ET.fromstring(xml_data)
    return get_date_by_activities(root)


def get_logged_total_seconds(activities: list[Activity]) -> int:
    return sum(obj.logged.seconds for obj in activities if obj.logged)


if __name__ == "__main__":
    # t = datetime.now()
    # print(t)
    #
    # xml_data = get_rss_jira_log()
    # print(len(xml_data), repr(xml_data[:50]))
    # print()
    #
    # # Структура документа - xml
    # date_by_activities: dict[date, list[Activity]] = parse_date_by_activities(xml_data)
    # # print(date_by_activities)
    # # print()
    #
    # # Для красоты выводим результат в табличном виде
    # lines = [
    #     ("DATE", "LOGGED", "SECONDS", "ACTIVITIES"),
    # ]
    # total_activities = 0
    # for entry_date, activities in sorted(
    #     date_by_activities.items(), key=lambda x: x[0], reverse=True
    # ):
    #     total_activities += len(activities)
    #
    #     total_seconds: int = get_logged_total_seconds(activities)
    #     total_seconds_str: str = seconds_to_str(total_seconds)
    #
    #     date_str: str = get_human_date(entry_date)
    #     lines.append((date_str, total_seconds_str, total_seconds, len(activities)))
    #
    # # Список строк станет списком столбцов, у каждого столбца подсчитается максимальная длина
    # max_len_columns = [max(map(len, map(str, col))) for col in zip(*lines)]
    #
    # # Создание строки форматирования: [30, 14, 5] -> "{:<30} | {:<14} | {:<5}"
    # my_table_format = " | ".join("{:<%s}" % max_len for max_len in max_len_columns)
    #
    # for line in lines:
    #     print(my_table_format.format(*line))
    #
    # print("total_activities:", total_activities)
    # print(datetime.now(), datetime.now() - t)
    # print('\n\n')

    total_activities = 0

    from datetime import datetime, timedelta


    def get_zero_time(dt: datetime) -> datetime:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)


    def get_items(
        start_dt: datetime,
        end_dt: datetime,
        delta: timedelta,
    ) -> list[tuple[datetime, datetime]]:
        print(f"[get_items] start_dt: {start_dt}, end_dt: {end_dt}, delta: {delta}")
        items = []

        dt = end_dt
        while True:
            if dt <= start_dt:
                break

            dt1 = dt
            dt -= delta

            if dt < start_dt:
                dt = start_dt

            items.append((dt, dt1))

        return items


    def to_ms(dt: datetime) -> int:
        return int(dt.timestamp() * 1000)


    # dt = get_zero_time(datetime.utcnow())
    # print(dt)
    dt = get_zero_time(datetime.now())
    print(dt)
    # 2024-12-04 00:00:00

    for dt1, dt2 in get_items(
        # start_dt=get_zero_time(dt - timedelta(weeks=12)),
        # start_dt=get_zero_time(dt - timedelta(weeks=4)),
        start_dt=dt,
        end_dt=get_zero_time(dt + timedelta(days=1)),
        delta=timedelta(weeks=1),
    ):
        t = datetime.now()
        # print(t)

        print(f"{dt1} - {dt2}. {to_ms(dt1)}+{to_ms(dt2)}")

        xml_data = get_rss_jira_log_v2(dt1, dt2)
        print(len(xml_data), repr(xml_data[:50]))
        print()

        # Структура документа - xml
        date_by_activities: dict[date, list[Activity]] = parse_date_by_activities(xml_data)
        # print(date_by_activities)
        # print()

        # Для красоты выводим результат в табличном виде
        lines = [
            ("DATE", "LOGGED", "SECONDS", "ACTIVITIES"),
        ]
        for entry_date, activities in sorted(
            date_by_activities.items(), key=lambda x: x[0], reverse=True
        ):
            total_activities += len(activities)
            total_seconds: int = get_logged_total_seconds(activities)
            total_seconds_str: str = seconds_to_str(total_seconds)

            date_str: str = get_human_date(entry_date)
            lines.append((date_str, total_seconds_str, total_seconds, len(activities)))

        # Список строк станет списком столбцов, у каждого столбца подсчитается максимальная длина
        max_len_columns = [max(map(len, map(str, col))) for col in zip(*lines)]

        # Создание строки форматирования: [30, 14, 5] -> "{:<30} | {:<14} | {:<5}"
        my_table_format = " | ".join("{:<%s}" % max_len for max_len in max_len_columns)

        print()

        for line in lines:
            print(my_table_format.format(*line))

        print()
        print("total_activities:", total_activities)
        print(datetime.now(), datetime.now() - t)

        print("\n" + "-" * 100 + "\n")
