"""The PlantUML rendering engine for the PlantUML plugin.

Author: Randy Paredis
Date:   10/05/2020
"""
from main.Preferences import bool
from main.extra.IOHandler import IOHandler
import subprocess

Config = IOHandler.get_preferences()

_CONV_CACHE = {}
def convert(text: str):
    # TODO: change to execution of jar / allow user to set commands
    if text not in _CONV_CACHE:
        contents = text.encode("ascii")
        process = subprocess.run(["plantuml", "-tsvg", "-p"], input=contents,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _CONV_CACHE[text] = process.stdout
    return _CONV_CACHE[text]

_SYN_CACHE = {}
def syntax(text: str):
    if bool(Config.value("plugin/plantuml/highlight", False)):
        if text not in _CONV_CACHE:
            contents = text.encode("ascii")
            _SYN_CACHE[text] = subprocess.run(["plantuml", "-syntax"], input=contents, stdout=subprocess.PIPE)
        errs = _SYN_CACHE[text].stdout.decode("utf-8").split("\n")
        if errs[0] == "ERROR":
            errs = errs[1:]
            return [(int(errs[0]), errs[1])]
    return []
