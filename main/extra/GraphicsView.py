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

from PyQt5 import QtWidgets, QtCore, QtSvg, QtGui
from main.extra import IOHandler, isSVG, Constants, tango
import os

Config = IOHandler.IOHandler.get_preferences()

FILE_TYPES_OUT = {
    "Windows Bitmap Format": ["bmp"],
    "JPEG": ["jpg", "jpeg"],
    "Portable Network Graphics": ["png"],
    "Portable Pixmap": ["ppm"],
    "X11 Bitmap": ["xbm"],
    "X11 Pixmap": ["xpm"]
}

class GraphicsView(QtWidgets.QWidget):
    zoomed = QtCore.pyqtSignal(float)

    def __init__(self, mainwindow, parent=None, controls=False):
        super(GraphicsView, self).__init__(parent)
        self.mainwindow = mainwindow
        self._scene = QtWidgets.QGraphicsScene()
        self._view = QtWidgets.QGraphicsView(self._scene, parent)
        self._view.wheelEvent = self.viewWheelEvent
        self._view.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self._view, 0, 0, 1, -1)

        self.controls = controls
        self.zoom_factor_base = 2.0
        self.zoom_factor_scroll = 1.0015
        self.zoom_level_min = 0.1
        self.zoom_level_max = 4.5
        self.zoomlevel = 1.0

        self.pb_zoom_out = QtWidgets.QPushButton(QtGui.QIcon(":/icons/tango/list-remove.png"), "")
        self.pb_zoom_out.setToolTip("Zoom Out")
        self.pb_zoom_out.clicked.connect(self.zoomOut)

        self.slider_zoom = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_zoom.setSingleStep(0)
        self.slider_zoom.setPageStep(0)
        self.slider_zoom.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider_zoom.setTickInterval(10)
        self.slider_zoom.sliderMoved.connect(lambda x: self.zoomTo(float(x) / 100))
        self.setMinZoomLevel(self.zoom_level_min)
        self.setMaxZoomLevel(self.zoom_level_max)
        self.slider_zoom.setValue(100)

        self.pb_zoom_in = QtWidgets.QPushButton(QtGui.QIcon(":/icons/tango/list-add.png"), "")
        self.pb_zoom_in.setToolTip("Zoom In")
        self.pb_zoom_in.clicked.connect(self.zoomIn)

        self.lb_zoom = QtWidgets.QLabel("100%")

        self.pb_zoom_reset = QtWidgets.QPushButton("Reset")
        self.pb_zoom_reset.setToolTip("Reset Zoom Level")
        self.pb_zoom_reset.clicked.connect(self.resetZoom)
        self.zoomed.connect(self._zoomed)

        self.pb_zoom_fit = QtWidgets.QPushButton(QtGui.QIcon(":/icons/tango/view-fullscreen.png"), "")
        self.pb_zoom_fit.setToolTip("Zoom to Fit")
        self.pb_zoom_fit.clicked.connect(self.zoomToFit)

        self.pb_save = QtWidgets.QPushButton(QtGui.QIcon(":/icons/tango/image-x-generic.png"), "")
        self.pb_save.setToolTip("Export to Image...")
        self.pb_save.clicked.connect(self.save)

        self.layout.addWidget(self.pb_zoom_out, 1, 0)
        self.layout.addWidget(self.slider_zoom, 1, 1)
        self.layout.addWidget(self.lb_zoom, 1, 2)
        self.layout.addWidget(self.pb_zoom_in, 1, 3)
        self.layout.addWidget(self.pb_zoom_reset, 1, 4)
        self.layout.addWidget(self.pb_zoom_fit, 1, 5)
        self.layout.addWidget(self.pb_save, 1, 6)
        self.setLayout(self.layout)

        self.setControls(self.controls)

    def setMaxZoomLevel(self, level):
        self.zoom_level_max = level
        self.slider_zoom.setMaximum(level * 100)

    def setMinZoomLevel(self, level):
        self.zoom_level_min = level
        self.slider_zoom.setMinimum(level * 100)

    def setZoomFactorBase(self, factor):
        self.zoom_factor_base = factor

    def setControls(self, enabled: bool):
        self.controls = enabled
        self.pb_zoom_out.setVisible(self.controls)
        self.pb_zoom_in.setVisible(self.controls)
        self.pb_zoom_reset.setVisible(self.controls)
        self.slider_zoom.setVisible(self.controls)
        self.lb_zoom.setVisible(self.controls)

        if self.controls:
            self._view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        else:
            self._view.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    def _zoomed(self, zoomlevel):
        if self.controls:
            self.slider_zoom.setValue(zoomlevel * 100)
            self.lb_zoom.setText("%6.2f%%" % (zoomlevel * 100))
        self.pb_zoom_in.setDisabled(self.isMaximalZoomed())
        self.pb_zoom_out.setDisabled(self.isMinimalZoomed())

    def isMinimalZoomed(self):
        return self.zoom_level_min == self.zoomlevel

    def isMaximalZoomed(self):
        return self.zoom_level_max == self.zoomlevel

    def clear(self):
        self._scene.clear()
        self._scene.deleteLater()
        self._view.setScene(QtWidgets.QGraphicsScene())
        self._scene = self._view.scene()

    def add(self, bdata):
        if isSVG(bdata):
            svgRenderer = QtSvg.QSvgRenderer(bdata)
            dot = QtSvg.QGraphicsSvgItem()
            dot.setSharedRenderer(svgRenderer)
            self._scene.addItem(dot)
        else:
            image = QtGui.QImage()
            image.loadFromData(bdata)
            pixmap = QtGui.QPixmap.fromImage(image)
            self._scene.addPixmap(pixmap)
        margin = 25
        sr = self._scene.itemsBoundingRect()
        sr.adjust(-margin, -margin, margin, margin)
        self._scene.setSceneRect(sr)

    @QtCore.pyqtSlot(QtCore.QPoint, name="centerOn")
    def centerOn(self, point):
        self._view.centerOn(point)

    @QtCore.pyqtSlot(float, name="zoom")
    def zoom(self, factor):
        if self.zoomlevel * factor > self.zoom_level_max:
            return self.zoomTo(self.zoom_level_max)
        if self.zoomlevel * factor < self.zoom_level_min:
            return self.zoomTo(self.zoom_level_min)
        self._view.scale(factor, factor)
        self.zoomlevel *= factor
        self.zoomed.emit(self.zoomlevel)

    @QtCore.pyqtSlot(name="resetZoom")
    def resetZoom(self):
        self.zoomTo(1.0)

    @QtCore.pyqtSlot(float, name="zoomTo")
    def zoomTo(self, zoomlevel):
        self.zoom(float(zoomlevel) / self.zoomlevel)

    @QtCore.pyqtSlot(name="zoomIn")
    def zoomIn(self):
        self.zoom(self.zoom_factor_base)

    @QtCore.pyqtSlot(name="zoomOut")
    def zoomOut(self):
        self.zoom(1.0 / self.zoom_factor_base)

    @QtCore.pyqtSlot(name="zoomToFit")
    def zoomToFit(self):
        rect = self._view.frameRect()
        sceneRect = self._scene.itemsBoundingRect()
        w = rect.width() / sceneRect.width()
        h = rect.height() / sceneRect.height()
        self.zoomTo(min(w, h))

    def save(self):
        options, folder = self.mainwindow.io()
        fileName, t = QtWidgets.QFileDialog \
            .getSaveFileName(self, "Export a File", folder, Constants.file_list(FILE_TYPES_OUT), options=options)
        if fileName:
            ext = fileName.split(".")[-1]
            rext = Constants.obtain_exts(t)
            if fileName == ext:
                ext = rext[0]
                fileName += "." + ext
                if os.path.isfile(fileName):
                    yes = self.question("File already exists!", "This file already exists. Are you sure, you want "
                                                                "to replace it?")
                    if not yes:
                        # Reboot file chooser window
                        return self.save()

            # Do the actual saving
            self._scene.clearSelection()    # If there were to be any selections, these would also render to the file
            self._scene.setSceneRect(self._scene.itemsBoundingRect())
            image = QtGui.QImage(self._scene.sceneRect().size().toSize(), QtGui.QImage.Format_ARGB32)
            image.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            self._scene.render(painter)
            image.save(fileName)
            painter.end()

    def viewWheelEvent(self, event: QtGui.QWheelEvent):
        mods = Config.value("view/scrollKey").split(" + ")
        modifiers = QtCore.Qt.NoModifier
        alt = False
        for m in mods:
            if m == "CTRL":
                modifiers |= QtCore.Qt.ControlModifier
            elif m == "ALT":
                modifiers |= QtCore.Qt.AltModifier
                alt = True
            elif m == "SHIFT":
                modifiers |= QtCore.Qt.ShiftModifier
            elif m == "META":
                modifiers |= QtCore.Qt.MetaModifier

        if event.modifiers() == modifiers:
            delta = event.angleDelta()
            if alt:
                angle = delta.x()
            else:
                angle = delta.y()
            factor = pow(self.zoom_factor_scroll, angle)
            self.zoom(factor)
        else:
            QtWidgets.QGraphicsView.wheelEvent(self._view, event)
