"""This file uses the LARK module in order to identify the validity of a DOT-file.

It also loads the Graphviz grammar from the vendor folder.

Author: Randy Paredis
Date:   16/12/2019
"""
from main.extra.IOHandler import IOHandler
from main.parsers.Parser import Parser, CheckVisitor
from lark import Lark, Tree, Token
from graphviz import Digraph

TRUE = "Yes"
FALSE = "No"

class FlowchartParser(Parser):
    def __init__(self):
        super(FlowchartParser, self).__init__(IOHandler.dir_grammars("flowchart.lark"))
        self.visitor = CheckFlowchartVisitor(self)

    def toGraphviz(self, text: str):
        T = self.parse(text)
        vis = ConversionVisitor()
        vis.visit(T)
        return vis.graphviz.source

class CheckFlowchartVisitor(CheckVisitor):
    def __init__(self, parser):
        super(CheckFlowchartVisitor, self).__init__(parser)
        self.depth = 0

    def previsit(self, tree: Tree):
        if tree.data == "while":
            self.depth += 1

    def tokenvisit(self, token: Token):
        if token.type in ["BREAK", "CONTINUE"]:
            if self.depth == 0:
                self.errors.append((token, "Loop control statements outside of loop.", {}))

    def postvisit(self, tree: Tree):
        if tree.data == "while":
            self.depth -= 1

class ConversionVisitor:
    def __init__(self):
        self.graphviz = Digraph()
        self.graphviz.attr(splines="polyline")
        self.broken = []
        self.continued = []

    def connect(self, prev, next):
        assert isinstance(prev, list)
        if not isinstance(next, list):
            next = [next]
        for p, l in prev:
            for n in next:
                self.graphviz.edge(p, n, l)

    def isString(self, value):
        return value in ["STRINGD", "STRINGS"]

    def string(self, token):
        if self.isString(token.type):
            return token.value[1:-1]
        return token.value

    def isBroken(self):
        return len(self.broken) > 0 and self.broken[-1] is not None

    def isContinued(self):
        return len(self.continued) > 0 and self.continued[-1] is not None

    def visit(self, tree: Tree, links=None):
        assert isinstance(links, list) or links is None
        if tree is None:
            return []
        name = tree.data
        if name == "start":
            self.graphviz.node("n0", "start")
            l = self.visit(tree.children[0], [("n0", "")])
            self.connect(l, "end")
            return [("end", "")]
        if name == "stmts":
            for child in tree.children:
                links = self.visit(child, links)
                if self.isBroken():
                    break
            return links
        if name == "stmt":
            child = tree.children[0]
            if isinstance(child, Tree):
                return self.visit(child, links)
            if isinstance(child, Token):
                if child.type == "BREAK":
                    self.broken[-1] = links
                    return []
                elif child.type == "CONTINUE":
                    self.continued[-1] = links
                    return []
                else:
                    node = "n%i" % id(child)
                    value = self.string(child)
                    self.graphviz.node(node, value, shape="box")
                    self.connect(links, node)
                    return [(node, "")]
        if name == "assign":
            t = []
            for child in tree.children:
                if isinstance(child, Token):
                    t.append(child.value)
                elif isinstance(child, Tree):
                    if child.data == "operation":
                        for c in child.children:
                            t.append(c.value)
            node = "n%i" % id(tree)
            lbl = " ".join(t)
            self.graphviz.node(node, lbl, shape="box")
            self.connect(links, node)
            return [(node, "")]
        if name == "condition":
            t = []
            for child in tree.children:
                t.append(self.string(child))
            node = "n%i" % id(tree)
            self.graphviz.node(node, " ".join(t), shape="diamond")
            self.connect(links, node)
            return [(node, "")]
        if name == "ifthenelse":
            condition = self.visit(tree.children[1], links)[0][0]
            then = None
            elifs = []
            _else = None
            for child in tree.children:
                if isinstance(child, Tree):
                    if child.data == "iftype":
                        types = [self.string(x) for x in child.children]
                    elif child.data == "stmts":
                        then = child
                    elif child.data == "elif":
                        elifs.append(child)
                    elif child.data == "else":
                        _else = child.children[1]
            res = self.visit(then, [(condition, TRUE)])
            if len(elifs) > 0:
                p = condition
                for e in elifs:
                    con = self.visit(e.children[1], [(p, FALSE)])[0][0]
                    res += self.visit(e.children[3], [(con, TRUE)])
                    p = con
                if _else is not None:
                    res += self.visit(_else, [(p, FALSE)])
            elif _else is not None:
                res += self.visit(_else, [(condition, FALSE)])
            else:
                res.append((condition, FALSE))
            return res
        if name == "while":
            condition = self.visit(tree.children[1], links)[0][0]
            self.broken.append(None)
            self.continued.append([])
            res = self.visit(tree.children[3], [(condition, TRUE)])
            self.connect(res, condition)
            self.connect(self.continued.pop(), condition)
            broken = self.broken.pop()
            if broken is not None:
                return broken
            return [(condition, FALSE)]

        return links
