"""This file uses the LARK module in order to identify the validity of a DOT-file.

It also loads the Graphviz grammar from the vendor folder.

Author: Randy Paredis
Date:   16/12/2019
"""
from main.extra.IOHandler import IOHandler
from main.parsers.Parser import Parser
from lark import Lark, Tree, Token
from graphviz import Digraph

class FlowchartParser(Parser):
    def __init__(self):
        super(FlowchartParser, self).__init__(IOHandler.dir_grammars("flowchart.lark"))

    def toGraphviz(self, text: str):
        T = self.parse(text)
        vis = ConversionVisitor()
        vis.visit(T)
        return vis.graphviz.source

class ConversionVisitor:
    def __init__(self):
        self.graphviz = Digraph()

    def visit(self, tree: Tree, link=None, label=""):
        name = tree.data
        if name == "start":
            self.graphviz.node("n0", "start")
            e, _ = self.visit(tree.children[0], 0)
            self.graphviz.edge("n%s" % str(e), "end")
            return "e", ""
        if name == "stmts":
            last = link
            for child in tree.children:
                last, label = self.visit(child, last, label)
            return last, label
        elif name == "stmt":
            child = tree.children[0]
            cid = id(tree)
            llb = ""
            if isinstance(child, Tree):
                cid, llb = self.visit(child, link)
                # if child.data == "ifthenelse":
                #     self.graphviz.edge("n%s" % link, "n%s" % cid, label)
            elif isinstance(child, Token):
                self.graphviz.node("n%s" % cid, child.value, shape="box")
            self.graphviz.edge("n%s" % link, "n%s" % cid, label)
            return cid, llb
        elif name == "assign":
            n = ""
            for child in tree.children:
                n += child.value
            self.graphviz.node("n%i" % id(tree), n, shape="box")
            return str(id(tree)), ""
        elif name == "ifthenelse":
            condition = tree.children[1].children[0].value
            self.graphviz.node("n%i" % id(tree), condition, shape="diamond")
            last, llb = self.visit(tree.children[3], str(id(tree)), "True")
            if len(tree.children) > 5:
                pass
            else:
                return last, llb
