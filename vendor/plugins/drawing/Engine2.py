"""The Pillow rendering engine for the Pillow plugin.

Author: Randy Paredis
Date:   01/06/2020
"""
from lark import Transformer, v_args, Tree, Token


class PillowVisitor:
    def __init__(self):
        self.variables = {}

    def __default__(self, elms):
        res = None
        for elm in elms:
            res = self.visit(elm)
        return res

    def __default_token__(self, token: Token):
        return token.value

    def error(self, message: str, token: Token):
        # TODO: highlight in red
        raise Exception("%s at line %i" % (message, token.line))

    def visit(self, tree: Tree):
        if isinstance(tree, Token):
            return getattr(self, tree.type, self.__default_token__)(tree)
        return getattr(self, tree.data, self.__default__)(tree.children)

    def get_variable(self, token: Token):
        vname = token.value
        if vname not in self.variables:
            self.error("Variable '%s' is not yet defined" % vname, token)
        ret = self.variables[vname]
        return ret

    NUMBER = float
    NAME = str

    def STRING(self, elm):
        return elm.value[1:-1]

    def TRUE(self, _):
        return True

    def FALSE(self, _):
        return False

    def NOT(self, _):
        return "not"

    def POW(self, _):
        return "**"

    def MUL(self, _):
        return "*"

    def DIV(self, _):
        return "/"

    def MOD(self, _):
        return "%"

    def ADD(self, _):
        return "+"

    def SUB(self, _):
        return "-"

    def AND(self, _):
        return "and"

    def OR(self, _):
        return "or"

    def define(self, elms):
        vname = elms[1].value
        if vname in self.variables:
            self.error("Duplicate definition of '%s'" % vname, elms[1])
        self.variables[vname] = self.visit(elms[3])

    def assign(self, elms):
        vname = elms[0].value
        val = self.get_variable(elms[0])
        if len(elms[1].value) == 2:
            ta = self.visit(elms[2])
            res = {
                "+": self.add,
                "-": self.sub,
                "*": self.mul,
                "/": self.div,
                "%": self.mod
            }[elms[1].value[0]](val, ta)
        else:
            res = self.visit(elms[2])
        self.variables[vname] = res

    def sum(self, elms):
        if len(elms) > 1:
            lhs = self.visit(elms[0])
            rhs = self.visit(elms[2])
            if elms[1].value == "+":
                return self.add(lhs, rhs)
            return self.sub(lhs, rhs)
        return self.visit(elms[0])

    def prod(self, elms):
        if len(elms) > 1:
            lhs = self.visit(elms[0])
            rhs = self.visit(elms[2])
            if elms[1].value == "*":
                return self.mul(lhs, rhs)
            if elms[1].value == "/":
                return self.div(lhs, rhs)
            return self.mod(lhs, rhs)
        return self.visit(elms[0])

    def power(self, elms):
        if len(elms) > 1:
            lhs = self.visit(elms[0])
            rhs = self.visit(elms[2])
            # TODO; string concat, color addition...
            return lhs ** rhs
        return self.visit(elms[0])

    def add(self, lhs, rhs):
        # TODO; string concat, color addition...
        return lhs + rhs

    def sub(self, lhs, rhs):
        # TODO; string concat, color addition...
        return lhs - rhs

    def mul(self, lhs, rhs):
        # TODO; string concat, color addition...
        return lhs * rhs

    def div(self, lhs, rhs):
        # TODO; string concat, color addition...
        return lhs / rhs

    def mod(self, lhs, rhs):
        # TODO; string concat, color addition...
        return lhs % rhs

    def bop(self, lhs, op, rhs):
        # TODO; string comp, color comp...
        return eval("%s %s %s" % (str(lhs), op, str(rhs)))

    def bexpr(self, elms):
        if len(elms) == 2:
            return not self.visit(elms[1])
        return self.bop(self.visit(elms[0]), elms[1].value, self.visit(elms[2]))

    def var(self, elms):
        return self.get_variable(elms[0])

    def if_(self, elms):
        # TODO: order of conditions
        cond = self.visit(elms[1])
        if cond:
            return self.visit(elms[2])
        if len(elms) == 3:
            return None
        if len(elms[3:]) == 2:
            return self.visit(elms[-1])
        return self.if_(elms[3:])

    def for_(self, elms):
        # TODO
        pass


def convert(T):
    visit = PillowVisitor()
    visit.visit(T)
    print(visit.variables)
    return None
