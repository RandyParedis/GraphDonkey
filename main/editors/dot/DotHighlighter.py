"""The syntax highlighter for dot files

Author: Randy Paredis
Date:   12/14/2019
"""

from PyQt5 import QtCore
from main.extra import Constants
from main.editors.dot.DotParser import DotParser
from main.extra.IOHandler import IOHandler
from main.editors import Highlighter as hglt

Config = IOHandler.get_preferences()

class DotHighlighter(hglt.BaseHighlighter):
    def __init__(self, parent=None, editor=None):
        super(DotHighlighter, self).__init__(parent, editor)
        self.parser = DotParser()

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

    def highlightMultilineComments(self, text):
        self.multilineHighlighter(text, self.commentStartExpression, self.commentEndExpression, hglt.BLOCKSTATE_COMMENT,
                                  self.format_comment_multi())

    def highlightMultilineStrings(self, text):
        self.multilineHighlighter(text, self.stringExpression, self.stringExpression, hglt.BLOCKSTATE_STRING_1,
                                  self.format_string())

    def highlightMultilineHtml(self, text):
        self.multilineHighlighter(text, self.htmlStartExpression, self.htmlEndExpression, hglt.BLOCKSTATE_STRING_2,
                                  self.format_html(), self.htmlTag)

    def syntaxHighlighting(self, text):
        hglt.BaseHighlighter.syntaxHighlighting(self, text)
        self.highlightMultilineStrings(text)
        self.highlightMultilineHtml(text)
        self.highlightMultilineComments(text)
