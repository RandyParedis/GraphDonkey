"""This file contains a set of immutable variables.

Author: Randy Paredis
Date:   12/15/2019
"""
from PyQt5.QtGui import QIcon, QImage
from main.extra.IOHandler import IOHandler

APP_NAME = "GraphDonkey"
APP_VERSION = "0.1.1"
APP_ICON = QIcon(IOHandler.dir_icons("graphdonkey.svg"))

ICON_GRAPHVIZ = QImage(IOHandler.dir_icons("graphviz.png"))
ICON_UNDO = QImage(IOHandler.dir_icons("undo.png"))
ICON_REDO = QImage(IOHandler.dir_icons("redo.png"))
ICON_NEW = QImage(IOHandler.dir_icons("new.png"))
ICON_OPEN = QImage(IOHandler.dir_icons("open.png"))
ICON_SAVE = QImage(IOHandler.dir_icons("save.png"))
ICON_RENDER = QImage(IOHandler.dir_icons("render.png"))


################################
#       FILE TYPE CONFIG       #
################################

FILE_TYPES_OPEN = {
    "DOT": ["canon", "dot", "gv", "xdot", "xdot1.2", "xdot1.4"],
}

FILE_TYPES_SAVE = {
    "Windows Bitmap Format": ["bmp"],
    "CGImage Bitmap Format": ["cgimage"],
    "Encapsulated PostScript": ["eps"],
    "OpenEXR": ["exr"],
    "FIG": ["fig"],
    "GD/GD2": ["gd", "gd2"],
    "GIF": ["gif"],
    "GTK Canvas": ["gtk"],
    "Icon": ["ico"],
    "Server-Side and Client-Side Imagemaps": ["imap", "cmapx", "imap_np", "cmapx_np"],
    "JPEG 2000": ["jp2"],
    "JPEG": ["jpg", "jpeg", "jpe"],
    "JSON": ["json", "json0", "dot_json", "xdot_json"],
    "PICT": ["pct", "pict"],
    "Portable Document Format": ["pdf"],
    "Kernighan's PIC Graphics Language": ["pic"],
    "Simple Text": ["plain", "plain-ext"],
    "Portable Network Graphics": ["png"],
    "POV-Ray Markup Language": ["pov"], # Prototype
    "PostScript": ["ps"],
    "PostScript for PDF": ["ps2"],
    "PSD": ["psd"],
    "SGI": ["sgi"],
    "Scalable Vector Graphics": ["svg", "svgz"],
    "Truevision TGA": ["tga"],
    "Tag Image File Format": ["tif", "tiff"],
    "TK Graphics": ["tk"],
    "Vector Markup Language": ["vml", "vmlz"],
    "VRML": ["vrml"],
    "Wireless BitMap": ["wbmp"],
    "Web Image": ["webp"],
    "Xlib Canvas": ["xlib", "x11"]
}

for k in FILE_TYPES_OPEN:
    FILE_TYPES_SAVE[k] = FILE_TYPES_OPEN[k]

def file_list_open():
    return ";;".join(["%s Files (*.%s)" % (x, " *.".join(FILE_TYPES_OPEN[x])) for x in FILE_TYPES_OPEN])

def file_list_save():
    return ";;".join(["%s Files (*.%s)" % (x, " *.".join(FILE_TYPES_SAVE[x])) for x in FILE_TYPES_SAVE])

def obtain_ext(category):
    if "." in category:
        i = 0
        for c in range(len(category)):
            if category[c] == '(':
                i = c
                break
        exts = category[i + 3:-1]
        return exts.split(" *.")[0]
    else:
        return ""

def valid_ext(extension, group):
    for x in group:
        if extension in group[x]:
            return True
    return False


################################
#        KEYWORD CONFIG        #
################################

STRICT_KEYWORDS = [
    "strict", "graph", "digraph", "node", "edge", "subgraph"
]

ATTRIBUTES = [
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

SPECIAL_ATTRIBUTES = [
    "n", "ne", "e", "se", "s", "sw", "w", "nw", "c", "_"
]
