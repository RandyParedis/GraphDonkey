"""Graphviz

Render graphs in Graphviz/Dot format.

Graphviz is open source graph visualization software. Graph visualization is a way of
representing structural information as diagrams of abstract graphs and networks. It has
important applications in networking, bioinformatics,  software engineering, database
and web design, machine learning, and in visual interfaces for other technical domains.

Website:    https://www.graphviz.org/
Author:     Randy Paredis
"""
from vendor.plugins.graphviz.CheckDot import CheckDotVisitor
from vendor.plugins.graphviz.Engine import convert
from vendor.plugins.graphviz.Settings import GraphvizSettings
from main.extra import Constants

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
    "DOT": {
        "name": "Graphviz",
        "extensions": ["canon", "dot", "gv", "xdot", "xdot1.2", "xdot1.4"],
        "grammar": "graphviz.lark",
        "semantics": CheckDotVisitor,
        "highlighting": [
            {
                "regex": {
                    "pattern": "\\b(%s)\\b" % "|".join(["(%s)" % x for x in keywords]),
                    "caseInsensitive": True
                },
                "format": "keyword"
            },
            {
                "regex": "(%s)(?=\\s*[=])" % "|".join(["(%s)" % x for x in attributes]),
                "format": "attribute"
            },
            {
                "regex": "\\b(%s)\\b" % "|".join(["(%s)" % x for x in sp_attrs]),
                "format": "attribute"
            },
            {
                "regex": "\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b",
                "format": "number"
            },
            {
                "start": '"',
                "end": '"',
                "format": "string"
            },
            {
                "start": '<',
                "end": '>',
                "format": "html",
                "exclude": "</?[^<>/%s]*>" % Constants.LINE_ENDING
            },
            {
                "regex": "^#[^%s]*$" % Constants.LINE_ENDING,
                "format": "comment_hash"
            },
            {
                "regex": "^//[^%s]*$" % Constants.LINE_ENDING,
                "format": "comment_single"
            },
            {
                "start": "/\\*",
                "end": "\\*/",
                "format": "comment_multi"
            }
        ],
        "converter": {
            "Graphviz": lambda x, T: x
        }
    }
}

ENGINES = {
    "Graphviz": {
        "convert": convert,
        "preferences": {
            "file": "preferences.ui",
            "class": GraphvizSettings
        }
    }
}
