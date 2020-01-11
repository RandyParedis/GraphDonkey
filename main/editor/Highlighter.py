"""The syntax highlighter for the code editor of GraphDonkey

Author: Randy Paredis
Date:   12/14/2019
"""

from PyQt5 import QtGui, QtCore
from main.extra import Constants
from main.editor.Parser import Parser, EOFToken
from main.extra.IOHandler import IOHandler
from main.Preferences import bool

from lark import UnexpectedToken, UnexpectedCharacters, Token

Config = IOHandler.get_preferences()

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

    def isOpenFold(self):
        return len(self.parenthesis) > 0 and self.parenthesis[-1].char in Constants.INDENT_OPEN

    def isCloseFold(self):
        return len(self.parenthesis) > 0 and self.parenthesis[0].char in Constants.INDENT_CLOSE

class BaseHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None, editor=None):
        super(BaseHighlighter, self).__init__(parent)
        self.editor = editor
        self.highlightingRules = []
        self.parser = Parser()

    def setRules(self, rules):
        def obtainRegex(value):
            if isinstance(value, str):
                return QtCore.QRegExp(value)
            elif isinstance(value, dict):
                if value.get("caseInsensitive", False):
                    return QtCore.QRegExp(value["pattern"], QtCore.Qt.CaseInsensitive)
                else:
                    return QtCore.QRegExp(value["pattern"])
            return None

        state = 1
        for rule in rules:
            if "regex" in rule and "format" in rule:
                regex = obtainRegex(rule["regex"])
                fmt = getattr(self, "format_%s" % rule["format"])
                if regex is not None:
                    self.highlightingRules.append((regex, fmt))
            elif "start" in rule and "end" in rule and "format" in rule:
                start = obtainRegex(rule["start"])
                end = obtainRegex(rule["end"])
                exclude = obtainRegex(rule.get("exclude", None))
                fmt = getattr(self, "format_%s" % rule["format"])
                if start is not None and end is not None:
                    self.highlightingRules.append((start, end, state, fmt(), exclude))
                    state *= 2
            else:
                raise ValueError("Invalid Highlighting Rule %s" % str(rule))

    def multilineHighlighter(self, text, startexp, endexp, blockstate, format, skipexp=None):
        startIndex = 0
        pbs = self.previousBlockState()
        if pbs == -1 or not pbs & blockstate:
            startIndex = startexp.indexIn(text)

        while startIndex >= 0:
            begin = startIndex + 1
            if skipexp:
                skipIndex = skipexp.lastIndexIn(text)
                if skipIndex != -1:
                    begin = skipIndex + skipexp.matchedLength()
            endIndex = endexp.indexIn(text, begin)

            if endIndex == -1:
                self.setCurrentBlockState(self.currentBlockState() | blockstate)
                length = len(text) - startIndex
            else:
                length = endIndex - startIndex + endexp.matchedLength()

            self.setFormat(startIndex, length, format)
            startIndex = startexp.indexIn(text, startIndex + length)

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
        self.setCurrentBlockState(0)
        sh = bool(Config.value("editor/syntaxHighlighting", True))
        if sh:
            for rule in self.highlightingRules:
                if len(rule) == 2:
                    pattern, formatter = rule
                    expression = QtCore.QRegExp(pattern)
                    index = expression.indexIn(text)
                    while index >= 0:
                        length = expression.matchedLength()
                        self.setFormat(index, length, formatter())
                        index = expression.indexIn(text, index + length)
                else:
                    self.multilineHighlighter(text, *rule)

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
    def format_hash():
        hashCommentFormat = QtGui.QTextCharFormat()
        hashCommentFormat.setForeground(QtGui.QColor(Config.value("col/hash")))
        hashCommentFormat.setFontItalic(True)
        return hashCommentFormat

    @staticmethod
    def format_comment():
        singleLineCommentFormat = QtGui.QTextCharFormat()
        singleLineCommentFormat.setForeground(QtGui.QColor(Config.value("col/comment")))
        singleLineCommentFormat.setFontItalic(True)
        return singleLineCommentFormat

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
    def format_error():
        errorFormat = QtGui.QTextCharFormat()
        errorFormat.setFontUnderline(True)
        errorFormat.setUnderlineColor(QtGui.QColor(Config.value("col/error")))
        errorFormat.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
        return errorFormat