"""Drawing

Engine for drawing in a 2D space. This can be used by many formats that are
not representable in a graph.

Author:         Randy Paredis
Requires:       The `Pillow` and `pycairo` packages.
"""
from vendor.plugins.drawing import Cairo, Engine, Lindenmayer
from main.extra import Constants

# TODO: Pillow, Docs, Export as SVG

keywords = [
    "at", "from", "to", "of", "in",
    "point", "line", "ellipse", "rectangle", "polygon",
    "arc", "chord", "pie", "pieslice"
]

attributes = [
    "width", "filled", "color", "colour"
]

other = [
    "radians", "degrees", "deg", "rad", "d", "r"
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
                "regex": other + ["center"],
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
                    "pattern": r"\"(?:[^\"\\]|\\.)*\"",
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
            "Cairo": Engine.transform
        },
        "comments": "//"
    },
    "Lindenmayer": {
        "extensions": ["l", "lm", "l2", "lindenmayer"],
        "grammar": "lindenmayer.lark",
        "parser": "earley",
        "semantics": Lindenmayer.CheckLVisitor,
        "highlighting": [
            {
                "regex": {
                    "pattern": [
                        "alphabet", "alpha",
                        "axiom", "start", "initial", "init", "initializer",
                        "angle", "seed", "depth", "n", "to", "is"
                    ],
                    "insensitive": True
                },
                "format": "keyword"
            },
            {
                "regex": {
                    "pattern": other,
                    "insensitive": True
                },
                "format": "attribute"
            },
            {
                "regex": "-?([1-9][0-9]*|0)",
                "format": "number"
            },
            {
                "regex": "0?\\.[0-9]+",
                "format": "number"
            },
            {
                "regex": "-?([1-9][0-9]*|0)(\\.[0-9]+)?",
                "format": "number"
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
            "Cairo": Lindenmayer.transform
        }
    }
}

ENGINES = {
    "Cairo": {
        "convert": Cairo.convert,
        # "export": {
        #     "extensions": ['fig', 'jpeg', 'pdf', 'tk', 'eps', 'cmapx_np', 'jpe', 'ps', 'ismap', 'x11', 'dot_json', 'gd',
        #                    'plain', 'vmlz', 'xlib', 'pic', 'plain-ext', 'pov', 'vml', 'json0', 'cmapx', 'jpg', 'svg',
        #                    'wbmp', 'vrml', 'xdot_json', 'gd2', 'png', 'gif', 'imap_np', 'svgz', 'ps2', 'cmap', 'json',
        #                    'mp', 'imap'],
        #     "exporter": export
        # }
    }
}
