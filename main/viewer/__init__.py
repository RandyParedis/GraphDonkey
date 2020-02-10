"""Set of predefined variables w.r.t. the view.

"""
from enum import Enum

from PyQt5 import QtSvg, QtGui

from main.extra import isSVG


class ReturnType(Enum):
    IMAGE = 0
    DRAWING = 1

def display(data, scene):
    # TODO: check if tuple
    kind, bdata = data
    if kind == ReturnType.IMAGE:
        if isSVG(bdata):
            svgRenderer = QtSvg.QSvgRenderer(bdata)
            dot = QtSvg.QGraphicsSvgItem()
            dot.setSharedRenderer(svgRenderer)
            scene.addItem(dot)
        else:
            image = QtGui.QImage()
            image.loadFromData(bdata)
            pixmap = QtGui.QPixmap.fromImage(image)
            scene.addPixmap(pixmap)

    elif kind == ReturnType.DRAWING:
        # bdata is a set of elements in {Line, Rectangle, Ellipse, Polygon, Bezier}
        pass
