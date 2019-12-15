"""This file contains a set of mutable variables.

Author: Randy Paredis
Date:   12/14/2019
"""
from PyQt5.QtGui import QColor

STX_KEYWORD_COLOR = QColor(128, 0, 0)
STX_COMMENT_COLOR = QColor("blue")
STX_ATTRIBUTE_COLOR = QColor("darkBlue")
STX_NUMBER_COLOR = QColor(255, 0, 255)
STX_STRING_COLOR = QColor("green")

STX_CLNUM_COLOR = QColor("yellow").lighter(160)
STX_CLNUM_BCOLOR = QColor("120, 120, 120").darker(160)
STX_OLNUM_COLOR = QColor("black")
STX_OLNUM_BCOLOR = QColor(120, 120, 120)
STX_CLINE_COLOR = QColor("yellow").lighter(160)

SHORTCUTS = {
    "New": ["Ctrl+N"],
    "Open": ["Ctrl+O"],
    "Save": ["Ctrl+S"],
    "Save As": ["Ctrl+Shift+S"],
    "Exit": ["Ctrl+Q"],

    "Undo": ["Ctrl+Z"],
    "Redo": ["Ctrl+Shift+Z"],
    "Select All": ["Ctrl+A"],
    "Copy": ["Ctrl+C"],
    "Cut": ["Ctrl+X"],
    "Paste": ["CTRL+V"],
    "Render": ["Ctrl+R", "Ctrl+Enter"],
}