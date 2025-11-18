#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from typing import Any

from PyQt5.QtCore import Qt, pyqtSignal, QLocale, QRegularExpression, QRect
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QCursor
from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QFormLayout,
    QWidget,
    QDoubleSpinBox,
    QPlainTextEdit,
    QTabWidget,
    QToolButton,
    QSplitter,
    QToolTip,
    QStyle,
    QLineEdit, QPushButton,
)

from widgets import get_scroll_area
from widgets.addons import AddonWidget, AddonDockWidget, Defaults
from widgets.addons.total_efforts_calc.parse_total_efforts import (
    PATTERN_ARG,
    PATTERN_RESULT,
    DEFAULT_ARG_VALUE,
    SAMPLE_TEMPLATE,
    process as parse_total_efforts,
    get_args,
)


SAMPLE_ARGS: dict[str, str] = dict.fromkeys(
    get_args(SAMPLE_TEMPLATE),
    DEFAULT_ARG_VALUE,
)


def create_syntax_highlighter(
    text_edit: QPlainTextEdit,
    reg_expr: str,
    foreground_color: int,
) -> QSyntaxHighlighter:
    expression = QRegularExpression(reg_expr)

    char_format = QTextCharFormat()
    char_format.setFontWeight(QFont.Bold)
    char_format.setForeground(foreground_color)

    class MySyntaxHighlighter(QSyntaxHighlighter):
        def highlightBlock(self, text):
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(
                    match.capturedStart(), match.capturedLength(), char_format
                )

    syntax_highlighter = MySyntaxHighlighter(text_edit.document())
    syntax_highlighter.setParent(text_edit)
    return syntax_highlighter


class KeyValueWidget(QWidget):
    changed_data = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.key_by_widget: dict[str, QDoubleSpinBox] = dict()

        widget = QWidget()
        self.form_layout = QFormLayout(widget)
        self.form_layout.setContentsMargins(0, 0, 0, 0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 0, 5, 0)
        main_layout.addWidget(get_scroll_area(widget))

    def _add_widget_value(self, key: str, value: str):
        if key in self.key_by_widget:
            double_spin_box = self.key_by_widget[key]
        else:
            double_spin_box = QDoubleSpinBox()
            double_spin_box.setRange(-0.1, 1000)
            double_spin_box.setSingleStep(0.1)
            double_spin_box.setValue(1.0)
            double_spin_box.setSpecialValueText(DEFAULT_ARG_VALUE)
            # NOTE: Locale=English, чтобы разделителем была точка
            double_spin_box.setLocale(QLocale(QLocale.Language.English))
            double_spin_box.setDecimals(1)
            double_spin_box.textChanged.connect(self.changed_data.emit)

            clear_action = double_spin_box.lineEdit().addAction(
                self.style().standardIcon(QStyle.SP_LineEditClearButton),
                QLineEdit.TrailingPosition,
            )
            clear_action.triggered.connect(
                lambda: double_spin_box.setValue(double_spin_box.minimum())
            )
            double_spin_box.textChanged.connect(
                lambda val: clear_action.setVisible(val != DEFAULT_ARG_VALUE)
            )

            self.form_layout.addRow(f"{key}:", double_spin_box)
            self.key_by_widget[key] = double_spin_box

        if value.upper() == DEFAULT_ARG_VALUE.upper():
            double_spin_box.setValue(double_spin_box.minimum())
        else:
            double_spin_box.setValue(float(value))

    def set_value(self, data: dict[str, str]):
        for k, v in data.items():
            self._add_widget_value(k, v)

        # Удаление строки с виджетом, если в данных нет ключа
        for k, widget in list(self.key_by_widget.items()):
            if k not in data:
                self.form_layout.removeRow(widget)
                self.key_by_widget.pop(k)

    def get_value(self) -> dict[str, str]:
        return {k: widget.text() for k, widget in self.key_by_widget.items()}


class AddonTotalEffortsCalcWidget(AddonWidget):
    def __init__(self, addon_dock_widget: AddonDockWidget):
        super().__init__(addon_dock_widget)

        self.setWindowTitle("Калькулятор итоговой трудоемкости")

        self.template_edit = QPlainTextEdit()
        self.template_edit.setPlainText(SAMPLE_TEMPLATE)
        self.template_edit.textChanged.connect(self._refill_args)
        create_syntax_highlighter(
            text_edit=self.template_edit,
            reg_expr=f"{PATTERN_ARG.pattern}|{PATTERN_RESULT.pattern}",
            foreground_color=Qt.darkGreen,
        )

        self.result_edit = QPlainTextEdit()
        create_syntax_highlighter(
            text_edit=self.result_edit,
            reg_expr=f"(?i){DEFAULT_ARG_VALUE}",
            foreground_color=Qt.red,
        )

        self.args_widget = KeyValueWidget()
        self.args_widget.changed_data.connect(self._process)

        button_copy_result = QToolButton()
        button_copy_result.setText("📋")
        button_copy_result.setToolTip("Скопировать результат в буфер обмена")
        button_copy_result.setAutoRaise(True)
        button_copy_result.clicked.connect(
            lambda: (
                QApplication.instance()
                .clipboard()
                .setText(self.result_edit.toPlainText()),
                QToolTip.showText(
                    QCursor.pos(),
                    "👌",
                    button_copy_result,
                    QRect(),
                    2000,
                ),
            )
        )

        button_show_args = QToolButton()
        button_show_args.setText("Аргументы")
        button_show_args.setCheckable(True)
        button_show_args.setChecked(True)
        button_show_args.setAutoRaise(True)
        button_show_args.clicked.connect(self.args_widget.setVisible)
        self.args_widget.setVisible(button_show_args.isChecked())

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.South)
        self.tab_widget.addTab(self.result_edit, "Результат")
        self.tab_widget.addTab(self.template_edit, "Шаблон")
        self.tab_widget.setCornerWidget(button_copy_result, Qt.TopLeftCorner)
        self.tab_widget.setCornerWidget(button_show_args, Qt.TopRightCorner)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.tab_widget)
        splitter.addWidget(self.args_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(splitter)

    def _refill_args(self):
        args_from_template: list[str] = get_args(self.template_edit.toPlainText())
        arg_by_value: dict[str, str] = self.args_widget.get_value()
        self.args_widget.set_value(
            {
                arg: arg_by_value.get(arg, DEFAULT_ARG_VALUE)
                for arg in args_from_template
            }
        )

        self._process()

    def defaults(self) -> Defaults:
        return Defaults(
            is_visible=False,
            is_active=True,
            area=Qt.DockWidgetArea.RightDockWidgetArea,
        )

    def is_supported_refresh(self) -> bool:
        return False

    def is_supported_logs(self) -> bool:
        return False

    def is_supported_settings(self) -> bool:
        return False

    def _process(self):
        text = parse_total_efforts(
            template=self.template_edit.toPlainText(),
            arg_by_value=self.args_widget.get_value(),
        )
        self.result_edit.setPlainText(text)

    def read_settings(self, settings: dict[str, Any] | None):
        if settings is None:
            settings: dict[str, Any] = dict()

        template: str | None = settings.get("template")
        if template is None:
            template = SAMPLE_TEMPLATE
        self.template_edit.setPlainText(template)

        args: dict[str, str] | None = settings.get("args")
        if args is None:
            args = SAMPLE_ARGS
        self.args_widget.set_value(args)

        self._refill_args()
        self._process()

    def write_settings(self, settings: dict[str, Any]):
        settings["template"] = self.template_edit.toPlainText()
        settings["args"] = self.args_widget.get_value()


if __name__ == "__main__":
    from config import PATH_STYLE_SHEET

    app = QApplication([])

    # Использование qss из ресурсов, если он не был задан в аргументах
    if not app.styleSheet():
        app.setStyleSheet(f"file:///{PATH_STYLE_SHEET}")

    w = AddonDockWidget(AddonTotalEffortsCalcWidget)
    w.read_settings(None)
    w.resize(400, 400)
    w.show()

    app.exec()
