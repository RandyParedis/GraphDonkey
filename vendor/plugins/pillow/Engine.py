"""The Pillow rendering engine.

Author: Randy Paredis
Date:   01/09/2020
"""
from main.extra.IOHandler import IOHandler
from lark import Tree, Lark
from PIL import Image, ImageDraw, ImageColor, ImageQt, ImageFont
import cmath

Config = IOHandler.get_preferences()

class ConversionVisitor:
    def __init__(self):
        self.image = Image.new('RGBA', (640, 480))
        self.drawing = ImageDraw.Draw(self.image)

    def get(self):
        return ImageQt.ImageQt(self.image)

    def child(self, tree: Tree, pos):
        if 0 <= pos < len(tree.children):
            return tree.children[pos]
        return None

    def coordinate(self, coord: Tree):
        if coord.children[0].type == "CENTER":
            return self.image.width // 2, self.image.height // 2
        return float(coord.children[0].value), float(coord.children[2].value)

    def color(self, tree: Tree, pos):
        node = self.child(tree, pos)
        if node is None:
            color = "#000000"
        else:
            color = node.children[1].value
        return ImageColor.getrgb(color)

    def width(self, tree: Tree, pos):
        node = self.child(tree, pos)
        if node is None:
            width = 1
        else:
            width = node.children[1].value
        return int(width)

    def font(self, tree: Tree, pos):
        node = self.child(tree, pos)
        if node is None:
            return None
        return ImageFont.truetype(node.children[1].value[1:-1], int(node.children[0].value))

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
        # print("TREE:", name)
        if name in ["start", "stmt", "shape"]:
            self.visit(tree.children[0])
        elif name == "stmts":
            for child in tree.children:
                self.visit(child)
        elif name == "point":
            coord = self.coordinate(tree.children[2])
            color, width = self.cw(tree.children[3])
            if width == 1:
                self.drawing.point(coord, color)
            else:
                w = width // 2
                self.drawing.ellipse([(coord[0] - w, coord[1] - w), (coord[0] + w, coord[1] + w)], fill=color)
        elif name == "line":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            color, width = self.cw(tree.children[5])
            self.drawing.line([coord1, coord2], color, width)
        elif name == "grid":
            color, width = self.cw(tree.children[1])
            for x in range(0, self.image.width, width):
                self.drawing.line([(x, 0), (x, self.image.height)], color, 1)
            for y in range(0, self.image.height, width):
                self.drawing.line([(0, y), (self.image.width, y)], color, 1)
        elif name == "border":
            color, width = self.cw(tree.children[1])
            self.drawing.line([(0, 0), (0, self.image.height)], color, width)
            self.drawing.line([(0, 0), (self.image.width, 0)], color, width)
            self.drawing.line([(0, self.image.height), (self.image.width, self.image.height)], color, width)
            self.drawing.line([(self.image.width, 0), (self.image.width, self.image.height)], color, width)
        elif name == "ellipse":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            color, width = self.cw(tree.children[5])
            fill = self.child(tree, 6)
            if fill is not None:
                fill = self.color(tree, 6)
            self.drawing.ellipse([coord1, coord2], fill, color, width)
        elif name == "rectangle":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            color, width = self.cw(tree.children[5])
            fill = self.child(tree, 6)
            if fill is not None:
                fill = self.color(tree, 6)
            self.drawing.rectangle([coord1, coord2], fill, color, width)
        elif name == "polygon":
            coords = []
            for child in tree.children:
                if isinstance(child, Tree) and child.data == "coord":
                    coords.append(self.coordinate(child))
            end = 2 * len(coords) + 1
            color = self.color(tree, end)
            fill = self.child(tree, end + 1)
            if fill is not None:
                fill = self.color(tree, end + 1)
            self.drawing.polygon(coords, fill, color)
        elif name == "arc":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            # Counter-clockwise!
            start = (360 - self.angle(tree.children[8])) % 360
            end = (360 - self.angle(tree.children[6])) % 360
            color, width = self.cw(tree.children[9])
            self.drawing.arc([coord1, coord2], start, end, color, width)
        elif name == "chord":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            # Counter-clockwise!
            end = 360 - self.angle(tree.children[6])
            start = 360 - self.angle(tree.children[8])
            color, width = self.cw(tree.children[9])
            fill = self.child(tree, 10)
            if fill is not None:
                fill = self.color(tree, 10)
            self.drawing.chord([coord1, coord2], start, end, fill, color, width)
        elif name == "pieslice":
            coord1 = self.coordinate(tree.children[2])
            coord2 = self.coordinate(tree.children[4])
            if coord1[0] > coord2[0]:
                coord1, coord2 = (coord2[0], coord1[1]), (coord1[0], coord2[0])
            if coord1[1] > coord2[1]:
                coord1, coord2 = (coord1[0], coord2[1]), (coord2[0], coord1[0])
            # Counter-clockwise!
            end = 360 - self.angle(tree.children[6])
            start = 360 - self.angle(tree.children[8])
            color, width = self.cw(tree.children[9])
            fill = self.child(tree, 10)
            if fill is not None:
                fill = self.color(tree, 10)
            self.drawing.pieslice([coord1, coord2], start, end, fill, color, width)
        elif name == "text":
            text = tree.children[1].value[1:-1]
            coord = self.coordinate(tree.children[3])
            color = self.color(tree, 4)
            # TODO: font loading
            font = self.font(tree, 6)
            self.drawing.text(coord, text, color, font)
        # TODO: load image?
        # TODO: control: size, variables, computations...


def convert(T):
    if isinstance(T, Tree):
        vis = ConversionVisitor()
        vis.visit(T)
        return vis.get()

    if isinstance(T, list):  # Turtle
        image = Image.new('RGBA', (640, 480))
        drawing = ImageDraw.Draw(image)
        for f, t in T:
            drawing.line([f, t], fill='black', width=1)
        return ImageQt.ImageQt(image)

    # Parse the input!
    with open(IOHandler.dir_plugins("pillow", "drawing.lark")) as file:
        data = file.read()
    parser = Lark(data, parser="earley", propagate_positions=True)
    return convert(parser.parse(T))
