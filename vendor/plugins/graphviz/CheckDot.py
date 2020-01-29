"""Check semantics of Graphviz file."""

from main.editor.Parser import CheckVisitor
from lark import Tree

class CheckDotVisitor(CheckVisitor):
    def __init__(self, parser):
        super(CheckDotVisitor, self).__init__(parser)
        self.type = None
        self.a_list = False

    def GRAPH(self, _):
        self.type = "GRAPH"

    def DIGRAPH(self, _):
        self.type = "DIGRAPH"

    def exit_edgeop(self, tree: Tree):
        op = tree.children[0]
        if (self.type == "GRAPH" and op.type == "DIOP") or (self.type == "DIGRAPH" and op.type == "UNOP"):
            self.errors.append((op, "Invalid edge operation for graph type at line %i col %i." % (op.line, op.column),
                                {self.parser.lookup("DIOP") if self.type == "GRAPH" else self.parser.lookup("UNOP")}))

    def enter_node_stmt(self, tree: Tree):
        it = self.terminals(tree)[0]
        self.completer.add(it)

    def enter_a_list(self, tree: Tree):
        self.indent(tree)
        if self.encapsulates(tree):
            self.a_list = True

    def exit_a_list(self, _):
        self.a_list = False

    def enter_start(self, T):
        self.a_list = False

    def exit_stmt_list(self, tree: Tree):
        if self.encapsulates(tree) and not self.a_list:
            self.completer.add(["graph", "subgraph", "node", "edge"])

    def exit_port(self, tree: Tree):
        if self.encapsulates(tree):
            self.completer.add(["n", "ne", "e", "se", "s", "sw", "w", "nw", "c", "_"])

    def enter_scope(self, tree):
        self.indent(tree)

    def STRING(self, T):
        self.indent(T)

    def HTML(self, T):
        self.indent(T)

