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

    def setUp(self):
        self.combo_engine.currentTextChanged.connect(lambda x: self.setGraphvizRenderer())
        self.combo_format.currentTextChanged.connect(lambda x: self.setGraphvizRenderer())
        self.combo_renderer.currentTextChanged.connect(lambda x: self.setGraphvizFormatter())
        cmd = [self.combo_engine.currentText(), "-T:"]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
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
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self._setGraphviz(e, fmt, 1, self.combo_renderer)
            self.setGraphvizFormatter()

    def setGraphvizFormatter(self):
        fmt = self.combo_format.currentText()
        cmd = [self.combo_engine.currentText(), "-T%s:" % fmt]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self._setGraphviz(e, fmt, 2, self.combo_formatter,
                              lambda f: f.split(":")[1] == self.combo_renderer.currentText())

    def _setGraphviz(self, e, fmt, idx, field, cond=lambda x: True):
        fmts = e.output.decode("utf-8").replace("\n", "")[len('Format: "%s:" not recognized. Use one of: ' % fmt):] \
            .split(" ")
        fmts = sorted(list(set(f.split(":")[idx] for f in fmts if cond(f))))
        field.clear()
        for fmt in fmts:
            field.addItem(fmt)

    def apply(self):
        self.preferences.setValue("plugin/graphviz/format", self.combo_format.currentText())
        self.preferences.setValue("plugin/graphviz/engine", self.combo_engine.currentText())
        self.preferences.setValue("plugin/graphviz/renderer", self.combo_renderer.currentText())
        self.preferences.setValue("plugin/graphviz/formatter", self.combo_formatter.currentText())

    def rectify(self):
        self.combo_engine.setCurrentText(self.preferences.value("plugin/graphviz/engine", "dot"))
        self.combo_format.setCurrentText(self.preferences.value("plugin/graphviz/format", "svg"))
        self.combo_renderer.setCurrentText(self.preferences.value("plugin/graphviz/renderer", "svg"))
        self.combo_formatter.setCurrentText(self.preferences.value("plugin/graphviz/formatter", "core"))
