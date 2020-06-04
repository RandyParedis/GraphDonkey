"""Handles all that has to do with plugins.

The Plugin class is a representation of a single plugin.
The PluginLoader loads a list of all plugins

Author: Randy Paredis
Date:   01/09/2020
"""
from main.extra.IOHandler import IOHandler
from main.editor.Parser import Parser
from main.editor.Highlighter import BaseHighlighter
import sys, ast

_ioh = IOHandler

def command(cmd):
    if sys.platform == 'linux':
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    if sys.platform == 'win32':
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)

class Plugin:
    def __init__(self, filename):
        self.filename = filename
        self._dir = IOHandler.directory(self.filename)
        self.requirements = set()
        self.name = ""
        self.description = ""
        self.attrs = []
        self.icon = ""
        self.types = {}
        self.engines = {}
        self.preferences = {}
        self.enabled = True
        self.deps = True
        self.reqs = True
        self.load()

    def path(self, *paths):
        return IOHandler.join(self._dir, *paths)

    def load(self):
        self.name = ""
        self.description = ""
        self.icon = ""
        self.requirements.clear()
        self.attrs.clear()
        self.types.clear()
        self.engines.clear()
        self.deps = True

        rf = os.path.join(self._dir, "requirements.txt")
        if os.path.isfile(rf):
            with open(rf, 'r') as reqs:
                self.requirements = set([x for x in reqs.read().split("\n") if "#" not in x and len(x) > 0])

        _locals = {}
        with open(self.filename) as file:
            contents = file.read()

        module = ast.parse(contents)
        doc = ast.get_docstring(module)
        if doc is None:
            doc = ""
        _locals['__doc__'] = doc

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

        try:
            exec(open(self.filename).read(), {}, _locals)
            if "TYPES" in _locals:
                self.types = _locals["TYPES"]
                for t in self.types:
                    if "grammar" in self.types[t]:
                        self.types[t]["grammar"] = self.path(self.types[t]["grammar"])
            if "ENGINES" in _locals:
                self.engines = _locals["ENGINES"]
            if "ICON" in _locals:
                self.icon = self.path(_locals["ICON"])
        except ImportError as e:
            # TODO: Show Error Message
            self.disable()
            self.deps = False

    def enable(self, on=True):
        self.enabled = on

    def disable(self, off=True):
        self.enabled = not off

    def getParser(self, typeid):
        if typeid in self.types:
            tp = self.types[typeid]
            parser = Parser(tp.get("grammar", ""), tp.get("parser", "earley"))
            parser.transformer = tp.get("transformer", {})
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


from main.extra import Constants

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

    def reload(self):
        for p in self.get(False):
            p.load()

    def load(self, failOnDuplicate=False):
        self.plugins.clear()
        for filename in os.listdir(IOHandler.dir_plugins()):
            if filename == ".dependencies":
                continue
            dname = IOHandler.dir_plugins(filename)
            if os.path.isdir(dname):
                plugin = Plugin(IOHandler.join(dname, "__init__.py"))
                if len(plugin.name) == 0:
                    continue
                elif plugin.name not in self.plugins:
                    self.plugins[plugin.name] = plugin
                elif failOnDuplicate:
                    raise KeyError("Duplicate plugin name found: %s!" % plugin.name)

    def get(self, active=True):
        if active:
            return [self.plugins[p] for p in self.plugins if self.plugins[p].enabled]
        else:
            return self.plugins.values()

    def getPlugin(self, name: str):
        return self.plugins.get(name, None)

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

    def getPairedBrackets(self, filetype, active=True):
        types = {}
        for d in [x.types for x in self.get(active)]:
            types.update(d)
        return types.get(filetype, {}).get("paired", Constants.BRACKETS)


from PyQt5 import QtWidgets, QtCore, uic

class Settings(QtWidgets.QGroupBox):
    def __init__(self, pathname, parent=None):
        super(Settings, self).__init__(parent)
        uic.loadUi(pathname, self)
        self.preferences = None
        self.plugin = None
        self.check()

    def check(self):
        """Allows for checking the system validity needed for this plugin."""
        pass

    def apply(self):
        raise NotImplementedError()

    def rectify(self):
        raise NotImplementedError()


import subprocess, os
from main.extra.Threading import WorkerThread, time

class PluginInstaller(QtWidgets.QDialog):
    installed = QtCore.pyqtSignal(bool)

    def __init__(self, plugin, update=False, parent=None):
        super(PluginInstaller, self).__init__(parent)
        uic.loadUi(IOHandler.dir_ui("PluginInstaller.ui"), self)
        self.plugin = plugin
        self.upd = update
        self.main.setText("Installing all requirements for the plugin <b>%s</b>.<br/>" % self.plugin.name)
        self.cmd = ["python3", "-m", "pip"]
        self.depfol = IOHandler.dir_plugins(".dependencies")
        self.success = False
        self.thread = WorkerThread(self.run)
        self.thread.finished.connect(self.end)
        self.freeze()

    def freeze(self):
        """Loads all requirements that are already installed."""
        out = command(self.cmd + ["freeze"]).decode("utf-8").split(os.linesep)
        if os.path.isdir(self.depfol):
            out += command(self.cmd + ["freeze", "--path", self.depfol]).decode("utf-8").split(os.linesep)
        return set(out)

    def reject(self):
        if self.thread.isRunning():
            self.thread.terminate()
        QtWidgets.QDialog.reject(self)

    def exec_(self):
        self.thread.start()
        QtWidgets.QDialog.exec_(self)

    def run(self):
        self.progress.reset()
        try:
            self.info.setText("Obtaining requirements...")
            time.sleep(0.01)
            req = self.plugin.requirements - self.freeze()
            lr = len(req)
            if lr != 0:
                self.connection()
                i = 0
                for r in req:
                    self.install(r)
                    i += 1
                    self.progress.setValue(i // lr)
                    time.sleep(0.01)
                self.info.setText("Installed all requirements.")
            else:
                self.info.setText("All requirements were already satisfied.")
            time.sleep(0.01)
            self.progress.setValue(100)
            self.success = True
        except Exception as e:
            # TODO: show error message
            self.success = False

    def end(self):
        self.installed.emit(self.success)
        self.pb_cancel.setText("Finish")
        self.repaint()

    def connection(self):
        self.info.setText("Waiting for a valid internet connection...")

    def install(self, req):
        self.info.setText("Installing %s..." % req)
        cmd = self.cmd + ["install", req, '-t', IOHandler.dir_plugins(self.depfol)]
        if not self.upd:
            cmd += ["--upgrade"]
        subprocess.check_call(cmd)


if __name__ == '__main__':
    from main.extra.IOHandler import IOHandler

    pl = PluginLoader()
    print("Enabled Plugins:", pl.get())
