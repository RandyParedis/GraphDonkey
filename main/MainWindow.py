"""Mainwindow for the GraphDonkey application.

Author: Randy Paredis
Date:   14/12/2019
"""
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from main.FindReplace import FindReplace
from main.Preferences import Preferences, bool
from main.Snippets import Snippets
from main.extra.IOHandler import IOHandler
from main.editor.CodeEditor import EditorWrapper, StatusBar
from main.extra.GraphicsView import GraphicsView
from main.extra import Constants, tabPathnames
from main.wizards.UpdateWizard import UpdateWizard
from markdown.extensions.legacy_em import LegacyEmExtension as legacy_em
import os, sys, chardet, markdown
from main.extra.qrc import tango

from main.plugins import PluginLoader
from main.wizards.WelcomeWizard import WelcomeWizard

Config = IOHandler.get_preferences()
pluginloader = PluginLoader.instance()

rccv = tango.rcc_version

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowFlags())
        uic.loadUi(IOHandler.dir_ui("MainWindow.ui"), self)
        self.files.installEventFilter(TabPressEater())
        self.view = GraphicsView(self, self.viewDock)
        self.viewDockWidgetContents.layout().addWidget(self.view)
        self.view.zoomed.connect(self.zoomed)

        self.transformationActions = []
        self.disableDisplay = []
        self.lockDisplay(False)

        self.files.clear()
        self.files.currentChanged.connect(self.tabChanged)
        self.files.tabBarClicked.connect(self.tabChanged)
        self.files.tabCloseRequested.connect(self.closeFile)
        self.updateTitle()
        self.setStatusBar(QtWidgets.QStatusBar())

        if len(Config.allKeys()) == 0:
            wiz = WelcomeWizard()
            wiz.exec_()

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
        self.action_Undo.triggered.connect(lambda: self.editorEvent("undo"))
        self.action_Redo.triggered.connect(lambda: self.editorEvent("redo"))
        self.action_Select_All.triggered.connect(lambda: self.editorEvent("selectAll"))
        self.action_Clear.triggered.connect(lambda: self.editorEvent("clearContents"))
        self.action_Delete.triggered.connect(lambda: self.editorEvent("delete"))
        self.action_Copy.triggered.connect(lambda: self.editorEvent("copy"))
        self.action_Paste.triggered.connect(lambda: self.editorEvent("paste"))
        self.action_Cut.triggered.connect(lambda: self.editorEvent("cut"))
        self.action_Duplicate.triggered.connect(lambda: self.editorEvent("duplicate"))
        self.action_Comment.triggered.connect(lambda: self.editorEvent("comment"))
        self.action_Indent.triggered.connect(lambda: self.editorEvent("indent"))
        self.action_Unindent.triggered.connect(lambda: self.editorEvent("unindent"))
        self.action_Auto_Indent.triggered.connect(lambda: self.editorEvent("autoIndent"))
        self.action_Move_Up.triggered.connect(lambda: self.editorEvent("moveUp"))
        self.action_Move_Down.triggered.connect(lambda: self.editorEvent("moveDown"))
        self.action_Goto_Line.triggered.connect(lambda: self.editorEvent("goto"))
        self.action_Find.triggered.connect(self.findReplace)
        self.action_Autocomplete.triggered.connect(lambda: self.editorEvent("complete"))
        self.action_UpperCase.triggered.connect(lambda: self.editorEvent("uppercase"))
        self.action_LowerCase.triggered.connect(lambda: self.editorEvent("lowercase"))
        self.action_WordCase.triggered.connect(lambda: self.editorEvent("wordcase"))
        self.action_SentenceCase.triggered.connect(lambda: self.editorEvent("sentenceCase"))
        self.action_DromedaryCase.triggered.connect(lambda: self.editorEvent("dromedaryCase"))
        self.action_PascalCase.triggered.connect(lambda: self.editorEvent("pascalCase"))
        self.action_SnakeCase.triggered.connect(lambda: self.editorEvent("snakeCase"))
        self.viewDock.closeEvent = self.viewDockCloseEvent
        self.action_Snippets.triggered.connect(self.openSnippets)
        self.action_Next_File.triggered.connect(lambda: self.changeTab(self.files.currentIndex() + 1))
        self.action_Previous_File.triggered.connect(lambda: self.changeTab(self.files.currentIndex() - 1))
        self.action_Render.triggered.connect(self.forceDisplay)
        self.action_Save_Rendered_View.triggered.connect(self.view.save)
        self.action_View_Parse_Tree.triggered.connect(lambda: self.editorEvent("viewParseTree"))
        self.action_Zoom_In.triggered.connect(self.view.zoomIn)
        self.action_Zoom_Out.triggered.connect(self.view.zoomOut)
        self.action_Reset_Zoom.triggered.connect(self.view.resetZoom)
        self.action_Zoom_To_Fit.triggered.connect(self.view.zoomToFit)
        self.action_Help.triggered.connect(self.help)
        self.action_Report_Issue.triggered.connect(self.reportIssue)
        self.action_Updates.triggered.connect(self.updatesWizard)
        self.action_Qt.triggered.connect(self.aboutQt)
        self.action_GraphDonkey.triggered.connect(self.aboutGraphDonkey)

        # Set Transformation Functions
        trns = []
        for p in pluginloader.get():
            for t in p.types:
                target = p.types[t].get("transformer", {})
                for c in target:
                    if c != t and c in pluginloader.getFileTypes().keys():
                        trns.append((t, c, target[c]))
        for fr, to, convfunc in trns:
            action = QtWidgets.QAction("%s > %s" % (fr, to))
            action.triggered.connect(lambda b, fnc=convfunc, to=to: self.transform(fnc, to))
            action.setData(fr)
            self.menu_Transform.addAction(action)
            self.transformationActions.append(action)
        self.tabChanged(self.files.currentIndex())

    def setStatusBar(self, status: StatusBar):
        if self.statusBar() and isinstance(self.statusBar(), StatusBar):
            self.statusBar().setParent(self.statusBar().wrapper)
        super(MainWindow, self).setStatusBar(status)

    def editorEvent(self, name):
        edit = self.editor()
        if edit is not None:
            getattr(edit, name)()

    def zoomed(self, z):
        self.action_Zoom_In.setDisabled(self.view.isMaximalZoomed())
        self.action_Zoom_Out.setDisabled(self.view.isMinimalZoomed())

    def setUndoEnabled(self, on):
        self.action_Undo.setEnabled(on)

    def setRedoEnabled(self, on):
        self.action_Redo.setEnabled(on)

    def setEditEnabled(self, on):
        if on is False:
            self.setUndoEnabled(on)
            self.setRedoEnabled(on)
        self.action_Select_All.setEnabled(on)
        self.action_Clear.setEnabled(on)
        self.action_Delete.setEnabled(on)
        self.action_Copy.setEnabled(on)
        self.action_Paste.setEnabled(on)
        self.action_Cut.setEnabled(on)
        self.action_Duplicate.setEnabled(on)
        self.action_Comment.setEnabled(on)
        self.action_Indent.setEnabled(on)
        self.action_Unindent.setEnabled(on)
        self.action_Auto_Indent.setEnabled(on)
        self.action_Find.setEnabled(on)
        self.action_Autocomplete.setEnabled(on)
        self.action_UpperCase.setEnabled(on)
        self.action_LowerCase.setEnabled(on)
        self.action_WordCase.setEnabled(on)
        self.action_SentenceCase.setEnabled(on)
        self.action_DromedaryCase.setEnabled(on)
        self.action_PascalCase.setEnabled(on)
        self.action_SnakeCase.setEnabled(on)
        self.action_Goto_Line.setEnabled(on)

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

    def setEditorType(self, type, idx=-1):
        if idx == -1:
            idx = self.files.currentIndex()
        wrapper = self.files.widget(idx)
        if wrapper is not None:
            wrapper.setType(type)

    def editor(self, idx=-1):
        if idx == -1:
            idx = self.files.currentIndex()
        if idx > -1:
            self.setEditEnabled(True)
            self.action_Close_File.setEnabled(True)
            self.action_Export.setEnabled(True)
            self.action_Render.setEnabled(True)
            return self.files.widget(idx).editor
        self.setEditEnabled(False)
        self.action_Export.setEnabled(False)
        self.action_Close_File.setEnabled(False)
        self.action_Render.setEnabled(False)
        return None

    def editorWrapper(self):
        idx = self.files.currentIndex()
        return self.files.widget(idx)

    def tabChanged(self, index):
        self.updateTitle()
        edit = self.editor(index)
        if edit is not None:
            edit.highlighter.rehighlight()
            self.setStatusBar(edit.wrapper.statusBar)
            self.displayGraph()
            self.setUndoEnabled(edit.document().isUndoAvailable())
            self.setRedoEnabled(edit.document().isRedoAvailable())
            ft = edit.wrapper.filetype.currentText()
            for ac in self.transformationActions:
                ac.setEnabled(ac.data() == ft)

    def changeTab(self, index):
        if self.files.count() > 0:
            index %= self.files.count()
            self.files.setCurrentIndex(index)
            edit = self.editor()
            if edit is not None:
                edit.setFocus(True)

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
        label = self.statusBar().statusMessage
        metrics = QtGui.QFontMetrics(label.font())
        elidedText = metrics.elidedText(text, QtCore.Qt.ElideRight, label.width())
        label.setText(elidedText)
        label.setToolTip(text)

    def newTab(self, label):
        editor = EditorWrapper(self)
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
            if settings.contains("recents"):
                self.recents = settings.value("recents")
            if settings.contains("zoomlevel"):
                self.view.zoomTo(float(settings.value("zoomlevel")))
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
                succ = self.openFile(files[file], True)
                if succ and file < len(cursors):
                    curs = self.editor().textCursor()
                    curs.setPosition(cursors[file][0])
                    curs.setPosition(cursors[file][1], QtGui.QTextCursor.KeepAnchor)
                    self.editor().setTextCursor(curs)
            self.changeTab(active)
        self.updateRecents()

    def closeEvent(self, event: QtGui.QCloseEvent):
        self.lockDisplay()
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

        self.releaseDisplay()

        if saved:
            settings = IOHandler.get_settings()
            if bool(Config.value("rememberLayout", True)):
                settings.setValue("geometry", self.saveGeometry())
                state = self.saveState()
                settings.setValue("windowState", state)
                settings.setValue("recents", self.recents)
                settings.setValue("zoomlevel", self.view.zoomlevel)
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
        if self.recents is None:
            return

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

    def updateFileTypes(self):
        for i in range(self.files.count()):
            self.updateFileType(i)

    def updateFileType(self, indx=-1):
        edit = self.editor(indx)
        if edit is None:
            return

        for i in range(self.files.count()):
            self.editor(i).wrapper.setTypes()

        fn = edit.filename

        if fn == '':
            return

        ext = fn.split(".")[-1]
        exts = pluginloader.getFileExtensions()

        # Detect line separator
        with open(fn, "r", newline='') as file:
            text = file.read()
            if "\r\n" in text:
                linesep = '\r\n'
            elif "\n" in text:
                linesep = '\n'
            elif "\r" in text:
                linesep = '\r'
            else:
                linesep = os.linesep

        # Actually open the file
        with open(fn, "rb") as myfile:
            data = myfile.read()
            enc = chardet.detect(data)
            et = enc['encoding']
            lan = enc['language']
            idx = self.editor().wrapper.encoding.findText(et.upper())
            if idx == -1:
                self.warn("Unknown File Encoding", "Cannot identify encoding.\n"
                                                   "Detected as %s.\n"
                                                   "Reverting to UTF-8."
                          % (et.upper() + ("" if len(lan) == 0 else " (%s)" % lan)))
                et = 'utf-8'
            if et == 'ascii':  # Only use ASCII if specified by the user, otherwise use the superset
                et = 'utf-8'
            data = data.decode(et)
        edit.wrapper.encoding.setCurrentText(et.upper())
        edit.wrapper.statusBar.setLineSep(linesep)
        c = edit.textCursor()
        cstr = c.selectionStart()
        cend = c.selectionEnd()
        edit.setText(data)
        c.setPosition(cstr)
        c.setPosition(cend, QtGui.QTextCursor.KeepAnchor)
        edit.setTextCursor(c)
        edit.filecontents = data.replace(linesep, "\n")
        self.setEditorType(Constants.lookup(ext, exts, ""), indx)

    def openFile(self, fileName, ignoreopen=False):
        self.lockDisplay()
        if fileName and fileName != "":
            valid = True
            try:
                edit = self.editor()
                if ignoreopen or edit is None or not (edit.filename == "" and edit.isSaved()):
                    self.newTab(fileName)
                self.editor().filename = fileName
                self.updateFileType()
                self.updateRecents(fileName)
            except IOError as e:
                self.warn("I/O Error", "%s\nPlease retry.\nFilename: %s" % (str(e), fileName))
                self.closeFile()
                valid = False
            self.updateTitle()
            self.releaseDisplay()
            return valid
        else:
            self.new()
        self.releaseDisplay()
        return True

    def io(self):
        folder = ""
        edit = self.editor()
        if edit is not None:
            folder = IOHandler.directory(edit.filename)
        if len(folder) == 0:
            folder = os.path.expanduser("~")
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        return options, folder

    def open(self):
        options, folder = self.io()
        fileName, _ = QtWidgets.QFileDialog\
            .getOpenFileName(self, "Open a File", folder,
                             "All Files (*);;" + Constants.file_list(pluginloader.getFileExtensions()), options=options)
        if fileName != "":
            self.openFile(fileName)

    def save(self):
        editor = self.editor()
        if editor is None: return
        if editor.filename == "":
            self.saveAs()
        else:
            contents = editor.toPlainText()
            contents = contents.replace("\n", editor.wrapper.linesep.currentData())
            try:
                bc = bytes(contents, editor.wrapper.encoding.currentData())
                with open(editor.filename, 'wb') as myfile:
                    myfile.write(bc)
                editor.save()
                self.updateTitle()
            except Exception as e:
                self.error("Error", str(e))
        editor.stoppedTyping()

    def saveAll(self):
        old = self.files.currentIndex()
        for idx in range(self.files.count()):
            self.changeTab(idx)
            self.save()
        self.changeTab(old)

    def saveAs(self):
        options, folder = self.io()
        fileName, t = QtWidgets.QFileDialog\
            .getSaveFileName(self, "Save a File", folder,
                             "All Files (*);;" + Constants.file_list(pluginloader.getFileExtensions()), options=options)
        if fileName:
            spt = fileName.split(".")
            ext = spt[-1]
            rext = Constants.obtain_exts(t)
            if len(rext) == 0:
                fext = pluginloader.getFileExtensions()
                # FIXME: TypeError: unhashable type: 'list'
                rext = [e for x in fext for e in fext[x]]
                # print(fext, fext.items())
                # rext = fext[next(iter(fext.items()))] if len(fext) > 0 else []
            if ext not in rext:
                ext = rext[0] if len(rext) > 0 else "txt"
                fileName += "." + ext
            if Constants.valid_ext(ext, pluginloader.getFileExtensions()):
                self.editor().filename = fileName
                self.save()
                self.updateFileType()
            else:
                self.warn("Invalid File", "It looks like you want to save a file with an invalid file type of '%s'."
                                          "Please try another extension." % rext)

    def export(self):
        # SHOULD ONLY BE POSSIBLE WHEN A FILE IS OPEN
        edit = self.editor()
        if edit is None:
            return
        ename = edit.wrapper.engine.currentText()
        engine = pluginloader.getEngines().get(ename, None)
        if engine is None:
            return
        export = engine.get("export", {})
        _exts = export.get("extensions", [])
        if "exporter" not in export or len(_exts) == 0:
            self.error("Cannot Export", "The current selected engine (%s) cannot export." % ename)
            return
        exts = {}
        ftps = Constants.FILE_TYPES
        ftps.update(engine.get("filetypes", {}))
        for ft in _exts:
            name = Constants.lookup(ft, ftps)
            if name is None:
                name = ft.upper()
            if name in exts:
                exts[name].append(ft)
            else:
                exts[name] = [ft]
        options, folder = self.io()
        fileName, t = QtWidgets.QFileDialog \
            .getSaveFileName(self, "Export a File", folder, Constants.file_list(exts), options=options)
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
                        return self.export()
            if Constants.valid_ext(ext, exts):
                try:
                    contents = export["exporter"](self.editor().transform(ename), ext)
                    if contents is not None and len(contents) > 0:
                        with open(fileName, 'bw') as myfile:
                            myfile.write(contents)
                    else:
                        self.error("Cannot Export", "It looks as if you cannot export such a file.\n"
                                                    "This is either because the graph cannot be expressed as a %s file,"
                                                    " or due to an error in the rendering engine you're currently using"
                                                    " (which is '%s').\n\n"
                                                    "Please try another file extension, or refer to the current"
                                                    " engine's documentation." % (ext.upper(), ename))
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
        if old >= self.files.count():
            old = self.files.count() - 1
        if old == -1:
            self.view.clear()
            self.setStatusBar(QtWidgets.QStatusBar())
        else:
            self.changeTab(old)
        self.updateTitle()

    def forceDisplay(self):
        if self.canDisplay():
            res = self.displayGraph()
            if res is not None and len(res) > 0:
                self.error("Error", res)
        else:
            self.error("Cannot Render", "A process is currently trying to render the graph, please wait.")

    def displayGraph(self):
        if self.canDisplay() and self.editor() is not None:
            ename = self.editorWrapper().engine.currentText()
            if ename == "": return None
            try:
                engine = pluginloader.getEngines().get(ename, None)
                if engine is None:
                    raise RuntimeError("Unknown rendering engine '%s'." % ename)
                res = self.editor().transform(ename)
                if res is not None:
                    bdata = engine["convert"](res)
                    self.view.clear()
                    self.view.add(bdata)
            except Exception as e:
                print(str(e), file=sys.stderr)
                self.updateStatus(str(e))
                return str(e)
        return None

    def openSnippets(self):
        self.snippets.exec_()

    def findReplace(self):
        sel = self.editor().textCursor().selectedText()
        if sel != "":
            self.find.le_find.setText(sel)
            self.find.le_replace.setText("")
        self.find.show()

    def transform(self, func, to):
        self.lockDisplay()
        editor = self.editor()
        txt = editor.toPlainText()
        res = func(txt, editor.highlighter.parser.parse(txt))
        self.new()
        self.editor().setPlainText(res)
        self.editor().wrapper.setType(to)
        self.releaseDisplay()

    def help(self):
        QtGui.QDesktopServices().openUrl(QtCore.QUrl("https://github.com/RandyParedis/GraphDonkey/wiki"))

    def reportIssue(self):
        QtGui.QDesktopServices().openUrl(QtCore.QUrl("https://github.com/RandyParedis/GraphDonkey/issues/new/choose"))

    def updatesWizard(self):
        wiz = UpdateWizard(self)
        app = QtWidgets.QApplication.instance()
        app.setQuitOnLastWindowClosed(False)
        self.close()
        app.setQuitOnLastWindowClosed(True)
        wiz.show()

    def aboutGraphDonkey(self):
        with open(IOHandler.dir_root("README.md")) as file:
            ctns = "\n\n".join(file.read().split("\n\n")[2:5])
        QtWidgets\
            .QMessageBox\
            .about(self,
                   "About GraphDonkey",
                   "%s<p>Current version is <b>%s</b>.</p><p>Created and Maintained by <b>Randy Paredis</b>." %
                   (markdown.markdown(ctns, extensions=[legacy_em()]),
                    Constants.APP_VERSION_NAME + " v" + Constants.APP_VERSION))

    def aboutQt(self):
        QtWidgets.QMessageBox.aboutQt(self)


class TabPressEater(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and \
                event.key() == QtCore.Qt.Key_Tab and event.modifiers() & QtCore.Qt.ControlModifier:
            return True
        return QtCore.QObject.eventFilter(self, obj, event)
