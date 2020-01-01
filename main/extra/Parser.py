"""This file uses the LARK module in order to identify the validity of a DOT-file.

It also loads the Graphviz grammar from the vendor folder.

Author: Randy Paredis
Date:   16/12/2019
"""
import graphviz

from main.extra.IOHandler import IOHandler
from lark import Lark, Tree, Token
from lark.exceptions import UnexpectedCharacters, UnexpectedToken, UnexpectedEOF

class Parser:
    def __init__(self):
        self.grammar = ""
        with open(IOHandler.dir_grammars("graphviz.lark"), "r") as file:
            self.grammar = file.read()
        self.parser = Lark(self.grammar, parser="lalr")

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
        self.pos_in_stream = len(text.rstrip()) - 1
        self.end_pos = self.pos_in_stream + 1

    def __len__(self):
        return self.end_pos - self.pos_in_stream

    def __repr__(self):
        return "EOFToken <%i, %i; %i, %i>" % (self.line, self.column, self.pos_in_stream, self.end_pos)


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
        for child in tree.children:
            if isinstance(child, Tree):
                self.visit(child)
            else: # TOKENS
                if child.type in ["GRAPH", "DIGRAPH"]:
                    self.type = child.type


class DotVisitor:
    """Helper class that generates a dot file from the parse tree."""
    def __init__(self):
        self.nodes = {}
        self.root = graphviz.Digraph()

    def visit(self, tree: Tree):
        for child in tree.children:
            if isinstance(child, Tree):
                self.nodes[id(child)] = self.root.node("node_%i" % id(child), child.data)
                self.visit(child)
            elif isinstance(child, Token): # TOKENS
                self.nodes[id(child)] = self.root.node("node_%i" % id(child), child.type + ":\n" + child.value,
                                                       color="blue", fontcolor="blue", shape="box")
            if id(tree) in self.nodes and id(child) in self.nodes:
                self.root.edge("node_%i" % id(tree), "node_%i" % id(child))

    def show(self):
        self.root.view()



if __name__ == "__main__":
    from sys import stderr

    parser = Parser()
    txt = "digraph T { start [label=\"\", shape=none, width=\"0\"]; start -> bla; }"
    T = parser.parse(txt)
    if T is None:
        for token, msg, exp in parser.errors:
            print("[%s ERROR AT %i]" % (type(token), token.pos_in_stream), file=stderr)
            print(msg, file=stderr)
            print("\t" + txt.split("\n")[token.line - 1], file=stderr)
            print("\t" + ("~" * (token.column - 1)) + "^", file=stderr)
            print("suggested:", file=stderr)
            print("\t" + ", ".join([x.name for x in exp]), file=stderr)
    else:
        dot = DotVisitor()
        dot.visit(T)
        dot.show()
