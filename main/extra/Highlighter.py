"""The syntax highlighter for the code editor of GraphDonkey

Author: Randy Paredis
Date:   12/14/2019
"""

from PyQt5 import QtGui, QtCore
from main.extra import Constants
from main.extra.Parser import Parser, EOFToken
from main.extra.IOHandler import IOHandler
from main.Preferences import bool

from lark import UnexpectedToken, UnexpectedCharacters, Token

Config = IOHandler.get_preferences()

BLOCKSTATE_NORMAL = 0
BLOCKSTATE_COMMENT = 1
BLOCKSTATE_STRING = 2
BLOCKSTATE_HTML = 4

class ParenthesisInfo:
    def __init__(self, char, pos):
        self.char = char
        self.pos = pos

    def __repr__(self):
        return "ParenthesisInfo <%s, %i>" % (self.char, self.pos)

class TextBlockData(QtGui.QTextBlockUserData):
    def __init__(self):
        super(TextBlockData, self).__init__()
        self.parenthesis = []

    def insert(self, info):
        i = 0
        while i < len(self.parenthesis) and info.pos > self.parenthesis[i].pos:
            i += 1
        self.parenthesis.insert(i, info)

class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None, editor=None):
        super(Highlighter, self).__init__(parent)
        self.editor = editor
        self.highlightingRules = []
        self._setPatterns()
        self.parser = Parser()

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

    def storeErrors(self):
        self.editor.errors = []
        text = self.editor.toPlainText()
        T = self.parser.parse(text) if text != "" else None
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
                elif isinstance(token, (EOFToken, Token)):
                    size = len(token)
                self.editor.errors.append((startIndex, size, msg))
                self.editor.mainwindow.updateStatus(msg)
        else:
            self.editor.mainwindow.updateStatus("")
            if bool(Config.value("editor/autorender")):
                self.editor.mainwindow.displayGraph()

    def highlightRules(self, text, rules):
        for pattern, formatter in rules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, formatter())
                index = expression.indexIn(text, index + length)

    def storeParenthesis(self, text:str):
        data = TextBlockData()
        for c in Constants.INDENT_OPEN + Constants.INDENT_CLOSE:
            leftpos = text.find(c)
            while leftpos != -1:
                info = ParenthesisInfo(c, leftpos)
                data.insert(info)
                leftpos = text.find(c, leftpos + 1)
        self.setCurrentBlockUserData(data)

    def highlightBlock(self, text):
        self.storeParenthesis(text)
        self.storeErrors()
        self.setCurrentBlockState(BLOCKSTATE_NORMAL)
        sh = bool(Config.value("editor/syntaxHighlighting", True))
        if sh:
            self.highlightRules(text, self.highlightingRules)
            self.highlightMultilineStrings(text)
            self.highlightMultilineHtml(text)
            self.highlightMultilineComments(text)

    @staticmethod
    def format_keyword():
        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(QtGui.QColor(Config.value("col/keyword")))
        keywordFormat.setFontWeight(QtGui.QFont.Bold)
        return keywordFormat

    @staticmethod
    def format_attribute():
        attributeFormat = QtGui.QTextCharFormat()
        attributeFormat.setForeground(QtGui.QColor(Config.value("col/attribute")))
        attributeFormat.setFontWeight(QtGui.QFont.Bold)
        return attributeFormat

    @staticmethod
    def format_comment_hash():
        hashCommentFormat = QtGui.QTextCharFormat()
        hashCommentFormat.setForeground(QtGui.QColor(Config.value("col/hash")))
        hashCommentFormat.setFontItalic(True)
        return hashCommentFormat

    @staticmethod
    def format_comment_single():
        singleLineCommentFormat = QtGui.QTextCharFormat()
        singleLineCommentFormat.setForeground(QtGui.QColor(Config.value("col/comment")))
        singleLineCommentFormat.setFontItalic(True)
        return singleLineCommentFormat

    @staticmethod
    def format_comment_multi():
        multiLineCommentFormat = QtGui.QTextCharFormat()
        multiLineCommentFormat.setForeground(QtGui.QColor(Config.value("col/comment")))
        multiLineCommentFormat.setFontItalic(True)
        return multiLineCommentFormat

    @staticmethod
    def format_number():
        numberFormat = QtGui.QTextCharFormat()
        numberFormat.setForeground(QtGui.QColor(Config.value("col/number")))
        return numberFormat

    @staticmethod
    def format_string():
        quotedStringFormat = QtGui.QTextCharFormat()
        quotedStringFormat.setForeground(QtGui.QColor(Config.value("col/string")))
        return quotedStringFormat

    @staticmethod
    def format_html():
        htmlStringFormat = QtGui.QTextCharFormat()
        htmlStringFormat.setForeground(QtGui.QColor(Config.value("col/html")))
        return htmlStringFormat

    @staticmethod
    def format_error(tooltip=""):
        errorFormat = QtGui.QTextCharFormat()
        errorFormat.setFontUnderline(True)
        errorFormat.setUnderlineColor(QtGui.QColor(Config.value("col/error")))
        errorFormat.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
        errorFormat.setToolTip(tooltip)
        return errorFormat