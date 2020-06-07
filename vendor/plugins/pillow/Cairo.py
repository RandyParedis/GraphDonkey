"""Cairo rendering engine for GraphDonkey.

Author: Randy Paredis
Date:   06/07/2020
"""
from main.viewer.shapes import *

import cairo, io

def convert(shapes):
    file = io.BytesIO()

    props = shapes.pop(0)
    WIDTH, HEIGHT = props.width, props.height
    surface = cairo.SVGSurface(file, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    # BORDER
    # ctx.move_to(0, 0)
    # ctx.line_to(WIDTH, 0)
    # ctx.line_to(WIDTH, HEIGHT)
    # ctx.line_to(0, HEIGHT)
    # ctx.line_to(0, 0)
    #
    # ctx.set_source_rgb(0.0, 0.8, 0.5)  # Solid color
    # ctx.set_line_width(2)
    # ctx.stroke()

    for shape in shapes:
        if isinstance(shape, Line):
            ctx.move_to(shape.x, shape.y)
            ctx.line_to(shape.xto, shape.yto)
            ctx.set_source_rgb(0, 0, 0)  # Solid color
            ctx.set_line_width(shape.width)
            ctx.stroke()

    surface.flush()
    surface.finish()

    return file.getvalue()

