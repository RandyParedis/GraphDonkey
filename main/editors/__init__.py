"""This file is meant for easy access to any and all editor types.

Author: Randy Paredis
Date:   01/04/2020
"""

from main.highlighters.Highlighter import Highlighter
from main.highlighters.DotHighlighter import DotHighlighter
from main.highlighters.FlowchartHighlighter import FlowchartHighlighter

EDITORTYPES = {
    "": ("No File Type", Highlighter),
    "DOT": ("Graphviz", DotHighlighter),
    "Flowchart": ("Flowchart / Pseudocode", FlowchartHighlighter)
}
