"""This file uses the LARK module in order to identify the validity of a DOT-file.

It also loads the Graphviz grammar from the vendor folder.

Author: Randy Paredis
Date:   16/12/2019
"""
from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedToken, UnexpectedEOF
from main.editor.Intellisense import CompletionStorage

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

    def parse(self, text: str, yld=False, line=-1, col=-1):
        self.errors = []
        try:
            if self.parser is not None:
                tree = self.parser.parse(text)
                if tree is not None:
                    self.visitor.clear()
                    self.visitor.line = line
                    self.visitor.column = col
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

    def convert(self, text, engine, line=-1, col=-1):
        # TODO: what if engine does not exist?
        T = self.parse(text, line=line, col=col)
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

    Additionally, this class allows for setting the autocompletion as you desire.

    Attrs:
        line (int):         The current line number of the cursor.
        column (int):       The current column of the cursor.
        completer (Any):    A CompletionStorage object that can be used by subclasses in order
                            to identify context-specific autocompletion.
        parser (Parser):    The Parser object that's used for syntax checking.
                            This allows for a mere lookup of terminals and rules.
        errors (list):      A list of 3-tuples (tok, msg, alt); where
                                tok (Token):    The token on which the error occurred.
                                msg (str):      The error message for the issue at hand.
                                alt (set):      A set of alternative tokens to use instead.
    """
    def __init__(self, parser):
        self.line = -1
        self.column = -1
        self.completer = CompletionStorage()
        self.scope = {}
        self.parser = parser
        self.errors = []

    def indent(self, tree: Tree, n=1):
        """Sets the indentation level for the lines in this scope.

        All children of the tree will be annotated with an additional indent.
        This is done as follows:
            - If the tree spans over a single line, do nothing.
            - Otherwise, mark the first line to increase the indent and denote
              the last line to decrease the indent. This last line is the line
              before the one on which the scope ends, UNLESS the scope starts
              at this line. This is done to allow the closing scope tokens
              to be indented visually at the upper scope level.

        Args:
            tree (Any):     The Tree/Token to set the indentation level on.
            n (int):        The increase for the new indentation level.
                            Only set this value if you want to increase the indentation with
                            more than 1 level for the scope defined by the tree.
                            This is not an absolute value, but rather a relative attribute,
                            i.e. it's the *increase* of the indentation. Defaults to 1.

        Examples:
            Let '{' denote the opening of a scope and '}' denote its closing. The '.'
            will indicate an indentation level.
            Let '#' denote the beginning of a line comment, allowing for more clarity.
            The following code fragment indicates how the scopes will be set.

            ---

            {       # Opens a scope, increasing the indent with n
            .   some text within the scope
            .   { open and close }  # No annotation of its children
            .   {   # Opens another scope
            .   .   you can do other things here.
            .   .   even opening yet another scope
            .   .   { text here     # Open another scope with text immediately here
            .   .   }   # Close the new scope at this line!
            .   }   # Closes the inner scope at the previous line
            .   some other text
            .   This can also be code
            }       # Closes a scope, setting the decrease of the indent to the previous line
        """
        if tree.line != tree.end_line:
            self.scope[tree.line] = self.scope.get(tree.line, 0) + n
            el = tree.end_line - 1
            if tree.line == el:
                el += 1
            self.scope[el] = self.scope.get(el, 0) - n

    def obtain(self, line, start=1):
        """Get the indentation level for a specific line of code.

        Args:
            line (int):     The line for which to determine the absolute
                            indentation level. It will accumulate all
                            previous indentations and interpolates the
                            value for empty lines. This value is 1-based.
            start (int):    The line from which to start accumulating
                            the indentation level. This value is 1-based.
                            Defaults to 1.

        Returns:
            The absolute indentation level of the line as an int.
        """
        indent = 0
        for i in range(start, line):
            if i in self.scope:
                indent += self.scope[i]
        return indent

    def visit(self, tree):
        """Main visit function to be called. DO NOT CHANGE!

        If you want to define specialities in subclasses, it is preferred to use
        the available methods thereof.

        Tokens can be called by their name, rules by either enter_rule or exit_rule
        (where 'rule' must be replaced with the rule name in question). These set of
        functions accept a single argument: the Tree/Token they refer to.

        These functions are parser/grammar-specific and can be omitted.

        ONLY ALTER THIS METHOD IF YOU KNOW WHAT YOU'RE DOING!

        Args:
            tree (Any): A Tree or a Token to use as an entrypoint. Commonly, this is
                        the root of the parsed file.

        Examples:
            Given a grammar:
                start: a | b
                a: A
                b: B
                A: "A"i
                B: "B"i

            This function will call the methods `enter_start`, `exit_start`, `enter_a`, `exit_a`, `enter_b`, `exit_b`,
            `A` and `B` if available and when they're needed to be called.
        """
        if isinstance(tree, Tree):
            getattr(self, "enter_" + tree.data, lambda x: x)(tree)
            for child in tree.children:
                self.visit(child)
            getattr(self, "exit_" + tree.data, lambda x: x)(tree)
        elif isinstance(tree, Token):
            getattr(self, tree.type, lambda x: x)(tree)

    def terminals(self, tree):
        """Get a list of values for all the non-consumed terminals in the tree.

        Args:
            tree (Any): A Tree or a Token.
        """
        if isinstance(tree, Tree):
            res = []
            for child in tree.children:
                res += self.terminals(child)
            return res
        elif isinstance(tree, Token):
            return [tree.value]

    def encapsulates(self, item):
        """Returns True when the given item encapsulates the current position.

        Args:
            item (Any): Expected to be either a Tree or a Token.
        """
        if item.meta.empty: return False
        if item.line == self.line:
            if self.line == item.end_line:
                return item.column <= self.column <= item.end_column
            else:
                return item.column <= self.column
        if item.end_line == self.line:
            return self.column <= item.end_column
        return item.line <= self.line <= item.end_line

    def clear(self):
        """Clear the visitor."""
        self.errors.clear()
        self.completer.clear()
        self.scope.clear()
        self.line = -1
        self.column = -1
