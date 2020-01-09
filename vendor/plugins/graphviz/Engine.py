"""The Graphviz rendering engine for the Graphviz plugin.

Author: Randy Paredis
Date:   01/09/2020
"""
import graphviz
from main.extra.IOHandler import IOHandler

Config = IOHandler.get_preferences()

def convert(text: str):
    dot = graphviz.Source(text, engine=Config.value("plugin/graphviz/engine"))
    return dot.pipe(Config.value("plugin/graphviz/format"), Config.value("plugin/graphviz/renderer"),
                    Config.value("plugin/graphviz/formatter"))
