"""Check semantics of Flowchart / Pseudocode file."""

from main.extra import delNodes
from main.editor.Parser import CheckVisitor
from lark import Tree, Token
from graphviz import Digraph

class CheckFlowchartVisitor(CheckVisitor):
    def __init__(self, parser):
        super(CheckFlowchartVisitor, self).__init__(parser)
        self.depth = 0

    def previsit(self, tree: Tree):
        if tree.data in ["while", "do"]:
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

    def get(self):
        self.graphviz.attr(splines=self.splines)
        return self.graphviz

    def connect(self, prev, next, **kwargs):
        assert isinstance(prev, list)
        if not isinstance(next, list):
            next = [next]
        for p, l in prev:
            for n in next:
                self.graphviz.edge(p, n, l, **kwargs)

    def isString(self, value):
        return value in ["STRINGD", "STRINGS", "STRINGT"]

    def string(self, token, encap=True):
        if self.isString(token.type):
            res = token.value[1:-1].replace(r"\n", "<br/>")
            if token.type == "STRINGD":
                res = res.replace("\\\"", "\"")
            elif token.type == "STRINGS":
                res = res.replace("\\'", "'")
            elif token.type == "STRINGT":
                res = res.replace("\\`", "`")
            if encap:
                return "<%s>" % res
            else:
                return res
        return token.value

    def stringValue(self, old):
        if old[0] == old[-1] and old[0] in "`'\"":
            return old[1:-1]
        return old

    def isBroken(self):
        return len(self.broken) > 0 and self.broken[-1] is not None

    def isContinued(self):
        return len(self.continued) > 0 and self.continued[-1] is not None

    def nodeName(self, tree: Tree):
        name = tree.data
        if name == "start":
            return "start"
        if name == "stmts":
            return self.nodeName(tree.children[0])
        if name == "stmt":
            child = tree.children[0]
            if isinstance(child, Tree):
                return self.nodeName(child)
            if isinstance(child, Token):
                if child.type in ["BREAK", "CONTINUE"]:
                    return None
                else:
                    return "n%i" % id(child)
        if name == "ifthenelse":
            return self.nodeName(tree.children[1])
        if name == "while":
            return self.nodeName(tree.children[1])
        if name == "do":
            stmts = tree.children[1]
            if isinstance(stmts, Token):
                stmts = tree.children[2]
            return self.nodeName(stmts)
        if name in ["assign", "condition", "io", "return", "comment"]:
            return "n%i" % id(tree)
        return None

    def terminals(self, tree: Tree):
        lst = []
        for child in tree.children:
            if isinstance(child, Token):
                lst.append(self.string(child))
            else:
                lst += self.terminals(child)
        return lst

    def isComment(self, tree: Tree):
        if tree.data == "comment":
            return True
        if len(tree.children) > 0 and isinstance(tree.children[0], Tree):
            return self.isComment(tree.children[0])
        return False

    def visit(self, tree: Tree, links=None):
        assert isinstance(links, list) or links is None or len(links) == 0
        if tree is None:
            return []
        name = tree.data
        if name == "start":
            l = self.visit(tree.children[0], [("start", "")])
            self.connect(l, "end")
            return [("end", "")]
        if name == "stmts":
            cmnt = []
            for child in tree.children:
                if len(cmnt) > 0 and not self.isComment(child) and self.nodeName(child) is not None:
                    self.connect([(x[0], "") for x in cmnt], self.nodeName(child), style="dashed", arrowhead="none")
                    cmnt.clear()
                nlinks = self.visit(child, links)
                if self.isComment(child):
                    cmnt.append(nlinks[0])
                else:
                    links = nlinks
                    if len(links) == 0:
                        if len(cmnt) > 0:
                            if self.isBroken():
                                self.broken[-1] = [(b[0], "<%s>" % "<br/>".join([x[1][1:-1] for x in cmnt]))
                                                   for b in self.broken[-1]]
                            elif self.isContinued():
                                self.continued[-1] = [(c[0], "<%s>" % "<br/>".join([x[1][1:-1] for x in cmnt]))
                                                      for c in self.continued[-1]]
                            delNodes(self.graphviz, [c[0] for c in cmnt])
                            cmnt.clear()
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
                    node = self.nodeName(tree)
                    value = self.string(child)
                    self.graphviz.node(node, value, shape="box")
                    self.connect(links, node)
                    return [(node, "")]
        if name == "pstmt":
            attr = tree.children[1].value.lower()
            value = self.string(tree.children[2])
            if attr == "TRUE":
                self.true = value
            elif attr == "FALSE":
                self.false = value
            # elif attr == "TF":
            #     self.true, self.false = [self.stringValue(x.strip()) for x in value.split(",")]
            elif attr == "splines":
                self.splines = value
            elif attr == "start":
                if tree.children[2].type == "NAME" and value.lower() in ["false", "no", "off"]:
                    links = []
                else:
                    self.graphviz.node("start", value)
        if name == "assign":
            node = self.nodeName(tree)
            lbl = " ".join(self.terminals(tree))
            self.graphviz.node(node, lbl, shape="box")
            self.connect(links, node)
            return [(node, "")]
        if name == "condition":
            node = self.nodeName(tree)
            self.graphviz.node(node, " ".join(self.terminals(tree)), shape="diamond")
            self.connect(links, node)
            return [(node, "")]
        if name == "ifthenelse":
            condition = self.visit(tree.children[1], links)[0][0]
            then = None
            elifs = []
            _else = None
            for child in tree.children:
                if isinstance(child, Tree):
                    if child.data == "stmts":
                        then = child
                    elif child.data == "elif":
                        elifs.append(child)
                    elif child.data == "else":
                        _else = child.children[1]
            res = self.visit(then, [(condition, self.true)])
            if len(elifs) > 0:
                p = condition
                for e in elifs:
                    cond = None
                    stmts = None
                    for c in e.children:
                        if isinstance(c, Tree):
                            if c.data == "condition":
                                cond = c
                            elif c.data == "stmts":
                                stmts = c
                    con = self.visit(cond, [(p, self.false)])[0][0]
                    res += self.visit(stmts, [(con, self.true)])
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
            stmts = tree.children[3]
            if isinstance(stmts, Token):
                stmts = tree.children[4]
            res = self.visit(stmts, [(condition, self.true)])
            self.connect(res, condition)
            self.connect(self.continued.pop(), condition)
            broken = self.broken.pop()
            if broken is not None:
                return broken
            return [(condition, self.false)]
        if name == "do":
            self.broken.append(None)
            self.continued.append([])
            stmts = tree.children[2]
            if isinstance(stmts, Token):
                stmts = tree.children[3]
            res = self.visit(stmts, links)
            frst = self.nodeName(stmts)
            if frst is None:
                frst = links
            self.connect(res, frst)
            self.connect(self.continued.pop(), frst)
            broken = self.broken.pop()
            if broken is not None:
                return broken
            return []
        if name == "io":
            node = self.nodeName(tree)
            value = "<<b>%s</b>>" % tree.children[0].value
            if len(tree.children) == 2:
                v = self.string(tree.children[1], False)
                value = "<<b>%s: </b> %s>" % (tree.children[0].value, v)
            self.graphviz.node(node, value, shape="parallelogram")
            self.connect(links, node)
            return [(node, "")]
        if name == "return":
            node = self.nodeName(tree)
            value = "end"
            if len(tree.children) == 2:
                value = self.string(tree.children[1])
            self.graphviz.node(node, value)
            self.connect(links, node)
            return []
        if name == "comment":
            node = self.nodeName(tree)
            child = tree.children[1]
            value = self.string(child)
            self.graphviz.node(node, value, shape="note")
            return [(node, value)]

        return links

def convert(text, T):
    vis = ConversionVisitor()
    vis.visit(T)
    return vis.get().source