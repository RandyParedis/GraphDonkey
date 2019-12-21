"""This file uses the LARK module in order to identify the validity of a DOT-file.

It also loads the Graphviz grammar from the vendor folder.

Author: Randy Paredis
Date:   16/12/2019
"""
from main.extra.IOHandler import IOHandler
from lark import Lark, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedToken, UnexpectedEOF

class Parser:
    def __init__(self):
        self.grammar = ""
        with open(IOHandler.dir_grammars("graphviz.lark"), "r") as file:
            self.grammar = file.read()
        self.parser = Lark(self.grammar)

        self.errors = []

    def parse(self, text: str):
        self.errors = []
        try:
            tree = self.parser.parse(text)
            visitor = CheckVisitor(self)
            visitor.visit(tree)
            self.errors += visitor.errors
            if len(self.errors) == 0:
                return tree
        except (UnexpectedCharacters, UnexpectedToken) as e:
            splt = str(e).split("\n")
            while "" in splt:
                splt.remove("")
            exp = [x[1:-1] for x in splt[-1][len("Expecting: {"):-1].split(", ")]
            exp = [self.lookup(x) for x in exp if x is not None]
            self.errors.append((e, splt[0], exp))
        except UnexpectedEOF as e:
            self.errors.append((EOFToken(text), "Unexpected end-of-input.", set(e.expected)))
        return None

    def lookup(self, terminal_name):
        if terminal_name in self.parser._terminals_dict:
            return self.parser._terminals_dict[terminal_name]
        return None


class EOFToken:
    """Helperclass for UnexpectedEOF errors."""
    def __init__(self, text):
        split = text.split("\n")
        self.line = len(split)
        self.column = len(split[-1])
        self.pos_in_stream = sum([len(x) for x in split]) - 1
        self.end_pos = self.pos_in_stream + 1


class CheckVisitor:
    """Helper class that makes sure additional conditions on rules are valid."""
    def __init__(self, parser):
        self.parser = parser
        self.type = None
        self.errors = []

    def visit(self, tree: Tree):
        if tree.data == "edgeop":
            op = tree.children[0]
            if (self.type == "GRAPH" and op.type == "DIOP") or \
                    (self.type == "DIGRAPH" and op.type == "UNOP"):
                self.errors.append((op,
                                    "Invalid edge operation for graph type at line %i col %i." % (op.line, op.column),
                                    {self.parser.lookup("DIOP") if self.type == "GRAPH" else self.parser.lookup("UNOP")}))
        for child in tree.children:
            if isinstance(child, Tree):
                self.visit(child)
            else: # TOKENS
                if child.type in ["GRAPH", "DIGRAPH"]:
                    self.type = child.type


if __name__ == "__main__":
    from sys import stderr

    parser = Parser()
    txt = "graph T { test [label=\"0, 5\"]; }"
    T = parser.parse(txt)
    if T is None:
        for token, msg, exp in parser.errors:
            print("[%s ERROR AT %i]" % (type(token), token.pos_in_stream), file=stderr)
            print(msg, file=stderr)
            print("\t" + txt.split("\n")[token.line - 1], file=stderr)
            print("\t" + ("~" * (token.column - 1)) + "^", file=stderr)
            print("suggested:", file=stderr)
            print("\t" + ", ".join([x.name for x in exp]), file=stderr)
