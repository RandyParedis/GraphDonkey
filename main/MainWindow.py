"""Mainwindow for the GraphDonkey application.

Author: Randy Paredis
Date:   14/12/2019
"""
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from main.FindReplace import FindReplace
from main.Preferences import Preferences, bool
from main.extra.IOHandler import IOHandler
from main.CodeEditor import CodeEditor
from main.extra import Constants
from main.UpdateChecker import UpdateChecker
from graphviz import Source
import graphviz

Config = IOHandler.get_preferences()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowFlags())
        uic.loadUi(IOHandler.dir_ui("MainWindow.ui"), self)
        self.scene = self.view.scene()
        if self.scene is None:
            self.scene = QtWidgets.QGraphicsScene(self.view)
            self.view.setScene(self.scene)

        self.filename = ""
        self.saved = False
        self.updateTitle()

        self.editor = None
        self.setupEditor()

        self.preferences = Preferences(self)
        self.preferences.apply()

        self.recents = []
        self.restore()

        self.find = FindReplace(self, self.editor)

        # Set menu
        self.action_New.triggered.connect(self.new)
        self.action_Open.triggered.connect(self.open)
        self.action_Save.triggered.connect(self.save)
        self.action_Save_As.triggered.connect(self.saveAs)
        self.action_Export.triggered.connect(self.export)
        self.action_Preferences.triggered.connect(lambda: self.preferences.exec_())
        self.action_Exit.triggered.connect(self.close) # TODO: Check for saved
        self.action_Undo.triggered.connect(self.editor.undo)
        self.action_Redo.triggered.connect(self.editor.redo)
        self.action_Select_All.triggered.connect(self.editor.selectAll)
        self.action_Delete.triggered.connect(lambda x: self.editor.insertPlainText(""))
        self.action_Copy.triggered.connect(self.editor.copy)
        self.action_Paste.triggered.connect(self.editor.paste)
        self.action_Cut.triggered.connect(self.editor.cut)
        self.action_Duplicate.triggered.connect(self.editor.duplicate)
        self.action_Comment.triggered.connect(self.editor.comment)
        self.action_Indent.triggered.connect(self.editor.indent)
        self.action_Unindent.triggered.connect(self.editor.unindent)
        self.action_Auto_Indent.triggered.connect(self.editor.autoIndent)
        self.action_Find.triggered.connect(self.findReplace)
        self.action_Render.triggered.connect(self.displayGraph)
        self.action_CheckUpdates.triggered.connect(self.checkUpdates)
        self.action_AboutGraphviz.triggered.connect(self.aboutGraphviz)
        self.action_AboutQt.triggered.connect(self.aboutQt)
        self.action_AboutGraphDonkey.triggered.connect(self.aboutGraphDonkey)

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

    def updateTitle(self):
        rest = "undefined"
        if self.filename != "":
            rest = self.filename
        if not self.saved:
            rest += "*"
        self.setWindowTitle(" " + rest)

    def updateStatus(self, text):
        self.statusBar().clearMessage()
        self.statusBar().showMessage(text)

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
        if bool(Config.value("rememberLayout", True)):
            if settings.contains("geometry"):
                self.restoreGeometry(settings.value("geometry"))
            if settings.contains("windowState"):
                self.restoreState(settings.value("windowState"))
            if settings.value("recents", None) is not None:
                self.recents = settings.value("recents")
        if int(Config.value("restore", 0)) == 1:
            self.openFile(settings.value("open", ""))
        self.updateRecents()

    def closeEvent(self, event: QtGui.QCloseEvent):
        settings = IOHandler.get_settings()
        if bool(Config.value("rememberLayout", True)):
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            settings.setValue("recents", self.recents)
        if int(Config.value("restore", 0)) == 1:
            settings.setValue("open", self.filename)

        QtWidgets.QMainWindow.closeEvent(self, event)

    def textChangedEvent(self):
        self.saved = False
        self.updateTitle()

    def updateRecents(self, file=None):
        if file is not None:
            while file in self.recents:
                self.recents.remove(file)
            self.recents.insert(0, file)
            self.recents = self.recents[:Config.value("recents")]
        self.menuOpen_Recent.clear()

        for file in self.recents:
            self.menuOpen_Recent.addAction(file, lambda: self.openFile(file))
        if len(self.recents) > 0:
            self.menuOpen_Recent.addSeparator()
        clear = self.menuOpen_Recent.addAction("Clear Recents")
        clr = Config.value("ks.clear_recents")
        if clr != "":
            clear.setShortcuts(QtGui.QKeySequence(clr))
        clear.triggered.connect(lambda x: self.clearRecents())

    def warn(self, title, msg):
        QtWidgets.QMessageBox.warning(self, title, msg)

    def error(self, title, msg):
        QtWidgets.QMessageBox.critical(self, title, msg)

    def question(self, title, msg):
        btn = QtWidgets.QMessageBox.question(self, title, msg)
        return btn == QtWidgets.QMessageBox.Yes

    def clearRecents(self):
        self.recents.clear()
        self.updateRecents()

    def new(self):
        q = True
        if self.filename != "" and not self.saved:
            q = self.question("Not Saved", "There are changes detected in this file. "
                                           "Are you sure you want to open a new one?\n"
                                           "All changes will be lost.")
        if q:
            self.setupEditor()
            self.filename = ""
            self.saved = False
            self.updateTitle()

    def openFile(self, fileName):
        if fileName:
            ext = fileName.split(".")[-1]
            if Constants.valid_ext(ext, Constants.FILE_TYPES_OPEN):
                self.setupEditor()
                with open(fileName, "r") as myfile:
                    data = myfile.read()
                    self.editor.setText(data)

                self.updateRecents(fileName)
                self.filename = fileName
                self.saved = True
                self.updateTitle()
            else:
                self.warn("Invalid File", "It looks like this file cannot be opened.")

    def open(self):
        q = True
        if not self.saved:
            q = self.question("Not Saved", "There are changes detected in this file. "
                                           "Are you sure you want to open another?\n"
                                           "All changes will be lost.")
        if q:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            fileName, _ = QtWidgets.QFileDialog\
                .getOpenFileName(self, "Open a Graphviz File", "", "All Files (*);;" + Constants.file_list_open(),
                                 options=options)
            self.openFile(fileName)

    def save(self):
        if self.filename == "":
            self.saveAs()
        else:
            contents = self.editor.toPlainText()
            with open(self.filename, 'w') as myfile:
                myfile.write(contents)
            self.saved = True
            self.updateTitle()

    def saveAs(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, t = QtWidgets.QFileDialog\
            .getSaveFileName(self, "Save a Graphviz File", "", "All Files (*);;" + Constants.file_list_open(),
                             options=options)
        if fileName:
            ext = fileName.split(".")[-1]
            rext = Constants.obtain_ext(t)
            if len(fileName.split(".")) == 1:
                ext = "dot"
            if rext == "":
                rext = ext
            if ext is not rext:
                fileName += "." + rext
            if Constants.valid_ext(rext, Constants.FILE_TYPES_OPEN):
                self.filename = fileName
                self.save()
            else:
                self.warn("Invalid File", "It looks like you want to save a file with an invalid file type of '%s'."
                                          "Please try another extension." % rext)

    def export(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, t = QtWidgets.QFileDialog\
            .getSaveFileName(self, "Export a Graphviz File", "", "All Files (*);;" + Constants.file_list_save(),
                             options=options)
        if fileName:
            ext = fileName.split(".")[-1]
            rext = Constants.obtain_ext(t)
            if len(fileName.split(".")) == 1:
                ext = "plain"
            if rext == "":
                rext = ext
            if ext is not rext:
                fileName += "." + rext
            if Constants.valid_ext(rext, Constants.FILE_TYPES_SAVE):
                try:
                    dot = Source(self.editor.toPlainText())
                    contents = dot.pipe(ext)
                    with open(self.filename, 'bw') as myfile:
                        myfile.write(contents)
                except graphviz.backend.CalledProcessError as e:
                    self.error("Uh oh!", "It looks like there are some errors in your dot file. Cannot export!\n" +
                               e.stderr.decode("utf-8"))
                except Exception as e:
                    self.error("Uh oh!", "It looks as if something went wrong whilst trying to save this file.\n" +
                               str(e))

    def displayGraph(self):
        self.scene.clear()
        dot = Source(self.editor.toPlainText())
        bdata = dot.pipe('jpg')
        image = QtGui.QImage()
        image.loadFromData(bdata)
        pixmap = QtGui.QPixmap.fromImage(image)
        self.scene.addPixmap(pixmap)

    def findReplace(self):
        self.find.show()

    def checkUpdates(self):
        checker = UpdateChecker(self)
        checker.exec_()

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
                   "<p>Created by <b>Randy Paredis</b>." % (Constants.APP_VERSION_NAME + " v" + Constants.APP_VERSION))

    def aboutQt(self):
        QtWidgets.QMessageBox.aboutQt(self)