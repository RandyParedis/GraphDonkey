"""Graphviz

Render graphs in Graphviz/Dot format.

Graphviz is open source graph visualization software. Graph visualization is a way of
representing structural information as diagrams of abstract graphs and networks. It has
important applications in networking, bioinformatics,  software engineering, database
and web design, machine learning, and in visual interfaces for other technical domains.

This plugin includes:

*   Syntax Highlighting and (LALR) Parsing for Graphviz-Files
*   A rendering engine for Graphviz. This engine allows:
    + Rendering in `dot`, `neato`, `twopi`, `circo`, `fdp`, `sfdp`, `patchwork` and `osage`
    + Exporting to numerous filetypes
    + Rendering AST structures to be shown
*   Customizable options

Author:         Randy Paredis
Website:        https://www.graphviz.org/
Credits:        https://www.graphviz.org/credits/
Requires:       Obviously, this requires the `graphviz` package.
Documentation:  https://github.com/RandyParedis/GraphDonkey/wiki/Graphviz
"""
from vendor.plugins.graphviz.CheckDot import CheckDotVisitor
from vendor.plugins.graphviz.Engine import convert, export, AST
from vendor.plugins.graphviz.Settings import GraphvizSettings
from main.extra import Constants

ICON = "graphviz.png"

keywords = [
    "strict", "graph", "digraph", "node", "edge", "subgraph"
]

attributes = [
    "Damping", "K", "URL", "_background", "area", "arrowhead", "arrowsize", "arrowtail", "bb",
    "bgcolor", "center", "charset", "clusterrank", "color", "colorscheme", "comment", "compound",
    "concentrate", "constraint", "decorate", "defaultdist", "dim", "dimen", "dir", "diredgeconstraints",
    "distortion", "dpi", "edgeURL", "edgehref", "edgetarget", "edgetooltip", "epsilon", "esep", "fillcolor",
    "fixedsize", "fontcolor", "fontname", "fontnames", "fontpath", "fontsize", "forcelabels", "gradientangle",
    "group", "headURL", "head_lp", "headclip", "headhref", "headlabel", "headport", "headtarget", "headtooltip",
    "height", "href", "id", "image", "imagepath", "imagepos", "imagescale", "inputscale", "label", "labelURL",
    "label_scheme", "labelangle", "labeldistance", "labelfloat", "labelfontcolor", "labelfontname", "labelfontsize",
    "labelhref", "labeljust", "labelloc", "labeltarget", "labeltooltip", "landscape", "layer", "layerlistsep",
    "layers", "layerselect", "layersep", "layout", "len", "levels", "levelsgap", "lhead", "lheight", "lp",
    "ltail", "lwidth", "margin", "maxiter", "mclimit", "mindist", "minlen", "mode", "model", "mosek", "newrank",
    "nodesep", "nojustify", "normalize", "notranslate", "nslimit", "nslimit1", "ordering", "orientation",
    "outputorder", "overlap", "overlap_scaling", "overlap_shrink", "pack", "packmode", "pad", "page", "pagedir",
    "pencolor", "penwidth", "peripheries", "pin", "pos", "quadtree", "quantum", "rank", "rankdir", "ranksep",
    "ratio", "rects", "regular", "remincross", "repulsiveforce", "resolution", "root", "rotate", "rotation",
    "samehead", "sametail", "samplepoints", "scale", "searchsize", "sep", "shape", "shapefile", "showboxes", "sides",
    "size", "skew", "smoothing", "sortv", "splines", "start", "style", "stylesheet", "tailURL", "tail_lp", "tailclip",
    "tailhref", "taillabel", "tailport", "tailtarget", "tailtooltip", "target", "tooltip", "truecolor", "vertices",
    "viewport", "voro_margin", "weight", "width", "xdotversion", "xlabel", "xlp", "z"
]

sp_attrs = [
    "n", "ne", "e", "se", "s", "sw", "w", "nw", "c", "_"
]

TYPES = {
    "Graphviz": {
        "extensions": ["canon", "dot", "gv", "xdot", "xdot1.2", "xdot1.4"],
        "grammar": "graphviz.lark",
        "parser": "earley",
        "semantics": CheckDotVisitor,
        "highlighting": [
            {
                "regex": {
                    "pattern": keywords,
                    "insensitive": True
                },
                "format": "keyword"
            },
            {
                "regex": "(%s)(?=\\s*[=])" % "|".join(["(%s)" % x for x in attributes]),
                "format": "attribute"
            },
            {
                "regex": sp_attrs,
                "format": "attribute"
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
                "regex": "//[^%s]*$" % Constants.LINE_ENDING,
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
            "Graphviz": lambda x, T: x
        },
        "snippets": {
            "FSA Start Node": "start [label=\"\", shape=none, width=0];",
            "FSA End Node": "end [shape=doublecircle];",
            "Disable Ordering": 'graph [ordering="out"];'
        },
        "paired": [
            ("{", "}"), ("[", "]"), ("<", ">"), ('"', '"')
        ],
        "comments": {
            "symbol": "//",
            "indent": False
        }
    }
}

ENGINES = {
    "Graphviz": {
        "convert": convert,
        "preferences": {
            "file": "preferences.ui",
            "class": GraphvizSettings
        },
        "AST": AST,
        "export": {
            "extensions": ['fig', 'jpeg', 'pdf', 'tk', 'eps', 'cmapx_np', 'jpe', 'ps', 'ismap', 'x11', 'dot_json', 'gd',
                           'plain', 'vmlz', 'xlib', 'pic', 'plain-ext', 'pov', 'vml', 'json0', 'cmapx', 'jpg', 'svg',
                           'wbmp', 'vrml', 'xdot_json', 'gd2', 'png', 'gif', 'imap_np', 'svgz', 'ps2', 'cmap', 'json',
                           'mp', 'imap'],
            "exporter": export
        }
    }
}
