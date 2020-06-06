"""Helper file for rendering shapes.

This file is part of the GraphDonkey core for future support and
plugin-independency features.

Athor:  Randy Paredis
Date:   06/06/2020
"""
# TODO: Colors (+ Filled Colors), Width, Rotation, Bezier, Curve, Image, Text...

import math

def sign(x):
    """Gets the sign of a number, or 0."""
    return -1 if x < 0 else 1 if x > 0 else 0


class Shape:
    """A generic shape, superclass of all shape objects.

    Args:
        x (numeric):    The x-value of the shape.
        y (numeric):    The y-value of the shape.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def boundingBox(self):
        """Gets the bounding box for the shape, as a :class:`Rectangle`."""
        raise NotImplementedError()


class FillableShape(Shape):
    """Superclass for all shapes that have an area.

    Args:
        x (numeric):    The x-value of the shape.
        y (numeric):    The y-value of the shape.
        filled (bool):  Whether or not the shape is filled.
    """
    def __init__(self, x, y, filled):
        super().__init__(x, y, filled)

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
        x (numeric):    The x-value of the first coordinate of the shape.
        y (numeric):    The y-value of the first coordinate of the shape.
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
        x (numeric):        The left of the rectangle.
        y (numeric):        The top of the rectangle.
        width (numeric):    The width of the rectangle.
        height (numeric):   The height of the rectangle.
        filled (bool):      Whether or not the shape is filled.

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
        self.width = width
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
        x (numeric):    The x-value of the center of the ellipse.
        y (numeric):    The y-value of the center of the ellipse.
        rx (numeric):   The horizontal radius of the ellipse.
        ry (numeric):   The vertical radius of the ellipse.
        filled (bool):  Whether or not the shape is filled.

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
        rx = rect.width / 2
        ry = rect.height / 2
        cx = rect.x + rx
        cy = rect.y + ry
        return Ellipse(cx, cy, rx, ry, filled)


class Polygon(FillableShape):
    """A polygon.

    Attributes:
        x (numeric):    The x-value of the first point of the polygon.
        y (numeric):    The y-value of the first point of the polygon.
        points (list):  The points that make up the polygon, as tuples (x, y).
        filled (bool):  Whether or not the shape is filled.

    Args:
        *points:        The points that make up the polygon, as tuples (x, y).
                        Must contain at least one point.
        filled (bool):  Whether or not the shape is filled. Defaults to ``False``.
    """
    def __init__(self, *points, filled=False):
        assert len(points) > 0
        super().__init__(*points[0])
        self.points = points

    def boundingBox(self):
        """Gets the bounding box for the polygon, as a :class:`Rectangle`."""
        x, y = list(zip(self.points))
        left = min(x)
        top = min(y)
        right = max(x)
        bottom = max(y)
        return Rectangle(left, top, right - left, bottom - top)


class Arc(Shape):
    """A portion of the outline of an ellipse.

    Attributes:
        x (numeric):    The x-value of the start of the arc.
        y (numeric):    The y-value of the start of the arc.
        xto (numeric):  The x-value of the end of the arc.
        yto (numeric):  The y-value of the end of the arc.
        rx (numeric):   The horizontal radius of the ellipse.
        ry (numeric):   The vertical radius of the ellipse.
        large (bool):   Whether or not to use the arc with an angle > 180°.
        sweep (bool):   Whether or not the angle is negative.

    Args:
        x1 (numeric):   The x-value of the start of the arc.
        y1 (numeric):   The y-value of the start of the arc.
        x2 (numeric):   The x-value of the end of the arc.
        y2 (numeric):   The y-value of the end of the arc.
        rx (numeric):   The horizontal radius of the ellipse.
                        Must be strictly positive.
        ry (numeric):   The vertical radius of the ellipse.
                        Must be strictly positive.
        large (bool):   Whether or not to use the arc with an angle > 180°.
                        Defaults to ``False``.
        sweep (bool):   Whether or not the angle is negative. Defaults to
                        ``False``.
    """
    def __init__(self, x1, y1, x2, y2, rx, ry, large=False, sweep=False):
        assert rx > 0 and ry > 0
        super().__init__(x1, y1)
        self.xto = x2
        self.yto = y2
        self.rx = rx
        self.ry = ry
        self.large = large
        self.sweep = sweep

    def ellipse(self):
        """Gets the ellipse that corresponds to the arc.

        Solution based on
        https://stackoverflow.com/questions/197649/how-to-calculate-center-of-an-ellipse-by-two-points-and-radius-sizes
        """
        r1 = (self.x - self.xto) / (2 * self.rx)
        r2 = (self.y - self.yto) / (2 * self.ry)

        # Prevent Errors
        if r2 == 0: return Ellipse((self.xto - self.x) / 2, self.y, self.rx, self.ry)

        k = 1
        if self.large ^ self.sweep:
            k = -1

        a1 = math.atan2(r1, r2)
        a2 = math.asin(k * math.sqrt(r1 ** 2 + r2 ** 2))
        t1 = a1 + a2

        s = k * sign(r2)

        cx = self.x + self.rx * math.cos(t1) * s
        cy = self.y - self.ry * math.sin(t1) * s
        return Ellipse(cx, cy, self.rx, self.ry)

    def boundingBox(self):
        """Gets the bounding box for the arc, as a :class:`Rectangle`.

        Note:
            To obtain the bounding box for the ellipse that encompases
            the arc, use :meth:`ellipse` instead.
        """
        if self.large:
            return self.ellipse().boundingBox()
        return Line(self.x, self.y, self.xto, self.yto).boundingBox()

    @staticmethod
    def fromEllipse(ellipse, start=0, end=360):
        """Creates a new arc that belongs to the given ellipse.

        Args:
            ellipse (Ellipse):  The ellipse to which the arc belongs.
            start (numeric):    Starting angle in degrees, following the unit
                                circle; i.e. We start at 3 o'clock and increase
                                counter-clockwise. Defaults to 0 degrees.
            end (numeric):      Ending angle in degrees, following the unit
                                circle; i.e. We start at 3 o'clock and increase
                                counter-clockwise. Defaults to 360 degrees.
        """
        ls = abs(end - start) > 180
        x1 = math.cos(math.radians(start)) * ellipse.rx
        y1 = math.sin(math.radians(start)) * ellipse.ry
        x2 = math.cos(math.radians(end)) * ellipse.rx
        y2 = math.sin(math.radians(end)) * ellipse.ry
        return Arc(x1, y1, x2, y2, ellipse.rx, ellipse.ry, ls, ls)


class Chord(Arc, FillableShape):
    """Same as :class:`Arc`, but connects the endpoints in a straight line.

    Attributes:
        x (numeric):    The x-value of the start of the arc.
        y (numeric):    The y-value of the start of the arc.
        xto (numeric):  The x-value of the end of the arc.
        yto (numeric):  The y-value of the end of the arc.
        rx (numeric):   The horizontal radius of the ellipse.
        ry (numeric):   The vertical radius of the ellipse.
        large (bool):   Whether or not to use the arc with an angle > 180°.
        sweep (bool):   Whether or not the angle is negative.
        filled (bool):  Whether or not the shape is filled.

    Args:
        x1 (numeric):   The x-value of the start of the arc.
        y1 (numeric):   The y-value of the start of the arc.
        x2 (numeric):   The x-value of the end of the arc.
        y2 (numeric):   The y-value of the end of the arc.
        rx (numeric):   The horizontal radius of the ellipse.
                        Must be strictly positive.
        ry (numeric):   The vertical radius of the ellipse.
                        Must be strictly positive.
        large (bool):   Whether or not to use the arc with an angle > 180°.
                        Defaults to ``False``.
        sweep (bool):   Whether or not the angle is negative. Defaults to
                        ``False``.
        filled (bool):  Whether or not the shape is filled. Defaults to ``False``.
    """
    def __init__(self, x1, y1, x2, y2, rx, ry, large=False, sweep=False, filled=False):
        FillableShape.__init__(self, 0, 0, filled)
        Arc.__init__(self, x1, y1, x2, y2, rx, ry, large, sweep)

    @staticmethod
    def fromEllipse(ellipse, start=0, end=360, filled=False):
        """Creates a new chord that belongs to the given ellipse.

        Args:
            ellipse (Ellipse):  The ellipse to which the chord belongs.
            start (numeric):    Starting angle in degrees, following the unit
                                circle; i.e. We start at 3 o'clock and increase
                                counter-clockwise. Defaults to 0 degrees.
            end (numeric):      Ending angle in degrees, following the unit
                                circle; i.e. We start at 3 o'clock and increase
                                counter-clockwise. Defaults to 360 degrees.
            filled (bool):      Whether or not the shape is filled. Defaults to
                                ``False``.
        """
        arc = Arc.fromEllipse(ellipse, start, end)
        arc.__class__ = Chord  # Python can be fun
        arc.filled = filled
        return arc


class Pie(Arc, FillableShape):
    """Same as :class:`Arc`, but connects the endpoints to the :class:`Ellipse`'s center.

    Attributes:
        x (numeric):    The x-value of the start of the arc.
        y (numeric):    The y-value of the start of the arc.
        xto (numeric):  The x-value of the end of the arc.
        yto (numeric):  The y-value of the end of the arc.
        rx (numeric):   The horizontal radius of the ellipse.
        ry (numeric):   The vertical radius of the ellipse.
        large (bool):   Whether or not to use the arc with an angle > 180°.
        sweep (bool):   Whether or not the angle is negative.
        filled (bool):  Whether or not the shape is filled.

    Args:
        x1 (numeric):   The x-value of the start of the arc.
        y1 (numeric):   The y-value of the start of the arc.
        x2 (numeric):   The x-value of the end of the arc.
        y2 (numeric):   The y-value of the end of the arc.
        rx (numeric):   The horizontal radius of the ellipse.
                        Must be strictly positive.
        ry (numeric):   The vertical radius of the ellipse.
                        Must be strictly positive.
        large (bool):   Whether or not to use the arc with an angle > 180°.
                        Defaults to ``False``.
        sweep (bool):   Whether or not the angle is negative. Defaults to
                        ``False``.
        filled (bool):  Whether or not the shape is filled. Defaults to ``False``.
    """
    def __init__(self, x1, y1, x2, y2, rx, ry, large=False, sweep=False, filled=False):
        FillableShape.__init__(self, 0, 0, filled)
        Arc.__init__(self, x1, y1, x2, y2, rx, ry, large, sweep)

    def boundingBox(self):
        """Gets the bounding box for the pie, as a :class:`Rectangle`.

        Note:
            To obtain the bounding box for the ellipse that encompases
            the pie, use :meth:`ellipse` instead.
        """
        ellipse = self.ellipse()
        return Polygon((ellipse.x, ellipse.y), (self.x, self.y), (self.xto, self.yto)).boundingBox()

    @staticmethod
    def fromEllipse(ellipse, start=0, end=360, filled=False):
        """Creates a new pie that belongs to the given ellipse.

        Args:
            ellipse (Ellipse):  The ellipse to which the pie belongs.
            start (numeric):    Starting angle in degrees, following the unit
                                circle; i.e. We start at 3 o'clock and increase
                                counter-clockwise. Defaults to 0 degrees.
            end (numeric):      Ending angle in degrees, following the unit
                                circle; i.e. We start at 3 o'clock and increase
                                counter-clockwise. Defaults to 360 degrees.
            filled (bool):      Whether or not the shape is filled. Defaults to
                                ``False``.
        """
        arc = Arc.fromEllipse(ellipse, start, end)
        arc.__class__ = Pie  # Python can be fun
        arc.filled = filled
        return arc

Pieslice = Pie
"""Synonym for :class:`Pie`."""


class Group(Shape):
    """A shape that is made up of multiple shapes.

    Attributes:
        x (numeric):    The x-value of the first shape of the group.
        y (numeric):    The y-value of the first shape of the group.
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


class Text(Shape): pass
