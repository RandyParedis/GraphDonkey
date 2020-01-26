"""Handles all that has to do with plugins.

The Plugin class is a representation of a single plugin.
The PluginLoader loads a list of all plugins

Author: Randy Paredis
Date:   01/09/2020
"""
from main.extra.IOHandler import IOHandler
from main.editor.Parser import Parser
from main.editor.Highlighter import BaseHighlighter
import os

class Plugin:
    def __init__(self, filename):
        self.filename = filename
        self._dir = IOHandler.directory(self.filename)
        self.name = ""
        self.description = ""
        self.attrs = []
        self.icon = ""
        self.types = {}
        self.engines = {}
        self.preferences = {}
        self.enabled = True
        self.load()

    def path(self, *paths):
        return IOHandler.join(self._dir, *paths)

    def load(self):
        self.name = ""
        self.description = ""
        self.icon = ""
        self.attrs.clear()
        self.types.clear()
        self.engines.clear()

        _locals = {}
        exec(open(self.filename).read(), {}, _locals)

        doc = _locals['__doc__'].splitlines()
        if isinstance(doc, list) and len(doc) > 0:
            self.name = doc.pop(0)
            idx = 0
            for i in range(len(doc)):
                if doc[i] != "":
                    idx = i
                    break
            for p in reversed(doc):
                if ":" in p:
                    k, v = p.split(":", 1)
                    self.attrs.append((k.strip(), v.strip()))
                    doc.pop()
                elif p != "":
                    break
                else:
                    doc.pop()
            self.attrs.reverse()
            for i in range(len(self.attrs) - 1, -1, -1):
                if i > 0:
                    k, v = self.attrs[i]
                    if k == "":
                        kp, vp = self.attrs[i-1]
                        self.attrs[i-1] = kp, vp + " " + v
                        self.attrs.pop(i)

            self.description = "\n".join(doc[idx:])
        if "TYPES" in _locals:
            self.types = _locals["TYPES"]
            for t in self.types:
                if "grammar" in self.types[t]:
                    self.types[t]["grammar"] = self.path(self.types[t]["grammar"])
        if "ENGINES" in _locals:
            self.engines = _locals["ENGINES"]
        if "ICON" in _locals:
            self.icon = self.path(_locals["ICON"])

    def enable(self, on=True):
        self.enabled = on

    def disable(self, off=True):
        self.enabled = not off

    def getParser(self, typeid):
        if typeid in self.types:
            tp = self.types[typeid]
            parser = Parser(tp.get("grammar", ""), tp.get("parser", "earley"))
            parser.converter = tp.get("transformer", {})
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
            return tp.get("semantics", None)
        return None

    def getFileTypes(self):
        res = {}
        for t in self.types:
            res[t] = (t, lambda p, e, tp=t: self.getHighlighter(tp, p, e))
        return res

    def getPreferencesUi(self, engineid):
        prefs = self.engines[engineid].get("preferences", {})
        klass = prefs.get("class", None)
        if klass is not None:
            return klass(self.path(prefs["file"]))
        return None

    def __repr__(self):
        return "Plugin <%s, %s>" % (self.name, self.enabled)


class PluginLoader:
    _instance = None
    @staticmethod
    def instance():
        if PluginLoader._instance is None:
            PluginLoader._instance = PluginLoader()
        return PluginLoader._instance

    def __init__(self):
        self.plugins = {}
        self.load()

    def load(self, failOnDuplicate=False):
        self.plugins.clear()
        for filename in os.listdir(IOHandler.dir_plugins()):
            dname = IOHandler.dir_plugins(filename)
            if os.path.isdir(dname):
                plugin = Plugin(IOHandler.join(dname, "__init__.py"))
                if len(plugin.name) == 0:
                    raise KeyError("Plugin name cannot be empty!")
                elif plugin.name not in self.plugins:
                    self.plugins[plugin.name] = plugin
                elif failOnDuplicate:
                    raise KeyError("Duplicate plugin name found: %s!" % plugin.name)

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

    def getFileExtensions(self, active=True):
        res = {}
        ps = self.get(active)
        for p in ps:
            for t in p.types:
                res[t] = p.types[t].get("extensions", [])
        return res

    def getEngines(self, active=True):
        res = {}
        ps = self.get(active)
        for p in ps:
            res.update(p.engines)
        return res

    def getEnginesForFileType(self, filetype, active=True):
        en = []
        ps = self.get(active)
        ens = set(self.getEngines(active))
        for p in ps:
            if filetype in p.types:
                ta = p.types[filetype].get("transformer", {})
                ta = set(ta).intersection(ens)
                if len(ta) > 0:
                    en.append(list(ta))
        return [i for s in en for i in s]


from PyQt5 import QtWidgets, uic

class Settings(QtWidgets.QGroupBox):
    def __init__(self, pathname, parent=None):
        super(Settings, self).__init__(parent)
        uic.loadUi(pathname, self)
        self.preferences = None
        self.plugin = None

    def apply(self):
        raise NotImplementedError()

    def rectify(self):
        raise NotImplementedError()


if __name__ == '__main__':
    from main.extra.IOHandler import IOHandler

    pl = PluginLoader()
    print("Enabled Plugins:", pl.get())
