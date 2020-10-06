"""Loads the preferences for this plugin.

Author: Randy Paredis
Date:   10/06/2020
"""
from main.plugins import Settings
from main.Preferences import bool

class PlantUMLSettings(Settings):
    # def check(self):
    #     cmd = [self.combo_engine.currentText(), "-V"]
    #     try:
    #         command(cmd)
    #     except subprocess.CalledProcessError as e:
    #         if e.returncode != 0:
    #             raise RuntimeError("It seems Graphviz package is not installed on your system, but"
    #                                " is required when using this plugin. Take a look at "
    #                                "<a href='https://graphviz.gitlab.io/download/'>the Graphviz download page</a> "
    #                                "to learn more on how to install it.")

    def apply(self):
        self.preferences.setValue("highlight", self.check_highlight.isChecked())

    def rectify(self):
        self.check_highlight.setChecked(bool(self.preferences.value("highlight", self.check_highlight.isChecked())))
