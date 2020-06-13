"""Cairo rendering engine for GraphDonkey.

Author: Randy Paredis
Date:   06/07/2020
"""
from main.viewer.shapes import *

import cairo, io, math

def convert(shapes):
    file = io.BytesIO()

    props = shapes.pop(0)
    WIDTH, HEIGHT = props.width, props.height
    surface = cairo.SVGSurface(file, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    draw_shapes(shapes, ctx)
    surface.flush()
    surface.finish()
    return file.getvalue()

def draw_shapes(shapes, ctx):
    for shape in shapes:
        color = True
        if isinstance(shape, Point):
            ctx.arc(shape.x, shape.y, shape.width / 2, 0, 2 * math.pi)
            ctx.set_source_rgba(*shape.color)
            ctx.fill()
            color = False
        elif isinstance(shape, Line):
            ctx.move_to(shape.x, shape.y)
            ctx.line_to(shape.xto, shape.yto)
        elif isinstance(shape, Rectangle):
            ctx.rectangle(shape.x, shape.y, shape.width_, shape.height)
        elif isinstance(shape, Ellipse):
            box = shape.boundingBox()
            ctx.new_sub_path()
            ctx.save()
            ctx.translate(box.x + shape.rx, box.y + shape.ry)
            ctx.scale(shape.rx, shape.ry)
            ctx.arc(0., 0., 1., 0., 2 * math.pi)
            ctx.restore()
        elif isinstance(shape, Polygon):
            ctx.move_to(shape.x, shape.y)
            for x, y in shape.points[1:]:
                ctx.line_to(x, y)
            ctx.close_path()
        elif isinstance(shape, Chord):
            ell = shape.ellipse()
            box = ell.boundingBox()
            ctx.save()
            ctx.translate(box.x + ell.rx, box.y + ell.ry)
            ctx.scale(ell.rx, ell.ry)
            ctx.new_sub_path()
            ctx.arc(0., 0., 1., math.radians(shape.start), math.radians(shape.end))
            ctx.close_path()
            ctx.restore()
        elif isinstance(shape, Pie):
            ell = shape.ellipse()
            box = ell.boundingBox()
            ctx.save()
            ctx.translate(box.x + ell.rx, box.y + ell.ry)
            ctx.scale(ell.rx, ell.ry)
            ctx.move_to(0, 0)
            ctx.arc(0., 0., 1., math.radians(shape.start), math.radians(shape.end))
            ctx.close_path()
            ctx.restore()
        elif isinstance(shape, Arc):
            ell = shape.ellipse()
            box = ell.boundingBox()
            ctx.save()
            ctx.translate(box.x + ell.rx, box.y + ell.ry)
            ctx.scale(ell.rx, ell.ry)
            ctx.new_sub_path()
            ctx.arc(0., 0., 1., math.radians(shape.start), math.radians(shape.end))
            ctx.restore()
        elif isinstance(shape, Group):
            draw_shapes(shape.shapes, ctx)
            color = False

        # Coloring
        if color:
            if issubclass(type(shape), FillableShape) and shape.filled is not None:
                ctx.set_source_rgba(*shape.filled)
                ctx.fill_preserve()
            ctx.set_source_rgba(*shape.color)
            ctx.set_line_width(shape.width)
            ctx.stroke()

