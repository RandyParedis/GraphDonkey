from PyQt5.QtGui import QColor

APP_NAME = "DotGaper"
APP_VERSION = "0.0.1"

STX_KEYWORD_COLOR = QColor(128, 0, 0)
STX_COMMENT_COLOR = QColor("blue")
STX_NUMBER_COLOR = QColor(255, 0, 255)
STX_STRING_COLOR = QColor("green")

STX_CLNUM_COLOR = QColor("yellow").lighter(160)
STX_CLNUM_BCOLOR = QColor("120, 120, 120").darker(160)
STX_OLNUM_COLOR = QColor("black")
STX_OLNUM_BCOLOR = QColor(120, 120, 120)
STX_CLINE_COLOR = QColor("yellow").lighter(160)