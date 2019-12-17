"""Preferences window for the GraphDonkey application.

Author: Randy Paredis
Date:   17/12/2019
"""
from PyQt5 import QtWidgets, QtGui, uic
from main.extra.IOHandler import IOHandler


def bool(name: str):
    if name in ["True", "true"]:
        return True
    if name in ["False", "false"]:
        return False
    return name

class Preferences(QtWidgets.QDialog):
    def __init__(self, parent):
        super(Preferences, self).__init__(parent)
        uic.loadUi(IOHandler.dir_ui("Preferences.ui"), self)

        self.preferences = IOHandler.get_preferences()
        self.check_parse.toggled.connect(self.parseDisable)
        self.fillQuickSelect()
        self._setColorPickers()
        self.rectify()

    def parseDisable(self, b):
        if not b:
            self.check_autorender.setChecked(False)

    def fillQuickSelect(self):
        pass

    def _setColorPickers(self):
        names_general = [
            "col_foreground",
            "col_window",
            "col_base",
            "col_alternateBase",
            "col_tooltipBase",
            "col_tooltipText",
            "col_text",
            "col_button",
            "col_buttonText",
            "col_brightText",
            "col_highlight",
            "col_highlightedText",
            "col_link",
            "col_visitedLink"
        ]
        names_editor =[
            "col_cline",
            "col_lnf",
            "col_lnb",
            "col_clnf",
            "col_clnb"
        ]
        names_syntax =[
            "col_keyword",
            "col_attribute",
            "col_number",
            "col_string",
            "col_html",
            "col_comment",
            "col_hash",
            "col_error",
            "col_other"
        ]
        lo = self.box_general.layout()
        for i in range(len(names_general)):
            name = names_general[i]
            setattr(self, name, ColorButton(parent=self))
            lo.addWidget(getattr(self, name), i, 2)

        lo = self.box_editor.layout()
        for i in range(len(names_editor)):
            name = names_editor[i]
            setattr(self, name, ColorButton(parent=self))
            lo.addWidget(getattr(self, name), i, 2)

        lo = self.box_syntax.layout()
        for i in range(len(names_syntax)):
            name = names_syntax[i]
            setattr(self, name, ColorButton(parent=self))
            lo.addWidget(getattr(self, name), i, 2)

    def rectify(self):
        # GENERAL
        self.check_rememberLayout.setChecked(bool(self.preferences.value("rememberLayout", True)))
        if self.preferences.value("restore", 0) == 0:
            self.radio_ws_restore.setChecked(False)
            self.radio_ws_openempty.setChecked(True)
        else:
            self.radio_ws_restore.setChecked(True)
            self.radio_ws_openempty.setChecked(False)
        self.num_recents.setValue(int(self.preferences.value("recents", 5)))

        # EDITOR
        self.check_lineNumbers.setChecked(bool(self.preferences.value("showLineNumbers", True)))
        self.check_highlightLine.setChecked(bool(self.preferences.value("highlightCurrentLine", True)))
        self.check_monospace.setChecked(bool(self.preferences.value("monospace", True)))
        self.num_tabwidth.setValue(int(self.preferences.value("tabwidth", 4)))
        self.check_syntax.setChecked(bool(self.preferences.value("syntaxHighlighting", True)))
        self.check_parse.setChecked(bool(self.preferences.value("useParser", True)))
        self.check_autorender.setChecked(bool(self.preferences.value("autorender", True)))
        self.parseDisable(self.check_parse.isChecked())

        # APPEARANCE
        self.combo_style.setCurrentIndex(int(self.preferences.value("style", 0)))
        self.combo_theme.setCurrentIndex(int(self.preferences.value("theme", 0)))
        self.col_foreground.setColor(QtGui.QColor(self.preferences.value("col.foreground", "#000000")))
        self.col_window.setColor(QtGui.QColor(self.preferences.value("col.window", "#efefef")))
        self.col_base.setColor(QtGui.QColor(self.preferences.value("col.base", "#ffffff")))
        self.col_alternateBase.setColor(QtGui.QColor(self.preferences.value("col.alternateBase", "#f7f7f7")))
        self.col_tooltipBase.setColor(QtGui.QColor(self.preferences.value("col.tooltipBase", "#ffffdc")))
        self.col_tooltipText.setColor(QtGui.QColor(self.preferences.value("col.tooltipText", "#000000")))
        self.col_text.setColor(QtGui.QColor(self.preferences.value("col.text", "#000000")))
        self.col_button.setColor(QtGui.QColor(self.preferences.value("col.button", "#efefef")))
        self.col_buttonText.setColor(QtGui.QColor(self.preferences.value("col.buttonText", "#000000")))
        self.col_brightText.setColor(QtGui.QColor(self.preferences.value("col.brightText", "#dcdcff")))
        self.col_highlight.setColor(QtGui.QColor(self.preferences.value("col.highlight", "#30ecc6")))
        self.col_highlightedText.setColor(QtGui.QColor(self.preferences.value("col.highlightedText", "#ffffff")))
        self.col_link.setColor(QtGui.QColor(self.preferences.value("col.link", "#8be9fd")))
        self.col_visitedLink.setColor(QtGui.QColor(self.preferences.value("col.visitedLink", "#253fe8")))
        self.col_cline.setColor(QtGui.QColor(self.preferences.value("col.cline", "#fffeb5")))
        self.col_lnf.setColor(QtGui.QColor(self.preferences.value("col.lnf", "#000000")))
        self.col_lnb.setColor(QtGui.QColor(self.preferences.value("col.lnb", "#787878")))
        self.col_clnf.setColor(QtGui.QColor(self.preferences.value("col.clnf", "#fffeb5")))
        self.col_clnb.setColor(QtGui.QColor(self.preferences.value("col.clnb", "#3b3b3b")))
        self.col_keyword.setColor(QtGui.QColor(self.preferences.value("col.keyword", "#800000")))
        self.col_attribute.setColor(QtGui.QColor(self.preferences.value("col.attribute", "#000080")))
        self.col_number.setColor(QtGui.QColor(self.preferences.value("col.number", "#ff00ff")))
        self.col_string.setColor(QtGui.QColor(self.preferences.value("col.string", "#00ff00")))
        self.col_html.setColor(QtGui.QColor(self.preferences.value("col.html", "#00ff00")))
        self.col_comment.setColor(QtGui.QColor(self.preferences.value("col.comment", "#0000ff")))
        self.col_hash.setColor(QtGui.QColor(self.preferences.value("col.hash", "#0000ff")))
        self.col_error.setColor(QtGui.QColor(self.preferences.value("col.error", "#ff0000")))
        self.col_other.setColor(QtGui.QColor(self.preferences.value("col.other", "#000000")))

        # SHORTCUTS
        self.ks_new.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.new", "CTRL+N")))
        self.ks_open.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.open", "CTRL+O")))
        self.ks_save.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.save", "CTRL+S")))
        self.ks_save_as.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.save_as", "CTRL+SHIFT+S")))
        self.ks_clear_recents.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.clear_recents", "")))
        self.ks_preferences.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.preferences", "CTRL+P")))
        self.ks_exit.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.exit", "CTRL+Q")))
        self.ks_undo.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.undo", "CTRL+Z")))
        self.ks_redo.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.redo", "CTRL+SHIFT+Z")))
        self.ks_select_all.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.select_all", "CTRL+A")))
        self.ks_delete.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.delete", "")))
        self.ks_copy.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.copy", "CTRL+C")))
        self.ks_cut.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.cut", "CTRL+X")))
        self.ks_paste.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.paste", "CTRL+V")))
        self.ks_toggleCodeEditor.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.toggle_editor", "")))
        self.ks_render.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.render", "CTRL+R,CTRL+Return")))
        self.ks_updates.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.updates", "")))
        self.ks_graphDonkey.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.graphDonkey", "")))
        self.ks_graphviz.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.graphviz", "")))
        self.ks_qt.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks.qt", "")))

    def apply(self):
        # GENERAL
        self.preferences.setValue("rememberLayout", self.check_rememberLayout.isChecked())
        if self.radio_ws_openempty.isChecked():
            self.preferences.setValue("restore", 0)
        else:
            self.preferences.setValue("restore", 1)
        self.preferences.setValue("recents", self.num_recents.value())

        # EDITOR
        self.preferences.setValue("showLineNumbers", self.check_lineNumbers.isChecked())
        self.preferences.setValue("highlightCurrentLine", self.check_highlightLine.isChecked())
        self.preferences.setValue("monospace", self.check_monospace.isChecked())
        self.preferences.setValue("tabwidth", self.num_tabwidth.value())
        self.preferences.setValue("syntaxHighlighting", self.check_syntax.isChecked())
        self.preferences.setValue("useParser", self.check_parse.isChecked())
        self.preferences.setValue("autorender", self.check_autorender.isChecked())

        # APPEARANCE
        self.preferences.setValue("style", self.combo_style.currentIndex())
        self.preferences.setValue("theme", self.combo_theme.currentIndex())
        self.preferences.setValue("col.foreground", self.col_foreground.colorName())
        self.preferences.setValue("col.window", self.col_window.colorName())
        self.preferences.setValue("col.base", self.col_base.colorName())
        self.preferences.setValue("col.alternateBase", self.col_alternateBase.colorName())
        self.preferences.setValue("col.tooltipBase", self.col_tooltipBase.colorName())
        self.preferences.setValue("col.tooltipText", self.col_tooltipText.colorName())
        self.preferences.setValue("col.text", self.col_text.colorName())
        self.preferences.setValue("col.button", self.col_button.colorName())
        self.preferences.setValue("col.buttonText", self.col_buttonText.colorName())
        self.preferences.setValue("col.brightText", self.col_brightText.colorName())
        self.preferences.setValue("col.highlight", self.col_highlight.colorName())
        self.preferences.setValue("col.link", self.col_link.colorName())
        self.preferences.setValue("col.visitedLink", self.col_visitedLink.colorName())
        self.preferences.setValue("col.cline", self.col_cline.colorName())
        self.preferences.setValue("col.lnf", self.col_lnf.colorName())
        self.preferences.setValue("col.lnb", self.col_lnb.colorName())
        self.preferences.setValue("col.clnf", self.col_clnf.colorName())
        self.preferences.setValue("col.clnb", self.col_clnb.colorName())
        self.preferences.setValue("col.keyword", self.col_keyword.colorName())
        self.preferences.setValue("col.attribute", self.col_attribute.colorName())
        self.preferences.setValue("col.number", self.col_number.colorName())
        self.preferences.setValue("col.string", self.col_string.colorName())
        self.preferences.setValue("col.html", self.col_html.colorName())
        self.preferences.setValue("col.comment", self.col_comment.colorName())
        self.preferences.setValue("col.hash", self.col_hash.colorName())
        self.preferences.setValue("col.error", self.col_error.colorName())
        self.preferences.setValue("col.other", self.col_other.colorName())

        # SHORTCUTS
        self.preferences.setValue("ks.new", self.ks_new.keySequence().toString())
        self.preferences.setValue("ks.open", self.ks_open.keySequence().toString())
        self.preferences.setValue("ks.save", self.ks_save.keySequence().toString())
        self.preferences.setValue("ks.save_as", self.ks_save_as.keySequence().toString())
        self.preferences.setValue("ks.clear_recents", self.ks_clear_recents.keySequence().toString())
        self.preferences.setValue("ks.preferences", self.ks_preferences.keySequence().toString())
        self.preferences.setValue("ks.exit", self.ks_exit.keySequence().toString())
        self.preferences.setValue("ks.undo", self.ks_undo.keySequence().toString())
        self.preferences.setValue("ks.redo", self.ks_redo.keySequence().toString())
        self.preferences.setValue("ks.select_all", self.ks_select_all.keySequence().toString())
        self.preferences.setValue("ks.delete", self.ks_delete.keySequence().toString())
        self.preferences.setValue("ks.copy", self.ks_copy.keySequence().toString())
        self.preferences.setValue("ks.cut", self.ks_cut.keySequence().toString())
        self.preferences.setValue("ks.paste", self.ks_paste.keySequence().toString())
        self.preferences.setValue("ks.toggle_editor", self.ks_toggleCodeEditor.keySequence().toString())
        self.preferences.setValue("ks.render", self.ks_render.keySequence().toString())
        self.preferences.setValue("ks.updates", self.ks_updates.keySequence().toString())
        self.preferences.setValue("ks.graphDonkey", self.ks_graphDonkey.keySequence().toString())
        self.preferences.setValue("ks.graphviz", self.ks_graphviz.keySequence().toString())
        self.preferences.setValue("ks.qt", self.ks_qt.keySequence().toString())


class ColorButton(QtWidgets.QPushButton):
    def __init__(self, color=None, parent=None):
        QtWidgets.QPushButton.__init__(self, parent)
        if color:
            self.setColor(color)
        self.clicked.connect(lambda x: self.colorPicker())

    def color(self):
        pal = self.palette()
        return pal.color(QtGui.QPalette.Button)

    def colorName(self):
        return self.color().name()

    def setColor(self, col):
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Button, col)
        self.setAutoFillBackground(True)
        self.setPalette(pal)

    def colorPicker(self):
        color = self.color()
        dialog = QtWidgets.QColorDialog(color, self.parent())
        dialog.setOption(QtWidgets.QColorDialog.DontUseNativeDialog)
        dialog.setCurrentColor(color)
        dialog.currentColorChanged.connect(self.setColor)
        dialog.open()