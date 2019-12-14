from PyQt5 import QtWidgets, QtCore, QtGui, uic
from main.extra.IOHandler import IOHandler
from main.Highlighter import CodeEditor
from main.Setup import Setup
from graphviz import Source

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowFlags())
        uic.loadUi(IOHandler.dir_ui("MainWindow.ui"), self)
        self.scene = self.view.scene()
        if self.scene is None:
            self.scene = QtWidgets.QGraphicsScene(self.view)
            self.view.setScene(self.scene)

        self.restore()

        self.editor = None
        self.setupEditor()
        self.pb_render.clicked.connect(self.displayGraph)

    def setupEditor(self):
        font = QtGui.QFont()
        font.setFamily('Ubuntu Monospace')
        font.setFixedPitch(True)
        font.setPointSize(12)

        self.editor = CodeEditor(self)
        self.editor.setFont(font)

        self.graphvizData.layout().addWidget(self.editor)

    def displayGraph(self):
        self.scene.clear()
        dot = Source(self.editor.toPlainText())
        bdata = dot.pipe('jpg')
        image = QtGui.QImage()
        image.loadFromData(bdata)
        pixmap = QtGui.QPixmap.fromImage(image)
        self.scene.addPixmap(pixmap)

    def restore(self):
        # Restore layout from memory iff needs be/possible
        settings = IOHandler.get_settings()
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))

    def closeEvent(self, event: QtGui.QCloseEvent):
        settings = IOHandler.get_settings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        QtWidgets.QMainWindow.closeEvent(self, event)
