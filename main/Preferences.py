"""Preferences window for the GraphDonkey application.

Author: Randy Paredis
Date:   17/12/2019
"""
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from main.extra.IOHandler import IOHandler
from main.extra import Constants, isColorDark
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
        self.pluginUi = {}

        self.buttonBox.clicked.connect(self.restoreDefaults)
        self.check_monospace.toggled.connect(self.setFontCombo)
        self.num_zoom_level_min.valueChanged.connect(self.setMaxZoom)
        self.num_zoom_level_max.valueChanged.connect(self.setMinZoom)
        self._setupKs()

        self.themes = []
        self.preferences = IOHandler.get_preferences()
        self.check_parse.toggled.connect(self.parseDisable)
        self._setColorPickers()
        self.fillQuickSelect()

        self._setupPlugins()
        self.defaults = {}
        self.rectify()

        self.combo_theme.activated.connect(self.setTheme)
        self.pb_reload.clicked.connect(self.setTheme)
        self.pb_saveTheme.clicked.connect(self.saveTheme)

    def setMaxZoom(self, val):
        if self.num_zoom_level_max.value() < val:
            self.num_zoom_level_max.setValue(val)

    def setMinZoom(self, val):
        if self.num_zoom_level_min.value() > val:
            self.num_zoom_level_min.setValue(val)

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
        self.names_general_ext = [
            ("col_foreground", QtGui.QPalette.WindowText),
            ("col_window", QtGui.QPalette.Window),
            ("col_base", QtGui.QPalette.Base),
            ("col_alternateBase", QtGui.QPalette.AlternateBase),
            ("col_tooltipBase", QtGui.QPalette.ToolTipBase),
            ("col_tooltipText", QtGui.QPalette.ToolTipText),
            ("col_text", QtGui.QPalette.Text),
            ("col_button", QtGui.QPalette.Button),
            ("col_buttonText", QtGui.QPalette.ButtonText),
            ("col_brightText", QtGui.QPalette.BrightText),
            ("col_highlight", QtGui.QPalette.Highlight),
            ("col_highlightedText", QtGui.QPalette.HighlightedText),
            ("col_link", QtGui.QPalette.Link),
            ("col_visitedLink", QtGui.QPalette.LinkVisited)
        ]
        self.names_general = [x[0] for x in self.names_general_ext]
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
            "col_note",
            "col_comment",
            "col_hash",
            "col_error"
        ]
        for lo, names in [(self.box_general.layout(), self.names_general),
                          (self.box_editor.layout(), self.names_editor),
                          (self.box_syntax.layout(), self.names_syntax)]:
            for i in range(len(names)):
                name = names[i]
                btn = ColorButton(parent=self)
                btn.setProperty("key", name.replace("_", "/"))
                btn.setToolTip("The %s color." % name.split("_")[1])
                setattr(self, name, btn)
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
            "New", "Open", "Save", "Save_All", "Save_As", "Export", "Clear_Recents", "Preferences", "Close_File",
            "Exit", "Restart",
            "Undo", "Redo", "Select_All", "Clear", "Delete", "Copy", "Paste", "Cut", "Duplicate", "Comment",
            "Indent", "Unindent", "Auto_Indent", "Move_Up", "Move_Down", "Autocomplete",
            "UpperCase", "LowerCase", "WordCase", "SentenceCase", "DromedaryCase", "PascalCase", "SnakeCase",
            "Previous_File", "Next_File", "First_File", "Last_File", "Find", "Goto_Line",
            "Show_Render_Area", "Snippets", "Render", "Save_Rendered_View", "View_Parse_Tree", "Zoom_In", "Zoom_Out",
            "Reset_Zoom", "Zoom_To_Fit",
            "Help", "Report_Issue", "Updates", "GraphDonkey", "Qt"
        ]

        def pressEvent(kseq, event):
            QtWidgets.QKeySequenceEdit.keyPressEvent(kseq, event)
            if len(kseq.keySequence()) > 0:
                kseq.setKeySequence(QtGui.QKeySequence(kseq.keySequence()[0]))

        def menu(kseq, point):
            m = QtWidgets.QMenu(self)
            m.addAction("Clear Field", lambda: kseq.clear())
            m.addSeparator()
            m.addAction("Set to 'Tab'", lambda: kseq.setKeySequence(QtCore.Qt.Key_Tab))
            m.addAction("Set to 'Shift+Tab'", lambda: kseq.setKeySequence("Shift+Tab"))
            m.exec_(self.mapToGlobal(
                kseq.parent().parent().mapToParent(kseq.parent().mapToParent(kseq.mapToParent(point)))))

        for action in self.shortcuts:
            ks = getattr(self, "ks_" + action.lower())
            ks.setToolTip("Shortcut for the '%s' action." % action.replace("_", " "))
            ks.keyPressEvent = lambda e, k=ks: pressEvent(k, e)
            ks.keySequenceChanged.connect(lambda _: self.checkShortcuts())

            # Bypass because Qt works weirdly:
            le = ks.findChild(QtWidgets.QLineEdit)
            le.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            le.customContextMenuRequested.connect(lambda p, k=ks: menu(k, p))
            le.setClearButtonEnabled(True)
            clear = le.findChild(QtWidgets.QAction)
            clear.triggered.connect(ks.clear)

    def checkShortcuts(self):
        # TODO: follow theme!
        mapped = []
        for sc in self.shortcuts:
            ks = getattr(self, "ks_" + sc.lower())
            scs = ks.keySequence().toString()

            if scs not in mapped or scs == "":
                mapped.append(scs)
                ks.setStyleSheet("background-color: rgb(255, 255, 255);")
            else:
                loc = mapped.index(scs)
                ks.setStyleSheet("background-color: rgb(255, 0, 0);")
                getattr(self, "ks_" + self.shortcuts[loc].lower()).setStyleSheet("background-color: rgb(255, 0, 0);")

    def rectify(self):
        # Set static, hardcoded attributes
        self.defaults[self.combo_engine.property("key")] = "Graphviz"
        self.defaults[self.combo_theme.property("key")] = "Light Lucy"

        for elem in self.__dict__.values():
            if isinstance(elem, QtWidgets.QCheckBox):
                key = elem.property("key")
                elem.setChecked(bool(self.preferences.value(key, self.defaults.setdefault(key, elem.isChecked()))))
            elif isinstance(elem, QtWidgets.QRadioButton):
                key = elem.property("key")
                value = elem.property("value")
                val = int(self.preferences.value(key, 0))
                if val == value:
                    elem.setChecked(True)
            elif isinstance(elem, QtWidgets.QSpinBox):
                key = elem.property("key")
                elem.setValue(int(self.preferences.value(key, self.defaults.setdefault(key, elem.value()))))
            elif isinstance(elem, QtWidgets.QDoubleSpinBox):
                key = elem.property("key")
                elem.setValue(float(self.preferences.value(key, self.defaults.setdefault(key, elem.value()))))
            elif isinstance(elem, QtWidgets.QFontComboBox):
                key = elem.property("key")
                if elem.property("monospace"):
                    defFont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
                else:
                    defFont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.GeneralFont)
                elem.setCurrentFont(
                    QtGui.QFont(self.preferences.value(key, self.defaults.setdefault(key, defFont.family()))))
            elif isinstance(elem, QtWidgets.QComboBox):
                key = elem.property("key")
                if elem.property("asInt"):
                    elem.setCurrentIndex(
                        int(self.preferences.value(key, self.defaults.setdefault(key, elem.currentIndex()))))
                else:
                    elem.setCurrentText(self.preferences.value(key, self.defaults.setdefault(key, elem.currentText())))
            elif isinstance(elem, QtWidgets.QKeySequenceEdit):
                key = elem.property("key")
                elem.setKeySequence(QtGui.QKeySequence(
                    self.preferences.value(key, self.defaults.setdefault(key, elem.keySequence().toString()))))

        # Colors
        lst = self.names_general + self.names_editor + self.names_syntax
        for name in lst:
            cname = name.replace("_", ".")
            getattr(self, name).setColor(QtGui.QColor(self.preferences.value(cname, self.findColor(cname[4:]))))

        # Plugins
        plst = pluginloader.get()
        pls = self.preferences.value("plugin/enabled", None)
        if pls is None:
            pls = []
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

        mapping = {}
        for elem in self.__dict__.values():
            if isinstance(elem, QtWidgets.QCheckBox):
                mapping[elem.property("key")] = elem.isChecked()
            elif isinstance(elem, QtWidgets.QRadioButton):
                key = elem.property("key")
                if elem.isChecked():
                    mapping[key] = elem.property("value")
            elif isinstance(elem, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                mapping[elem.property("key")] = elem.value()
            elif isinstance(elem, QtWidgets.QFontComboBox):
                mapping[elem.property("key")] = elem.currentFont().family()
            elif isinstance(elem, QtWidgets.QComboBox):
                key = elem.property("key")
                if elem.property("asInt"):
                    mapping[key] = elem.currentIndex()
                else:
                    mapping[key] = elem.currentText()
            elif isinstance(elem, QtWidgets.QKeySequenceEdit):
                mapping[elem.property("key")] = elem.keySequence().toString()
            elif isinstance(elem, ColorButton):
                mapping[elem.property("key")] = elem.colorName()

        for key, value in mapping.items():
            self.preferences.setValue(key, value)

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

        # Determine theme color
        window = self.col_window.color()
        dark = isColorDark(window.red(), window.green(), window.blue())

        # Apply all colors
        for name, role in self.names_general_ext:
            color = getattr(self, name).color()
            palette.setColor(role, color)

            # Disabled items should have a different color
            if dark:
                palette.setColor(QtGui.QPalette.Disabled, role, color.darker(150))
            else:
                if color.black() == 255:
                    color.setHsv(color.hue(), color.saturation(), 100)
                palette.setColor(QtGui.QPalette.Disabled, role, color.lighter(150))

        # Set 3D effect colors
        effs = [QtGui.QPalette.Light, QtGui.QPalette.Midlight, QtGui.QPalette.Dark, QtGui.QPalette.Mid,
                QtGui.QPalette.Shadow]
        col = self.col_button.color()
        if dark:
            cols = [col.darker(), col.darker(75), col.lighter(), col.lighter(75), QtCore.Qt.white]
        else:
            cols = [col.lighter(), col.lighter(75), col.darker(), col.darker(75), QtCore.Qt.black]
        for i in range(len(effs)):
            palette.setColor(effs[i], cols[i])

        # Apply Palette
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
            editor.setCenterOnScroll(self.check_centerOnScroll.isChecked())

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
            editor.centerCursor()

    def applyPlugins(self):
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
            self.preferences.setValue("col/theme", self.combo_theme.currentText())
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
                    self.prefs.pluginUi[e] = box
            else:
                box = self.prefs.pluginUi[e]
            if box is not None:
                box.preferences = self.prefs.preferences
                box.plugin = self.plugin
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
            cb.setToolTip("When checked, the plugin can be used.")
            cb.setChecked(self.plugin.enabled)
            cb.toggled.connect(self.plugin.enable)
            lo.addWidget(cb, 1, 0, 1, 1)
            pb = QtWidgets.QPushButton("Update Dependencies")
            pb.setToolTip("Update the installation candidates for this plugin.")
            pb.clicked.connect(self.update_)
            lo.addWidget(pb, 1, 1, 1, 1)
        else:
            pb = QtWidgets.QPushButton("Install Dependencies")
            pb.setToolTip("Install all dependencies for this plugin.")
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
