"""Flowchart

Easily create flowcharts from pseudocode.

Website:    docs/Flowcharts.md
Author:     Randy Paredis
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
                    "pattern": "\\b(%s)\\b" % "|".join(["(%s)" % x for x in keywords]),
                    "caseInsensitive": True
                },
                "format": "keyword"
            },
            {
                "regex": "\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b",
                "format": "number"
            },
            {
                "start": '"',
                "end": '"',
                "format": "string",
                "exclude": '\\\\"'
            },
            {
                "start": "'",
                "end": "'",
                "format": "string",
                "exclude": "\\\\'"
            },
            {
                "start": '`',
                "end": '`',
                "format": "string",
                "exclude": "\\\\`"
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
                "start": "/\\*",
                "end": "\\*/",
                "format": "comment"
            }
        ],
        "converter": {
            "Graphviz": convert
        }
    }
}
