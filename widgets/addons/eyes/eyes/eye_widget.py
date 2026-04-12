#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPaintEvent, QPainter, QPen
from PyQt6.QtCore import QPointF, Qt

from .common import percent_number
from .eye import Eye, Iris, Pupil


MINIMAL_SIZE_EYE: int = 50


class EyeWidget(QWidget):
    eye: Eye = Eye(
        brush=Qt.GlobalColor.white,
        pen=QPen(Qt.GlobalColor.black, 2.0),
        iris=Iris(
            brush=Qt.GlobalColor.black,
            pen=QPen(Qt.GlobalColor.black, 1.0),
        ),
        pupil=Pupil(
            brush=Qt.GlobalColor.black,
            pen=QPen(Qt.GlobalColor.white, 1.0),
        ),
    )

    d_percent_iris_radius_x: int = 30
    d_percent_iris_radius_y: int = 30

    d_percent_pupil_radius_x: int = 55
    d_percent_pupil_radius_y: int = 55

    position_look: QPointF = QPointF(0.0, 0.0)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.set_diameter(MINIMAL_SIZE_EYE)

    def set_diameter(self, diameter: int) -> None:
        diameter = max(diameter, MINIMAL_SIZE_EYE)

        self.setFixedSize(diameter, diameter)

    def look_there(self, position: QPointF) -> None:
        self.position_look = QPointF(self.mapFromGlobal(position))
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        indent: int = 3

        # По размерам окна определим примерно размер глаз
        # расчет будет по высоте и ширине
        r_x_from_width: float = (self.width() - indent * 2) / 2
        r_y_from_heigth: float = (self.height() - indent * 2) / 2

        radius_x_eye: float = min(r_x_from_width, r_y_from_heigth)
        radius_y_eye: float = radius_x_eye

        radius_x_iris: float = percent_number(radius_x_eye, self.d_percent_iris_radius_x)
        radius_y_iris: float = percent_number(radius_y_eye, self.d_percent_iris_radius_y)

        radius_x_pupil: float = percent_number(
            radius_x_iris, self.d_percent_pupil_radius_x
        )
        radius_y_pupil: float = percent_number(
            radius_y_iris, self.d_percent_pupil_radius_y
        )

        x: float = float(radius_x_eye + indent)
        y: float = float(radius_y_eye + indent)

        self.eye.radiusX = radius_x_eye
        self.eye.radiusY = radius_y_eye
        self.eye.center = QPointF(x, y)

        # Радужка глаза
        iris = self.eye.iris
        iris.radiusX = radius_x_iris
        iris.radiusY = radius_y_iris
        iris.center = self.position_look

        # Зрачок глаза
        pupil = self.eye.pupil
        pupil.radiusX = radius_x_pupil
        pupil.radiusY = radius_y_pupil

        self.eye.draw(painter)
