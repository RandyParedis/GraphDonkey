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

    def event(self, event: QtCore.QEvent):
        if event.type() == QtCore.QEvent.ShortcutOverride:
            return False
        return QtWidgets.QTextEdit.event(self, event)

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

        if bool(Config.value("useParser", True)):
            self.highlighter.highlightErrors(self.toPlainText())
            # TODO: apply QSyntaxHighlighter first on file before going over all blocks


class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None, editor=None):
        super(Highlighter, self).__init__(parent)
        self.editor = editor
        self.highlightingRules = []
        self.multiLineCommentFormat = None
        self.commentStartExpression = None
        self.commentEndExpression = None
        self.setPatterns()
        self.parser = Parser()

    def setPatterns(self):
        keywordPatterns = ["\\b%s\\b" % x for x in Constants.STRICT_KEYWORDS]
        self.highlightingRules = [(QtCore.QRegExp(pattern, QtCore.Qt.CaseInsensitive), self.format_keyword)
                                  for pattern in keywordPatterns]

        attributePatterns = "|".join(["(" + x + ")" for x in Constants.ATTRIBUTES])
        attributePatterns = "(%s)(?=\\s*[=])" % attributePatterns
        self.highlightingRules.append((QtCore.QRegExp("(%s)(?=\\s*[=])" % attributePatterns), self.format_attribute))
        for a in Constants.SPECIAL_ATTRIBUTES:
            self.highlightingRules.append((QtCore.QRegExp("\\b%s\\b" % a), self.format_attribute))

        self.highlightingRules.append((QtCore.QRegExp("^#[^\n]*$"), self.format_comment_hash))
        self.highlightingRules.append((QtCore.QRegExp("//[^\n]*"), self.format_comment_single))

        self.commentStartExpression = QtCore.QRegExp("/\\*")
        self.commentEndExpression = QtCore.QRegExp("\\*/")

        self.highlightingRules.append((QtCore.QRegExp("\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b"), self.format_number))
        # TODO: quoted strings may contain newlines
        #       also; "yay" + "yay" will be marked as string as a whole, which is okay for now
        self.highlightingRules.append((QtCore.QRegExp("\".*\""), self.format_string))
        self.highlightingRules.append((QtCore.QRegExp("<.*>"), self.format_html))

    def highlightMultilineComments(self, text):
        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()

            self.setFormat(startIndex, commentLength, self.format_comment_multi())
            startIndex = self.commentStartExpression.indexIn(text, startIndex + commentLength)

    def highlightErrors(self, text):
        T = self.parser.parse(text)
        if T is None:
            for token, msg, exp in self.parser.errors:
                self.setCurrentBlockState(0)
                startIndex = token.pos_in_stream
                size = 1
                if isinstance(token, UnexpectedToken):
                    size = len(token.token)
                elif isinstance(token, UnexpectedCharacters):
                    regex = QtCore.QRegExp(r"\s")
                    endIndex = regex.indexIn(text, startIndex)
                    if endIndex == -1:
                        self.setCurrentBlockState(1)
                        endIndex = len(text) - startIndex
                    size = endIndex - startIndex
                elif isinstance(token, Token):
                    size = len(token)
                self.setFormat(startIndex, size, self.format_error(msg))
                self.editor.mainwindow.updateStatus(msg)
        else:
            self.editor.mainwindow.updateStatus("")
            if Config.value("autorender"):
                self.editor.mainwindow.displayGraph()


    def highlightBlock(self, text):
        if bool(Config.value("syntaxHighlighting", True)):
            for pattern, formatter in self.highlightingRules:
                expression = QtCore.QRegExp(pattern)
                index = expression.indexIn(text)
                while index >= 0:
                    length = expression.matchedLength()
                    self.setFormat(index, length, formatter())
                    index = expression.indexIn(text, index + length)
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
        return errorFormat


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, QPaintEvent):
        self.editor.lineNumberAreaPaintEvent(QPaintEvent)