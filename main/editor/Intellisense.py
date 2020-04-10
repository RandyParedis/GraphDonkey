"""This file concerns itself with the autocompletion functionality of GraphDonkey.

It is meant to be used in plugins in order to allow for a good intellisense-like
autocompletion.

Author: Randy Paredis
Date:   01/21/2020
"""
from enum import Enum
import re

class Types(Enum):
    """Allows future expansion into different autocompletion types."""
    DEFAULT = 0
    SNIPPET = 1

class Trie:
    def __init__(self, data: str = None, contents=None, prefix: str = '', parent: tuple = None):
        """Create a simple Trie structure.

        Args:
            data (str):     The string that needs to be inserted on creation.
                            When None, no string is inserted, otherwise see
                            Trie.insert for more details.
            contents (Any): The contents associated with the data.
                            Only makes sense when data is not None.
                            Ignored otherwise. Defaults to None.
            parent (tuple): The parent of the current Trie.
                            This must be a tuple of the form (Trie, str).
                            Defaults to None.
        """
        self.parent = parent
        self.children = {}
        self.contents = None
        self.final = False
        self.prefix = prefix
        if data is not None:
            self.insert(data, contents)

    def find(self, key: str):
        """Find a node for this key.

        Args:
            key (str):  The key to find.
                        When this is the empty string, the current node is
                        returned.

        Returns:
            The node associated with this key, or None if it does not exists.
        """
        if len(key) == 0:
            return self
        else:
            c = key[0]
            if c in self.children:
                return self.children[c].find(key[1:])
            else:
                return None

    def insert(self, key: str, value=None):
        """Insert an item into this Trie, overwriting the existing one.

        Args:
            key (str):      The key for which to add the item.
                            When key is the empty string, the
                            current node is marked as a final
                            node with the given item as value.
            value (Any):    The item itself. Defaults to None.
        """
        if len(key) == 0:
            self.final = True
            self.contents = value
        else:
            char = key[0]
            if char in self.children:
                self.children[char].insert(key[1:], value)
                self.children[char].prefix = self.prefix + char
            else:
                self.children[char] = Trie(prefix = self.prefix + char, data = key[1:], contents = value,
                                           parent = (self, char))

    def clear(self):
        """Clears the Trie and all its children."""
        for child in self.children:
            self.children[child].clear()
        self.children.clear()
        self.contents = None
        self.final = False
        self.prefix = ''

    def list(self):
        """List all final nodes for this Trie.

        If the current node is final, it will be included in the result.
        If it has children that are final, all of them will be listed as well.

        Returns:
            A list of all final nodes in this subtree (depth-first order).
        """
        res = []
        if self.final:
            res.append(self)
        for child in self.children:
            res += self.children[child].list()
        return res

    def key(self):
        """Get the key used to obtain this element."""
        return self.prefix

    def keys(self):
        """Get all keys for all final nodes."""
        return [x.key() for x in self.list()]

    def value(self):
        """Get the contents of the current node, if set."""
        return self.contents

    def values(self):
        """Get all the contents of all final nodes."""
        return [x.value() for x in self.list()]

    def __len__(self):
        return len(self.children)

class CompletionStorage:
    """Helper class to allow for a simple interaction with all autocompletable values.

    It is known that this corresponds to some duplicate functionality presented by
    Qt, but because the future is uncertain, this class provides a simple interface
    to keep future changes working as well.
    """
    def __init__(self):
        self.completions = Trie()
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
        if isinstance(items, str):
            self.completions.insert(items, (type, value))
            self.items.append(items)
        elif isinstance(items, (list, tuple, iter)):
            for it in items:
                self.completions.insert(it, (type, value))
                self.items.append(it)

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
        node = self.completions.find(prefix)
        if node is not None:
            nodes = node.list()
            return [(x.key(), *x.value()) for x in nodes], prefix
        return [], prefix
