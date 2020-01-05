"""The syntax highlighter for dot files

Author: Randy Paredis
Date:   12/14/2019
"""

from PyQt5 import QtCore
from main.extra import Constants
from main.parsers.FlowchartParser import FlowchartParser
from main.extra.IOHandler import IOHandler
from main.Preferences import bool
from main.highlighters import Highlighter as hlgt

Config = IOHandler.get_preferences()

KEYWORDS = ["if", "then", "else", "elif", "fi", "end", "do", "done", "while", "is", "in", "mod", "and", "or", "inc",
            "dec", "increment", "decrement", "break", "continue", "input", "output", "return"]

class FlowchartHighlighter(hlgt.Highlighter):
    def __init__(self, parent=None, editor=None):
        super(FlowchartHighlighter, self).__init__(parent, editor)
        self.parser = FlowchartParser()

    def _setPatterns(self):
        keywordPatterns = ["\\b%s\\b" % x for x in KEYWORDS]
        self.highlightingRules = [(QtCore.QRegExp(pattern, QtCore.Qt.CaseInsensitive), self.format_keyword)
                                  for pattern in keywordPatterns]

        self.highlightingRules.append((QtCore.QRegExp("\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b"), self.format_number))

        self.highlightingRules.append((QtCore.QRegExp("'[^%s]*'" % Constants.LINE_ENDING), self.format_string))
        self.highlightingRules.append((QtCore.QRegExp('"[^%s]*"' % Constants.LINE_ENDING), self.format_string))
        self.highlightingRules.append((QtCore.QRegExp("//[^%s]*" % Constants.LINE_ENDING), self.format_comment_single))
        self.highlightingRules.append((QtCore.QRegExp("%%[^%s]*" % Constants.LINE_ENDING), self.format_comment_hash))

        self.commentStartExpression = QtCore.QRegExp("/\\*")
        self.commentEndExpression = QtCore.QRegExp("\\*/")

    def highlightMultilineComments(self, text):
        self.multilineHighlighter(text, self.commentStartExpression, self.commentEndExpression, hlgt.BLOCKSTATE_COMMENT,
                                  self.format_comment_multi())

    def highlightBlock(self, text):
        hlgt.Highlighter.highlightBlock(self, text)
        sh = bool(Config.value("editor/syntaxHighlighting", True))
        if sh:
            self.highlightMultilineComments(text)
