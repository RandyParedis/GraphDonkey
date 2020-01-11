"""This file uses the LARK module in order to identify the validity of a DOT-file.

It also loads the Graphviz grammar from the vendor folder.

Author: Randy Paredis
Date:   16/12/2019
"""
import graphviz

from lark import Lark, Tree, Token
from lark.exceptions import UnexpectedCharacters, UnexpectedToken, UnexpectedEOF

class Parser:
    def __init__(self, file="", parser="lalr"):
        self.grammar = ""
        self.parser = None
        if file != "":
            with open(file, "r") as file:
                self.grammar = file.read()
            self.parser = Lark(self.grammar, parser=parser, propagate_positions=True)
        self.errors = []
        self.visitor = CheckVisitor(self)
        self.converter = {}

    def parse(self, text: str, yld=False):
        self.errors = []
        self.visitor.clear()
        try:
            if self.parser is not None:
                tree = self.parser.parse(text)
                self.visitor.visit(tree)
                self.errors += self.visitor.errors
                if len(self.errors) == 0 or yld:
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

    def convert(self, text, engine):
        # TODO: what if engine does not exist?
        T = self.parse(text)
        if T is not None:
            return self.converter[engine](text, T)
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
    """Helper class that makes sure additional conditions on rules are valid.

    This is ideally inherited from when defining semantic analysis, making sure
    all functions and attributes are set correctly.

    Attrs:
        parser (Parser):    The Parser object that's used for syntax checking.
                            This allows for a mere lookup of terminals and rules.
        errors (list):      A list of 3-tuples (tok, msg, alt); where
                                tok (Token):    The token on which the error occurred.
                                msg (str):      The error message for the issue at hand.
                                alt (set):      A set of alternative tokens to use instead.
    """
    def __init__(self, parser):
        self.parser = parser
        self.errors = []

    def previsit(self, tree: Tree):
        """Function to call before visiting a rule."""
        pass

    def tokenvisit(self, token: Token):
        """Function to call on visiting a token."""
        pass

    def postvisit(self, tree: Tree):
        """Function to call after visiting a rule."""
        pass

    def visit(self, tree: Tree):
        """Actual visit function.

        Do not override this function unless you know what you're doing.
        """
        self.previsit(tree)
        for child in tree.children:
            if isinstance(child, Tree):
                self.visit(child)
            else: # TOKENS
                self.tokenvisit(child)
        self.postvisit(tree)

    def clear(self):
        """Clear the errors."""
        self.errors.clear()


class DotVisitor:
    """Helper class that generates a dot file from any parse tree."""
    def __init__(self):
        self.nodes = {}
        self.root = graphviz.Digraph()

    def visit(self, tree: Tree):
        for child in tree.children:
            if isinstance(child, Tree):
                self.nodes[id(child)] = self.root.node("node_%i" % id(child), child.data)
                self.visit(child)
            elif isinstance(child, Token): # TOKENS
                val = child.value.replace("\\", "\\\\")
                self.nodes[id(child)] = self.root.node("node_%i" % id(child), child.type + ":\n" + val,
                                                       color="blue", fontcolor="blue", shape="box")
            if id(tree) in self.nodes and id(child) in self.nodes:
                self.root.edge("node_%i" % id(tree), "node_%i" % id(child))

    def show(self):
        self.root.view()
