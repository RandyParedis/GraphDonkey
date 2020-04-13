"""This file contains the simplicities of finite automata.

We can see our prefix tree as a simple e-NFA, but we will allow the creation
of additional edges with the same labels (for capital completion).

Author: Randy Paredis
Date:   01/21/2020
"""

class Node:
    def __init__(self, label = "", final: bool = False, data = None):
        self.label = label
        self.final = final
        self.data = data
        self.transitions = set()

    def addTransition(self, end, label, skip=False):
        trans = Transition(self, end, label, skip)
        if trans not in self.transitions:
            self.transitions.add(trans)

    def clear(self):
        self.final = False
        self.data = None
        self.transitions.clear()

    def follow(self, label, follow_skip=False):
        for trans in self.transitions:
            if not follow_skip and trans.skip: continue
            if trans.label == label:
                return trans.end
        return None

    def followAll(self, label):
        res = set()
        for trans in self.transitions:
            if trans.label == label:
                res.add(trans.end)
        return res

    def findFinals(self):
        finals = set()
        if self.final:
            finals.add(self)
        for trans in self.transitions:
            finals |= trans.end.findFinals()
        return finals


class Transition:
    def __init__(self, start, end, label, skip=False):
        self.start = start
        self.end = end
        self.label = label
        self.skip = skip

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end and self.label == other.label

    def __hash__(self):
        return hash((self.start, self.end, self.label))


class FSA:
    def __init__(self, start=None):
        self.start = Node() if start is None else start
        self.nodes = [self.start]
        self.alphabet = set()

    def clear(self):
        self.start.clear()
        self.nodes = [self.start]

    def follow(self, word):
        nodes = {self.start}
        for c in word:
            new = set()
            for node in nodes:
                new |= node.followAll(c)
            nodes = new
        return nodes

    def insert(self, word, data = None):
        node = self.start
        path = []
        for i in range(len(word)):
            c = word[i]
            self.alphabet.add(c)
            nx = node.follow(c)
            if nx is None:
                nx = Node(word[:i+1])
                node.addTransition(nx, c)
                self.nodes.append(nx)
            node = nx
            if c.isupper():
                for n in path:
                    n.addTransition(node, c, True)
            path.append(node)
        node.final = True
        node.label = word
        node.data = data

    def find(self, prefix):
        nodes = self.follow(prefix)
        fins = set()
        for node in nodes:
            fins |= node.findFinals()
        return fins

    def toDot(self):
        res = "digraph FSA {\n"
        for i in range(len(self.nodes)):
            s = ""
            if self.nodes[i].final:
                s = ' color="red"'
            res += '\tN%i [label="%s"%s];\n' % (i, self.nodes[i].label, s)
        res += "\n"
        for i in range(len(self.nodes)):
            node = self.nodes[i]
            for trans in node.transitions:
                s = ""
                if trans.skip:
                    s = ' color="blue"'
                res += '\tN%i -> N%i [label="%s"%s];\n' % (i, self.nodes.index(trans.end), trans.label, s)
        res += "}"
        return res

def ssc(nfa: FSA):
    toCheck = []

    start = Node(label='{%s}' % nfa.start.label, data={nfa.start})
    dfa = FSA(start)
    dfa.DFA = True
    toCheck.append(start)

    # garbage = Node(label='{} [GARBAGE]', data=set())
    # toCheck.append(garbage)
    # dfa.nodes.append(garbage)

    while len(toCheck) > 0:
        prevNode = toCheck.pop(0)
        elements = prevNode.data

        for character in nfa.alphabet:
            newElements = set()
            for elem in elements:
                newElements |= elem.followAll(character)

            if len(newElements) == 0: continue

            found = False
            for n in dfa.nodes:
                if n.data == newElements:
                    prevNode.addTransition(n, character)
                    found = True
                    break
            if found:
                continue

            isAccept = any([n.final for n in newElements])

            newNode = Node(label = '{%s}' % ", ".join([ne.label for ne in newElements]),final=isAccept, data=newElements)
            dfa.nodes.append(newNode)
            prevNode.addTransition(newNode, character)
            toCheck.append(newNode)

    return dfa


