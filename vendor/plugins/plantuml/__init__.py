"""PlantUML

Render graphs following the PlantUML syntax.

PlantUML is a component that allows to quickly write numerous diagrams.

Author:         Randy Paredis
Website:        https://plantuml.com/
Requires:       The `plantuml` command to be available.
"""

from vendor.plugins.plantuml.Engine import convert, syntax
from vendor.plugins.plantuml.Settings import PlantUMLSettings
from main.extra import Constants

# TODO: custom preferences -- command for plantuml (i.e. jar location)

ICON = "icon.png"

keywords = [
    "actor", "boundary", "control", "entity", "database", "collections", "participant",
    "alt", "else", "opt", "loop", "par", "break", "critical", "group", "note", "hnote", "rnote",
    "skinparam", "autonumber", "header", "footer", "title", "newpage", "end", "ref", "Title",
    "activate", "deactivate", "return", "create", "box", "hide", "colors", "help", "show",
    "usecase", "package", "rectangle", "class", "enum", "abstract", "interface", "annotation",
    "scale", "namespace", "set", "start", "stop", "several", "if", "then", "else", "endif", "elseif",
    "repeat", "while", "endwhile", "fork", "detatch", "partition", "endfork", "split", "legend", "caption",
    "component", "cloud", "frame", "folder", "node", "sprite", "state", "object", "agent", "artifact",
    "card", "file", "label", "queue", "stack", "storage", "robust", "concise", "clock", "binary",
    "nwdiag", "network", "inet", "listopeniconic", "archimate", "listsprite", "Project", "projectscale",
    "task", "milestone", "wbsDiagram", "Linecolor", "arrow"
]

attributes = [
    "right", "of", "over", "left", "footbox", "center", "true", "false", "to", "up", "down", "none",
    "link", "empty", "members", "fields", "circle", "attributes", "stereotype", "extends", "width",
    "direction", "backward", "again", "as", "height", "is", "with", "period", "lasts", "days", "starts",
    "ends", "at", "in", "happens", "links", "on"
]

TYPES = {
    "PlantUML": {
        "extensions": ["puml", "pu", "plantuml"],
        "parser": syntax,
        "highlighting": [
            {
                "regex": keywords,
                "format": "keyword"
            },
            {
                "regex": attributes,
                "format": "attribute"
            },
            {
                "regex": "<<.*?>>",
                "format": "string"
            },
            {
                "regex": {
                    "pattern": r'".*?"',
                    "single": True
                },
                "format": "string",
                "global": True
            },
            {
                "regex": "\\b(\\+|-)?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b",
                "format": "number"
            },
            {
                "regex": "#([0-9a-f]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3}|[a-zA-Z]+)(?!\\d)",
                "format": "number"
            },
            {
                "regex": r"%[a-zA-Z]+?%",
                "format": "number"
            },
            {
                "regex": "==[a-zA-Z ]+==$",
                "format": "note"
            },
            {
                "regex": "([_=~.-]{2})(.*?(?1))?$",
                "format": "note"
            },
            {
                "regex": "^[.]{3}(.+?[.]{3})?$",
                "format": "note"
            },
            {
                "regex": "^([|]{3})|([|]{2}[1-9][0-9]*[|]{2})$",
                "format": "note"
            },
            {
                "regex": "^![^%s]*$" % Constants.LINE_ENDING,
                "format": "hash"
            },
            {
                "regex": "^@[^%s]*$" % Constants.LINE_ENDING,
                "format": "hash"
            },
            {
                "regex": "^'[^%s]*$" % Constants.LINE_ENDING,
                "format": "comment"
            },
            {
                "regex": "//[^%s]*$" % Constants.LINE_ENDING,
                "format": "comment"
            },
            {
                "regex": {
                    "pattern": "/'.*?'/",
                    "single": True
                },
                "format": "comment",
                "global": True
            }
        ],
        "transformer": {
            "PlantUML": lambda x, T: x
        },
        "paired": [
            ("{", "}"), ("[", "]"), ("(", ")"), ('"', '"')
        ],
        "comments": {
            "symbol": "'",
            "indent": False
        }
    }
}

ENGINES = {
    "PlantUML": {
        "convert": convert,
        "preferences": {
            "file": "preferences.ui",
            "class": PlantUMLSettings
        },
    }
}
