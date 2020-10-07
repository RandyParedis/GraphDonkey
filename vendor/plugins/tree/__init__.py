"""Tree

Render JSON/XML as a mindmap.

Author:         Randy Paredis
"""

from vendor.plugins.tree.TreeTransformer import convert_json
from main.extra import Constants

TYPES = {
    "JSON": {
        "extensions": ["json"],
        "grammar": "json.lark",
        "parser": "lalr",
        "highlighting": [
            {
                "regex": ["null", "true", "false"],
                "format": "keyword"
            },
            {
                "regex": r"-?(0|([1-9][0-9]*))(\.[0-9]+)?([eE][+-]?[0-9]+)?",
                "format": "number"
            },
            {
                "regex": r'"([^\\"]|(\\["bfnrtu]))*"',
                "format": "string"
            },
            {
                "regex": r'(?<="[^\\"]|(\\"))*\\([\\\/bfnrt]|(u[0-9a-fA-F]{4}))(?=[^\\"]|(\\")")*',
                "format": "number"
            }
        ],
        "transformer": {
            "Graphviz": convert_json
        },
        "paired": [
            ("{", "}"), ("[", "]"), ('"', '"')
        ],
        "comments": {
            "symbol": "//",
            "indent": False
        }
    }
}
