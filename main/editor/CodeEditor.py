"""The code editor of GraphDonkey, with a few features:

- Syntax Highlighting
- Error Highlighting
- Line Numbers
    Based on https://stackoverflow.com/questions/2443358/how-to-add-lines-numbers-to-qtextedit
- Selection/Line Events (Duplicate, Copy, Cut, Comment/Uncomment, Auto-Indent, Indent/Unindent...)
- Parenthesis Matching
    Based on QtQuarterly 31: https://doc.qt.io/archives/qq/QtQuarterly31.pdf
- Auto-Expand Squiggly and Square brackets

Author: Randy Paredis
Date:   12/14/2019
"""
from PyQt5 import QtGui, QtWidgets, QtCore

from main.extra import Constants, left
from main.extra.IOHandler import IOHandler
from main.editor.Highlighter import BaseHighlighter
from main.extra.GraphicsView import GraphicsView
from main.Preferences import bool
from main.plugins import PluginLoader
from main.editor.Intellisense import Types
import os

pluginloader = PluginLoader.instance()
Config = IOHandler.get_preferences()

class StatusBar(QtWidgets.QStatusBar):
    def __init__(self, wrapper, parent=None):
        super(StatusBar, self).__init__(parent)
        self.wrapper = wrapper
        self.statusMessage = QtWidgets.QLabel("")
        self.statusMessage.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.positionIndicator = QtWidgets.QLabel(":")
        self.positionIndicator.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.leCombo = QtWidgets.QComboBox()
        self.seps = {
            "Posix (LF)": '\n',
            "Mac OS [Pre-OSX] (CR)": '\r',
            "Windows (CRLF)": '\r\n'
        }
        for name in self.seps:
            self.leCombo.addItem(name, self.seps[name])
        self.setLineSep(os.linesep)

        self.encCombo = QtWidgets.QComboBox()
        self.encCombo.addItem("UTF-8", "utf-8")
        self.encCombo.addItem("UTF-16", "utf-16")
        self.encCombo.addItem("ASCII", "ascii")
        self.encCombo.addItem("ISO-8859-1", "latin1")

        self.ftCombo = QtWidgets.QComboBox()

        rdr = QtWidgets.QLabel("Render with:")
        rdr.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.rendererCombo = QtWidgets.QComboBox()

        self.addPermanentWidget(QtWidgets.QLabel(" "))
        self.addPermanentWidget(self.statusMessage, 7)
        self.addPermanentWidget(self.positionIndicator, 1)
        self.addPermanentWidget(self.leCombo, 1)
        self.addPermanentWidget(self.encCombo, 1)
        self.addPermanentWidget(self.ftCombo, 0)
        self.addPermanentWidget(rdr, 1)
        self.addPermanentWidget(self.rendererCombo, 0)
        self.addPermanentWidget(QtWidgets.QLabel(" "))

    def setLineSep(self, sep):
        seps = {self.seps[n]: n for n in self.seps}
        self.leCombo.setCurrentText(seps.get(sep, ""))

class EditorWrapper(QtWidgets.QWidget):
    def __init__(self, parent):
        super(EditorWrapper, self).__init__(parent)
        self._layout = QtWidgets.QGridLayout()
        self.editor = CodeEditor(self)
        self.mainwindow = parent
        self.types = []
        self.statusBar = StatusBar(self)
        self.filetype = self.statusBar.ftCombo
        self.engine = self.statusBar.rendererCombo
        self.linesep = self.statusBar.leCombo
        self.encoding = self.statusBar.encCombo

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.editor, 0, 0, 1, -1)
        self.filetype.currentIndexChanged.connect(self.alter)
        self.setTypes()
        self.setLayout(self._layout)

    def setTypes(self):
        self.types = pluginloader.getFileTypes()
        txt = self.filetype.currentText()
        self.filetype.clear()
        for type in self.types:
            name, klass = self.types[type]
            self.filetype.addItem(name, klass)
        # TODO: determine filetype based on extension
        self.filetype.setCurrentText(txt)

    def alter(self, idx):
        self.engine.clear()
        if idx >= 0:
            data = self.filetype.itemData(idx)
            self.editor.alter(data(self.editor.document(), self.editor))
            self.editor.highlighter.rehighlight()
            ens = pluginloader.getEnginesForFileType(self.filetype.itemText(idx))
            for en in ens:
                self.engine.addItem(en)
            self.engine.setCurrentText(Config.value("view/engine"))
        self.mainwindow.displayGraph()

    def setType(self, type):
        self.filetype.setCurrentText(self.types[type][0])


class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)
        self.mainwindow = parent.parent()
        self.wrapper = parent
        self.lineNumberArea = LineNumberArea(self)

        self.undoAvailable.connect(self.mainwindow.setUndoEnabled)
        self.redoAvailable.connect(self.mainwindow.setRedoEnabled)

        self.blockCountChanged.connect(self.lineNrChanged)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.positionChangedSlot)
        self.textChanged.connect(self.textChangedSlot)

        self.updateLineNumberAreaWidth()
        self.highlightCurrentLine()
        self.highlighter = BaseHighlighter(self.document(), self)

        self.matches = []
        self.errors = []

        self.setMouseTracking(True)

        self.filename = ""
        self.filecontents = ""

        self.completer = None
        self.setCompleter()

        self.treeView = None

    def textChangedSlot(self):
        txt = self.toPlainText()
        if bool(Config.value("editor/emptyline")) and not txt.endswith(Constants.LINE_ENDING) \
                and not txt.endswith('\n'):
            curs = self.textCursor()
            curs.movePosition(QtGui.QTextCursor.End)
            curs.insertText(Constants.LINE_ENDING)
            curs = self.textCursor()
            curs.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
            if len(curs.selectedText()) == 0:
                curs.movePosition(QtGui.QTextCursor.PreviousCharacter)
                self.setTextCursor(curs)

    def alter(self, highlighter):
        self.highlighter.deleteLater()
        self.highlighter = highlighter

    def convert(self, engine):
        curs = self.textCursor()
        return self.highlighter.parser.convert(self.toPlainText(), engine,
                                               line=curs.block().blockNumber() + 1, col=curs.columnNumber())

    def positionChangedSlot(self):
        self.highlighter.storeErrors()
        if bool(Config.value("editor/highlightCurrentLine")):
            self.highlightCurrentLine()
        if bool(Config.value("editor/parentheses")):
            self.matchBrackets()
        if bool(Config.value("editor/useParser", True)):
            self.highlightErrors()
        self.highlightMatches()
        self.updateIndicator()
        self.mainwindow.updateTitle()

    def lineNrChanged(self):
        self.updateLineNumberAreaWidth()
        self.highlighter.rehighlight()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.mainwindow.action_Undo)
        menu.addAction(self.mainwindow.action_Redo)
        menu.addSeparator()
        menu.addAction(self.mainwindow.action_Copy)
        menu.addAction(self.mainwindow.action_Paste)
        menu.addAction(self.mainwindow.action_Cut)
        menu.addAction(self.mainwindow.action_Delete)
        menu.addSeparator()
        menu.addAction(self.mainwindow.action_Select_All)
        menu.exec_(event.globalPos())

    def isSaved(self):
        """Returns True if the file was saved."""
        if self.filename != "":
            return self.toPlainText() == self.filecontents
        txt = self.toPlainText()
        if bool(Config.value("editor/emptyline")):
            txt = txt[:-len(os.linesep)]
        return txt == ""

    def save(self):
        self.filecontents = self.toPlainText()
        if self.treeView is not None and self.treeView.isVisible():
            self.viewParseTree(False)

    def clearContents(self):
        self.selectAll()
        self.insertPlainText("")

    def clearFile(self):
        self.filename = ""
        self.filecontents = ""

    def setCompleter(self):
        self.completer = QtWidgets.QCompleter(self)
        self.completer.setModel(QtGui.QStandardItemModel())
        self.completer.setModelSorting(QtWidgets.QCompleter.CaseInsensitivelySortedModel)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setWrapAround(False)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)

    def insertCompletion(self, completion):
        comp, _ = self.highlighter.parser.visitor.completer.get(completion)
        if len(comp) == 0:
            text = completion
        else:
            text = comp[0][0] if comp[0][2] is None else comp[0][2]
        cursor = self.textCursor()
        extra = len(self.completer.completionPrefix())
        if extra > 0:
            cursor.movePosition(QtGui.QTextCursor.PreviousCharacter, n=extra)
        cursor.movePosition(QtGui.QTextCursor.EndOfWord, QtGui.QTextCursor.KeepAnchor)
        cursor.insertText(text)
        self.setTextCursor(cursor)

    def encapsulateText(self, o, c):
        curs = self.textCursor()
        s = curs.selectionStart()
        e = curs.selectionEnd()
        curs.beginEditBlock()
        curs.setPosition(s)
        self.setTextCursor(curs)
        self.insertPlainText(o)

        mc = True
        if s == e:
            ci = curs.block().userData().indexOf(curs.positionInBlock())
            cpos = self.getClosingBracketPos((o, c), curs.block(), ci)
            if cpos >= 0:
                curs.setPosition(cpos)
                oi = curs.block().userData().indexOf(curs.positionInBlock())
                opos = self.getOpeningBracketPos((o, c), curs.block(), oi - 1)
                if opos == s or opos == -1:
                    mc = False
        if mc:
            curs.setPosition(e + len(o))
            self.setTextCursor(curs)
            self.insertPlainText(c)
        curs.setPosition(s + len(o))
        curs.setPosition(e + len(o), QtGui.QTextCursor.KeepAnchor)
        curs.endEditBlock()
        self.setTextCursor(curs)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        paired = pluginloader.getPairedBrackets(self.wrapper.filetype.currentText())

        if self.completer.popup().isVisible():
            if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Tab]:
                completion = self.completer.popup().currentIndex().data()
                self.insertCompletion(completion)
                self.completer.popup().hide()
            elif event.key() == QtCore.Qt.Key_Escape:
                self.completer.popup().hide()
            else:
                QtWidgets.QPlainTextEdit.keyPressEvent(self, event)
                self.completer.popup().hide()
                self.complete()
        elif event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self.insertPlainText(Constants.LINE_ENDING)
            self.autoIndent()
            cursor = self.textCursor()
            cursor.beginEditBlock()
            pos = cursor.position()
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            txt = cursor.selectedText().lstrip()
            cursor.setPosition(pos)
            cursor.movePosition(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
            if len(txt) > 0 and txt[0] in [x[1] for x in paired] and len(cursor.selectedText()) == 0:
                cursor.setPosition(pos)
                cursor.insertText(Constants.LINE_ENDING)
                cursor.movePosition(QtGui.QTextCursor.Up, QtGui.QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)
                self.autoIndent()
                cursor.setPosition(pos)
                cursor.movePosition(QtGui.QTextCursor.EndOfLine)
                self.setTextCursor(cursor)
            cursor.endEditBlock()
        elif event.key() == QtCore.Qt.Key_Home:
            cursor = self.textCursor()
            cursor.movePosition(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
            txt = cursor.selectedText()
            if len(txt.strip()) == 0 != len(txt):
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            else:
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                cursor.movePosition(QtGui.QTextCursor.NextWord)
            self.setTextCursor(cursor)
        elif event.key() == QtCore.Qt.Key_Backspace:
            if bool(Config.value("editor/pairedBrackets")):
                curs = self.textCursor()
                s = curs.selectionStart()
                e = curs.selectionEnd()
                if s == e:
                    curs.movePosition(QtGui.QTextCursor.PreviousCharacter, QtGui.QTextCursor.KeepAnchor)
                    prev = curs.selectedText()
                    curs.setPosition(s)
                    curs.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
                    next = curs.selectedText()
                    curs.setPosition(s)
                    if (prev, next) in paired:
                        curs.movePosition(QtGui.QTextCursor.PreviousCharacter)
                        curs.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor, 2)
                        self.setTextCursor(curs)
            QtWidgets.QPlainTextEdit.keyPressEvent(self, event)
        elif event.key() not in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Tab]:
            if bool(Config.value("editor/pairedBrackets")):
                et = event.text()
                if et in [x[0] for x in paired]:    # OPEN
                    pair = [x for x in paired if et in x][0]
                    if pair[0] == pair[1]:
                        curs = self.textCursor()
                        s = curs.selectionStart()
                        e = curs.selectionEnd()
                        if s == e:
                            curs.setPosition(e)
                            curs.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
                            txt = curs.selectedText()
                            if txt != pair[0]:
                                self.encapsulateText(*pair)
                            else:
                                curs.setPosition(e)
                                curs.movePosition(QtGui.QTextCursor.NextCharacter)
                                self.setTextCursor(curs)
                        else:
                            self.encapsulateText(*pair)
                    else:
                        self.encapsulateText(*pair)
                elif et in [x[1] for x in paired]:  # CLOSE
                    pair = [x for x in paired if et in x][0]
                    curs = self.textCursor()
                    s = curs.selectionStart()
                    e = curs.selectionEnd()
                    if s == e:
                        curs.setPosition(e)
                        curs.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
                        txt = curs.selectedText()
                        if txt != pair[1]:
                            self.insertPlainText(pair[1])
                        else:
                            curs.setPosition(e)
                            curs.movePosition(QtGui.QTextCursor.NextCharacter)
                            self.setTextCursor(curs)
                    else:
                        self.insertPlainText(pair[1])
                else:
                    QtWidgets.QPlainTextEdit.keyPressEvent(self, event)
            else:
                QtWidgets.QPlainTextEdit.keyPressEvent(self, event)

    def event(self, event: QtCore.QEvent):
        if event.type() == QtCore.QEvent.ShortcutOverride:
            return False
        return QtWidgets.QPlainTextEdit.event(self, event)

    def setText(self, text):
        self.document().setPlainText(text)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        pos = event.pos()
        cursor = self.cursorForPosition(pos)
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        tpos = cursor.position()
        for start, size, msg in self.errors:
            if start <= tpos <= start + size:
                QtWidgets.QToolTip.showText(event.globalPos(), msg, self)
        return QtWidgets.QPlainTextEdit.mouseMoveEvent(self, event)

    def delete(self):
        cursor = self.textCursor()
        txt = cursor.selectedText()
        if txt == "":
            cursor.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        self.insertPlainText("")

    def _cc(self):
        cursor = self.textCursor()
        txt = cursor.selectedText()
        if txt == "":
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)

    def copy(self):
        self._cc()
        QtWidgets.QPlainTextEdit.copy(self)

    def cut(self):
        self._cc()
        QtWidgets.QPlainTextEdit.cut(self)

    def duplicate(self):
        cursor = self.textCursor()
        txt = cursor.selectedText()
        posE = cursor.selectionEnd()
        if txt == "":   # Duplicate line
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            txt = cursor.selectedText()
            cursor.insertText(txt + Constants.LINE_ENDING + txt)
        else:           # Duplicate selection
            cursor.insertText(txt + txt)
            cursor.setPosition(posE)
            cursor.setPosition(posE + len(txt), QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)

    def lines(self, func, state=None):
        cursor = self.textCursor()
        posS = cursor.selectionStart()
        posE = cursor.selectionEnd()

        cursor.beginEditBlock()
        cursor.setPosition(posS)
        cursor.movePosition(QtGui.QTextCursor.StartOfLine)
        cursor.setPosition(posE, QtGui.QTextCursor.KeepAnchor)
        cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
        otxt = cursor.selectedText()
        txt = otxt.split(Constants.LINE_ENDING)
        add = 0
        for i in range(len(txt)):
            state, line = func(txt[i], state)
            if i == 0:
                add = len(line) - len(txt[i])
            txt[i] = line
        ntxt = Constants.LINE_ENDING.join(txt)
        cursor.setPosition(posS)
        cursor.movePosition(QtGui.QTextCursor.StartOfLine)
        cursor.setPosition(posE, QtGui.QTextCursor.KeepAnchor)
        if cursor.selectedText() == Constants.LINE_ENDING or posS == posE:
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
        cursor.insertText(ntxt)
        cursor.setPosition(posS + add)
        cursor.setPosition(posE + len(ntxt) - len(otxt), QtGui.QTextCursor.KeepAnchor)
        cursor.endEditBlock()
        self.setTextCursor(cursor)

        return cursor

    def comment(self):
        # TODO: identify indents before/after comment signs
        def cmnt(line, state):
            txt = line
            if txt[:2] == "//" and state in [True, None]:
                txt = txt[2:]
                state = True
            elif len(txt) > 0 and txt[0] == "#" and state in [True, None]:
                txt = txt[1:]
                state = True
            elif state in [False, None]:
                txt = "//" + txt
                state = False
            return state, txt

        self.lines(cmnt)

    def indent(self):
        tab = '\t'
        if bool(Config.value("editor/spacesOverTabs")):
            tab = ' ' * int(Config.value("editor/tabwidth"))

        def func(line, state):
            return state, tab + line

        cursor = self.textCursor()
        txt = cursor.selectedText()
        if txt != "":
            self.lines(func)
        else:
            self.insertPlainText(tab)

    def unindent(self):
        # 1) take all left whitespace;
        # 2) replace tabs with spaces (w.r.t. Config);
        # 3) remove 1 character;
        # 4) reduce string length until length % tablength == 0;
        # 5) this is new whitespace length
        ws = (' ', '\t')
        useSpaces = bool(Config.value("editor/spacesOverTabs"))
        tablength = int(Config.value("editor/tabwidth"))

        def func(line, state):
            txt = line
            lft = left(txt, ws)
            if useSpaces:
                lft = lft.replace("\t", " " * tablength)
                if len(lft) > 0:
                    lft = lft[:-1]
                lft = lft[:(len(lft) // tablength) * tablength]
                txt = lft + txt.lstrip()
            else:
                if len(lft) > 0 and lft[-1] in ws:
                    txt = lft[:-1] + txt.lstrip()
            return state, txt

        self.lines(func)

    def autoIndent(self):
        cursor = self.textCursor()
        posS = cursor.selectionStart()
        cursor.setPosition(posS)
        s = cursor.movePosition(QtGui.QTextCursor.Up)
        linenr = 0
        indent = 0
        tw = int(Config.value("editor/tabwidth"))
        sot = bool(Config.value("editor/spacesOverTabs"))
        if s:
            linenr = cursor.blockNumber() + 1
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            txt = cursor.selectedText()
            for c in txt:
                if c == ' ':
                    indent += 1
                elif c == '\t':
                    indent += tw
                else:
                    break

        if not sot:
            indent //= tw

        vis = self.highlighter.parser.visitor

        def indentLine(line, state):
            vobt = vis.obtain(state, linenr)
            txt = line.lstrip()
            if sot:
                inc = indent + (vobt * tw)
                line = (" " * inc) + txt
            else:
                inc = indent + vobt
                line = ("\t" * inc) + txt
            state += 1
            return state, line

        self.lines(indentLine, linenr + 1)

    def moveUp(self):
        curs = self.textCursor()
        curs.beginEditBlock()
        start = curs.selectionStart()
        end = curs.selectionEnd()
        curs.setPosition(start)
        curs.movePosition(QtGui.QTextCursor.PreviousBlock)
        curs.movePosition(QtGui.QTextCursor.StartOfLine)
        curs.movePosition(QtGui.QTextCursor.PreviousCharacter)
        curs.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
        curs.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
        txt = curs.selectedText()
        curs.removeSelectedText()
        start -= len(txt)
        end -= len(txt)
        curs.setPosition(end)
        curs.movePosition(QtGui.QTextCursor.EndOfLine)
        curs.insertText(txt)
        curs.setPosition(start)
        curs.setPosition(end, QtGui.QTextCursor.KeepAnchor)
        curs.endEditBlock()
        self.setTextCursor(curs)

    def moveDown(self):
        curs = self.textCursor()
        curs.beginEditBlock()
        start = curs.selectionStart()
        end = curs.selectionEnd()
        curs.setPosition(end)
        curs.movePosition(QtGui.QTextCursor.NextBlock)
        curs.movePosition(QtGui.QTextCursor.StartOfLine)
        curs.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
        curs.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
        txt = curs.selectedText()
        curs.removeSelectedText()
        curs.setPosition(start)
        curs.movePosition(QtGui.QTextCursor.StartOfLine)
        curs.insertText(txt)
        start += len(txt)
        end += len(txt)
        curs.setPosition(start)
        curs.setPosition(end, QtGui.QTextCursor.KeepAnchor)
        curs.endEditBlock()
        self.setTextCursor(curs)

    def complete(self):
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        prefix = cursor.selectedText()

        ctr = self.highlighter.parser.visitor.completer
        tp = self.wrapper.filetype.currentText()
        for p in pluginloader.get():
            snps = p.types.get(tp, {}).get("snippets", {})
            for n in snps:
                ctr.add(n, Types.SNIPPET, snps[n])
        snps = self.mainwindow.snippets.snippets
        for n in snps.get(tp, {}):
            ctr.add(n, Types.SNIPPET, snps[tp].get(n, None))
        completions, prefix = self.highlighter.parser.visitor.completer.get(prefix)

        mdl = self.completer.model()
        mdl.clear()
        for c in completions:
            it = QtGui.QStandardItem(c[0])
            mdl.appendRow(it)

        if len(completions) == 0:
            return

        if prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(prefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setLeft(cr.left() + self.completer.popup().verticalScrollBar().sizeHint().width() * 3)
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) * 2 +
                    self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def matchBrackets(self):
        paired = pluginloader.getPairedBrackets(self.wrapper.filetype.currentText())
        bopen = [x[0] for x in paired]
        bclose = [x[1] for x in paired]

        curs = self.textCursor()
        data = curs.block().userData()
        if data:
            infos = data.parenthesis

            pos = curs.block().position()
            curPos = curs.positionInBlock()
            block = curs.block()
            for i in range(len(infos)):
                info = infos[i]
                if info.at(curPos):
                    oidx = bopen.index(info.char) if info.char in bopen else -1
                    cidx = bclose.index(info.char) if info.char in bclose else -1
                    if info.char in bopen:
                        cpos = self.getClosingBracketPos(paired[oidx], block, i + 1)
                        if cpos >= 0:
                            curs.setPosition(cpos)
                            j = curs.block().userData().indexOf(curs.positionInBlock())
                            opos = self.getOpeningBracketPos(paired[oidx], curs.block(), j - 1)
                            if info.pos == opos - pos:
                                self.highlightBrackets(opos, len(paired[oidx][0]))
                                self.highlightBrackets(cpos, len(paired[oidx][1]))
                    if info.char in bclose:
                        opos = self.getOpeningBracketPos(paired[cidx], block, i - 1)
                        if opos >= 0:
                            curs.setPosition(opos)
                            j = curs.block().userData().indexOf(curs.positionInBlock())
                            cpos = self.getClosingBracketPos(paired[cidx], curs.block(), j + 1)
                            if info.pos == cpos - pos:
                                self.highlightBrackets(cpos, len(paired[cidx][1]))
                                self.highlightBrackets(opos, len(paired[cidx][0]))

    def getOpeningBracketPos(self, pair, block, i, num=0):
        data = block.userData()
        infos = data.parenthesis

        docPos = block.position()
        for j in range(i, -1, -1):
            if len(infos) == 0:
                break
            info = infos[j]

            if info.char == pair[1] and pair[0] != pair[1]:
                num += 1
                continue
            if info.char == pair[0]:
                if num == 0:
                    return docPos + info.pos
                num -= 1

        block = block.previous()
        if block.isValid():
            return self.getOpeningBracketPos(pair, block, 0, num)

        return -1

    def getClosingBracketPos(self, pair, block, i, num=0):
        if i < 0:
            return -1
        data = block.userData()
        infos = data.parenthesis

        docPos = block.position()
        for j in range(i, len(infos)):
            info = infos[j]

            if info.char == pair[0] and pair[0] != pair[1]:
                num += 1
                continue
            if info.char == pair[1]:
                if num == 0:
                    return docPos + info.pos
                num -= 1

        block = block.next()
        if block.isValid():
            return self.getClosingBracketPos(pair, block, 0, num)

        return -1

    def highlightBrackets(self, pos, size=1):
        selection = QtWidgets.QTextEdit.ExtraSelection()
        selection.format.setBackground(QtGui.QColor(Config.value("col/clnb")))
        selection.format.setForeground(QtGui.QColor(Config.value("col/clnf")))

        curs = self.textCursor()
        curs.setPosition(pos)
        curs.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor, size)
        selection.cursor = curs

        selections = self.extraSelections()
        selections.append(selection)
        self.setExtraSelections(selections)

    def highlightMatches(self):
        selections = self.extraSelections()

        for start, end, _ in self.matches:
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format.setBackground(QtGui.QColor(Config.value("col/find")))

            curs = self.textCursor()
            curs.setPosition(start)
            curs.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            selection.cursor = curs
            selections.append(selection)

        self.setExtraSelections(selections)

    def highlightErrors(self):
        selections = self.extraSelections()
        for start, size, message in self.errors:
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format = BaseHighlighter.format_error()

            curs = self.textCursor()
            curs.setPosition(start)
            curs.setPosition(start + size, QtGui.QTextCursor.KeepAnchor)
            selection.cursor = curs
            selections.append(selection)
        self.setExtraSelections(selections)

    def highlightCurrentLine(self):
        selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format.setBackground(QtGui.QColor(Config.value("col/cline")))
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)

        self.setExtraSelections(selections)

    def lineNumberAreaPaintEvent(self, event):
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
        painter = QtGui.QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QtGui.QColor(Config.value("col/lnb")))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        currentBlockNumber = self.textCursor().block().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                if currentBlockNumber == blockNumber:
                    painter.fillRect(QtCore.QRect(0, top, self.lineNumberArea.width(), self.fontMetrics().height()),
                                     QtGui.QColor(Config.value("col/clnb")))
                    painter.setPen(QtGui.QColor(Config.value("col/clnf")))
                else:
                    painter.setPen(QtGui.QColor(Config.value("col/lnf")))
                painter.drawText(0, top, self.lineNumberArea.textWidth(), self.fontMetrics().height(),
                                 QtCore.Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            blockNumber += 1

    def lineNumberAreaWidth(self):
        if not bool(Config.value("editor/showLineNumbers", True)):
            return 0
        digits = 1
        _max = max(1, self.document().blockCount())
        while _max >= 10:
            _max /= 10
            digits += 1

        return 13 + self.fontMetrics().width('9') * digits + self.lineNumberArea.offset

    def resizeEvent(self, event):
        QtWidgets.QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def updateIndicator(self):
        if isinstance(self.mainwindow.statusBar(), StatusBar):
            text = ""
            cursor = self.textCursor()
            if cursor.selectedText() != "":
                text = "[%i chars]" % len(cursor.selectedText())
            self.mainwindow.statusBar().positionIndicator\
                .setText("%s      %i:%i" % (text, cursor.blockNumber() + 1, cursor.columnNumber() + 1))

    def updateLineNumberAreaWidth(self, newBlockCount=0):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())

        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()

    def viewParseTree(self, focus=True):
        txt = self.toPlainText()
        T = self.highlighter.parser.parse(txt, True)
        if T is not None:
            if self.treeView is None:
                self.treeView = QtWidgets.QDialog(self.parent(), flags=QtCore.Qt.Window)
                layout = QtWidgets.QGridLayout()
                view = GraphicsView(self.mainwindow, self.parent())
                layout.addWidget(view)
                self.treeView.setLayout(layout)
            self.treeView.setWindowTitle("Lark LALR Parse Tree of %s" % self.filename)
            view = self.treeView.layout().itemAtPosition(0, 0).widget()
            view.setControls(bool(Config.value("view/controls")))
            view.setMinZoomLevel(float(Config.value("view/zoomMin")) / 100)
            view.setMaxZoomLevel(float(Config.value("view/zoomMax")) / 100)
            view.setZoomFactorBase(float(Config.value("view/zoomFactor")))
            view.clear()

            ename = self.wrapper.engine.currentText()
            T = self.highlighter.parser.parse(self.toPlainText())
            engine = pluginloader.getEngines()[ename]
            if T is not None:
                if "AST" in engine:
                    bdata = engine["AST"](T)
                    view.add(bdata)
                else:
                    engine = pluginloader.getEngines().get("Graphviz", {})
                    if "AST" in engine:
                        bdata = engine["AST"](T)
                        view.add(bdata)
                    else:
                        self.mainwindow.error("Error!", "The current rendering engine '%s' does not support the "
                                                        "rendering of Abstract Syntax Trees and the fallback renderer "
                                                        "'Graphviz' cannot be found.\n\nCurrently unable to display the"
                                                        " AST." % ename)
                        return

            if not self.treeView.isVisible():
                self.treeView.show()
            if focus:
                self.treeView.activateWindow()
                self.treeView.raise_()
                self.treeView.setFocus()
        else:
            self.mainwindow.warn("Warning!", "It looks like your file contains some errors. Impossible to render AST.")
            if self.treeView is not None and self.treeView.isVisible():
                self.treeView.close()


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.editor = editor
        self.offset = 10

    def textWidth(self):
        return self.width() - self.offset

    def sizeHint(self):
        return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, QPaintEvent):
        self.editor.lineNumberAreaPaintEvent(QPaintEvent)
