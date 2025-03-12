#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re


PATTERN_ARG: re.Pattern = re.compile(r"<(\w+)>")
PATTERN_RESULT: re.Pattern = re.compile(r"<=([\w +]+)>")

DEFAULT_ARG_VALUE: str = "NaN"

SAMPLE_TEMPLATE = """
*Итоговая трудоемкость в человеко-днях:* <=a+b+c+d+e> ч/д, в том числе:
|Аналитика (проектирование/техническая спецификация)|<a> ч/д|
|Разработка (программирование)|<b> ч/д|
|Рецензирование решения и кода|<c> ч/д|
|Тестирование (только силами разработчика)|<d> ч/д|
|Резерв на непредвиденные работы и риски|<e> ч/д|

*Total efforts in man-days:* <= a+b+c+d+e> m/d, including:
|Analysis (design and tech specs)|<a> m/d|
|Implementation (including coding)|<b> m/d|
|Code and solution review|<c> m/d|
|Testing (only by the developer)|<d> m/d|
|Reserve for potential gaps and risks|<e> m/d|
""".strip()


def get_args(template: str) -> list[str]:
    args: list[str] = []
    for m in PATTERN_ARG.finditer(template):
        value: str = m.group(1)
        if value not in args:
            args.append(value)

    return args


def process(template: str, arg_by_value: dict[str, str]) -> str:
    def _get_norm_str_float(value: str) -> str:
        return DEFAULT_ARG_VALUE if value == "nan" else value.removesuffix(".0")

    def _get_value_from_arg(
        arg: str,
        default_value: str = DEFAULT_ARG_VALUE,
        get_float: bool = True,
    ) -> str:
        value = arg_by_value.get(arg)
        if value:
            value = value.strip()
            value = _get_norm_str_float(value)

        # Проверка валидности значения
        try:
            float(value)
        except Exception:
            value = None

        if not value:
            value = default_value

        if get_float:
            value = f"float({value!r})"

        return value

    text: str = PATTERN_ARG.sub(
        lambda m: _get_value_from_arg(
            arg=m.group(1),
            get_float=False,
        ),
        template,
    )

    def _process_result(m: re.Match) -> str:
        template_expr: str = m.group(1)

        expr: str = re.sub(
            r"\w+",
            lambda m: _get_value_from_arg(arg=m.group()),
            template_expr,
        )

        try:
            value = eval(expr)
        except SyntaxError:
            value = float(DEFAULT_ARG_VALUE)

        result: str = f"{value:.1f}"
        return _get_norm_str_float(result)

    return PATTERN_RESULT.sub(_process_result, text)


if __name__ == "__main__":
    args: list[str] = get_args(SAMPLE_TEMPLATE)
    print(args)
    assert args == ["a", "b", "c", "d", "e"]

    print()

    arg_by_value: dict[str, str] = dict(
        a="1.1",
        b="0.1",
        c="0.5",
        d="12",
        e="1.0",
    )
    text = process(SAMPLE_TEMPLATE, arg_by_value)
    print(text)
    assert text == """
*Итоговая трудоемкость в человеко-днях:* 14.7 ч/д, в том числе:
|Аналитика (проектирование/техническая спецификация)|1.1 ч/д|
|Разработка (программирование)|0.1 ч/д|
|Рецензирование решения и кода|0.5 ч/д|
|Тестирование (только силами разработчика)|12 ч/д|
|Резерв на непредвиденные работы и риски|1 ч/д|

*Total efforts in man-days:* 14.7 m/d, including:
|Analysis (design and tech specs)|1.1 m/d|
|Implementation (including coding)|0.1 m/d|
|Code and solution review|0.5 m/d|
|Testing (only by the developer)|12 m/d|
|Reserve for potential gaps and risks|1 m/d|
    """.strip()

    print("\n" + "-" * 10 + "\n")

    arg_by_value["e"] = "1.3"
    text = process(SAMPLE_TEMPLATE, arg_by_value)
    print(text)
    assert text == """
*Итоговая трудоемкость в человеко-днях:* 15 ч/д, в том числе:
|Аналитика (проектирование/техническая спецификация)|1.1 ч/д|
|Разработка (программирование)|0.1 ч/д|
|Рецензирование решения и кода|0.5 ч/д|
|Тестирование (только силами разработчика)|12 ч/д|
|Резерв на непредвиденные работы и риски|1.3 ч/д|

*Total efforts in man-days:* 15 m/d, including:
|Analysis (design and tech specs)|1.1 m/d|
|Implementation (including coding)|0.1 m/d|
|Code and solution review|0.5 m/d|
|Testing (only by the developer)|12 m/d|
|Reserve for potential gaps and risks|1.3 m/d|
    """.strip()

    print("\n" + "-" * 10 + "\n")

    arg_by_value: dict[str, str] = dict(
        a="",
        b="b",
        c="  3  ",
        d="0",
    )
    text = process(SAMPLE_TEMPLATE, arg_by_value)
    print(text)
    assert text == """
*Итоговая трудоемкость в человеко-днях:* NaN ч/д, в том числе:
|Аналитика (проектирование/техническая спецификация)|NaN ч/д|
|Разработка (программирование)|NaN ч/д|
|Рецензирование решения и кода|3 ч/д|
|Тестирование (только силами разработчика)|0 ч/д|
|Резерв на непредвиденные работы и риски|NaN ч/д|

*Total efforts in man-days:* NaN m/d, including:
|Analysis (design and tech specs)|NaN m/d|
|Implementation (including coding)|NaN m/d|
|Code and solution review|3 m/d|
|Testing (only by the developer)|0 m/d|
|Reserve for potential gaps and risks|NaN m/d|
    """.strip()
