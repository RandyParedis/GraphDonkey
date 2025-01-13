"""The Graphviz rendering engine for the Graphviz plugin.

Author: Randy Paredis
Date:   01/09/2020
"""
import graphviz
from main.extra.IOHandler import IOHandler
from main.plugins import command
from PyQt6 import QtWidgets
import subprocess

Config = IOHandler.get_preferences()

def convert(text: str):
    dot = graphviz.Source(text, engine=Config.value("plugin/graphviz/engine"))
    try:
        return dot.pipe(Config.value("plugin/graphviz/format"), Config.value("plugin/graphviz/renderer"),
                        Config.value("plugin/graphviz/formatter"))
    except graphviz.backend.CalledProcessError as err:
        raise Exception(err.stderr.decode('utf-8'))

def export(text: str, extension: str):
    try:
        cmd = [Config.value("plugin/graphviz/engine"), "-T%s:" % extension]
        command(cmd)
    except subprocess.CalledProcessError as e:
        fmts = e.output.decode("utf-8").replace("\n", "") \
            [len('Format: "%s:" not recognized. Use one of: ' % extension):].split(" ")
        items = sorted(list(set(fmts)))
        if len(items) == 1:
            ok = True
            value = items[0]
        else:
            value, ok = QtWidgets.QInputDialog.getItem(None, "Export Options", "Please pick your renderer/formatter:",
                                                   items, 0, False)
        if ok:
            _, renderer, formatter = value.split(":")
            dot = graphviz.Source(text, engine=Config.value("plugin/graphviz/engine"))
            return dot.pipe(extension, renderer, formatter)
    return None

from lark import Tree, Token

class DotVisitor:
    """Helper class that generates a dot file from any parse tree."""
    def __init__(self):
        self.nodes = {}
        self.root = graphviz.Digraph()

    def visit(self, tree: Tree):
        for child in tree.children:
            if isinstance(child, Tree):
                self.nodes[id(child)] = \
                    self.root.node("node_%i" % id(child), child.data + "[%i:%i]" % (child.line, child.column))
                self.visit(child)
            elif isinstance(child, Token): # TOKENS
                val = child.value.replace("\\", "\\\\")
                self.nodes[id(child)] = self.root.node("node_%i" % id(child),
                                                       "%s [%i:%i]:\n%s" % (child.type, child.line, child.column, val),
                                                       color="blue", fontcolor="blue", shape="box")
            if id(tree) in self.nodes and id(child) in self.nodes:
                self.root.edge("node_%i" % id(tree), "node_%i" % id(child))

    def show(self):
        self.root.view()


def AST(tree: Tree):
    dot = DotVisitor()
    dot.visit(tree)
    return convert(dot.root.source)
