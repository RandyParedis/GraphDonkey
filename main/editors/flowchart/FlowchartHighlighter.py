"""The syntax highlighter for dot files

Author: Randy Paredis
Date:   12/14/2019
"""

from PyQt5 import QtCore
from main.extra import Constants
from main.editors.flowchart.FlowchartParser import FlowchartParser
from main.extra.IOHandler import IOHandler
from main.editors import Highlighter as hglt

Config = IOHandler.get_preferences()

KEYWORDS = ["if", "then", "else", "elif", "fi", "end", "do", "done", "while", "is", "in", "mod", "and", "or", "inc",
            "dec", "increment", "decrement", "break", "continue", "input", "output", "return", "comment"]

class FlowchartHighlighter(hglt.BaseHighlighter):
    def __init__(self, parent=None, editor=None):
        super(FlowchartHighlighter, self).__init__(parent, editor)
        self.parser = FlowchartParser()

    def _setPatterns(self):
        keywordPatterns = ["\\b%s\\b" % x for x in KEYWORDS]
        self.highlightingRules = [(QtCore.QRegExp(pattern, QtCore.Qt.CaseInsensitive), self.format_keyword)
                                  for pattern in keywordPatterns]

        self.highlightingRules.append((QtCore.QRegExp("\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b"), self.format_number))

        self.highlightingRules.append((QtCore.QRegExp("//[^%s]*" % Constants.LINE_ENDING), self.format_comment_single))
        self.highlightingRules.append((QtCore.QRegExp("^%%[^%s]*$" % Constants.LINE_ENDING), self.format_comment_hash))

        self.stringExpressions = [QtCore.QRegExp(x) for x in "'\"`"]
        self.commentStartExpression = QtCore.QRegExp("/\\*")
        self.commentEndExpression = QtCore.QRegExp("\\*/")

    def highlightMultilineComments(self, text):
        self.multilineHighlighter(text, self.commentStartExpression, self.commentEndExpression, hglt.BLOCKSTATE_COMMENT,
                                  self.format_comment_multi())

    def highlightMultilineStrings(self, text):
        lst = [hglt.BLOCKSTATE_STRING_1, hglt.BLOCKSTATE_STRING_2, hglt.BLOCKSTATE_STRING_3]
        for i in range(3):
            exp = self.stringExpressions[i]
            self.multilineHighlighter(text, exp, exp, lst[i], self.format_string(),
                                      QtCore.QRegExp("\\\\" + exp.pattern()))

    def syntaxHighlighting(self, text):
        hglt.BaseHighlighter.syntaxHighlighting(self, text)
        self.highlightMultilineStrings(text)
        self.highlightMultilineComments(text)
