"""Flowchart

Easily create flowcharts from pseudocode.

Author:         Randy Paredis
Requires:       `graphviz` package
Documentation:  https://github.com/RandyParedis/GraphDonkey/wiki/Flowcharts
"""
from vendor.plugins.flowchart.Flowchart import CheckFlowchartVisitor, convert
from main.extra import Constants

keywords = [
    "if", "then", "else", "elif", "fi", "end", "do", "done", "while", "is", "in", "mod", "and", "or", "inc",
    "dec", "increment", "decrement", "break", "continue", "input", "output", "return", "comment"
]

TYPES = {
    "Flowchart / Pseudocode": {
        "extensions": ["code", "psc", "pseudo", "pseudocode", "flowchart", "fc"],
        "grammar": "flowchart.lark",
        "semantics": CheckFlowchartVisitor,
        "highlighting": [
            {
                "regex": {
                    "pattern": keywords,
                    "insensitive": True
                },
                "format": "keyword"
            },
            {
                "regex": "\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b",
                "format": "number"
            },
            {
                "regex": "(?<q>\"|'|`)[^\\\\]*?(?:\\\\.[^\\\\]*?)*?(?P=q)",
                "format": "string",
                "global": True
            },
            {
                "regex": "^%%[^%s]*$" % Constants.LINE_ENDING,
                "format": "hash"
            },
            {
                "regex": "^//[^%s]*$" % Constants.LINE_ENDING,
                "format": "comment"
            },
            {
                "regex": {
                    "pattern": "/\\*.*?\\*/",
                    "single": True
                },
                "format": "comment",
                "global": True
            }
        ],
        "transformer": {
            "Graphviz": convert
        },
        "comments": {
            "symbol": "//",
            "indent": False
        },
        "paired": [("if", "fi"), ("do", "done"), ("(", ")"), ('"', '"'), ("'", "'")]
    }
}
