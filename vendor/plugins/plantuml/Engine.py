"""The PlantUML rendering engine for the PlantUML plugin.

Author: Randy Paredis
Date:   10/05/2020
"""
import subprocess

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
    if text not in _CONV_CACHE:
        contents = text.encode("ascii")
        _SYN_CACHE[text] = subprocess.run(["plantuml", "-syntax"], input=contents,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if len(_SYN_CACHE[text].stderr) > 0:
        errs = _SYN_CACHE[text].stdout.decode("utf-8").split("\n")[1:]
        return [(int(errs[0]), errs[1])]
    return []
