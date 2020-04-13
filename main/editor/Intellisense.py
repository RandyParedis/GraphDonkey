"""This file concerns itself with the autocompletion functionality of GraphDonkey.

It is meant to be used in plugins in order to allow for a good intellisense-like
autocompletion.

Author: Randy Paredis
Date:   01/21/2020
"""
from enum import Enum
import re

from PyQt5 import QtGui

from main.editor.automata import FSA, ssc
from main.extra import Constants


class Types(Enum):
    """Allows future expansion into different autocompletion types."""
    DEFAULT = 0
    SNIPPET = 1


ICONS = {
    Types.DEFAULT: QtGui.QIcon(),
    Types.SNIPPET: QtGui.QIcon()
}

class CompletionStorage:
    """Helper class to allow for a simple interaction with all autocompletable values.

    It is known that this corresponds to some duplicate functionality presented by
    Qt, but because the future is uncertain, this class provides a simple interface
    to keep future changes working as well.
    """
    def __init__(self):
        self.completions = FSA()
        self.items = []

    def add(self, items, type = Types.DEFAULT, value=None):
        """Add a set of items.

        Args:
            items (any):    When a string, this string will be added.
                            When an iterable, the set of strings will be added.
            type (Types):   Indicates the type for autocompletion, reserved for
                            future use. Defaults to Types.Default .
            value (Any):    Optional value to assign to the item(s). Can be used
                            for storing additional information.
                            Defaults to None.
        """
        def ins(item):
            self.completions.insert(item, (type, value))
            self.items.append(item)

        if isinstance(items, str):
            ins(items)
        elif isinstance(items, (list, tuple, iter)):
            for it in items:
                ins(it)

    def clear(self):
        """Clears the full list of completions. Only use with precaution!"""
        self.completions.clear()
        self.items.clear()

    def alphabet(self):
        """Get all the letters of the alphabet that makes up the autocomplete items.

        Returns:
            A set of single-character strings.
        """
        return set("".join(self.items))

    def get(self, prefix: str):
        """Get all possibilities for the given prefix.

        Args:
            prefix (str):   The prefix to check against.

        Returns:
            A tuple (list, str), respectively the list of completions and the transformed
            prefix string (all unknown characters are removed)
        """
        prefix = re.sub("[^%s]" % re.escape("".join(self.alphabet())), "", prefix)
        dfa = ssc(self.completions)
        nodes = dfa.find(prefix)
        comps = set()
        for fins in nodes:
            for node in fins.data:
                if node.data is not None:
                    comps.add((node.label, *node.data))
        return sorted(comps, key=lambda x: x[0].lower()), prefix
