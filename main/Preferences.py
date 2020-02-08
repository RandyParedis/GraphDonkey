"""Preferences window for the GraphDonkey application.

Author: Randy Paredis
Date:   17/12/2019
"""
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from main.extra.IOHandler import IOHandler
from main.extra import Constants
import configparser
import markdown
from markdown.extensions.legacy_em import LegacyEmExtension as legacy_em
import glob
import re
import os

def bool(name: str):
    if name in ["True", "true"]:
        return True
    if name in ["False", "false"]:
        return False
    return name

from main.plugins import PluginLoader, PluginInstaller
pluginloader = PluginLoader.instance()


class Preferences(QtWidgets.QDialog):
    def __init__(self, parent):
        super(Preferences, self).__init__(parent)
        uic.loadUi(IOHandler.dir_ui("Preferences.ui"), self)
        self.pluginUi = []

        self.buttonBox.clicked.connect(self.restoreDefaults)
        self.check_monospace.toggled.connect(self.setFontCombo)
        self._setupKs()

        self.themes = []
        self.preferences = IOHandler.get_preferences()
        self.check_parse.toggled.connect(self.parseDisable)
        self._setColorPickers()
        self.fillQuickSelect()

        self._setupPlugins()
        self.rectify()

        self.combo_theme.activated.connect(self.setTheme)
        self.pb_reload.clicked.connect(self.setTheme)
        self.pb_saveTheme.clicked.connect(self.saveTheme)

    def _setupPlugins(self):
        self.pluginUi = {}
        ps = pluginloader.get(False)
        for p in ps:
            for e in p.engines:
                self.combo_engine.addItem(e)
            self.pluginlist.layout().addWidget(PluginButton(p, self.pluginviewer, preferences=self))
        self.filterPlugins.textChanged.connect(self.pluginFilter)
        self.pluginFilter("")

    def pluginFilter(self, txt):
        fields = self.pluginlist.findChildren(PluginButton)
        for field in fields:
            field.setVisible(field.matches(txt))
        vis = [x for x in fields if x.isVisible()]
        if len(vis) > 0:
            vis[0].click()
        else:
            lo = self.pluginviewer.layout()
            for i in reversed(range(lo.count())):
                lo.itemAt(i).widget().setParent(None)
            lbl = QtWidgets.QLabel("No Plugin Selected.")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lo.addWidget(lbl, 0, 0, -1, -1)

    def parseDisable(self, b):
        if not b:
            self.check_autorender.setChecked(False)
            self.check_autorender.setEnabled(False)

    def fillQuickSelect(self):
        self.combo_theme.clear()
        files = [f for f in glob.glob(IOHandler.dir_styles() + "**/*.ini", recursive=True)]
        self.themes = sorted([Theme(f) for f in files])
        for theme in self.themes:
            self.combo_theme.addItem(theme.name, theme)

    def setFontCombo(self, on):
        f = QtWidgets.QFontComboBox.MonospacedFonts if on else QtWidgets.QFontComboBox.AllFonts
        self.font_editor.setFontFilters(f)

    def _setColorPickers(self):
        self.names_general = [
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
        self.names_editor =[
            "col_cline",
            "col_lnf",
            "col_lnb",
            "col_clnf",
            "col_clnb",
            "col_find"
        ]
        self.names_syntax =[
            "col_keyword",
            "col_attribute",
            "col_number",
            "col_string",
            "col_html",
            "col_comment",
            "col_hash",
            "col_error"
        ]
        lo = self.box_general.layout()
        for i in range(len(self.names_general)):
            name = self.names_general[i]
            setattr(self, name, ColorButton(parent=self))
            lo.addWidget(getattr(self, name), i, 2)

        lo = self.box_editor.layout()
        for i in range(len(self.names_editor)):
            name = self.names_editor[i]
            setattr(self, name, ColorButton(parent=self))
            lo.addWidget(getattr(self, name), i, 2)

        lo = self.box_syntax.layout()
        for i in range(len(self.names_syntax)):
            name = self.names_syntax[i]
            setattr(self, name, ColorButton(parent=self))
            lo.addWidget(getattr(self, name), i, 2)

    def setTheme(self, idx):
        name = self.combo_theme.currentText()
        theme = [x for x in self.themes if x.name == name][0]
        lst = self.names_general + self.names_editor + self.names_syntax
        for i in range(len(lst)):
            name = lst[i]
            getattr(self, name).setColor(QtGui.QColor(theme.color(name[4:].lower(), getattr(self, name).colorName())))

    def findColor(self, identifier):
        name = self.combo_theme.currentText()
        theme = [x for x in self.themes if x.name == name][0]
        return theme.color(identifier)

    def _setupKs(self):
        self.shortcuts = [
            "New", "Open", "Clear_Recents", "Save", "Save_As", "Save_All", "Export", "Preferences", "Close_File",
            "Exit", "Undo", "Redo", "Select_All", "Clear", "Delete", "Copy", "Cut", "Paste", "Duplicate", "Comment",
            "Indent", "Unindent", "Auto_Indent", "Find", "Autocomplete", "Show_Render_Area", "Snippets", "Next_File",
            "Previous_File", "Render", "Save_Rendered_View", "View_Parse_Tree", "Zoom_In", "Zoom_Out", "Reset_Zoom",
            "Zoom_To_Fit", "GraphDonkey", "Qt", "Move_Up", "Move_Down", "Updates", "Report_Issue"
        ]

        def pressEvent(kseq, event):
            QtWidgets.QKeySequenceEdit.keyPressEvent(kseq, event)
            kseq.setKeySequence(QtGui.QKeySequence.fromString(kseq.keySequence().toString().split(", ")[0]))
            self.checkShortcuts()

        for action in self.shortcuts:
            ks = getattr(self, "ks_" + action.lower())
            ks.keyPressEvent = lambda e, k=ks: pressEvent(k, e)

            # Bypass because Qt works weirdly:
            le = ks.findChild(QtWidgets.QLineEdit)
            le.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
            le.setClearButtonEnabled(True)

    def checkShortcuts(self):
        mapped = []
        for sc in self.shortcuts:
            ks = getattr(self, "ks_" + sc.lower())
            scs = ks.keySequence().toString()

            # TRUNCATE TO SINGLE SHORTCUT
            if ", " in scs:
                scs = scs.split(", ")[0]
                ks.setKeySequence(QtGui.QKeySequence.fromString(scs))

            if scs not in mapped or scs == "":
                mapped.append(scs)
                ks.setStyleSheet("background-color: rgb(255, 255, 255);")
            else:
                loc = mapped.index(scs)
                ks.setStyleSheet("background-color: rgb(255, 0, 0);")
                getattr(self, "ks_" + self.shortcuts[loc].lower()).setStyleSheet("background-color: rgb(255, 0, 0);")

    def rectify(self):
        # GENERAL
        if True:
            defFont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.GeneralFont)
            self.check_rememberLayout.setChecked(bool(self.preferences.value("rememberLayout", True)))
            self.check_autohide.setChecked(bool(self.preferences.value("autohide", True)))
            restore = int(self.preferences.value("restore", 0))
            if restore == 0:
                self.radio_ws_openempty.setChecked(True)
                self.radio_ws_restore.setChecked(False)
                self.radio_ws_none.setChecked(False)
            elif restore == 1:
                self.radio_ws_openempty.setChecked(False)
                self.radio_ws_restore.setChecked(True)
                self.radio_ws_none.setChecked(False)
            else:
                self.radio_ws_openempty.setChecked(False)
                self.radio_ws_restore.setChecked(False)
                self.radio_ws_none.setChecked(True)
            self.num_recents.setValue(int(self.preferences.value("recents", 5)))
            self.font_interface.setCurrentFont(QtGui.QFont(self.preferences.value("font", defFont.family())))
            self.num_font_interface.setValue(int(self.preferences.value("fontsize", 12)))

        # EDITOR
        if True:
            defFont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
            self.font_editor.setCurrentFont(QtGui.QFont(self.preferences.value("editor/font", defFont.family())))
            self.num_font_editor.setValue(int(self.preferences.value("editor/fontsize", 12)))
            self.num_tabwidth.setValue(int(self.preferences.value("editor/tabwidth", 4)))
            self.check_lineNumbers.setChecked(bool(self.preferences.value("editor/showLineNumbers", True)))
            self.check_highlightLine.setChecked(bool(self.preferences.value("editor/highlightCurrentLine", True)))
            self.check_parentheses.setChecked(bool(self.preferences.value("editor/parentheses", True)))
            self.check_spaceTabs.setChecked(bool(self.preferences.value("editor/spacesOverTabs", False)))
            self.check_monospace.setChecked(bool(self.preferences.value("editor/monospace", True)))
            self.check_showWhitespace.setChecked(bool(self.preferences.value("editor/showWhitespace", False)))
            self.check_syntax.setChecked(bool(self.preferences.value("editor/syntaxHighlighting", True)))
            self.check_parse.setChecked(bool(self.preferences.value("editor/useParser", True)))
            self.check_autorender.setChecked(bool(self.preferences.value("editor/autorender", True)))
            self.check_pairedBrackets.setChecked(bool(self.preferences.value("editor/pairedBrackets", True)))
            self.check_emptyline.setChecked(bool(self.preferences.value("editor/emptyline", True)))
            self.parseDisable(self.check_parse.isChecked())

        # VIEW
        if True:
            self.combo_engine.setCurrentText(self.preferences.value("view/engine", "Graphviz"))
            self.check_view_controls.setChecked(bool(self.preferences.value("view/controls", True)))
            self.combo_scroll_key.setCurrentText(self.preferences.value("view/scrollKey", "CTRL"))
            self.num_zoom_level_min.setValue(int(self.preferences.value("view/zoomMin", 10)))
            self.num_zoom_level_max.setValue(int(self.preferences.value("view/zoomMax", 450)))
            self.num_zoom_factor.setValue(float(self.preferences.value("view/zoomFactor", 2.0)))

        # THEME AND COLORS
        if True:
            self.combo_style.setCurrentIndex(int(self.preferences.value("col/style", 0)))
            self.combo_theme.setCurrentText(self.preferences.value("col/theme", "Light Lucy"))
            lst = self.names_general + self.names_editor + self.names_syntax
            for i in range(len(lst)):
                name = lst[i]
                cname = name.replace("_", ".")
                getattr(self, name).setColor(QtGui.QColor(self.preferences.value(cname, self.findColor(cname[4:]))))

        # SHORTCUTS
        if True:
            self.ks_new.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/new", "CTRL+N")))
            self.ks_open.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/open", "CTRL+O")))
            self.ks_save.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/save", "CTRL+S")))
            self.ks_save_all.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/save_all", "")))
            self.ks_save_as.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/save_as", "CTRL+SHIFT+S")))
            self.ks_export.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/export", "CTRL+E")))
            self.ks_clear_recents.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/clear_recents", "")))
            self.ks_preferences.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/preferences", "CTRL+P")))
            self.ks_close_file.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/close_file", "CTRL+W")))
            self.ks_exit.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/exit", "CTRL+Q")))
            self.ks_undo.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/undo", "CTRL+Z")))
            self.ks_redo.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/redo", "CTRL+SHIFT+Z")))
            self.ks_select_all.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/select_all", "CTRL+A")))
            self.ks_clear.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/clear", "")))
            self.ks_delete.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/delete", "DELETE")))
            self.ks_copy.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/copy", "CTRL+C")))
            self.ks_cut.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/cut", "CTRL+X")))
            self.ks_paste.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/paste", "CTRL+V")))
            self.ks_duplicate.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/duplicate", "CTRL+D")))
            self.ks_comment.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/comment", "CTRL+/")))
            self.ks_indent.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/indent", "TAB")))
            self.ks_unindent.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/unindent", "SHIFT+TAB")))
            self.ks_auto_indent.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/auto_indent", "CTRL+SHIFT+I")))
            self.ks_move_up.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/move_up", "CTRL+SHIFT+UP")))
            self.ks_move_down.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/move_down", "CTRL+SHIFT+DOWN")))
            self.ks_find.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/find", "CTRL+F")))
            self.ks_autocomplete.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/autocomplete", "CTRL+SPACE")))
            self.ks_show_render_area.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/show_render_area", "")))
            self.ks_render.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/render", "CTRL+R")))
            self.ks_save_rendered_view.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/save_rendered_view", "")))
            self.ks_view_parse_tree.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/view_parse_tree", "CTRL+T")))
            self.ks_snippets.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/snippets", "F2")))
            self.ks_next_file.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/next_file", "CTRL+TAB")))
            self.ks_previous_file.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/previous_file", "CTRL+SHIFT+TAB")))
            self.ks_zoom_in.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/zoom_in", "CTRL++")))
            self.ks_zoom_out.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/zoom_out", "CTRL+-")))
            self.ks_reset_zoom.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/reset_zoom", "CTRL+0")))
            self.ks_zoom_to_fit.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/zoom_to_fit", "")))
            self.ks_report_issue.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/report_issue", "")))
            self.ks_updates.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/updates", "")))
            self.ks_graphdonkey.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/graphdonkey", "")))
            self.ks_qt.setKeySequence(QtGui.QKeySequence(self.preferences.value("ks/qt", "")))

        # PLUGINS
        if True:
            plst = pluginloader.get()
            pls = self.preferences.value("plugin/enabled", None)
            if pls is None:
                pls = [p.name for p in plst]
            for plugin in plst:
                plugin.enable(plugin.name in pls)
            for eid in self.pluginUi:
                ui = self.pluginUi[eid]
                grp = "plugin/%s" % re.sub(r"[^a-z ]", "", ui.plugin.name.lower()).replace(" ", "")
                self.preferences.beginGroup(grp)
                ui.rectify()
                self.preferences.endGroup()

    def apply(self):
        self.preferences.clear()

        # GENERAL
        if True:
            self.preferences.setValue("rememberLayout", self.check_rememberLayout.isChecked())
            self.preferences.setValue("autohide", self.check_autohide.isChecked())
            if self.radio_ws_openempty.isChecked():
                self.preferences.setValue("restore", 0)
            elif self.radio_ws_restore.isChecked():
                self.preferences.setValue("restore", 1)
            else:
                self.preferences.setValue("restore", 2)
            self.preferences.setValue("recents", self.num_recents.value())
            self.preferences.setValue("font", self.font_interface.currentFont().family())
            self.preferences.setValue("fontsize", self.num_font_interface.value())

        # EDITOR
        if True:
            self.preferences.setValue("editor/font", self.font_editor.currentFont().family())
            self.preferences.setValue("editor/fontsize", self.num_font_editor.value())
            self.preferences.setValue("editor/showLineNumbers", self.check_lineNumbers.isChecked())
            self.preferences.setValue("editor/highlightCurrentLine", self.check_highlightLine.isChecked())
            self.preferences.setValue("editor/syntaxHighlighting", self.check_syntax.isChecked())
            self.preferences.setValue("editor/spacesOverTabs", self.check_spaceTabs.isChecked())
            self.preferences.setValue("editor/parentheses", self.check_parentheses.isChecked())
            self.preferences.setValue("editor/monospace", self.check_monospace.isChecked())
            self.preferences.setValue("editor/showWhitespace", self.check_showWhitespace.isChecked())
            self.preferences.setValue("editor/tabwidth", self.num_tabwidth.value())
            self.preferences.setValue("editor/useParser", self.check_parse.isChecked())
            self.preferences.setValue("editor/autorender", self.check_autorender.isChecked())
            self.preferences.setValue("editor/pairedBrackets", self.check_pairedBrackets.isChecked())
            self.preferences.setValue("editor/emptyline", self.check_emptyline.isChecked())

        # VIEW
        if True:
            self.preferences.setValue("view/engine", self.combo_engine.currentText())
            self.preferences.setValue("view/controls", self.check_view_controls.isChecked())
            self.preferences.setValue("view/scrollKey", self.combo_scroll_key.currentText())
            self.preferences.setValue("view/zoomMin", self.num_zoom_level_min.value())
            self.preferences.setValue("view/zoomMax", self.num_zoom_level_max.value())
            self.preferences.setValue("view/zoomFactor", self.num_zoom_factor.value())

        # THEME AND COLORS
        if True:
            self.preferences.setValue("col/style", self.combo_style.currentIndex())
            self.preferences.setValue("col/theme", self.combo_theme.currentText())
            self.preferences.setValue("col/foreground", self.col_foreground.colorName())
            self.preferences.setValue("col/window", self.col_window.colorName())
            self.preferences.setValue("col/base", self.col_base.colorName())
            self.preferences.setValue("col/alternateBase", self.col_alternateBase.colorName())
            self.preferences.setValue("col/tooltipBase", self.col_tooltipBase.colorName())
            self.preferences.setValue("col/tooltipText", self.col_tooltipText.colorName())
            self.preferences.setValue("col/text", self.col_text.colorName())
            self.preferences.setValue("col/button", self.col_button.colorName())
            self.preferences.setValue("col/buttonText", self.col_buttonText.colorName())
            self.preferences.setValue("col/brightText", self.col_brightText.colorName())
            self.preferences.setValue("col/highlight", self.col_highlight.colorName())
            self.preferences.setValue("col/link", self.col_link.colorName())
            self.preferences.setValue("col/visitedLink", self.col_visitedLink.colorName())
            self.preferences.setValue("col/cline", self.col_cline.colorName())
            self.preferences.setValue("col/lnf", self.col_lnf.colorName())
            self.preferences.setValue("col/lnb", self.col_lnb.colorName())
            self.preferences.setValue("col/clnf", self.col_clnf.colorName())
            self.preferences.setValue("col/clnb", self.col_clnb.colorName())
            self.preferences.setValue("col/find", self.col_find.colorName())
            self.preferences.setValue("col/keyword", self.col_keyword.colorName())
            self.preferences.setValue("col/attribute", self.col_attribute.colorName())
            self.preferences.setValue("col/number", self.col_number.colorName())
            self.preferences.setValue("col/string", self.col_string.colorName())
            self.preferences.setValue("col/html", self.col_html.colorName())
            self.preferences.setValue("col/comment", self.col_comment.colorName())
            self.preferences.setValue("col/hash", self.col_hash.colorName())
            self.preferences.setValue("col/error", self.col_error.colorName())

        # SHORTCUTS
        if True:
            self.preferences.setValue("ks/new", self.ks_new.keySequence().toString())
            self.preferences.setValue("ks/open", self.ks_open.keySequence().toString())
            self.preferences.setValue("ks/save", self.ks_save.keySequence().toString())
            self.preferences.setValue("ks/save_all", self.ks_save_all.keySequence().toString())
            self.preferences.setValue("ks/save_as", self.ks_save_as.keySequence().toString())
            self.preferences.setValue("ks/export", self.ks_export.keySequence().toString())
            self.preferences.setValue("ks/clear_recents", self.ks_clear_recents.keySequence().toString())
            self.preferences.setValue("ks/preferences", self.ks_preferences.keySequence().toString())
            self.preferences.setValue("ks/close_file", self.ks_close_file.keySequence().toString())
            self.preferences.setValue("ks/exit", self.ks_exit.keySequence().toString())
            self.preferences.setValue("ks/undo", self.ks_undo.keySequence().toString())
            self.preferences.setValue("ks/redo", self.ks_redo.keySequence().toString())
            self.preferences.setValue("ks/select_all", self.ks_select_all.keySequence().toString())
            self.preferences.setValue("ks/clear", self.ks_clear.keySequence().toString())
            self.preferences.setValue("ks/delete", self.ks_delete.keySequence().toString())
            self.preferences.setValue("ks/copy", self.ks_copy.keySequence().toString())
            self.preferences.setValue("ks/cut", self.ks_cut.keySequence().toString())
            self.preferences.setValue("ks/paste", self.ks_paste.keySequence().toString())
            self.preferences.setValue("ks/duplicate", self.ks_duplicate.keySequence().toString())
            self.preferences.setValue("ks/comment", self.ks_comment.keySequence().toString())
            self.preferences.setValue("ks/indent", self.ks_indent.keySequence().toString())
            self.preferences.setValue("ks/unindent", self.ks_unindent.keySequence().toString())
            self.preferences.setValue("ks/auto_indent", self.ks_auto_indent.keySequence().toString())
            self.preferences.setValue("ks/move_up", self.ks_move_up.keySequence().toString())
            self.preferences.setValue("ks/move_down", self.ks_move_down.keySequence().toString())
            self.preferences.setValue("ks/find", self.ks_find.keySequence().toString())
            self.preferences.setValue("ks/autocomplete", self.ks_autocomplete.keySequence().toString())
            self.preferences.setValue("ks/show_render_area", self.ks_show_render_area.keySequence().toString())
            self.preferences.setValue("ks/snippets", self.ks_snippets.keySequence().toString())
            self.preferences.setValue("ks/next_file", self.ks_next_file.keySequence().toString())
            self.preferences.setValue("ks/previous_file", self.ks_previous_file.keySequence().toString())
            self.preferences.setValue("ks/render", self.ks_render.keySequence().toString())
            self.preferences.setValue("ks/save_rendered_view", self.ks_save_rendered_view.keySequence().toString())
            self.preferences.setValue("ks/view_parse_tree", self.ks_view_parse_tree.keySequence().toString())
            self.preferences.setValue("ks/zoom_in", self.ks_zoom_in.keySequence().toString())
            self.preferences.setValue("ks/zoom_out", self.ks_zoom_out.keySequence().toString())
            self.preferences.setValue("ks/reset_zoom", self.ks_reset_zoom.keySequence().toString())
            self.preferences.setValue("ks/zoom_to_fit", self.ks_zoom_to_fit.keySequence().toString())
            self.preferences.setValue("ks/report_issue", self.ks_report_issue.keySequence().toString())
            self.preferences.setValue("ks/updates", self.ks_updates.keySequence().toString())
            self.preferences.setValue("ks/graphdonkey", self.ks_graphdonkey.keySequence().toString())
            self.preferences.setValue("ks/qt", self.ks_qt.keySequence().toString())

        self.preferences.sync()

        self.parent().lockDisplay()
        self.applyGeneral()
        self.applyEditor()
        self.applyView()
        self.applyStyle()
        self.applyShortcuts()
        self.applyPlugins()
        self.parent().releaseDisplay()

    def applyGeneral(self):
        font = self.font_interface.currentFont()
        font.setPointSize(self.num_font_interface.value())
        QtWidgets.QApplication.instance().setFont(font)

    def applyShortcuts(self):
        for action in self.shortcuts:
            getattr(self.parent(), "action_" + action).setShortcut(getattr(self, "ks_" + action.lower()).keySequence())

    def applyStyle(self):
        app = QtWidgets.QApplication.instance()
        app.setStyle(self.combo_style.currentText())
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.WindowText, self.col_foreground.color())
        palette.setColor(QtGui.QPalette.Window, self.col_window.color())
        palette.setColor(QtGui.QPalette.Base, self.col_base.color())
        palette.setColor(QtGui.QPalette.AlternateBase, self.col_alternateBase.color())
        palette.setColor(QtGui.QPalette.ToolTipBase, self.col_tooltipBase.color())
        palette.setColor(QtGui.QPalette.ToolTipText, self.col_tooltipText.color())
        palette.setColor(QtGui.QPalette.Text, self.col_text.color())
        palette.setColor(QtGui.QPalette.Button, self.col_button.color())
        palette.setColor(QtGui.QPalette.ButtonText, self.col_buttonText.color())
        palette.setColor(QtGui.QPalette.BrightText, self.col_brightText.color())
        palette.setColor(QtGui.QPalette.Highlight, self.col_highlight.color())
        palette.setColor(QtGui.QPalette.HighlightedText, self.col_highlightedText.color())
        palette.setColor(QtGui.QPalette.Link, self.col_link.color())
        palette.setColor(QtGui.QPalette.LinkVisited, self.col_visitedLink.color())
        app.setPalette(palette)

    def applyView(self):
        view = self.parent().view
        view.setControls(self.check_view_controls.isChecked())
        view.setMinZoomLevel(float(self.num_zoom_level_min.value()) / 100)
        view.setMaxZoomLevel(float(self.num_zoom_level_max.value()) / 100)
        view.setZoomFactorBase(self.num_zoom_factor.value())

    def applyEditor(self):
        self.parent().files.setTabBarAutoHide(self.check_autohide.isChecked())
        for index in range(self.parent().files.count()):
            editor = self.parent().editor(index)

            # SET FILE TYPES AND ENGINES
            editor.wrapper.setTypes()

            # SHOW WHITESPACES
            option = editor.document().defaultTextOption()
            if self.check_showWhitespace.isChecked():
                option.setFlags(option.flags() | QtGui.QTextOption.ShowTabsAndSpaces | QtGui.QTextOption.ShowLineAndParagraphSeparators)
            else:
                option.setFlags(option.flags() & ~QtGui.QTextOption.ShowTabsAndSpaces & ~QtGui.QTextOption.ShowLineAndParagraphSeparators)
            editor.document().setDefaultTextOption(option)

            # FONT
            font = QtGui.QFont()
            font.setFamily(self.font_editor.currentFont().family())
            font.setFixedPitch(self.check_monospace.isChecked())
            font.setPointSize(self.num_font_editor.value())
            editor.setFont(font)

            # TAB WIDTH
            fontWidth = QtGui.QFontMetrics(font).averageCharWidth()
            editor.setTabStopWidth(self.num_tabwidth.value() * fontWidth)

            # FIX DISPLAY
            editor.positionChangedSlot()
            editor.highlighter.rehighlight()

            # TURN TABS TO SPACES AND VICE VERSA
            cursor = editor.textCursor()
            seltxt = cursor.selectedText()
            cstart = cursor.selectionStart()
            cend = cursor.selectionEnd()
            cursor.setPosition(0)
            cursor.setPosition(cstart, QtGui.QTextCursor.KeepAnchor)
            before = cursor.selectedText()
            tw = self.num_tabwidth.value()
            txt = editor.toPlainText()
            if self.check_spaceTabs.isChecked():
                e = "\t"
                b4 = before.count(e) * (tw - 1)
                cstart += b4
                cend += seltxt.count(e) * (tw - 1) + b4
                txt = txt.replace(e, " " * tw)
            else:
                e = " " * tw
                b4 = before.count(e) * (tw - 1)
                cstart -= b4
                cend -= seltxt.count(e) * (tw - 1) + b4
                txt = txt.replace(e, "\t")
            editor.setText(txt)
            cursor.setPosition(cstart)
            cursor.setPosition(cend, QtGui.QTextCursor.KeepAnchor)
            editor.setTextCursor(cursor)

    def applyPlugins(self):
        # TODO: Select the first plugin, BUT this gives issues on Windows:
        #       the font size changes (it feels as if Rich Text QLabels are not
        #       rendered correctly when invisible on Windows)
        pll = self.pluginlist.findChildren(PluginButton)
        if len(pll) > 0:
            pll[0].click()
        self.preferences.setValue("plugin/enabled", [p.name for p in pluginloader.get()])
        for eid in self.pluginUi:
            ui = self.pluginUi[eid]
            grp = "plugin/%s" % re.sub(r"[^a-z ]", "", ui.plugin.name.lower()).replace(" ", "")
            self.preferences.beginGroup(grp)
            ui.apply()
            self.preferences.endGroup()
        self.parent().updateFileTypes()

    def open(self):
        self.rectify()
        QtWidgets.QDialog.open(self)

    def accept(self):
        self.apply()
        QtWidgets.QDialog.accept(self)

    def restoreDefaults(self, button):
        if button.text() == "Restore Defaults":
            self.preferences.clear()
            self.preferences.sync()
            self.rectify()

    def saveTheme(self, b):
        title, ok = "", True
        while ok and title == "":
            title, ok = QtWidgets.QInputDialog.getText(self, "Enter a Theme Name", "Theme Name",
                                                       text=self.combo_theme.currentText())
            if title in [x.name for x in self.themes]:
                btn = QtWidgets.QMessageBox.question(self,
                                                     "Enter a Title Name",
                                                     "The theme '%s' already exists.\n"
                                                     "Do you want to replace it?" % title)
                if btn == QtWidgets.QMessageBox.No:
                    title = ""

        config = configparser.ConfigParser()
        config["info"] = {"name": title, "description": title + " Theme"}
        lst = self.names_general + self.names_editor + self.names_syntax
        config["styles"] = {x[4:]: getattr(self, x).colorName() for x in lst}
        with open(IOHandler.dir_styles(re.sub(r'[^a-z0-9]', "-", title.lower()) + ".ini"), "w") as f:
            config.write(f)
        self.fillQuickSelect()
        self.combo_theme.setCurrentText(title)




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
        pal.setColor(QtGui.QPalette.ButtonText,
                     QtGui.QColor.fromHsv(col.hue(), col.saturation(), (col.value() - 100) % 255))
        self.setAutoFillBackground(True)
        self.setPalette(pal)
        self.setText(col.name())

    def colorPicker(self):
        color = self.color()
        dialog = QtWidgets.QColorDialog(color, self.parent())
        dialog.setOption(QtWidgets.QColorDialog.DontUseNativeDialog)
        dialog.setCurrentColor(color)
        dialog.currentColorChanged.connect(self.setColor)
        dialog.open()


class Theme:
    def __init__(self, fname:str):
        self.file = fname
        self.config = configparser.ConfigParser()
        self.config.read(self.file)
        self.name = self.config.get("info", "name", fallback=self.file)
        self.description = self.config.get("info", "description", fallback="")

    def __lt__(self, other):
        return self.name < other.name

    def color(self, name:str="", default=None):
        return self.config.get("styles", name, fallback=default)


class PluginButton(QtWidgets.QLabel):
    def __init__(self, plugin, viewer, preferences=None, parent=None):
        super(PluginButton, self).__init__(parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.plugin = plugin
        self.viewer = viewer
        self.prefs = preferences
        self.setTextFormat(QtCore.Qt.RichText)
        self.setText(self.getHeader(16, 12))

        self.installer = None

        try:
            self.setOptions()
        except Exception as e:
            # self.error(str(e))
            self.plugin.deps = False

    def error(self, msg):
        self.prefs.parent().error("Plugin Error", "<p>%s</p><p>You cannot use the '<i>%s</i>' plugin for now.</p>" %
                                  (msg, self.plugin.name))

    def getHeader(self, size=None, small=None):
        ic = ""
        if len(self.plugin.icon) > 0:
            ic = "<td width=64 valign='middle'><img src='%s' width=64 height=64></td>" % self.plugin.icon
        stl1, stl2 = "", ""
        if size is not None:
            stl1 = "style='font-size:%ipx'" % size
        if small is not None:
            stl2 = "style='font-size:%ipx'" % small
        return "<table width='100%%' cellspacing=10 %s>" \
               "<tr>%s" \
               "<td valign='middle'><b>%s</b><br><span %s>%s</span></td>" \
               "</tr>" \
               "</table>" % (stl1, ic, self.plugin.name, stl2, self.getSubSec())

    def getSubSec(self):
        author = ""
        version = ""
        for k, v in self.plugin.attrs:
            if k.lower() == "author":
                author = v
            if k.lower() == "version":
                version = v
        if len(author) > 0 < len(version):
            return "%s - %s" % (author, version)
        else:
            return author if len(author) > 0 else version if len(version) > 0 else ""

    def getDesc(self):
        desc = markdown.markdown(self.plugin.description, extensions=[legacy_em()])

        size = "%ipt" % self.font().pointSize()
        attrs = "<table width='100%%' cellspacing=10>%s</table>" % \
                ("".join(["<tr><td width='20%%' align='right'><b>%s</b></td><td>%s</td></tr>" %
                          (k, self.transform(v)) for k, v in self.plugin.attrs]))
        return "<span style='font-size: %s;'>%s<br>%s<br></font>" % (size, desc, attrs)

    def matches(self, txt):
        return txt in self.plugin.name or txt in self.plugin.description

    @staticmethod
    def transform(txt):
        m = re.match(r"^https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,4}\b([-a-zA-Z0-9@:%_+.~#?&/=]*)$", txt)
        if m is not None:
            return "<a href='%s'>%s</a>" % (txt, txt)
        return markdown.markdown(txt, extensions=[legacy_em()])

    def setOptions(self):
        lo = self.viewer.layout()
        for e in self.plugin.engines:
            if e not in self.prefs.pluginUi:
                box = self.plugin.getPreferencesUi(e)
                if box is not None:
                    box.preferences = self.prefs.preferences
                    box.plugin = self.plugin
                    self.prefs.pluginUi[e] = box
                lo.addWidget(self.prefs.pluginUi[e], lo.rowCount(), 0, -1, -1)

    def mousePressEvent(self, QMouseEvent):
        # Reset all button roles
        btns = self.parent().findChildren(PluginButton)
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Button, self.prefs.preferences.value('col_button', self.prefs.col_button.color()))
        for btn in btns:
            btn.setBackgroundRole(QtGui.QPalette.Button)
            btn.setPalette(pal)
            btn.setAutoFillBackground(True)

        # Set current button
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Button, self.prefs.preferences.value('col_base', self.prefs.col_base.color()))
        self.setBackgroundRole(QtGui.QPalette.Highlight)
        self.setPalette(pal)

        # Fill the viewer
        lo = self.viewer.layout()
        for i in reversed(range(lo.count())):
            lo.itemAt(i).widget().setParent(None)
        header = QtWidgets.QLabel(self.getHeader(20, 14))
        header.setTextFormat(QtCore.Qt.RichText)
        header.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        header.setWordWrap(True)
        lo.addWidget(header, 0, 0, 1, 2)

        if self.plugin.deps:
            cb = QtWidgets.QCheckBox("Enable Plugin")
            cb.setChecked(self.plugin.enabled)
            cb.toggled.connect(self.plugin.enable)
            lo.addWidget(cb, 1, 0, 1, 1)
            pb = QtWidgets.QPushButton("Update Dependencies")
            pb.clicked.connect(self.update_)
            lo.addWidget(pb, 1, 1, 1, 1)
        else:
            pb = QtWidgets.QPushButton("Install Dependencies")
            pb.clicked.connect(self.install)
            lo.addWidget(pb, 1, 0, 1, 2)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        lo.addWidget(line, 2, 0, 1, 2)

        desc = QtWidgets.QLabel(self.getDesc())
        desc.setTextFormat(QtCore.Qt.RichText)
        desc.setAlignment(QtCore.Qt.AlignJustify | QtCore.Qt.AlignTop)
        desc.setOpenExternalLinks(True)
        desc.setWordWrap(True)
        lo.addWidget(desc, 3, 0, 3, 2)

        if self.plugin.deps and self.plugin.enabled:
            self.setOptions()

    def click(self):
        self.mousePressEvent(None)

    def install(self):
        self.installer = PluginInstaller(self.plugin, self)
        self.installer.installed.connect(self.installed)
        self.installer.exec_()

    def update_(self):
        self.installer = PluginInstaller(self.plugin, update=True, parent=self)
        self.installer.installed.connect(self.installed)
        self.installer.exec_()

    def installed(self, succ):
        if succ:
            pluginloader.reload()
            for e in self.plugin.engines:
                try:
                    self.plugin.getPreferencesUi(e)
                except Exception as e:
                    self.error(str(e))
                    self.plugin.deps = False
                    self.installer.reject()
                    self.click()
                    return
            self.plugin.enable()
            self.setText(self.getHeader(16, 12))
            self.click()

            # set plugin preferences once more
            for e in self.plugin.engines:
                self.prefs.pluginUi[e].rectify()

            # set all mainwindow settings
            mw = self.prefs.parent()
            mw.updateFileTypes()
