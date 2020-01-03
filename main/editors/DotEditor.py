"""The editor for the DOT language.

It extends the normal editor via providing a custom highlighter and parser.

Author: Randy Paredis
Date:   01/03/2020
"""

from main.editors.CodeEditor import CodeEditor
from main.highlighters.DotHighlighter import DotHighlighter

class DotEditor(CodeEditor):
    def __init__(self, parent=None):
        super(DotEditor, self).__init__(parent)
        self.highlighter = DotHighlighter(self.document(), self)

    def graphviz(self):
        return self.toPlainText()
