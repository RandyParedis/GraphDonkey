"""Mark as module for PyTest."""

def left(string, seq=(' ', '\t', '\r', '\n')):
    res = ""
    for c in string:
        if c in seq:
            res += c
        else:
            break
    return res

def right(string, seq=(' ', '\t', '\r', '\n')):
    return left(reversed(string), seq)


import xml.etree.cElementTree as et

def isSVG(bdata):
    tag = None
    try:
        parser = et.XMLPullParser(["start"])
        parser.feed(bdata)
        for event, el in parser.read_events():
            tag = el.tag
            break
    except et.ParseError:
        pass
    return tag == '{http://www.w3.org/2000/svg}svg'


from graphviz import Source
from PyQt5 import QtGui

def dotToQPixmap(dot: Source, format: str, renderer: str, formatter: str):
    bdata = dot.pipe(format, renderer, formatter)
    image = QtGui.QImage()
    image.loadFromData(bdata)
    return QtGui.QPixmap.fromImage(image)

import os

def tabPathnames(names: list, skip=('undefined',)):
    splitnames = [name.split(os.path.sep) for name in names]
    mx = max([len(name) for name in splitnames])

    tabs = {}

    for s in skip:
        i = -1
        for o in range(names.count(s)):
            i = names.index(s, i+1)
            tabs[i] = s

    for i in range(mx):
        newnames = [os.path.sep.join(name[-i-1:]) for name in splitnames]
        for n1 in range(len(newnames)):
            if n1 in tabs:
                continue
            fnd = False
            for n2 in range(len(newnames)):
                if n1 == n2 or n2 in tabs:
                    continue
                if newnames[n1] == newnames[n2]:
                    fnd = True
                    break
            if not fnd:
                tabs[n1] = newnames[n1]

    nlist = names[:]
    for idx in tabs:
        nlist[idx] = tabs[idx]

    return nlist

from graphviz import Digraph

def delNodes(dot: Digraph, nodeNames: list):
    tr = []
    for i in range(len(dot.body)):
        line = dot.body[i]
        if "--" not in line or "->" not in line:
            l = line.strip().split(" ")
            if l[0] in nodeNames:
                tr.append(i)

    tr = sorted(tr, reverse=True)
    for i in tr:
        dot.body.pop(i)
