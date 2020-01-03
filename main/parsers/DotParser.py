"""This file uses the LARK module in order to identify the validity of a DOT-file.

It also loads the Graphviz grammar from the vendor folder.

Author: Randy Paredis
Date:   16/12/2019
"""
from main.extra.IOHandler import IOHandler
from main.parsers.Parser import Parser, CheckVisitor
from lark import Tree

class DotParser(Parser):
    def __init__(self):
        super(DotParser, self).__init__(IOHandler.dir_grammars("graphviz.lark"))
        self.visitor = CheckDotVisitor(self)


class CheckDotVisitor(CheckVisitor):
    """Helper class that makes sure additional conditions on rules are valid."""
    def __init__(self, parser):
        super(CheckDotVisitor, self).__init__(parser)
        self.type = None

    def previsit(self, tree: Tree):
        if tree.data == "edgeop":
            op = tree.children[0]
            if (self.type == "GRAPH" and op.type == "DIOP") or \
                    (self.type == "DIGRAPH" and op.type == "UNOP"):
                self.errors.append((op,
                                    "Invalid edge operation for graph type at line %i col %i." % (op.line, op.column),
                                    {self.parser.lookup("DIOP") if self.type == "GRAPH" else self.parser.lookup("UNOP")}))
        # FIXME: CURRENTLY DISCONTINUED
        #   (it would increase ease-of-use, but is not necessary atm)
        # elif tree.data == "attr":
        #     key = tree.children[0].children[0]
        #     value = tree.children[1].children[0]
        #     if key.value not in Constants.ATTRIBUTES:
        #         self.errors.append((key, "Invalid attribute", set()))
        #     # TODO: determine scope
        #     scope = "G"
        #     try:
        #         info = getattr(Graphviz, key)(Graphviz.strip(value), scope)
        #         # TODO: info as warnings?
        #     except ValueError as e:
        #         self.errors.append((value, str(e), set()))
        #     except KeyError as e:
        #         self.errors.append((value, str(e), set()))

    def tokenvisit(self, token):
                if token.type in ["GRAPH", "DIGRAPH"]:
                    self.type = token.type
