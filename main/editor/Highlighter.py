"""The syntax highlighter for the code editor of GraphDonkey

Author: Randy Paredis
Date:   12/14/2019
"""
import math

from PyQt5 import QtGui, QtCore
from main.extra import Constants
from main.editor.Parser import Parser, EOFToken
from main.extra.IOHandler import IOHandler
from main.Preferences import bool

from lark import UnexpectedToken, UnexpectedCharacters, Token

Config = IOHandler.get_preferences()

class BracketInfo:
    def __init__(self, char, pos):
        self.char = char
        self.pos = pos

    def at(self, pos):
        return self.pos <= pos <= self.pos + len(self.char)

    def __repr__(self):
        return "BracketInfo <%s, %i>" % (self.char, self.pos)

class TextBlockData(QtGui.QTextBlockUserData):
    def __init__(self):
        super(TextBlockData, self).__init__()
        self.parenthesis = []

    def insert(self, info):
        i = 0
        while i < len(self.parenthesis) and info.pos > self.parenthesis[i].pos:
            i += 1
        self.parenthesis.insert(i, info)

    def indexOf(self, pos):
        for i in range(len(self.parenthesis)):
            if pos <= self.parenthesis[i].pos:
                return i
        return -1

class BaseHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None, editor=None):
        super(BaseHighlighter, self).__init__(parent)
        self.editor = editor
        self.highlightingRules = []
        self.parser = Parser()

    def setRules(self, rules):
        def obtainRegex(value):
            if isinstance(value, str):
                return QtCore.QRegularExpression(value)
            elif isinstance(value, dict):
                reg = obtainRegex(value["pattern"])
                ptns = QtCore.QRegularExpression.NoPatternOption
                if value.get("insensitive", False):
                    ptns |= QtCore.QRegularExpression.CaseInsensitiveOption
                if value.get("single", False):
                    ptns |= QtCore.QRegularExpression.DotMatchesEverythingOption
                if value.get("multiline", False):
                    ptns |= QtCore.QRegularExpression.MultilineOption
                if value.get("extended", False):
                    ptns |= QtCore.QRegularExpression.ExtendedPatternSyntaxOption
                if value.get("unicode", False):
                    ptns |= QtCore.QRegularExpression.UseUnicodePropertiesOption
                if value.get("ungreedy", False):
                    ptns |= QtCore.QRegularExpression.InvertedGreedinessOption
                reg.setPatternOptions(ptns)
                return reg
            elif isinstance(value, list):
                return obtainRegex("\\b(%s)\\b" % "|".join(["(%s)" % x for x in value]))
            return None

        for rule in rules:
            if "regex" in rule and "format" in rule:
                regex = obtainRegex(rule["regex"])
                fmt = getattr(self, "format_%s" % rule["format"])
                if regex is not None:
                    self.highlightingRules.append((regex, fmt, rule.get("global", False)))
            else:
                raise ValueError("Invalid Highlighting Rule %s" % str(rule))

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

    def storeBrackets(self, text:str):
        from main.plugins import PluginLoader
        paired = PluginLoader.instance().getPairedBrackets(self.editor.wrapper.filetype.currentText())
        flattened = list(set([x for p in paired for x in p]))

        data = TextBlockData()
        for c in flattened:
            leftpos = text.find(c)
            while leftpos != -1:
                info = BracketInfo(c, leftpos)
                data.insert(info)
                leftpos = text.find(c, leftpos + 1)
        self.setCurrentBlockUserData(data)

    def highlightBlock(self, text):
        self.storeBrackets(text)
        self.setCurrentBlockState(0)
        sh = bool(Config.value("editor/syntaxHighlighting", True))
        if sh:
            bpos = self.currentBlock().position()
            blen = self.currentBlock().length()
            for rule in self.highlightingRules:
                expression, formatter, g = rule
                if g:
                    it = expression.globalMatch(self.editor.toPlainText())
                    while it.hasNext():
                        match = it.next()
                        index = match.capturedStart()
                        length = match.capturedLength()
                        if bpos <= index <= index + length <= bpos + blen:
                            self.setFormat(index - bpos, length, formatter())
                        elif bpos <= index:
                            self.setFormat(index - bpos, bpos + blen - index, formatter())
                        elif index <= bpos <= bpos + blen <= index + length:
                            self.setFormat(0, blen, formatter())
                        elif index <= bpos <= index + length <= bpos + blen:
                            self.setFormat(0, index + length - bpos, formatter())
                else:
                    match = expression.match(text)
                    index = match.capturedStart()
                    while match.isValid() and index >= 0:
                        length = match.capturedLength()
                        self.setFormat(index, length, formatter())
                        match = expression.match(text, index + length)
                        index = match.capturedStart()

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