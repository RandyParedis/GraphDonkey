"""Mainwindow for the GraphDonkey application.

Author: Randy Paredis
Date:   14/12/2019
"""
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from main.FindReplace import FindReplace
from main.Preferences import Preferences, bool
from main.Snippets import Snippets
from main.extra.IOHandler import IOHandler
from main.CodeEditor import CodeEditor
from main.extra import Constants, tabPathnames, tango
from main.UpdateChecker import UpdateChecker
from graphviz import Source
import graphviz, subprocess

Config = IOHandler.get_preferences()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowFlags())
        uic.loadUi(IOHandler.dir_ui("MainWindow.ui"), self)
        self.scene = self.view.scene()
        if self.scene is None:
            self.scene = QtWidgets.QGraphicsScene(self.view)
            self.view.setScene(self.scene)

        self.disableDisplay = []
        self.lockDisplay(False)

        # Set Statusbar
        self.statusMessage = QtWidgets.QLabel("")
        self.positionIndicator = QtWidgets.QLabel(":")
        self.encIndicator = QtWidgets.QLabel("")
        self.positionIndicator.setAlignment(QtCore.Qt.AlignRight)
        self.encIndicator.setAlignment(QtCore.Qt.AlignRight)
        self.statusBar().addPermanentWidget(QtWidgets.QLabel(" "))
        self.statusBar().addPermanentWidget(self.statusMessage, 7)
        self.statusBar().addPermanentWidget(self.positionIndicator, 1)
        self.statusBar().addPermanentWidget(self.encIndicator, 1)
        self.statusBar().addPermanentWidget(QtWidgets.QLabel(" "))

        self.files.clear()
        self.files.tabBar().setSelectionBehaviorOnRemove(QtWidgets.QTabBar.SelectPreviousTab)
        self.files.currentChanged.connect(self.tabChanged)
        self.files.tabCloseRequested.connect(self.closeFile)
        self.updateTitle()

        self.preferences = Preferences(self)
        self.preferences.apply()

        self.recents = []
        self.restore()

        self.releaseDisplay()

        self.find = FindReplace(self, self.editor())
        self.snippets = Snippets(self)

        # Set menu
        self.action_New.triggered.connect(self.new)
        self.action_Open.triggered.connect(self.open)
        self.action_Save.triggered.connect(self.save)
        self.action_Save_All.triggered.connect(self.saveAll)
        self.action_Save_As.triggered.connect(self.saveAs)
        self.action_Export.triggered.connect(self.export)
        self.action_Preferences.triggered.connect(self.preferences.exec_)
        self.action_Close_File.triggered.connect(self.closeFile)
        self.action_Exit.triggered.connect(self.close)
        self.action_Undo.triggered.connect(lambda: self.editor().undo())
        self.action_Redo.triggered.connect(lambda: self.editor().redo())
        self.action_Select_All.triggered.connect(lambda: self.editor().selectAll())
        self.action_Delete.triggered.connect(lambda: self.editor().delete())
        self.action_Copy.triggered.connect(lambda: self.editor().copy())
        self.action_Paste.triggered.connect(lambda: self.editor().paste())
        self.action_Cut.triggered.connect(lambda: self.editor().cut())
        self.action_Duplicate.triggered.connect(lambda: self.editor().duplicate())
        self.action_Comment.triggered.connect(lambda: self.editor().comment())
        self.action_Indent.triggered.connect(lambda: self.editor().indent())
        self.action_Unindent.triggered.connect(lambda: self.editor().unindent())
        self.action_Auto_Indent.triggered.connect(lambda: self.editor().autoIndent())
        self.action_Find.triggered.connect(self.findReplace)
        self.action_Autocomplete.triggered.connect(lambda: self.editor().complete())
        self.viewDock.closeEvent = self.viewDockCloseEvent
        self.action_Snippets.triggered.connect(self.openSnippets)
        self.action_Render.triggered.connect(self.forceDisplay)
        # self.action_CheckUpdates.triggered.connect(self.checkUpdates)
        self.action_Graphviz.triggered.connect(self.aboutGraphviz)
        self.action_Qt.triggered.connect(self.aboutQt)
        self.action_GraphDonkey.triggered.connect(self.aboutGraphDonkey)

    def lockDisplay(self, disp=False):
        if disp and self.canDisplay():
            self.displayGraph()
        self.disableDisplay.append(True)

    def releaseDisplay(self):
        if len(self.disableDisplay) > 0:
            self.disableDisplay.pop()
        if self.canDisplay():
            self.displayGraph()

    def canDisplay(self):
        return len(self.disableDisplay) == 0

    def editor(self, idx=-1):
        if idx == -1:
            idx = self.files.currentIndex()
        if idx > -1:
            return self.files.widget(idx)
        return None

    def tabChanged(self, index):
        self.updateTitle()
        edit = self.editor(index)
        if edit is not None:
            edit.highlighter.rehighlight()
            if edit.filename == "":
                self.displayGraph()

    def changeTab(self, index):
        self.files.setCurrentIndex(index)
        self.editor().setFocus(True)

    def updateTabs(self):
        names = []
        for t in range(self.files.count()):
            editor = self.editor(t)
            fname = editor.filename
            if fname == '':
                fname = 'undefined'
            if not editor.isSaved():
                fname += '*'
            names.append(fname)
        names = tabPathnames(names)

        for i in range(len(names)):
            self.files.setTabText(i, names[i])
        
    def updateTitle(self):
        if self.editor() is not None:
            rest = "undefined"
            if self.editor().filename != "":
                rest = self.editor().filename
            if not self.editor().isSaved():
                rest += "*"
            self.setWindowTitle(" " + rest)

            self.updateTabs()
        else:
            self.setWindowTitle("")

    def updateStatus(self, text):
        self.statusMessage.setText(text)

    def newTab(self, label):
        editor = CodeEditor(self)
        editor.textChanged.connect(self.textChangedEvent)
        self.files.addTab(editor, label)
        self.changeTab(self.files.count() - 1)
        self.preferences.applyEditor()

    def viewDockCloseEvent(self, event):
        self.action_Show_Render_Area.setChecked(False)
        self.viewDock.setVisible(False)

    def restore(self):
        # Restore layout from memory iff needs be/possible
        settings = IOHandler.get_settings()
        if bool(Config.value("rememberLayout", True)):
            if settings.contains("geometry"):
                self.restoreGeometry(settings.value("geometry"))
            if settings.contains("windowState"):
                self.restoreState(settings.value("windowState"))
            if self.isMaximized():
                # WORKAROUND FOR INVALID RESTORE OF STATE/GEOMETRY
                #   https://bugreports.qt.io/browse/QTBUG-46620
                self.setGeometry(QtWidgets.QApplication.desktop().availableGeometry(self))
            if settings.value("recents", None) is not None:
                self.recents = settings.value("recents")
        restore = int(Config.value("restore", 0))
        if restore == 0:
            self.new()
        elif restore == 1:
            files = settings.value("open", list())
            cursors = settings.value("cursors", list())
            active = int(settings.value("active", 0))
            if files is None:
                files = []
            if cursors is None:
                cursors = []
            for file in range(len(files)):
                self.openFile(files[file])
                if file < len(cursors):
                    curs = self.editor().textCursor()
                    curs.setPosition(cursors[file][0])
                    curs.setPosition(cursors[file][1], QtGui.QTextCursor.KeepAnchor)
                    self.editor().setTextCursor(curs)
            self.changeTab(active)
        self.updateRecents()

    def closeEvent(self, event: QtGui.QCloseEvent):
        saved = True
        old = self.files.currentIndex()
        for tab in range(self.files.count()):
            self.changeTab(tab)
            if not self.editor().isSaved():
                saved = False
                break
        self.changeTab(old)
        if not saved:
            saved = self.question("Unsaved Changes", "It appears there are some unchanged changes.\n"
                                                     "Are you sure you want quit? All changes will be lost.")

        if saved:
            settings = IOHandler.get_settings()
            if bool(Config.value("rememberLayout", True)):
                settings.setValue("geometry", self.saveGeometry())
                state = self.saveState()
                settings.setValue("windowState", state)
                settings.setValue("recents", self.recents)
            if int(Config.value("restore", 0)) == 1:
                files = list()
                cursors = list()
                for tab in range(self.files.count()):
                    editor = self.editor(tab)
                    files.append(editor.filename)
                    curs = editor.textCursor()
                    cursors.append((curs.selectionStart(), curs.selectionEnd()))
                settings.setValue("open", files)
                settings.setValue("cursors", cursors)
                settings.setValue("active", self.files.currentIndex())

            QtWidgets.QMainWindow.closeEvent(self, event)
        else:
            event.ignore()

    def textChangedEvent(self):
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
        clr = Config.value("ks/clear_recents")
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
        self.newTab("undefined *")
        self.updateTitle()

    def openFile(self, fileName):
        if fileName and fileName != "":
            ext = fileName.split(".")[-1]
            if Constants.valid_ext(ext, Constants.FILE_TYPES_OPEN):
                try:
                    with open(fileName, "rb") as myfile:
                        data = myfile.read()
                        # TODO: On decoding crash => find actual encoding?
                        data = data.decode(Config.value("encoding"))
                    self.newTab(fileName)
                    self.editor().setText(data)
                    self.updateRecents(fileName)
                    self.editor().filename = fileName
                    self.editor().filecontents = data
                except IOError:
                    self.warn("File not found", "You're trying to open a file that does not exist. Please retry.")
                self.updateTitle()
            else:
                self.warn("Invalid File", "It looks like this file cannot be opened.")
        else:
            self.new()

    def open(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog\
            .getOpenFileName(self, "Open a Graphviz File", "", "All Files (*);;" + Constants.file_list_open(),
                             options=options)
        if fileName != "":
            self.openFile(fileName)

    def save(self):
        editor = self.editor()
        if editor is not None and editor.filename == "":
            self.saveAs()
        else:
            contents = editor.toPlainText()
            contents = contents.replace("\n", Constants.ENDINGS[int(Config.value("endings"))])
            bc = bytes(contents, Config.value("encoding"))
            # TODO: error on invalid encoding
            with open(editor.filename, 'wb') as myfile:
                myfile.write(bc)
            editor.save()
            self.updateTitle()

    def saveAll(self):
        old = self.files.currentIndex()
        for idx in range(self.files.count()):
            self.changeTab(idx)
            self.save()
        self.changeTab(old)

    def saveAs(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, t = QtWidgets.QFileDialog\
            .getSaveFileName(self, "Save a Graphviz File", "", "All Files (*);;" + Constants.file_list_open(),
                             options=options)
        if fileName:
            spt = fileName.split(".")
            ext = spt[-1]
            rext = Constants.obtain_exts(t)
            if len(spt) == 1 or len(rext) == 0:
                ext = "dot"
            if ext not in rext:
                ext = rext[0]
                fileName += "." + ext
            if Constants.valid_ext(ext, Constants.FILE_TYPES_OPEN):
                self.editor().filename = fileName
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
                    dot = Source(self.editor().toPlainText())
                    contents = dot.pipe(ext)
                    with open(self.editor().filename, 'bw') as myfile:
                        myfile.write(contents)
                except graphviz.backend.CalledProcessError as e:
                    self.error("Uh oh!", "It looks like there are some errors in your dot file. Cannot export!\n" +
                               e.stderr.decode("utf-8"))
                except Exception as e:
                    self.error("Uh oh!", "It looks as if something went wrong whilst trying to save this file.\n" +
                               str(e))

    def closeFile(self, idx=-1):
        old = self.files.currentIndex()
        if idx == -1 or idx is False:
            idx = old
        else:
            self.changeTab(idx)
        close = True
        if not self.editor().isSaved():
            close = self.question("Unsaved Changes", "It appears there are some unchanged changes in this file.\n"
                                                     "Are you sure you want to close it? All changes will be lost.")
        if close:
            self.files.removeTab(idx)
        self.changeTab(old)
        self.updateTitle()

    def forceDisplay(self):
        if self.canDisplay():
            self.displayGraph()
        else:
            self.error("Cannot Render", "A process is currently trying to render the graph, please wait.")

    def displayGraph(self):
        if self.canDisplay() and self.editor() is not None:
            self.scene.clear()
            try:
                dot = Source(self.editor().toPlainText(), engine=Config.value("graphviz/engine"))
                bdata = dot.pipe(Config.value("graphviz/format"), Config.value("graphviz/renderer"),
                                 Config.value("graphviz/formatter"))
                image = QtGui.QImage()
                image.loadFromData(bdata)
                pixmap = QtGui.QPixmap.fromImage(image)
                self.scene.addPixmap(pixmap)
            except graphviz.backend.CalledProcessError as e:
                self.error("Error", e.stderr.decode("utf-8"))

    def openSnippets(self):
        self.snippets.exec_()

    def findReplace(self):
        sel = self.editor().textCursor().selectedText()
        if sel != "":
            self.find.le_find.setText(sel)
            self.find.le_replace.setText("")
        self.find.show()

    def checkUpdates(self):
        checker = UpdateChecker(self)
        checker.exec_()

    def aboutGraphviz(self):
        cmd = [Config.value("graphviz/engine"), "-V"]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        version = " ".join(out.decode("utf-8").split(" ")[-2:])
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
                   "<a href='https://www.graphviz.org/'>www.graphviz.org</a>.</p>" % version)

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