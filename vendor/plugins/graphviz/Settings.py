"""Loads the preferences for this plugin.

Author: Randy Paredis
Date:   01/09/2020
"""
from main.plugins import Settings
import subprocess

class GraphvizSettings(Settings):
    def __init__(self, pathname, parent=None):
        super(GraphvizSettings, self).__init__(pathname, parent)
        self.setUp()

    def check(self):
        cmd = [self.combo_engine.currentText(), "-V"]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            if e.returncode != 0:
                raise RuntimeError("It seems Graphviz package is not installed on your system, but"
                                   " is required when using this plugin. Take a look at "
                                   "<a href='https://graphviz.gitlab.io/download/'>the Graphviz download page</a> "
                                   "to learn more on how to install it.")

    def setUp(self):
        self.combo_engine.currentTextChanged.connect(lambda x: self.setGraphvizRenderer())
        self.combo_format.currentTextChanged.connect(lambda x: self.setGraphvizRenderer())
        self.combo_renderer.currentTextChanged.connect(lambda x: self.setGraphvizFormatter())
        cmd = [self.combo_engine.currentText(), "-T:"]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            self.combo_format.clear()
            fmts = e.output.decode("utf-8").replace("\n", "")[len('Format: ":" not recognized. Use one of: '):] \
                .split(" ")
            fmts = [f.split(":")[0] for f in fmts]
            for f in ["gif", "jpe", "jpeg", "jpg", "png", "svg", "svgz", "wbmp"]:
                if f in fmts:
                    self.combo_format.addItem(f)
            self.setGraphvizRenderer()

    def setGraphvizRenderer(self):
        fmt = self.combo_format.currentText()
        cmd = [self.combo_engine.currentText(), "-T%s:" % fmt]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            self.setGraphviz(e, fmt, 1, self.combo_renderer)
            self.setGraphvizFormatter()

    def setGraphvizFormatter(self):
        fmt = self.combo_format.currentText()
        cmd = [self.combo_engine.currentText(), "-T%s:" % fmt]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            self.setGraphviz(e, fmt, 2, self.combo_formatter,
                             lambda f: f.split(":")[1] == self.combo_renderer.currentText())

    @staticmethod
    def setGraphviz(e, fmt, idx, field, cond=lambda x: True):
        fmts = e.output.decode("utf-8").replace("\n", "")[len('Format: "%s:" not recognized. Use one of: ' % fmt):] \
            .split(" ")
        fmts = sorted(list(set(f.split(":")[idx] for f in fmts if cond(f))))
        field.clear()
        for fmt in fmts:
            field.addItem(fmt)

    def apply(self):
        self.preferences.setValue("format", self.combo_format.currentText())
        self.preferences.setValue("engine", self.combo_engine.currentText())
        self.preferences.setValue("renderer", self.combo_renderer.currentText())
        self.preferences.setValue("formatter", self.combo_formatter.currentText())

    def rectify(self):
        self.combo_engine.setCurrentText(self.preferences.value("engine", "dot"))
        self.combo_format.setCurrentText(self.preferences.value("format", "svg"))
        self.combo_renderer.setCurrentText(self.preferences.value("renderer", "svg"))
        self.combo_formatter.setCurrentText(self.preferences.value("formatter", "core"))
