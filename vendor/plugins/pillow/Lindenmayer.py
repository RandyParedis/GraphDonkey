"""The engine for drawing Lindenmayer Systems

https://en.wikipedia.org/wiki/L-system

Author: Randy Paredis
Date:   06/02/2020
"""
from main.extra.IOHandler import IOHandler
from lark import Transformer
import math

Config = IOHandler.get_preferences()

class LSystemRule:
    def __init__(self, head, *tail):
        self.head = head
        self.tails = list(tail)

    def __repr__(self):
        return "%s -> %s" % (self.head, self.get_tail())

    def add_tail(self, tail):
        self.tails.append(tail)

    def get_tail(self):
        return self.tails[0]

class LSystem:
    def __init__(self):
        self.alphabet = set()
        self.axiom = None
        self.rules = dict()
        self.depth = 1
        self.angle = 90
        self.seed = 0
        self.size = 10

    def add_rule(self, rule):
        self.rules[rule.head] = rule

    def solve(self):
        current = self.rules[self.axiom].get_tail()
        for i in range(self.depth-1):
            new = []
            for tok in current:
                new += self.rules.get(tok, LSystemRule(tok, tok)).get_tail()
            current = new[:]
        return self.execute(current)

    def execute(self, stream):
        # TODO: Optimize!
        stack = []
        a = 0
        pos = (0, 0)
        trail = []
        for s in stream:
            if s == '+':
                a += self.angle
            elif s == '-':
                a -= self.angle
            elif s == '[':
                stack.append((pos, a))
            elif s == ']':
                pos, a = stack.pop()
            else:
                rad = math.radians(a)
                npos = pos[0] + math.cos(rad) * self.size, pos[1] + math.sin(rad) * self.size
                if s.isupper():
                    trail.append((pos, npos))
                pos = npos
        return trail


class LindenmayerTransformer(Transformer):
    def __init__(self):
        super().__init__(True)
        self.system = LSystem()

    LETTER = CONST = str
    PERC = float

    def INT(self, x):
        return int(float(x))

    def axiom(self, elms):
        self.system.axiom = elms[2]

    def letters(self, elms):
        self.system.alpha = elms
        return elms

    def seed(self, elms):
        self.system.seed = elms[2]

    def depth(self, elms):
        self.system.depth = elms[2]

    def angle(self, elms):
        self.system.angle = elms[2]

    def alpha(self, elms):
        self.system.alpha = set(elms[2])

    def tail(self, elms):
        return elms

    def rule(self, elms):
        # TODO: what if rule exists?
        self.system.add_rule(LSystemRule(elms[0], elms[2]))


class LImage:
    def __init__(self, path):
        self.path = path

    def find_bounds(self):
        xmin = xmax = ymin = ymax = 0
        for (x1, y1), (x2, y2) in self.path:
            xmin = min(x1, x2, xmin)
            xmax = max(x1, x2, xmax)
            ymin = min(y1, y2, ymin)
            ymax = max(y1, y2, ymax)
        return (xmin, ymin), (xmax, ymax)

    def transform(self, tx, ty, sx=1, sy=1):
        for i in range(len(self.path)):
            (x1, y1), (x2, y2) = self.path[i]
            self.path[i] = (x1 * sx + tx, y1 * sy + ty), (x2 * sx + tx, y2 * sy + ty)

    def pillow(self):
        stmts = []
        for (x1, y1), (x2, y2) in self.path:
            p = (round(x1, 6), round(y1, 6)), (round(x2, 6), round(y2, 6))
            stmts.append("line from %s to %s width 1" % p)
        return "\n".join(stmts)


def transform(text, T):
    trans = LindenmayerTransformer()
    trans.transform(T)
    img = LImage(trans.system.solve())
    (l, b), (r, t) = img.find_bounds()
    w = 640 / (r - l)
    h = 480 / (t - b)
    img.transform(0, t * 10, 1, -1)
    return img.path
