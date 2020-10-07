"""The engine for drawing Trees.

Author: Randy Paredis
Date:   10/07/2020
"""
from lark import Token, Tree
from graphviz import Digraph

class JSONVisitor:
    def __init__(self):
        self.graphviz = Digraph()
        self.graphviz.attr(rankdir="LR")
        self.cnt = 0
        self.stack = []

    def _visit_default(self, tree):
        for child in tree.children:
            self.visit(child)

    def visit(self, T):
        if isinstance(T, Tree):
            return getattr(self, f"{T.data}", self._visit_default)(T)

    def addNode(self, label):
        name = f"N{self.cnt}"
        self.graphviz.node(name, label)
        self.cnt += 1
        return name

    def addEdgeToParent(self, name, label=None):
        if len(self.stack) > 0:
            self.graphviz.edge(self.stack[-1], name, label=label)

    def value(self, tree):
        child = tree.children[0]
        if isinstance(child, Token):
            label = child.value
            if child.type == "STRING":
                label = label[1:-1]
            node = self.addNode(label)
            return node
        else:
            return self.visit(child)

    def keyvalue(self, tree):
        child = self.visit(tree.children[2])
        self.addEdgeToParent(child, tree.children[0].value[1:-1])

    def array(self, tree):
        arr = self.addNode("[]")
        self.stack.append(arr)
        for child in tree.children:
            if isinstance(child, Tree):
                c = self.visit(child)
                self.graphviz.edge(arr, c)
        self.stack.pop()
        return arr

    def object(self, tree):
        obj = self.addNode("{}")
        self.stack.append(obj)
        for child in tree.children:
            self.visit(child)
        self.stack.pop()
        return obj


def convert_json(text, T):
    vis = JSONVisitor()
    vis.visit(T)
    return vis.graphviz.source
