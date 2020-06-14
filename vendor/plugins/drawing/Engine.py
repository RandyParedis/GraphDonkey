"""The Drawing transformer to shapes

Author: Randy Paredis
Date:   01/09/2020
"""
from main.extra.IOHandler import IOHandler
from lark import Tree, Lark
from main.viewer.shapes import *
import cmath

Config = IOHandler.get_preferences()

# TODO: custom shapes, control statements, imports, variables, loops, text, images
class ConversionVisitor:
    def __init__(self):
        self.shapes = []
        self.WIDTH = 640
        self.HEIGHT = 480

    def get(self):
        return [Properties(self.WIDTH, self.HEIGHT)] + self.shapes

    def child(self, tree: Tree, pos):
        if 0 <= pos < len(tree.children):
            return tree.children[pos]
        return None

    def coordinate(self, coord: Tree):
        if coord.children[0].type == "CENTER":
            return self.WIDTH // 2, self.HEIGHT // 2
        return float(coord.children[0].value), float(coord.children[2].value)

    def color(self, tree: Tree, pos):
        node = self.child(tree, pos)
        if node is None:
            color = "#000000ff"
        else:
            color = node.children[1].value
        return colors(color)

    def width(self, tree: Tree, pos):
        node = self.child(tree, pos)
        if node is None:
            width = 1
        else:
            width = node.children[1].value
        return int(width)

    # def font(self, tree: Tree, pos):
    #     node = self.child(tree, pos)
    #     if node is None:
    #         return None
    #     return ImageFont.truetype(node.children[1].value[1:-1], int(node.children[0].value))

    def angle(self, tree: Tree):
        value = float(tree.children[0].value)
        if tree.children[1].type == "DEGREES":
            return value
        return 180 * value / cmath.pi

    def cw(self, tree: Tree):
        width, color = 1, "#000000"
        for c in range(len(tree.children)):
            child = tree.children[c]
            if child.data == "width":
                width = self.width(tree, c)
            elif child.data == "color":
                color = self.color(tree, c)
        return color, width

    def visit(self, tree: Tree):
        if tree is None:
            return
        name = tree.data
        if name in ["start", "stmt", "shape"]:
            self.visit(tree.children[0])
        elif name == "stmts":
            for child in tree.children:
                self.visit(child)
        elif name == "point":
            coord = self.coordinate(tree.children[2])
            color, width = self.cw(tree.children[3])
            shape = Point(*coord)
            shape.color = color
            shape.width = width
            self.shapes.append(shape)
        elif name == "line":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            color, width = self.cw(tree.children[5])
            shape = Line(*coord1, *coord2)
            shape.color = color
            shape.width = width
            self.shapes.append(shape)
        # elif name == "grid":
        #     color, width = self.cw(tree.children[1])
        #     for x in range(0, self.image.width, width):
        #         self.drawing.line([(x, 0), (x, self.image.height)], color, 1)
        #     for y in range(0, self.image.height, width):
        #         self.drawing.line([(0, y), (self.image.width, y)], color, 1)
        # elif name == "border":
        #     color, width = self.cw(tree.children[1])
        #     self.drawing.line([(0, 0), (0, self.image.height)], color, width)
        #     self.drawing.line([(0, 0), (self.image.width, 0)], color, width)
        #     self.drawing.line([(0, self.image.height), (self.image.width, self.image.height)], color, width)
        #     self.drawing.line([(self.image.width, 0), (self.image.width, self.image.height)], color, width)
        elif name == "ellipse":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            w = coord2[0] - coord1[0]
            h = coord2[1] - coord1[1]
            color, width = self.cw(tree.children[5])
            fill = self.child(tree, 6)
            if fill is not None:
                fill = self.color(tree, 6)
            shape = Ellipse.fromBoundingBox(Rectangle(*coord1, w, h), fill)
            shape.color = color
            shape.width = width
            self.shapes.append(shape)
        elif name == "rectangle":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            w = coord2[0] - coord1[0]
            h = coord2[1] - coord1[1]
            color, width = self.cw(tree.children[5])
            fill = self.child(tree, 6)
            if fill is not None:
                fill = self.color(tree, 6)
            shape = Rectangle(*coord1, w, h, fill)
            shape.color = color
            shape.width = width
            self.shapes.append(shape)
        elif name == "polygon":
            coords = []
            for child in tree.children:
                if isinstance(child, Tree) and child.data == "coord":
                    coords.append(self.coordinate(child))
            end = 2 * len(coords) + 1
            color, width = self.cw(tree.children[end])
            fill = self.child(tree, end + 1)
            if fill is not None:
                fill = self.color(tree, end + 1)
            shape = Polygon(*coords, filled=fill)
            shape.color = color
            shape.width = width
            self.shapes.append(shape)
        elif name == "arc":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            rx = (coord2[0] - coord1[0]) / 2
            ry = (coord2[1] - coord1[1]) / 2
            start = self.angle(tree.children[8]) % 360
            end = self.angle(tree.children[6]) % 360
            color, width = self.cw(tree.children[9])
            shape = Arc(coord1[0] + rx, coord1[1] + ry, rx, ry, start, end)
            shape.color = color
            shape.width = width
            self.shapes.append(shape)
        elif name == "chord":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            rx = (coord2[0] - coord1[0]) / 2
            ry = (coord2[1] - coord1[1]) / 2
            start = self.angle(tree.children[8]) % 360
            end = self.angle(tree.children[6]) % 360
            color, width = self.cw(tree.children[9])
            fill = self.child(tree, 10)
            if fill is not None:
                fill = self.color(tree, 10)
            shape = Chord(coord1[0] + rx, coord1[1] + ry, rx, ry, start, end, fill)
            shape.color = color
            shape.width = width
            self.shapes.append(shape)
        elif name == "pieslice":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            rx = (coord2[0] - coord1[0]) / 2
            ry = (coord2[1] - coord1[1]) / 2
            start = self.angle(tree.children[8]) % 360
            end = self.angle(tree.children[6]) % 360
            color, width = self.cw(tree.children[9])
            fill = self.child(tree, 10)
            if fill is not None:
                fill = self.color(tree, 10)
            shape = Pie(coord1[0] + rx, coord1[1] + ry, rx, ry, start, end, fill)
            shape.color = color
            shape.width = width
            self.shapes.append(shape)
        # elif name == "text":
        #     text = tree.children[1].value[1:-1]
        #     coord = self.coordinate(tree.children[3])
        #     color = self.color(tree, 4)
        #     # TODO: font loading
        #     font = self.font(tree, 6)
        #     self.drawing.text(coord, text, color, font)
        # TODO: load image?
        # TODO: control: size, variables, computations...


def transform(text, T):
    vis = ConversionVisitor()
    vis.visit(T)
    return vis.get()
