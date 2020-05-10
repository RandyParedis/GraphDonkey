"""Drawing

Engine for drawing in a 2D space. This can be used by many formats that are
not representable in a graph.

Author:         Randy Paredis
Requires:       The `Pillow` package.
"""
from vendor.plugins.drawing.Engine import convert
from main.extra import Constants

keywords = [
    "at", "from", "to", "of", "in", "grid", "border",
    "point", "line", "ellipse", "rectangle", "polygon",
    "arc", "chord", "pie", "pieslice", "text"
]

attributes = [
    "width", "filled", "color", "colour"
]

other = [
    "radians", "degrees", "deg", "rad", "d", "r", "°",
    "center"
]

TYPES = {
    "Drawing": {
        "extensions": ["draw"],
        "grammar": "drawing.lark",
        "parser": "earley",
        "highlighting": [
            {
                "regex": keywords,
                "format": "keyword"
            },
            {
                "regex": attributes,
                "format": "keyword"
            },
            {
                "regex": other,
                "format": "attribute"
            },
            {
                "regex": "#(([0-9a-f]{6})|([0-9A-F]{6}))",
                "format": "number"
            },
            {
                "regex": "\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b",
                "format": "number"
            },
            {
                "regex": {
                    "pattern": r"((<)|\")(?:(?(2)(.|<)*?|[^\"\\]*(?:\\.[^\"\\]*)*))(?(2)>|\")",
                    "single": True
                },
                "format": "string",
                "global": True
            },
            {
                "regex": "^#[^%s]*$" % Constants.LINE_ENDING,
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
            "Pillow": lambda x, T: T
        }
    }
}

ENGINES = {
    "Pillow": {
        "convert": convert,
        # "export": {
        #     "extensions": ['fig', 'jpeg', 'pdf', 'tk', 'eps', 'cmapx_np', 'jpe', 'ps', 'ismap', 'x11', 'dot_json', 'gd',
        #                    'plain', 'vmlz', 'xlib', 'pic', 'plain-ext', 'pov', 'vml', 'json0', 'cmapx', 'jpg', 'svg',
        #                    'wbmp', 'vrml', 'xdot_json', 'gd2', 'png', 'gif', 'imap_np', 'svgz', 'ps2', 'cmap', 'json',
        #                    'mp', 'imap'],
        #     "exporter": export
        # }
    }
}
