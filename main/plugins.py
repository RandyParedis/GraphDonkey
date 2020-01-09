"""Handles all that has to do with plugins.

The Plugin class is a representation of a single plugin.
The PluginLoader loads a list of all plugins

Author: Randy Paredis
Date:   09/01/2020
"""
from main.extra.IOHandler import IOHandler
from main.editors.Parser import Parser
from main.editors.Highlighter import BaseHighlighter
import os

class Plugin:
    def __init__(self, filename):
        self.filename = filename
        self._dir = IOHandler.directory(self.filename)
        self.name = ""
        self.description = ""
        self.types = {}
        self.enabled = True
        self.load()

    def path(self, *paths):
        return IOHandler.join(self._dir, *paths)

    def load(self):
        self.name = ""
        self.description = ""
        self.types = {}

        _locals = {}
        exec(open(self.filename).read(), {}, _locals)

        if '__doc__' in _locals:
            doc = _locals['__doc__'].split('\n')
            if isinstance(doc, list) and len(doc) > 0:
                self.name = doc.pop(0)
                idx = 0
                for i in range(len(doc)):
                    if doc[i] != "":
                        idx = i
                        break
                p = doc.pop()
                while p == "":
                    p = doc.pop()
                else:
                    doc.append(p)
                self.description = "\n".join(doc[idx:])
        if "TYPES" in _locals:
            self.types = _locals["TYPES"]
            for t in self.types:
                if "grammar" in self.types[t]:
                    self.types[t]["grammar"] = self.path(self.types[t]["grammar"])

    def enable(self, on=True):
        self.enabled = on

    def disable(self, off=True):
        self.enabled = not off

    def getParser(self, typeid):
        if typeid in self.types:
            tp = self.types[typeid]
            parser = Parser(tp.get("grammar", ""), tp.get("parser", "lalr"))
            parser.converter = tp.get("converter", {})
            visitor = self.getVisitorClass(typeid)
            if visitor is not None:
                parser.visitor = visitor(parser)
            return parser
        return None

    def getHighlighter(self, typeid, parent=None, editor=None):
        if typeid in self.types:
            tp = self.types[typeid]
            highlighter = BaseHighlighter(parent, editor)
            highlighter.setRules(tp.get("highlighting", []))
            parser = self.getParser(typeid)
            if parser is not None:
                highlighter.parser = parser
            return highlighter
        return None

    def getVisitorClass(self, typeid):
        if typeid in self.types:
            tp = self.types[typeid]
            visitor = tp.get("semantics", None)
            if visitor is not None:
                return visitor
        return None

    def typeName(self, typeid):
        return self.types.get(typeid, {}).get("name", "")

    def getFileTypes(self):
        res = {}
        for t in self.types:
            res[t] = (self.types[t].get("name", "???"), lambda p, e, tp=t: self.getHighlighter(tp, p, e))
        return res

    def convert(self, text, parser, typeid):
        if typeid in self.types:
            tp = self.types[typeid]
            T = parser.parse(text)
            # TODO
            engine = "DOT"
            return tp["converter"][engine](text, T)
        return text

    def __repr__(self):
        return "Plugin <%s, %s>" % (self.name, self.enabled)


class PluginLoader:
    def __init__(self):
        self.plugins = {}
        self.load()

    def load(self):
        self.plugins.clear()
        for filename in os.listdir(IOHandler.dir_plugins()):
            dname = IOHandler.dir_plugins(filename)
            if os.path.isdir(dname):
                plugin = Plugin(IOHandler.join(dname, "__init__.py"))
                self.plugins[plugin.name] = plugin

    def get(self, active=True):
        if active:
            return [self.plugins[p] for p in self.plugins if self.plugins[p].enabled]
        else:
            return self.plugins

    def getFileTypes(self, active=True):
        res = { "": ("No File Type", BaseHighlighter) }
        ps = self.get(active)
        for p in ps:
            res.update(p.getFileTypes())
        return res

if __name__ == '__main__':
    from main.extra.IOHandler import IOHandler

    pl = PluginLoader()
    print("Enabled Plugins:", pl.get())
