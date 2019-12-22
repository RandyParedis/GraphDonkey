"""The code editor of GraphDonkey, with a few features:

- Syntax Highlighting
- Line Numbers
    Based on https://stackoverflow.com/questions/2443358/how-to-add-lines-numbers-to-qtextedit

Author: Randy Paredis
Date:   12/14/2019
"""
from PyQt5 import QtGui, QtWidgets, QtCore
from lark import UnexpectedToken, Token, UnexpectedCharacters

from main.extra import Constants
from main.extra.Parser import Parser
from main.extra.IOHandler import IOHandler
from main.Preferences import bool

Config = IOHandler.get_preferences()

class CodeEditor(QtWidgets.QTextEdit):
    def __init__(self, parent):
        super(CodeEditor, self).__init__(parent)
        self.mainwindow = parent
        self.lineNumberArea = LineNumberArea(self)

        fontWidth = QtGui.QFontMetrics(self.currentCharFormat().font()).averageCharWidth()
        self.setTabStopWidth(4 * fontWidth)

        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberAreaScroll)
        self.textChanged.connect(self.updateLineNumberAreaText)
        self.cursorPositionChanged.connect(self.updateLineNumberAreaText)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        self.highlighter = Highlighter(self.document(), self)

        self.setMouseTracking(True)

    def event(self, event: QtCore.QEvent):
        if event.type() == QtCore.QEvent.ShortcutOverride:
            return False
        if event.type() == QtCore.QEvent.KeyPress:
            event = QtGui.QKeyEvent(event)
            if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
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
                return False
        return QtWidgets.QTextEdit.event(self, event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        pos = event.pos()
        cursor = self.cursorForPosition(pos)
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        tpos = cursor.position()
        error = self.highlighter.errors.get(tpos, "")
        if error != "":
            QtWidgets.QToolTip.showText(event.globalPos(), error, self)
        return QtWidgets.QTextEdit.mouseMoveEvent(self, event)

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
        cursor.setPosition(posS)
        cursor.movePosition(QtGui.QTextCursor.StartOfLine)
        line = cursor.selectionStart()
        cursor.setPosition(posE)
        cursor.movePosition(QtGui.QTextCursor.EndOfLine)
        lineE = cursor.selectionEnd()

        cursor.setPosition(line)
        lastL = None
        offset = 0
        ostart = None
        while line != lastL:
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)

            # Compute Offset
            before = len(cursor.selectedText())
            state = func(cursor, state)
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            after = len(cursor.selectedText())
            offset += after - before
            if ostart is None:
                ostart = after - before

            # Go to the next line
            if line > lineE:
                break
            cursor.movePosition(QtGui.QTextCursor.Down)
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            lastL = line
            line = cursor.selectionStart()

        cursor.setPosition(posS + ostart)
        cursor.setPosition(posE + offset, QtGui.QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        return cursor

    def comment(self):
        def cmnt(cursor, state):
            txt = cursor.selectedText()
            if txt[:2] == "//" and state in [True, None]:
                txt = txt[2:]
                state = True
            elif txt[0] == "#" and state in [True, None]:
                txt = txt[1:]
                state = True
            elif state in [False, None]:
                txt = "//" + txt
                state = False
            cursor.insertText(txt)
            return state

        self.lines(cmnt)

    def autoIndent(self):
        cursor = self.textCursor()
        posS = cursor.selectionStart()
        cursor.setPosition(posS)
        s = cursor.movePosition(QtGui.QTextCursor.Up)
        indent = 0
        tw = int(Config.value("tabwidth"))
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
        indent //= tw

        def indentLine(cursor, state):
            txt = cursor.selectedText().lstrip()
            if len(txt) > 0 and txt[0] in Constants.INDENT_CLOSE:
                state -= 1
            cursor.insertText(("\t" * state) + txt)
            for c in txt:
                if c in Constants.INDENT_CLOSE:
                    state -= 1
                    if state < 0:
                        state = 0
                elif c in Constants.INDENT_OPEN:
                    state += 1
            return state

        self.lines(indentLine, indent)


    def insertFromMimeData(self, QMimeData):
        self.insertPlainText(QMimeData.text())

    def highlightCurrentLine(self):
        selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            if bool(Config.value("highlightCurrentLine", True)):
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
        QtWidgets.QTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberAreaWidth(self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect):
        self.updateLineNumberAreaText()

    def updateLineNumberAreaScroll(self, dy):
        self.updateLineNumberAreaText()

    def updateLineNumberAreaText(self):
        self.highlightCurrentLine()

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


BLOCKSTATE_NORMAL = 0
BLOCKSTATE_COMMENT = 1
BLOCKSTATE_STRING = 2
BLOCKSTATE_HTML = 4

class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None, editor=None):
        super(Highlighter, self).__init__(parent)
        self.editor = editor
        self.highlightingRules = []
        self._setPatterns()
        self.parser = Parser()
        self.errors = {}

    def _setPatterns(self):
        keywordPatterns = ["\\b%s\\b" % x for x in Constants.STRICT_KEYWORDS]
        self.highlightingRules = [(QtCore.QRegExp(pattern, QtCore.Qt.CaseInsensitive), self.format_keyword)
                                  for pattern in keywordPatterns]

        attributePatterns = "|".join(["(" + x + ")" for x in Constants.ATTRIBUTES])
        attributePatterns = "(%s)(?=\\s*[=])" % attributePatterns
        self.highlightingRules.append((QtCore.QRegExp("(%s)(?=\\s*[=])" % attributePatterns), self.format_attribute))
        for a in Constants.SPECIAL_ATTRIBUTES:
            self.highlightingRules.append((QtCore.QRegExp("\\b%s\\b" % a), self.format_attribute))

        self.highlightingRules.append((QtCore.QRegExp("\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b"), self.format_number))

        self.highlightingRules.append((QtCore.QRegExp("^#[^%s]*$" % Constants.LINE_ENDING), self.format_comment_hash))
        self.highlightingRules.append((QtCore.QRegExp("//[^%s]*" % Constants.LINE_ENDING), self.format_comment_single))

        self.commentStartExpression = QtCore.QRegExp("/\\*")
        self.commentEndExpression = QtCore.QRegExp("\\*/")
        self.stringExpression = QtCore.QRegExp('"')
        self.htmlStartExpression = QtCore.QRegExp('<')
        self.htmlEndExpression = QtCore.QRegExp('>')
        self.htmlTag = QtCore.QRegExp("</?[^<>/%s]*>" % Constants.LINE_ENDING)

    def multilineHighlighter(self, text, startexp, endexp, blockstate, format, skipexp=None):
        startIndex = 0
        pbs = self.previousBlockState()
        if pbs == -1 or not pbs & blockstate:
            startIndex = startexp.indexIn(text)

        while startIndex >= 0:
            begin = 0 if startIndex == 0 else startIndex + 1
            if skipexp:
                skipIndex = skipexp.lastIndexIn(text)
                begin = skipIndex + skipexp.matchedLength()
            endIndex = endexp.indexIn(text, begin)

            if endIndex == -1:
                self.setCurrentBlockState(self.currentBlockState() | blockstate)
                length = len(text) - startIndex
            else:
                length = endIndex - startIndex + endexp.matchedLength()

            self.setFormat(startIndex, length, format)
            startIndex = startexp.indexIn(text, startIndex + length)

    def highlightMultilineComments(self, text):
        self.multilineHighlighter(text, self.commentStartExpression, self.commentEndExpression, BLOCKSTATE_COMMENT,
                                  self.format_comment_multi())

    def highlightMultilineStrings(self, text):
        self.multilineHighlighter(text, self.stringExpression, self.stringExpression, BLOCKSTATE_STRING,
                                  self.format_string())

    def highlightMultilineHtml(self, text):
        self.multilineHighlighter(text, self.htmlStartExpression, self.htmlEndExpression, BLOCKSTATE_HTML,
                                  self.format_html(), self.htmlTag)

    def highlightErrors(self):
        text = self.editor.toPlainText()
        self.errors = {}
        T = self.parser.parse(text)
        if T is None:
            for token, msg, exp in self.parser.errors:
                startIndex = token.pos_in_stream
                size = 1
                if isinstance(token, UnexpectedToken):
                    size = len(token.token)
                elif isinstance(token, UnexpectedCharacters):
                    regex = QtCore.QRegExp(r"\s")
                    endIndex = regex.indexIn(text, startIndex)
                    if endIndex == -1:
                        size = len(text) - startIndex
                    else:
                        size = endIndex - startIndex
                elif isinstance(token, Token):
                    size = len(token)
                bix = self.currentBlock().position()
                self.setFormat(startIndex - bix, size, self.format_error(msg))
                for i in range(startIndex, startIndex + size + 1):
                    self.errors[i] = msg
                    # self.setFormat(i - bix, 1, self.format_error(msg))
                self.editor.mainwindow.updateStatus(msg)
        else:
            self.editor.mainwindow.updateStatus("")
            if Config.value("autorender"):
                self.editor.mainwindow.displayGraph()


    def highlightRules(self, text, rules):
        for pattern, formatter in rules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, formatter())
                index = expression.indexIn(text, index + length)

    def highlightBlock(self, text):
        self.setCurrentBlockState(BLOCKSTATE_NORMAL)
        sh = bool(Config.value("syntaxHighlighting", True))
        if sh:
            self.highlightRules(text, self.highlightingRules)
            self.highlightMultilineStrings(text)
            self.highlightMultilineHtml(text)
        if bool(Config.value("useParser", True)):
            self.highlightErrors()
        if sh:
            self.highlightMultilineComments(text)

    @staticmethod
    def format_keyword():
        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(QtGui.QColor(Config.value("col.keyword")))
        keywordFormat.setFontWeight(QtGui.QFont.Bold)
        return keywordFormat

    @staticmethod
    def format_attribute():
        attributeFormat = QtGui.QTextCharFormat()
        attributeFormat.setForeground(QtGui.QColor(Config.value("col.attribute")))
        attributeFormat.setFontWeight(QtGui.QFont.Bold)
        return attributeFormat

    @staticmethod
    def format_comment_hash():
        hashCommentFormat = QtGui.QTextCharFormat()
        hashCommentFormat.setForeground(QtGui.QColor(Config.value("col.hash")))
        hashCommentFormat.setFontItalic(True)
        return hashCommentFormat

    @staticmethod
    def format_comment_single():
        singleLineCommentFormat = QtGui.QTextCharFormat()
        singleLineCommentFormat.setForeground(QtGui.QColor(Config.value("col.comment")))
        singleLineCommentFormat.setFontItalic(True)
        return singleLineCommentFormat

    @staticmethod
    def format_comment_multi():
        multiLineCommentFormat = QtGui.QTextCharFormat()
        multiLineCommentFormat.setForeground(QtGui.QColor(Config.value("col.comment")))
        multiLineCommentFormat.setFontItalic(True)
        return multiLineCommentFormat

    @staticmethod
    def format_number():
        numberFormat = QtGui.QTextCharFormat()
        numberFormat.setForeground(QtGui.QColor(Config.value("col.number")))
        return numberFormat

    @staticmethod
    def format_string():
        quotedStringFormat = QtGui.QTextCharFormat()
        quotedStringFormat.setForeground(QtGui.QColor(Config.value("col.string")))
        return quotedStringFormat

    @staticmethod
    def format_html():
        htmlStringFormat = QtGui.QTextCharFormat()
        htmlStringFormat.setForeground(QtGui.QColor(Config.value("col.html")))
        return htmlStringFormat

    @staticmethod
    def format_error(tooltip=""):
        errorFormat = QtGui.QTextCharFormat()
        errorFormat.setFontUnderline(True)
        errorFormat.setUnderlineColor(QtGui.QColor(Config.value("col.error")))
        errorFormat.setUnderlineStyle(QtGui.QTextCharFormat.WaveUnderline)
        errorFormat.setToolTip(tooltip)
        return errorFormat


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, QPaintEvent):
        self.editor.lineNumberAreaPaintEvent(QPaintEvent)