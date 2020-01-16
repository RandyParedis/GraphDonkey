"""This file contains a set of immutable variables.

Author: Randy Paredis
Date:   12/15/2019
"""
from PyQt5.QtGui import QIcon, QImage
from main.extra.IOHandler import IOHandler

APP_NAME = "GraphDonkey"
APP_VERSION = "0.2.0"
APP_VERSION_NAME = "Jack-in-a-Box"
APP_ICON = QIcon(IOHandler.dir_icons("graphdonkey.svg"))

LINE_ENDING = "\u2029"  # Qt Handles all line endings internally => only need to replace on save
ENDINGS = ['\n', '\r', '\r\n']

INDENT_OPEN = ['{', '[']
INDENT_CLOSE = ['}', ']']


################################
#       FILE TYPE CONFIG       #
################################

FILE_TYPES = {
    "Windows Bitmap Format": ["bmp"],
    "CGImage Bitmap Format": ["cgimage"],
    "Encapsulated PostScript": ["eps"],
    "OpenEXR": ["exr"],
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

def file_list(files):
    return ";;".join(sorted(["%s Files (*.%s)" % (x, " *.".join(files[x])) for x in files]))

def lookup(ext, group, unknown=None):
    for k in group:
        if ext in group[k]:
            return k
    return unknown

def obtain_exts(category):
    if "." in category:
        i = 0
        for c in range(len(category)):
            if category[c] == '(':
                i = c
                break
        exts = category[i + 3:-1]
        return exts.split(" *.")
    else:
        return []

def valid_ext(extension, group):
    for x in group:
        if extension in group[x]:
            return True
    return False
