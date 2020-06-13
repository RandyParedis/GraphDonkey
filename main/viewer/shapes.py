"""Helper file for rendering shapes.

This file is part of the GraphDonkey core for future support and
plugin-independency engine features.

Athor:  Randy Paredis
Date:   06/06/2020
"""

# TODO: Rotations, Text, Bezier Curve, Arrows

import math

def sign(x):
    """Gets the sign of a number, or 0."""
    return -1 if x < 0 else 1 if x > 0 else 0


def colors(color: str):
    if color.startswith('#'):
        color = color[1:]
        return tuple([int(color[i:i+2], 16) / 255 for i in range(0, len(color), 2)])
    # TODO: add more colors (user-specific?)
    return 0, 0, 0, 1



class Properties:
    """Class that can be used to pass on system properties.

    Attributes:
        width (numeric):    The width of the drawing area.
        height (numeric):   The height of the drawing area.

    Args:
        width (numeric):    The width of the drawing area.
        height (numeric):   The height of the drawing area.
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height


class Shape:
    """A generic shape, superclass of all shape objects.

    Attributes:
        x (numeric):        The x-value of the shape.
        y (numeric):        The y-value of the shape.
        rot (numeric):      The shape's rotation.
        width (numeric):    The width for the shape's stroke.
        color (any):        The color for the shape's stroke.
        stroke (any):       The style for the shape's stroke.

    Args:
        x (numeric):        The x-value of the shape.
        y (numeric):        The y-value of the shape.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 1
        self.color = (0, 0, 0, 1)
        self.stroke = None

    def boundingBox(self):
        """Gets the bounding box for the shape, as a :class:`Rectangle`."""
        raise NotImplementedError()


class FillableShape(Shape):
    """Superclass for all shapes that have an area.

    Args:
        x (numeric):    The x-value of the shape.
        y (numeric):    The y-value of the shape.
        filled (tuple): A tuple indicating the color, following (red, green, blue[, alpha=1])
                        with each element in the range of [0, 1]. When ``None``, no filling is
                        required.
    """
    def __init__(self, x, y, filled=None):
        super().__init__(x, y)
        self.filled = filled

    def boundingBox(self):
        raise NotImplementedError()


class Point(Shape):
    """A single point.

    Args:
        x (numeric):    The x-value of the point.
        y (numeric):    The y-value of the point.
    """
    def __init__(self, x, y):
        super().__init__(x, y)

    def boundingBox(self):
        """Gets the bounding box for the point, as a :class:`Rectangle`.

        Note:
            Since a point does not have a with, nor a height (mathematically),
            the bouding box has a width and a height of zero.
        """
        return Rectangle(self.x, self.y, 0, 0)


class Line(Shape):
    """A straight line.

    Attributes:
        xto (numeric):  The x-value of the second coordinate of the shape.
        yto (numeric):  The y-value of the second coordinate of the shape.

    Args:
        x1 (numeric):   The x-value of the first coordinate of the shape.
        y1 (numeric):   The y-value of the first coordinate of the shape.
        x2 (numeric):   The x-value of the second coordinate of the shape.
        y2 (numeric):   The y-value of the second coordinate of the shape.
    """
    def __init__(self, x1, y1, x2, y2):
        super().__init__(x1, y1)
        self.xto = x2
        self.yto = y2

    def __repr__(self):
        return "LINE (%f, %f) -> (%f, %f)" % (self.x, self.y, self.xto, self.yto)

    def boundingBox(self):
        """Gets the bounding box for the line, as a :class:`Rectangle`."""
        left = min(self.x, self.xto)
        top = min(self.y, self.yto)
        right = max(self.x, self.xto)
        bottom = max(self.y, self.yto)
        return Rectangle(left, top, right - left, bottom - top)


class Rectangle(FillableShape):
    """A square or rectangle.

    Attributes:
        width_ (numeric):   The width of the rectangle.
        height (numeric):   The height of the rectangle.

    Args:
        left (numeric):     The left of the rectangle.
        top (numeric):      The top of the rectangle.
        width (numeric):    The width of the rectangle.
        height (numeric):   The height of the rectangle.
        filled (bool):      Whether or not the shape is filled.
                            Defaults to ``False``.
    """
    def __init__(self, left, top, width, height, filled=False):
        super().__init__(left, top, filled)
        self.width_ = width
        self.height = height

    def topleft(self):
        """Returns the top-left coordinate."""
        return self.x, self.y

    def bottomright(self):
        """Returns the bottom-right coordinate."""
        return self.x + self.width, self.y + self.height

    def boundingBox(self):
        """Gets the bounding box for the rectangle, as a :class:`Rectangle`.

        Note:
            This is just the same rectangle.
        """
        return self


class Ellipse(FillableShape):
    """An ellipse or a circle.

    Attributes:
        rx (numeric):   The horizontal radius of the ellipse.
        ry (numeric):   The vertical radius of the ellipse.

    Args:
        x (numeric):    The x-value of the center of the ellipse.
        y (numeric):    The y-value of the center of the ellipse.
        rx (numeric):   The horizontal radius of the ellipse.
                        Must be strictly positive.
        ry (numeric):   The vertical radius of the ellipse.
                        Must be strictly positive.
        filled (bool):  Whether or not the shape is filled. Defaults
                        to ``False``.
    """
    def __init__(self, x, y, rx, ry, filled=False):
        assert rx > 0 and ry > 0
        super().__init__(x, y, filled)
        self.rx = rx
        self.ry = ry

    def boundingBox(self):
        """Gets the bounding box for the ellipse, as a :class:`Rectangle`."""
        return Rectangle(self.x - self.rx, self.y - self.ry, 2 * self.rx, 2 * self.ry)

    @staticmethod
    def fromBoundingBox(rect, filled=False):
        """Creates a new ellipse from a bounding box.

        Args:
            rect (Rectangle):   The bounding box for the ellipse.
            filled (bool):      Whether or not the shape is filled.
                                Defaults to ``False``.
        """
        rx = rect.width_ / 2
        ry = rect.height / 2
        cx = rect.x + rx
        cy = rect.y + ry
        return Ellipse(cx, cy, rx, ry, filled)


class Polygon(FillableShape):
    """A polygon.

    Attributes:
        points (list):  The points that make up the polygon, as tuples (x, y).

    Args:
        *points:        The points that make up the polygon, as tuples (x, y).
                        Must contain at least one point.
        filled (bool):  Whether or not the shape is filled. Defaults to ``False``.
    """
    def __init__(self, *points, filled=False):
        assert len(points) > 0
        super().__init__(*points[0], filled)
        self.points = points

    def boundingBox(self):
        """Gets the bounding box for the polygon, as a :class:`Rectangle`."""
        x, y = list(zip(self.points))
        left = min(x)
        top = min(y)
        right = max(x)
        bottom = max(y)
        return Rectangle(left, top, right - left, bottom - top)

# TODO: get arc when sweep/large is reversed?
# FIXME: bounding box, in the case of:
#          XXX
#         X   X
#         O   O
#         X   X
class Arc(Shape):
    """A portion of the outline of an ellipse.

    The angles are measured in degrees, starting at 3 o'clock and
    increasing clockwise.

    Attributes:
        x (numeric):        The x-value of the center of the ellipse.
        y (numeric):        The y-value of the center of the ellipse.
        rx (numeric):       The horizontal radius of the ellipse.
        ry (numeric):       The vertical radius of the ellipse.
        start (numeric):    Starting angle to draw from.
        end (numeric):      Ending angle to draw to.

    Args:
        x (numeric):        The x-value of the center of the ellipse.
        y (numeric):        The y-value of the center of the ellipse.
        rx (numeric):       The horizontal radius of the ellipse.
        ry (numeric):       The vertical radius of the ellipse.
        start (numeric):    Starting angle to draw from.
        end (numeric):      Ending angle to draw to.
    """
    def __init__(self, x, y, rx, ry, start, end):
        assert rx > 0 and ry > 0
        super().__init__(x, y)
        self.rx = rx
        self.ry = ry
        self.start = start % 360
        self.end = end % 360

    def ellipse(self):
        """Gets the ellipse that the arc is part of."""
        return Ellipse(self.x, self.y, self.rx, self.ry)

    def isLarge(self):
        """Whether or not the angle exceeds 180°."""
        return abs(self.start - self.end) > 180

    isSweep = isLarge
    """Synonym of :meth:`isLarge`.
    
    Because the center is known, sweep will always equal the largeness.
    """

    def startCoord(self):
        """Get the starting coordinate as a tuple (x, y)."""
        x = self.x + self.rx * math.cos(math.radians(self.start))
        y = self.y + self.ry * math.sin(math.radians(self.start))
        return x, y

    def endCoord(self):
        """Get the ending coordinate as a tuple (x, y)."""
        x = self.x + self.rx * math.cos(math.radians(self.end))
        y = self.y + self.ry * math.sin(math.radians(self.end))
        return x, y

    def boundingBox(self):
        """Gets the bounding box of the arc, as a :class:`Rectangle`."""
        x1, y1 = self.startCoord()
        x2, y2 = self.endCoord()
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        return Rectangle(x1, y1, x2 - x1, y2 - y1)


class Chord(Arc, FillableShape):
    """Same as :class:`Arc`, but connects the endpoints in a straight line.

    Args:
        x (numeric):        The x-value of the center of the ellipse.
        y (numeric):        The y-value of the center of the ellipse.
        rx (numeric):       The horizontal radius of the ellipse.
        ry (numeric):       The vertical radius of the ellipse.
        start (numeric):    Starting angle to draw from.
        end (numeric):      Ending angle to draw to.
        filled (tuple):     Color of the shape. Defaults to ``None``.
    """
    def __init__(self, x, y, rx, ry, start, end, filled=None):
        Arc.__init__(self, x, y, rx, ry, start, end)
        self.filled = filled


class Pie(Arc, FillableShape):
    """Same as :class:`Arc`, but connects the endpoints to the :class:`Ellipse`'s center.

    Args:
        x (numeric):        The x-value of the center of the ellipse.
        y (numeric):        The y-value of the center of the ellipse.
        rx (numeric):       The horizontal radius of the ellipse.
        ry (numeric):       The vertical radius of the ellipse.
        start (numeric):    Starting angle to draw from.
        end (numeric):      Ending angle to draw to.
        filled (tuple):     Color of the shape. Defaults to ``None``.
    """
    def __init__(self, x, y, rx, ry, start, end, filled=None):
        Arc.__init__(self, x, y, rx, ry, start, end)
        self.filled = filled

    def boundingBox(self):
        """Gets the bounding box for the pie, as a :class:`Rectangle`.

        Note:
            To obtain the bounding box for the ellipse that encompases
            the pie, use :meth:`ellipse` instead.
        """
        return Polygon((self.x, self.y), self.startCoord(), self.endCoord()).boundingBox()


Pieslice = Pie
"""Synonym for :class:`Pie`."""


class Group(Shape):
    """A shape that is made up of multiple shapes.

    Attributes:
        shapes (list):  The shapes that make up the group.

    Args:
        *shapes:        The shapes that make up the group.
                        Must contain at least one shape.
    """
    def __init__(self, *shapes):
        assert len(shapes) > 0
        super().__init__(shapes[0].x, shapes[0].y)
        self.shapes = shapes

    def boundingBox(self):
        """Obtains the bounding box for the group, as a :class:`Rectangle`."""
        points = []
        for shape in self.shapes:
            box = shape.boundingBox()
            points.append(box.topleft())
            points.append(box.bottomright())
        return Polygon(*points).boundingBox()


# class Image(Shape): pass
#
#
# class Text(Shape): pass
#
#
# class Bezier(Shape): pass
#
#
# Curve = Bezier
# """Synonym for :class:`Bezier`."""
#
#
# class Arrow(Line): pass
