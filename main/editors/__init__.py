"""This file is meant for easy access to any and all editor types.

Author: Randy Paredis
Date:   01/04/2020
"""

from main.editors.Highlighter import BaseHighlighter
from main.editors.dot.DotHighlighter import DotHighlighter
from main.editors.flowchart.FlowchartHighlighter import FlowchartHighlighter

EDITORTYPES = {
    "": ("No File Type", BaseHighlighter),
    "DOT": ("Graphviz", DotHighlighter),
    "Flowchart": ("Flowchart / Pseudocode", FlowchartHighlighter)
}
