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
from main.editors.Parser import DotVisitor
from main.extra.IOHandler import IOHandler
from main.editors.Highlighter import BaseHighlighter
from main.editors import EDITORTYPES
from main.extra.GraphicsView import GraphicsView
from main.Preferences import bool

Config = IOHandler.get_preferences()

class EditorWrapper(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(EditorWrapper, self).__init__(parent)
        self._layout = QtWidgets.QGridLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.editor = CodeEditor(parent)
        self._layout.addWidget(self.editor, 0, 0)
        self.filetype = QtWidgets.QComboBox()
        self.filetype.currentIndexChanged.connect(self.alter)
        self.setTypes()
        self._layout.addWidget(self.filetype, 1, 0)
        self.setLayout(self._layout)

    def setTypes(self):
        for type in EDITORTYPES:
            name, klass = EDITORTYPES[type]
            self.filetype.addItem(name, klass)

    def alter(self, idx):
        data = self.filetype.itemData(idx)
        self.editor.alter(data(self.editor.document(), self.editor))
        self.editor.highlighter.rehighlight()

    def setType(self, type):
        self.filetype.setCurrentText(EDITORTYPES[type][0])

class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)
        self.mainwindow = parent
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

    def alter(self, highlighter):
        self.highlighter.deleteLater()
        self.highlighter = highlighter

    def graphviz(self):
        return self.highlighter.parser.toGraphviz(self.toPlainText())

    def textChangedSlot(self):
        self.highlighter.storeErrors()

    def positionChangedSlot(self):
        if bool(Config.value("editor/highlightCurrentLine")):
            self.highlightCurrentLine()
        if bool(Config.value("editor/parentheses")):
            self.matchParenthesis()
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
        snippets = self.mainwindow.snippets.snippets
        for name in snippets:
            menu.addAction(name, lambda: self.insertPlainText(snippets[name]))
        menu.exec_(event.globalPos())

    def isSaved(self):
        """Returns True if the file was saved."""
        return self.filename != "" and self.toPlainText() == self.filecontents

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
        keywords = Constants.STRICT_KEYWORDS + Constants.ATTRIBUTES
        keywords.sort()
        self.completer = QtWidgets.QCompleter(keywords, self)
        self.completer.setModelSorting(QtWidgets.QCompleter.CaseInsensitivelySortedModel)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setWrapAround(False)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

    def insertCompletion(self, completion):
        cursor = self.textCursor()
        extra = len(self.completer.completionPrefix())
        if extra > 0:
            cursor.movePosition(QtGui.QTextCursor.Left)
        cursor.movePosition(QtGui.QTextCursor.EndOfWord)
        cursor.insertText(completion[extra:])
        self.setTextCursor(cursor)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
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
            pos = cursor.position()
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            txt = cursor.selectedText().lstrip()
            if len(txt) > 0 and txt[0] in Constants.INDENT_CLOSE:
                cursor.setPosition(pos)
                cursor.insertText(Constants.LINE_ENDING)
                cursor.movePosition(QtGui.QTextCursor.Up)
                cursor.movePosition(QtGui.QTextCursor.EndOfLine)
                cursor.movePosition(QtGui.QTextCursor.Down, QtGui.QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)
                self.autoIndent()
                bsel = cursor.selectionStart()
                cursor.setPosition(bsel)
                cursor.movePosition(QtGui.QTextCursor.EndOfLine)
                self.setTextCursor(cursor)
        elif event.key() not in [QtCore.Qt.Key_Delete]:
            k = event.key()
            keys = [QtCore.Qt.Key_ParenLeft, QtCore.Qt.Key_BraceLeft, QtCore.Qt.Key_BracketLeft, QtCore.Qt.Key_QuoteDbl,
                    QtCore.Qt.Key_Apostrophe]
            open = ["(", "{", "[", '"', "'"]
            close = [")", "}", "]", '"', "'"]
            if k in keys and bool(Config.value("editor/pairedBrackets")):
                idx = keys.index(k)
                curs = self.textCursor()
                s = curs.selectionStart()
                e = curs.selectionEnd()
                curs.setPosition(s)
                curs.beginEditBlock()
                self.setTextCursor(curs)
                self.insertPlainText(open[idx])
                curs.setPosition(e + 1)
                self.setTextCursor(curs)
                self.insertPlainText(close[idx])
                curs.endEditBlock()
                curs.setPosition(s + 1)
                curs.setPosition(e + 1, QtGui.QTextCursor.KeepAnchor)
                self.setTextCursor(curs)
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
        if cursor.selectedText() == Constants.LINE_ENDING:
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
        indent = 0
        tw = int(Config.value("editor/tabwidth"))
        sot = bool(Config.value("editor/spacesOverTabs"))
        if s:
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
            txt = txt.lstrip()
            for c in txt:
                if c in Constants.INDENT_OPEN:
                    indent += tw
                elif c in Constants.INDENT_CLOSE:
                    indent -= tw

        if not sot:
            indent //= tw


        def indentLine(line, state):
            txt = line.lstrip()
            if len(txt) > 0 and txt[0] in Constants.INDENT_CLOSE:
                state -= tw if sot else 1
            if sot:
                line = (" " * state) + txt
            else:
                line = ("\t" * state) + txt
            for c in txt:
                if c in Constants.INDENT_CLOSE:
                    state -= tw if sot else 1
                    if state < 0:
                        state = 0
                elif c in Constants.INDENT_OPEN:
                    state += tw if sot else 1
            return state, line

        self.lines(indentLine, indent)

    def complete(self):
        # TODO: identify context-specific actions
        #   Model list can be changed with self.completer.model().setStringList()
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        prefix = cursor.selectedText()
        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="

        if len(prefix) > 0 and prefix[-1] in eow:
            return

        if prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(prefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) +
                    self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def matchParenthesis(self):
        curs = self.textCursor()
        data = curs.block().userData()
        if data:
            infos = data.parenthesis

            pos = curs.block().position()
            for i in range(len(infos)):
                info = infos[i]
                curPos = curs.positionInBlock()
                if info.pos in [curPos, curPos - 1] and info.char in Constants.INDENT_OPEN:
                    if self.matchOpenParenthesis(Constants.INDENT_OPEN.index(info.char), curs.block(), i + 1):
                        self.highlightParenthesis(pos + info.pos)
                if info.pos in [curPos, curPos - 1] and info.char in Constants.INDENT_CLOSE:
                    if self.matchCloseParenthesis(Constants.INDENT_CLOSE.index(info.char), curs.block(), i - 1):
                        self.highlightParenthesis(pos + info.pos)

    def matchOpenParenthesis(self, cidx, block, i, num=0):
        data = block.userData()
        infos = data.parenthesis

        docPos = block.position()
        for j in range(i, len(infos)):
            info = infos[j]

            if info.char == Constants.INDENT_OPEN[cidx]:
                num += 1
                continue
            if info.char == Constants.INDENT_CLOSE[cidx]:
                if num == 0:
                    self.highlightParenthesis(docPos + info.pos)
                    return True
                num -= 1

        block = block.next()
        if block.isValid():
            return self.matchOpenParenthesis(cidx, block, 0, num)

        return False

    def matchCloseParenthesis(self, cidx, block, i, num=0):
        data = block.userData()
        infos = data.parenthesis

        docPos = block.position()
        for j in range(i, -1, -1):
            if len(infos) == 0:
                break
            info = infos[j]

            if info.char == Constants.INDENT_CLOSE[cidx]:
                num += 1
                continue
            if info.char == Constants.INDENT_OPEN[cidx]:
                if num == 0:
                    self.highlightParenthesis(docPos + info.pos)
                    return True
                num -= 1

        block = block.previous()
        if block.isValid():
            return self.matchCloseParenthesis(cidx, block, 0, num)

        return False

    def highlightParenthesis(self, pos):
        selection = QtWidgets.QTextEdit.ExtraSelection()
        selection.format.setBackground(QtGui.QColor(Config.value("col/clnb")))
        selection.format.setForeground(QtGui.QColor(Config.value("col/clnf")))

        curs = self.textCursor()
        curs.setPosition(pos)
        curs.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
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
            selection.format = BaseHighlighter.format_error(message)

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
        text = ""
        cursor = self.textCursor()
        if cursor.selectedText() != "":
            text = "[%i chars]" % len(cursor.selectedText())
        self.mainwindow.positionIndicator\
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
                view = GraphicsView(self.parent())
                layout.addWidget(view)
                self.treeView.setLayout(layout)
            self.treeView.setWindowTitle("Lark LALR Parse Tree of %s" % self.filename)
            view = self.treeView.layout().itemAtPosition(0, 0).widget()
            view.setControls(bool(Config.value("view/controls")))
            view.setMinZoomLevel(float(Config.value("view/zoomMin")) / 100)
            view.setMaxZoomLevel(float(Config.value("view/zoomMax")) / 100)
            view.setZoomFactorBase(float(Config.value("view/zoomFactor")))
            view.clear()

            dot = DotVisitor()
            dot.visit(T)
            view.addDot(dot.root, Config.value("graphviz/format"), Config.value("graphviz/renderer"),
                        Config.value("graphviz/formatter"))
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
