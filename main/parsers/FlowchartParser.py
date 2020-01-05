"""This file uses the LARK module in order to identify the validity of a DOT-file.

It also loads the Graphviz grammar from the vendor folder.

Author: Randy Paredis
Date:   16/12/2019
"""
from main.extra.IOHandler import IOHandler
from main.parsers.Parser import Parser, CheckVisitor
from lark import Tree, Token
from graphviz import Digraph

class FlowchartParser(Parser):
    def __init__(self):
        super(FlowchartParser, self).__init__(IOHandler.dir_grammars("flowchart.lark"))
        self.visitor = CheckFlowchartVisitor(self)

    def toGraphviz(self, text: str):
        T = self.parse(text)
        vis = ConversionVisitor()
        vis.visit(T)
        vis.graphviz.attr(splines=vis.splines)
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
        self.broken = []
        self.continued = []
        self.true = "Yes"
        self.false = "No"
        self.splines = "polyline"

    def connect(self, prev, next):
        assert isinstance(prev, list)
        if not isinstance(next, list):
            next = [next]
        for p, l in prev:
            for n in next:
                self.graphviz.edge(p, n, l)

    def isString(self, value):
        return value in ["STRINGD", "STRINGS", "STRINGT"]

    def string(self, token):
        if self.isString(token.type):
            return token.value[1:-1]
        return token.value

    def stringValue(self, old):
        if old[0] == old[-1] and old[0] in "`'\"":
            return old[1:-1]
        return old

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
                if self.isBroken() or len(links) == 0:
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
                elif len(links) == 0:
                    return []
                else:
                    node = "n%i" % id(child)
                    value = self.string(child)
                    self.graphviz.node(node, value, shape="box")
                    self.connect(links, node)
                    return [(node, "")]
        if name == "pstmt":
            attr = tree.children[1].value
            value = self.string(tree.children[2])
            if attr == "TRUE":
                self.true = value
            elif attr == "FALSE":
                self.false = value
            elif attr == "TF":
                self.true, self.false = [self.stringValue(x.strip()) for x in value.split(",")]
            elif attr == "splines":
                self.splines = value
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
            res = self.visit(then, [(condition, self.true)])
            if len(elifs) > 0:
                p = condition
                for e in elifs:
                    con = self.visit(e.children[1], [(p, self.false)])[0][0]
                    res += self.visit(e.children[3], [(con, self.true)])
                    p = con
                if _else is not None:
                    res += self.visit(_else, [(p, self.false)])
            elif _else is not None:
                res += self.visit(_else, [(condition, self.false)])
            else:
                res.append((condition, self.false))
            return res
        if name == "while":
            condition = self.visit(tree.children[1], links)[0][0]
            self.broken.append(None)
            self.continued.append([])
            res = self.visit(tree.children[3], [(condition, self.true)])
            self.connect(res, condition)
            self.connect(self.continued.pop(), condition)
            broken = self.broken.pop()
            if broken is not None:
                return broken
            return [(condition, self.false)]
        if name == "io":
            node = "n%i" % id(tree)
            value = "<<b>%s</b>>" % tree.children[0].type.lower()
            if len(tree.children) == 2:
                v = self.string(tree.children[1])
                v = v.replace("\\n", "<br/>")
                value = "<<b>%s: </b> %s>" % (tree.children[0].type.lower(), v)
            self.graphviz.node(node, value, shape="parallelogram")
            self.connect(links, node)
            return [(node, "")]
        if name == "return":
            node = "n%i" % id(tree)
            value = "end"
            if len(tree.children) == 2:
                value = self.string(tree.children[1])
            self.graphviz.node(node, value)
            self.connect(links, node)
            return []

        return links
