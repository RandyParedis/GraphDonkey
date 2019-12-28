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
from main.extra.Highlighter import Highlighter
from main.Preferences import bool

Config = IOHandler.get_preferences()

class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, parent):
        super(CodeEditor, self).__init__(parent)
        self.mainwindow = parent
        self.lineNumberArea = LineNumberArea(self)

        font = QtGui.QFont(Config.value("font"))

        fontWidth = QtGui.QFontMetrics(self.currentCharFormat().font()).averageCharWidth()
        self.setTabStopWidth(4 * fontWidth)

        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberAreaScroll)
        self.textChanged.connect(self.updateLineNumberAreaText)
        self.cursorPositionChanged.connect(self.updateLineNumberAreaText)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        self.highlighter = Highlighter(self.document(), self)

        self.matches = []
        self.errors = []
        self.extraCursors = set()

        self.setMouseTracking(True)

        self.filename = ""
        self.filecontents = ""

        self.completer = None
        self.setCompleter()

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
        if bool(Config.value("spacesOverTabs")):
            tab = ' ' * int(Config.value("tabwidth"))

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
        useSpaces = bool(Config.value("spacesOverTabs"))
        tablength = int(Config.value("tabwidth"))

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
        tw = int(Config.value("tabwidth"))
        sot = bool(Config.value("spacesOverTabs"))
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
                    if self.matchOpenParenthesis(Constants.INDENT_OPEN.index(info.char), curs.block(), i+1):
                        self.highlightParenthesis(pos + info.pos)
                if info.pos in [curPos, curPos - 1] and info.char in Constants.INDENT_CLOSE:
                    if self.matchCloseParenthesis(Constants.INDENT_CLOSE.index(info.char), curs.block(), i - 1):
                        self.highlightParenthesis(pos + info.pos)

    def matchOpenParenthesis(self, cidx, block, i, num=0):
        data = block.userData()
        infos = data.parenthesis

        docPos = block.position()
        for j in range(i, len(infos)):
            info = infos[i]

            if info.char == Constants.INDENT_OPEN[cidx]:
                num += 1
                continue
            if info.char == Constants.INDENT_CLOSE[cidx] and num == 0:
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
            info = infos[i]

            if info.char == Constants.INDENT_CLOSE[cidx]:
                num += 1
                continue
            if info.char == Constants.INDENT_OPEN[cidx] and num == 0:
                self.highlightParenthesis(docPos + info.pos)
                return True
            num -= 1

        block = block.previous()
        if block.isValid():
            return self.matchCloseParenthesis(cidx, block, 0, num)

        return False

    def highlightParenthesis(self, pos):
        selection = QtWidgets.QTextEdit.ExtraSelection()
        selection.format.setBackground(QtGui.QColor(Config.value("col.clnb")))
        selection.format.setForeground(QtGui.QColor(Config.value("col.clnf")))

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
            selection.format.setBackground(QtGui.QColor(Config.value("col.find")))

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
            selection.format = Highlighter.format_error(message)

            curs = self.textCursor()
            curs.setPosition(start)
            curs.setPosition(start + size, QtGui.QTextCursor.KeepAnchor)
            selection.cursor = curs
            selections.append(selection)
        self.setExtraSelections(selections)

    def insertFromMimeData(self, QMimeData):
        self.insertPlainText(QMimeData.text())

    def highlightCurrentLine(self):
        selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format.setBackground(QtGui.QColor(Config.value("col.cline")))
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)

        self.setExtraSelections(selections)

    def getFirstVisibleBlockId(self):
        curs = QtGui.QTextCursor(self.document())
        curs.movePosition(QtGui.QTextCursor.Start)
        for i in range(self.document().blockCount()):
            block = curs.block()
            r1 = self.viewport().geometry()
            r2 = self.document().documentLayout().blockBoundingRect(block).\
                translated(self.viewport().geometry().x(),
                           self.viewport().geometry().y() - self.verticalScrollBar().sliderPosition()).toRect()

            if r1.contains(r2, True): return i

            curs.movePosition(QtGui.QTextCursor.NextBlock)
        return 0

    def lineNumberAreaPaintEvent(self, event):
        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())
        painter = QtGui.QPainter(self.lineNumberArea)
        blockNumber = self.getFirstVisibleBlockId()

        block = self.document().findBlockByNumber(blockNumber)
        prev_block = self.document().findBlockByNumber(blockNumber - 1) if blockNumber > 0 else block
        translate_y = -self.verticalScrollBar().sliderPosition() if blockNumber > 0 else 0

        top = self.viewport().geometry().top()
        if blockNumber == 0:
            additionalMargin = self.document().documentMargin() - 1 - self.verticalScrollBar().sliderPosition()
        else:
            additionalMargin = self.document().documentLayout().blockBoundingRect(prev_block). \
                translated(0, translate_y).intersect(self.viewport().geometry()).height()

        top += additionalMargin

        bottom = top + self.document().documentLayout().blockBoundingRect(block).height()

        col_1 = QtGui.QColor(Config.value("col.clnf"))
        col_0 = QtGui.QColor(Config.value("col.lnf"))

        old = block, top, bottom, blockNumber

        painter.fillRect(event.rect(), QtGui.QColor(Config.value("col.lnb")))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top() and self.textCursor().blockNumber() == blockNumber:
                painter.fillRect(QtCore.QRect(event.rect().x(), top, event.rect().width(), self.fontMetrics().height()),
                                 QtGui.QColor(Config.value("col.clnb")))
            block = block.next()
            top = bottom
            bottom = top + self.document().documentLayout().blockBoundingRect(block).height()
            blockNumber += 1

        block, top, bottom, blockNumber = old
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(col_1 if self.textCursor().blockNumber() == blockNumber else col_0)
                painter.drawText(-5, top, self.lineNumberArea.width(), self.fontMetrics().height(),
                                 QtCore.Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.document().documentLayout().blockBoundingRect(block).height()
            blockNumber += 1

    def lineNumberAreaWidth(self):
        if not bool(Config.value("showLineNumbers", True)):
            return 0
        digits = 1
        _max = max(1, self.document().blockCount())
        while _max >= 10:
            _max /= 10
            digits += 1

        return 13 + self.fontMetrics().width('9') * digits

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

    def updateLineNumberAreaWidth(self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect):
        self.updateLineNumberAreaText()

    def updateLineNumberAreaScroll(self, dy):
        self.updateLineNumberAreaText()

    def updateLineNumberAreaText(self):
        if bool(Config.value("highlightCurrentLine")):
            self.highlightCurrentLine()
        if bool(Config.value("parentheses")):
            self.matchParenthesis()
        if bool(Config.value("useParser", True)):
            self.highlightErrors()
        self.highlightMatches()

        self.updateIndicator()

        self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())

        rect = self.contentsRect()
        self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        self.updateLineNumberAreaWidth(0)

        dy = self.verticalScrollBar().sliderPosition()
        if dy > -1:
            self.lineNumberArea.scroll(0, dy)

        first_block_id = self.getFirstVisibleBlockId()
        if first_block_id == 0 or self.textCursor().block().blockNumber() == first_block_id - 1:
            self.verticalScrollBar().setSliderPosition(dy - self.document().documentMargin())


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, QPaintEvent):
        self.editor.lineNumberAreaPaintEvent(QPaintEvent)