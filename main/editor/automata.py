"""This file contains the simplicities of finite automata.

We can see our prefix tree as a simple e-NFA, but we will allow the creation
of additional edges with the same labels (for capital completion).

Author: Randy Paredis
Date:   01/21/2020
"""

class Node:
    def __init__(self, label = "", final: bool = False, data = None):
        self.final = final
        self.data = data
        self.label = label
        self.transitions = set()

    def clear(self):
        self.final = False
        self.data = None
        self.transitions.clear()

    def follow(self, label):
        for trans in self.transitions:
            if trans.label == label:
                return trans.end
        return None

    def findFinals(self):
        finals = []
        if self.final:
            finals.append(self)
        for trans in self.transitions:
            finals += trans.end.findFinals()
        return finals


class Transition:
    def __init__(self, start, end, label):
        self.start = start
        self.end = end
        self.label = label


class FSA:
    def __init__(self):
        self.start = Node()
        self.nodes = [self.start]

    def clear(self):
        self.start.clear()
        self.nodes = [self.start]

    def follow(self, word):
        node = self.start
        for c in word:
            node = node.follow(c)
            if node is None:
                return None
        return node

    def insert(self, word, data = None):
        # TODO: add capital completion via adding more transitions
        #       for all nodes, starting from a previous capital, add
        #       a transition to the current capital.
        node = self.start
        for c in word:
            nx = node.follow(c)
            if nx is None:
                nx = Node()
                node.transitions.add(Transition(node, nx, c))
            node = nx
        node.final = True
        node.label = word
        node.data = data

    def find(self, prefix):
        node = self.follow(prefix)
        if node is None:
            return []
        return node.findFinals()


