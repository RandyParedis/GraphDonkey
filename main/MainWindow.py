"""Mainwindow for the GraphDonkey application.

Author: Randy Paredis
Date:   14/12/2019
"""
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from main.extra.IOHandler import IOHandler
from main.CodeEditor import CodeEditor
from main.extra import Constants, Config
from graphviz import Source
import graphviz

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowFlags())
        uic.loadUi(IOHandler.dir_ui("MainWindow.ui"), self)
        self.scene = self.view.scene()
        if self.scene is None:
            self.scene = QtWidgets.QGraphicsScene(self.view)
            self.view.setScene(self.scene)

        self.restore()

        self.filename = ""
        self.saved = False
        self.updateTitle()

        self.editor = None
        self.setupEditor()

        # Set menu
        self.action_New.triggered.connect(self.new)
        self.action_Open.triggered.connect(self.open)
        self.action_Save.triggered.connect(self.save)
        self.action_Save_As.triggered.connect(self.saveAs)
        self.action_Exit.triggered.connect(self.close) # TODO: Check for saved
        self.action_Undo.triggered.connect(self.editor.undo)
        self.action_Redo.triggered.connect(self.editor.redo)
        self.action_Select_All.triggered.connect(self.editor.selectAll)
        self.action_Delete.triggered.connect(lambda x: self.editor.insertPlainText(""))
        self.action_Copy.triggered.connect(self.editor.copy)
        self.action_Paste.triggered.connect(self.editor.paste)
        self.action_Cut.triggered.connect(self.editor.cut)
        self.action_Render.triggered.connect(self.displayGraph)
        self.actionAboutGraphviz.triggered.connect(self.aboutGraphviz)
        self.actionAboutQt.triggered.connect(self.aboutQt)
        self.actionAboutGraphDonkey.triggered.connect(self.aboutGraphDonkey)

        # Set Toolbar
        self.actionUndo.triggered.connect(self.editor.undo)
        self.actionUndo.setIcon(QtGui.QIcon(QtGui.QPixmap(Constants.ICON_UNDO)))
        self.actionRedo.triggered.connect(self.editor.redo)
        self.actionRedo.setIcon(QtGui.QIcon(QtGui.QPixmap(Constants.ICON_REDO)))
        self.actionNew.triggered.connect(self.new)
        self.actionNew.setIcon(QtGui.QIcon(QtGui.QPixmap(Constants.ICON_NEW)))
        self.actionOpen.triggered.connect(self.open)
        self.actionOpen.setIcon(QtGui.QIcon(QtGui.QPixmap(Constants.ICON_OPEN)))
        self.actionSave.triggered.connect(self.save)
        self.actionSave.setIcon(QtGui.QIcon(QtGui.QPixmap(Constants.ICON_SAVE)))
        self.actionRender.triggered.connect(self.displayGraph)
        self.actionRender.setIcon(QtGui.QIcon(QtGui.QPixmap(Constants.ICON_RENDER)))

        # Shortcuts
        for s in Config.SHORTCUTS:
            a = getattr(self, "action_" + s.replace(" ", "_"))
            a.setShortcuts([QtGui.QKeySequence(x) for x in Config.SHORTCUTS[s]])

    def updateTitle(self):
        rest = "undefined"
        if self.filename != "":
            rest = self.filename
        if not self.saved:
            rest += "*"
        self.setWindowTitle(" " + rest)

    def setupEditor(self):
        if self.editor is None:
            font = QtGui.QFont()
            font.setFamily('Ubuntu Monospace')
            font.setFixedPitch(True)
            font.setPointSize(12)

            self.editor = CodeEditor(self)
            self.editor.textChanged.connect(self.textChangedEvent)
            self.editor.setFont(font)
            self.graphvizData.layout().addWidget(self.editor)
            self.graphvizDataDock.closeEvent = self.gdDockCloseEvent
        else:
            self.editor.clear()

        self.displayGraph()

    def gdDockCloseEvent(self, event):
        self.action_ShowCode.setChecked(False)
        self.graphvizDataDock.setVisible(False)

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

    def textChangedEvent(self):
        self.saved = False
        self.updateTitle()

    def new(self):
        # TODO: confirmation if not saved
        self.setupEditor()
        self.filename = ""
        self.saved = False
        self.updateTitle()

    def open(self):
        # TODO: confirmation if not saved
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog\
            .getOpenFileName(self, "Open a Graphviz File", "", "All Files (*);;" + Constants.file_list_open(),
                             options=options)
        if fileName:
            ext = fileName.split(".")[-1]
            if Constants.valid_ext(ext, Constants.FILE_TYPES_OPEN):
                self.setupEditor()
                with open(fileName, "r") as myfile:
                    data = "".join(myfile.readlines())
                    dot = Source(data, format=ext)
                    self.editor.setText(dot.source)

                self.filename = fileName
                self.saved = True
                self.updateTitle()

                self.displayGraph()
            else:
                QtWidgets.QMessageBox.critical(self, "Invalid File", "It looks like this file cannot be opened.")

    def save(self):
        if self.filename == "":
            self.saveAs()
        else:
            ext = self.filename.split(".")[-1]
            dot = Source(self.editor.toPlainText())
            contents = dot.pipe(ext)
            with open(self.filename, 'bw') as myfile:
                myfile.write(contents)
            self.saved = True
            self.updateTitle()

    def saveAs(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, t = QtWidgets.QFileDialog\
            .getSaveFileName(self, "Save a Graphviz File", "", "All Files (*);;" + Constants.file_list_save(),
                             options=options)
        if fileName:
            # TODO: confirmation box
            ext = fileName.split(".")[-1]
            rext = Constants.obtain_ext(t)
            if len(fileName.split(".")) == 1:
                ext = "plain"
            if rext == "":
                rext = ext
            if ext is not rext:
                fileName += "." + rext
            if Constants.valid_ext(rext, Constants.FILE_TYPES_SAVE):
                self.filename = fileName
                self.save()

    def displayGraph(self):
        self.scene.clear()
        dot = Source(self.editor.toPlainText())
        bdata = dot.pipe('jpg')
        image = QtGui.QImage()
        image.loadFromData(bdata)
        pixmap = QtGui.QPixmap.fromImage(image)
        self.scene.addPixmap(pixmap)

    def aboutGraphviz(self):
        par = QtWidgets.QWidget(self)
        par.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(Constants.ICON_GRAPHVIZ)))
        QtWidgets\
            .QMessageBox\
            .about(par,
                   "About Graphviz",
                   "<p>Graphviz is open source graph visualization software. Graph visualization is a way of "
                   "representing structural information as diagrams of abstract graphs and networks. It has important "
                   "applications in networking, bioinformatics,  software engineering, database and web design, machine"
                   " learning, and in visual interfaces for other technical domains.</p>"
                   "<p>Current installed version is <b>%s</b>.</p>"
                   "<p>More information on "
                   "<a href='https://www.graphviz.org/'>www.graphviz.org</a>.</p>" % graphviz.__version__)

    def aboutGraphDonkey(self):
        QtWidgets\
            .QMessageBox\
            .about(self,
                   "About GraphDonkey",
                   "<p>A simple and easy-to-use application for visualizing and editing Graphviz Dot files. It is "
                   "based on the idea of xdot, combined with a texteditor that can live-update the images.</p>"
                   "<p>Current version is <b>%s</b>.</p>"
                   "<p>Created by <b>Randy Paredis</b>." % Constants.APP_VERSION)

    def aboutQt(self):
        QtWidgets.QMessageBox.aboutQt(self)