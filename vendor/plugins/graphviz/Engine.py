"""The Graphviz rendering engine for the Graphviz plugin.

Author: Randy Paredis
Date:   01/09/2020
"""
import graphviz
from main.extra.IOHandler import IOHandler
from PyQt5 import QtWidgets
import subprocess

Config = IOHandler.get_preferences()

def convert(text: str):
    dot = graphviz.Source(text, engine=Config.value("plugin/graphviz/engine"))
    return dot.pipe(Config.value("plugin/graphviz/format"), Config.value("plugin/graphviz/renderer"),
                    Config.value("plugin/graphviz/formatter"))

def export(text: str, extension: str):
    try:
        cmd = [Config.value("plugin/graphviz/engine"), "-T%s:" % extension]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        fmts = e.output.decode("utf-8").replace("\n", "") \
            [len('Format: "%s:" not recognized. Use one of: ' % extension):].split(" ")
        items = sorted(list(set(fmts)))
        if len(items) == 1:
            ok = True
            value = items[0]
        else:
            value, ok = QtWidgets.QInputDialog.getItem(None, "Export Options", "Please pick your renderer/formatter:",
                                                   items, 0, False)
        if ok:
            _, renderer, formatter = value.split(":")
            dot = graphviz.Source(text, engine=Config.value("plugin/graphviz/engine"))
            return dot.pipe(extension, renderer, formatter)
    return None
