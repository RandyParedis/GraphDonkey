"""This file is a collection of Graphviz attributes.

NOTE: THIS IS CURRENTLY DISCONTINUED (see below)

More specifically, all attributes are functions that check
the validity of the assigned value. All values need to be
passed as strings for generality. On top of that, they have
to be stripped from string separators for validity. This
can be done with the bundled 'strip' function.

The second parameter is the scope in which the attribute
was found. This is also a string, containing the "Used By"
letters (i.e. E, N, G, S and C).

They return a string with additional notes about the
attribute (to be shown as a warning).

If the scope is invalid, a KeyError is raised.
If the value cannot be converted, a ValueError is raised.

They raise a DeprecationWarning if the attribute is marked
as deprecated by Graphviz.

All attribute information found on:
    https://graphviz.gitlab.io/_pages/doc/info/attrs.html


Additionally, the 'check*' functions are used internally by
the attributes.

TODO: return 'constraints' dictionary for checking against
      other attributes

FIXME: If there is an issue in a graph, dot just ignores this.
        This is the reason this file is incomplete and remains
        incomplete until the user-base requests a feature like
        this. Or, until someone makes a PR with a completion of
        this file.

Author: Randy Paredis
Date:   12-26-2019
"""
import re

def strip(value):
    """Strips the string separators from the value."""
    if value[0] in '"<' and value[-1] in '">':
        return value[1:-1]
    return value

def checkValidScope(scheck, sref):
    f = False
    for c in scheck:
        if c in sref:
            f = True
            break
    if not f:
        raise KeyError("Invalid scope for attribute")

def checkDouble(value, minimum=None, inc=True):
    if len(value) == 0:
        return False

    val = float(value)
    if minimum is not None:
        if (inc and val >= minimum) or (not inc and val > minimum):
            return True
        raise ValueError("Value is too small")
    return True

def buildBasicArrowTypes():
    primitives = ["box", "crow", "curve", "icurve", "diamond", "dot", "inv", "none", "normal", "tee", "vee"]
    shapes = primitives[:]
    shapes += ['l' + x for x in primitives if x not in ["dot", "inv"]]
    shapes += ['r' + x for x in primitives if x not in ["dot", "inv"]]
    shapes += ['o' + x for x in primitives if x not in ["crow", "curve", "inv", "normal", "tee", "vee"]]
    shapes += ['ol' + x for x in primitives if x not in ["dot", "crow", "curve", "inv", "normal", "tee", "vee"]]
    shapes += ['or' + x for x in primitives if x not in ["dot", "crow", "curve", "inv", "normal", "tee", "vee"]]
    # Backwards compatibility of Graphviz:
    shapes += ["ediamond", "open", "halfopen", "empty", "invempty"]
    return shapes

AT_S = buildBasicArrowTypes()  # Efficient caching

def checkArrowType(value: str, idx=0):
    """Use the basic arrow types (AT_S cache) to check against the arrow types.

    Graphviz provides 3,111,696 different arrow types.
        * Normal list/set search ==> O(n)
        * This algorithm ==> O(n^(1/3))
    """
    if idx > 3:
        raise ValueError("Too many arrow shapes")
    for arrow in AT_S:
        if value.find(arrow) == 0:
            if value == arrow:
                if idx > 0 and value.endswith("none"):
                    raise ValueError("Arrow type cannot end with 'none' when it's not the first type")
                return True
            return checkArrowType(value[len(arrow):], True)
    raise ValueError("No such arrow type")

def checkRect(value):
    coords = value.split(",")
    if len(coords) != 4:
        raise ValueError("Invalid rectangle dimensions")
    [float(x) for x in coords]
    return True

def checkColor(val):
    if len(val) == 0:
        raise ValueError("Impossible color")
    if val[0] == "#":
        # RGB
        col = 0
        for c in val[1:]:
            if c in "0123456789abcdef":
                col += 1
            elif c in " \t":
                if col != 2:
                    raise ValueError("Invalid RGBA value")
                col = 0
            else:
                raise ValueError("Invalid RGBA value")
        if col == 2:
            return True
        raise ValueError("Invalid RGBA value")
    hsv = re.split(r"[, \t]", val)
    if len(hsv) == 3:
        # HSV
        hsv = [float(x) for x in hsv]
        for c in hsv:
            if c < 0 or 1 < c:
                raise ValueError("Invalid HSV value")
        return True

    # TODO: check against Color Name
    return True

def checkColorList(val):
    l = val.split(":")
    col = True
    num = 0
    for wc in l:
        cf = wc.split(";")
        if len(cf) == 1:
            col = col and checkColor(wc)
        elif len(cf) == 2:
            col = col and checkColor(cf[0])
            num += float(cf[1])
        else:
            raise ValueError("Too many values to unpack")
    if num > 1:
        raise ValueError("Color weights sum exceeds 1")
    if col:
        return True
    raise ValueError("No such color")

def checkString(val):
    # TODO: fix this, seeing as '\t' is valid (crf. layersep default value)
    if '\\' in val:
        raise ValueError("Escape character found in non-escapeable string")
    return True

def checkBool(val):
    lval = val.lower()
    if lval in ["true", "yes", "false", "no"]:
        return True
    raise ValueError("Invalid bool value")

def checkAddDouble(val):
    if len(val) > 0 and val[0] == '+':
        checkDouble(val[1:])
    else:
        checkDouble(val)

def checkPoint(val):
    if len(val) > 0 and val[-1] == '!':
        val = val[:-1]
    point = val.split(",")
    [float(x) for x in point]
    # TODO: can only be 3 if dim is 3!
    if len(point) not in (2, 3):
        raise ValueError("Invalid point")

def checkAddPoint(val):
    if len(val) > 0 and val[0] == '+':
        checkPoint(val[1:])
    else:
        checkPoint(val)


def Damping(val, scope):
    checkValidScope(scope, "G")
    checkDouble(val, 0.0)
    return "neato only"

def K(val, scope):
    checkValidScope(scope, "GC")
    checkDouble(val, 0)
    return "sfdp, fdp only"

def URL(val, scope):
    checkValidScope(scope, "ENGC")
    return "svg, postscript, map only"

def _background(val, scope):
    checkValidScope(scope, "G")
    # TODO: check against XDOT format
    checkString(val)
    return ""

def area(val, scope):
    checkValidScope(scope, "NC")
    checkDouble(val, 0, False)
    return "patchwork only"

def arrowhead(val, scope):
    # TODO: when using an undirected graph, this does not make sense
    checkValidScope(scope, "E")
    checkArrowType(val)
    return ""

def arrowsize(val, scope):
    checkValidScope(scope, "E")
    checkDouble(val, 0.0)
    return ""

def arrowtail(val, scope):
    # TODO: when using an undirected graph, this does not make sense
    checkValidScope(scope, "E")
    checkArrowType(val)
    return ""

def bb(val, scope):
    checkValidScope(scope, "G")
    checkRect(val)
    return "write only"

def bgcolor(val, scope):
    checkValidScope(scope, "GC")
    if ":" in val:
        checkColorList(val)
    else:
        checkColor(val)
    return ""

def center(val, scope):
    checkValidScope(scope, "G")
    checkBool(val)
    return ""

def charset(val, scope):
    checkValidScope(scope, "G")
    checkString(val)
    if val.lower() in ["utf-8", "latin1", "iso-8859-1"]:
        return ""
    # TODO: check against document charset
    raise ValueError("No such charset")

def clusterrank(val, scope):
    checkValidScope(scope, "G")
    if val in ["local", "global", "none"]:
        return "dot only"
    raise ValueError("No such clusterrank")

def color(val, scope):
    checkValidScope(scope, "ENC")
    if ":" in val:
        checkColorList(val)
    else:
        checkColor(val)
    return ""

def colorscheme(val, scope):
    checkValidScope(scope, "ENCG")
    checkString(val)
    # TODO: check color scheme names
    return ""

def comment(val, scope):
    checkValidScope(scope, "ENG")
    checkString(val)
    return ""

def compound(val, scope):
    checkValidScope(scope, "G")
    checkBool(val)
    return "dot only"

def concentrate(val, scope):
    checkValidScope(scope, "G")
    checkBool(val)
    if val.lower() in ("yes", "true"):
        return "pathsharing is dot only"
    return ""

def constraint(val, scope):
    checkValidScope(scope, "E")
    checkBool(val)
    return "dot only"

def decorate(val, scope):
    checkValidScope(scope, "E")
    checkBool(val)
    return ""

def defaultdist(val, scope):
    # TODO: only applicable if pack=false
    checkValidScope(scope, "G")
    checkDouble(val, 0.0001)
    return "neato only"

def dim(val, scope):
    checkValidScope(scope, "G")
    i = int(val)
    if i < 2 or 10 < i:
        raise ValueError("Invalid dimension")
    return "sfdp, fdp, neato only"

def dimen(val, scope):
    checkValidScope(scope, "G")
    i = int(val)
    if i < 2 or 10 < i:
        raise ValueError("Invalid dimension")
    return "sfdp, fdp, neato only"

def dir(val, scope):
    checkValidScope(scope, "E")
    if val in ["forward", "backward", "none", "both"]:
        # TODO: when using an undirected graph, this does not make sense
        return ""
    raise ValueError("Invalid direction")

def diredgeconstraints(val, scope):
    # TODO: only valid when mode="ipsep"
    checkValidScope(scope, "G")
    if val.lower() in ["hier", "false", "no", "true", "yes"]:
        return "neato only"
    raise ValueError("Invalid constraint")

def distortion(val, scope):
    checkValidScope(scope, "N")
    checkDouble(val, -100)
    # TODO: only for shape=polygon
    return ""

def dpi(val, scope):
    checkValidScope(scope, "G")
    checkDouble(val)
    return "svg, bitmap output only"

def edgeURL(val, scope):
    checkValidScope(scope, "E")
    return "svg, map only"

def edgehref(val, scope):
    # TODO: synonym for edgeurl, so don't use together
    checkValidScope(scope, "E")
    return "svg, map only"

def edgetarget(val, scope):
    checkValidScope(scope, "E")
    return "svg, map only"

def edgetooltip(val, scope):
    # TODO: used only if edge has URL or edgeURL
    checkValidScope(scope, "E")
    return "svg, cmap only"

def epsilon(val, scope):
    checkValidScope(scope, "G")
    checkDouble(val)
    return "neato only"

def esep(val, scope):
    # TODO: should normally be less than sep
    checkValidScope(scope, "G")
    if ',' in val:
        checkAddDouble(val)
    else:
        checkAddPoint(val)
    return "not dot"

def fillcolor(val, scope):
    checkValidScope(scope, "NEC")
    if ":" in val:
        checkColorList(val)
    else:
        checkColor(val)
    return ""

def fixedsize(val, scope):
    checkValidScope(scope, "N")
    checkString(val)
    if val.lower() not in ["true", "yes", "false", "no", "shape"]:
        raise ValueError("Invalid value")
    return ""

def fontcolor(val, scope):
    checkValidScope(scope, "ENGC")
    checkColor(val)
    return ""

def fontname(val, scope):
    checkValidScope(scope, "ENGC")
    checkString(val)
    return ""

def fontnames(val, scope):
    checkValidScope(scope, "G")
    checkString(val)
    return "svg only"

def fontpath(val, scope):
    checkValidScope(scope, "G")
    checkString(val)
    return ""

def fontsize(val, scope):
    checkValidScope(scope, "ENGC")
    checkDouble(val, 1.0)
    return ""

def forcelabels(val, scope):
    checkValidScope(scope, "G")
    checkBool(val)
    return ""

def gradientangle(val, scope):
    checkValidScope(scope, "NCG")
    k = int(val)
    return ""

def group(val, scope):
    checkValidScope(scope, "N")
    checkString(val)
    return "dot only"

def headURL(val, scope):
    # TODO: when using an undirected graph, this does not make sense
    checkValidScope(scope, "E")
    return "svg, map only"

def head_lp(val, scope):
    checkValidScope(scope, "E")
    checkPoint(val)
    return "write only"

def headclip(val, scope):
    checkValidScope(scope, "E")
    checkBool(val)
    return ""

def headhref(val, scope):
    # TODO: synonym for headURL, don't use both
    checkValidScope(scope, "E")
    return "svg, map only"

def headlabel(val, scope):
    # TODO: when using an undirected graph, this does not make sense
    checkValidScope(scope, "E")
    # TODO: type = escString or HTML label
    return ""

def headport(val, scope):
    # TODO: when using an undirected graph, this does not make sense
    checkValidScope(scope, "E")
    # TODO: check port pos
    return ""

def headtarget(val, scope):
    checkValidScope(scope, "E")
    return "svg, map only"

def headtooltip(val, scope):
    checkValidScope(scope, "E")
    # TODO: only used if the edge has a headURL attribute
    return "svg, cmap only"

def height(val, scope):
    # TODO: if shape is regular and width or height is set, that value is used. If both are set, max is used, min otherwise
    checkValidScope(scope, "N")
    checkDouble(val, 0.02)
    return ""

def href(val, scope):
    checkValidScope(scope, "GCNE")
    # TODO: synonym for URL, don't use both
    return "svg, postscript, map only"

def id(val, scope):
    checkValidScope(scope, "GCNE")
    return "svg, postscript, map only"

def image(val, scope):
    checkValidScope(scope, "N")
    checkString(val)
    return ""

def imagepath(val, scope):
    checkValidScope(scope, "G")
    checkString(val)
    return ""

def imagepos(val, scope):
    checkValidScope(scope, "N")
    checkString(val)
    if val not in ["tl", "tc", "tr", "ml", "mc", "mr", "bl", "bc", "br"]:
        raise ValueError("Invalid position")
    return ""

def imagescale(val, scope):
    checkValidScope(scope, "N")
    checkString(val)
    if val.lower not in ["true", "yes", "false", "no", "width", "height"]:
        raise ValueError("Invalid scale")
    return ""

def inputscale(val, scope):
    checkValidScope(scope, "G")
    checkDouble(val)
    return "fdp, neato only"

def label(val, scope):
    checkValidScope(scope, "ENGC")
    # TODO: type = escString or HTML label
    # TODO: record based nodes
    return ""

def labelURL(val, scope):
    checkValidScope(scope, "E")
    return "svg, map only"

def label_scheme(val, scope):
    checkValidScope(scope, "G")
    k = int(val)
    if k < 0:
        raise ValueError("Invalid scheme")
    return "sfdp only"

def labelangle(val, scope):
    checkValidScope(scope, "E")
    checkDouble(val, -180.0)
    return ""

def labeldistance(val, scope):
    checkValidScope(scope, "E")
    checkDouble(val, 0.0)
    return ""

def labelfloat(val, scope):
    checkValidScope(scope, "E")
    checkBool(val)
    return ""

def labelfontcolor(val, scope):
    checkValidScope(scope, "E")
    checkColor(val)
    return ""

def labelfontname(val, scope):
    checkValidScope(scope, "E")
    checkString(val)
    return ""

def labelfontsize(val, scope):
    checkValidScope(scope, "E")
    checkDouble(val, 1.0)
    return ""

def labelhref(val, scope):
    checkValidScope(scope, "E")
    # TODO: synonym of labelURL, don't use both
    return "svg, map only"

def labeljust(val, scope):
    checkValidScope(scope, "GC")
    checkString(val)
    if val not in ["l", "c", "r"]:
        raise ValueError("Invalid alignment")
    return ""

def labelloc(val, scope):
    checkValidScope(scope, "NGC")
    checkString(val)
    if (scope in "GC" and val not in ["t", "b"]) or (scope == "N" and val not in ["t", "c", "b"]):
        raise ValueError("Invalid location")
    return ""

def labeltarget(val, scope):
    checkValidScope(scope, "E")
    return "svg, map only"

def labeltooltip(val, scope):
    checkValidScope(scope, "E")
    # TODO: only used if edge has URL or labelURL
    return "svg, cmap only"

def landscape(val, scope):
    checkValidScope(scope, "G")
    checkBool(val)
    # TODO: synonym of rotate=90 or orientation=landscape
    return ""

def layer(val, scope):
    checkValidScope(scope, "ENC")
    # TODO: check layerRange
    return ""

def layerlistsep(val, scope):
    checkValidScope(scope, "G")
    checkString(val)
    return ""

def layers(val, scope):
    checkValidScope(scope, "G")
    # TODO: check layerList
    return ""

def layerselect(val, scope):
    checkValidScope(scope, "G")
    # TODO: check layerRange
    return ""

def layersep(val, scope):
    checkValidScope(scope, "G")
    checkString(val)
    return ""

def layout(val, scope):
    checkValidScope(scope, "G")
    checkString(val)
    if val not in ["circo", "dot", "fdp", "neato", "osage", "patchwork", "sfdp", "twopi"]:
        raise ValueError("No such layout")
    return ""

def len(val, scope):
    checkValidScope(scope, "E")
    checkDouble(val)
    return "fdp, neato only"

def levels(val, scope):
    checkValidScope(scope, "G")
    k = int(val)
    if k < 0:
        raise ValueError("Level must be at least 0")
    return "sfdp only"

def levelsgap(val, scope):
    checkValidScope(scope, "G")
    checkDouble(val)
    # TODO: only applied when mode="ipsep" or "hier"
    return "neato only"


# TODO: finish this
