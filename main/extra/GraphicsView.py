"""This file contains all information for a GraphicsView with additional features.

These features contain:
    - Default scene
    - Quick addition of graphviz code
    - Default drag mode = scrollhanddrag
    - Zooming
        ==> Inspired on https://stackoverflow.com/a/19114517

Author: Randy Paredis
Date:   01/01/2020
"""

from PyQt5 import QtWidgets, QtCore, QtSvg
from main.extra import dotToQPixmap

class GraphicsView(QtWidgets.QGraphicsView):
    zoomed = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        self._scene = QtWidgets.QGraphicsScene()
        super(GraphicsView, self).__init__(self._scene, parent)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

        self.zoom_factor_base = 1.0015
        self.target_scene_pos = QtCore.QPointF()
        self.target_viewport_pos = QtCore.QPointF()
        self.zoomlevel = 1.0

    def clear(self):
        self._scene.clear()

    def addDot(self, dot, format, renderer, formatter):
        if format == "svg":
            bdata = dot.pipe(format, renderer, formatter)
            svgRenderer = QtSvg.QSvgRenderer(bdata)
            dot = QtSvg.QGraphicsSvgItem()
            dot.setSharedRenderer(svgRenderer)
            self._scene.addItem(dot)
        else:
            pixmap = dotToQPixmap(dot, format, renderer, formatter)
            self._scene.addPixmap(pixmap)

    @QtCore.pyqtSlot(float, name="zoom")
    def zoom(self, factor):
        self.scale(factor, factor)
        self.centerOn(self.target_scene_pos)
        delta_viewport_pos = self.target_viewport_pos - QtCore.QPointF(self.viewport().width() / 2,
                                                                       self.viewport().height() / 2)
        viewport_center = self.mapFromScene(self.target_scene_pos) - delta_viewport_pos
        self.centerOn(self.mapToScene(viewport_center.toPoint()))
        self.zoomlevel *= factor
        self.zoomed.emit(self.zoomlevel)

    @QtCore.pyqtSlot(name="resetZoom")
    def resetZoom(self):
        self.zoomTo(1.0)

    @QtCore.pyqtSlot(float, name="zoomTo")
    def zoomTo(self, zoomlevel):
        self.zoom(float(zoomlevel) / self.zoomlevel)

    def eventFilter(self, object: QtCore.QObject, event: QtCore.QEvent):
        if event.type() == QtCore.QEvent.MouseMove:
            delta = self.target_viewport_pos - event.pos()
            if abs(delta.x()) > 5 or abs(delta.y()) > 5:
                self.target_viewport_pos = event.pos()
                self.target_scene_pos = self.mapToScene(event.pos())
        elif event.type() == QtCore.QEvent.Wheel:
            angle = event.angleDelta().y()
            factor = pow(self.zoom_factor_base, angle)
            self.zoom(factor)
            return True
        return QtWidgets.QGraphicsView.eventFilter(self, object, event)
