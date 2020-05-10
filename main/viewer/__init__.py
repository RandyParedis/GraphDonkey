"""Set of predefined variables w.r.t. the view.

"""
from enum import Enum

from PyQt5 import QtSvg, QtGui

from main.extra import isSVG


class ReturnType(Enum):
    IMAGE = 0
    DRAWING = 1   # <-- Can be solved using PIL.ImageDraw.ImageDraw instead

def display(data, scene):
    if isinstance(data, (tuple, list)):
        kind, bdata = data
    else:
        kind = ReturnType.IMAGE
        bdata = data
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
        # bdata is a PIL.ImageDraw.ImageDraw object
        pass
