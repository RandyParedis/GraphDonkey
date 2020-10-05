"""PlantUML

Render graphs following the PlantUML syntax.

PlantUML is a component that allows to quickly write numerous diagrams.

Author:         Randy Paredis
Website:        https://plantuml.com/
Requires:       Obviously, this requires the `graphviz` package.
Documentation:  https://github.com/RandyParedis/GraphDonkey/wiki/Graphviz
"""

from vendor.plugins.plantuml.Engine import convert, syntax

ICON = "icon.png"

TYPES = {
    "PlantUML": {
        "extensions": ["puml", "pu", "plantuml"],
        "parser": syntax,
        "highlighting": [],
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
        "convert": convert
    }
}
