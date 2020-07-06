"""The Welcome Wizard is the wizard that opens at first use.

It is required this wizard shows BEFORE the Preferences are loaded.

Author: Randy Paredis
Date:   02/08/2020
"""
from PyQt5 import QtWidgets, QtCore, uic
from main.extra.IOHandler import IOHandler
from main.plugins import PluginLoader, PluginInstaller
from main.extra.qrc import images

Config = IOHandler.get_preferences()
pluginloader = PluginLoader.instance()

rccv = images.rcc_version

class WelcomeWizard(QtWidgets.QWizard):
    def __init__(self, parent = None):
        super(WelcomeWizard, self).__init__(parent, QtCore.Qt.Dialog)
        uic.loadUi(IOHandler.dir_ui("WelcomeWizard.ui"), self)

    def accept(self):
        theme = "Light Lucy"
        if self.rb_burning_berta.isChecked():
            theme = "Burning Berta"
        elif self.rb_dark_doris.isChecked():
            theme = "Dark Doris"
        elif self.rb_fierce_fiona.isChecked():
            theme = "Fierce Fiona"
        elif self.rb_vicious_victoria.isChecked():
            theme = "Vicious Victoria"
        Config.setValue("col/theme", theme)

        plugins = ["Graphviz", "Flowchart"]
        for p in plugins:
            if getattr(self, "check_" + p.lower()).isChecked():
                plugin = pluginloader.getPlugin(p)
                pli = PluginInstaller(plugin)
                pli.installed.connect(lambda s: plugin.enable(s))
                pli.exec_()

        pluginloader.reload()

        # Technically not required, seeing as it should be empty
        Config.setValue("plugin/enabled", None)

        super(WelcomeWizard, self).accept()



