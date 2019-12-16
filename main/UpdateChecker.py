"""The Dialog that checks for updates and missing packages in requirements.txt

Author: Randy Paredis
Date:   16/12/2019
"""
from PyQt5 import QtWidgets, uic
from main.extra.IOHandler import IOHandler
import pkg_resources


class UpdateChecker(QtWidgets.QDialog):
    def __init__(self, parent, useui=True):
        super(UpdateChecker, self).__init__(parent)
        self.useui = useui
        if self.useui:
            uic.loadUi(IOHandler.dir_ui("UpdateChecker.ui"), self)

        self.dependencies = []
        self.load_dependencies()
        self.check_dependencies()

    def load_dependencies(self):
        if self.useui:
            self.lbl_info.setText("Fetching requirements...")
        with open(IOHandler.dir_root("requirements.txt")) as f:
            self.dependencies = f.read().replace("\r", "").split("\n")
        self.dependencies = [x.split("#")[0].strip() for x in self.dependencies]
        self.dependencies = [x for x in self.dependencies if x != ""]

    def check_dependencies(self):
        if self.useui:
            self.lbl_info.setText("Checking dependencies...")
        updates = False
        try:
            pkg_resources.require(self.dependencies)
        except pkg_resources.DistributionNotFound as ex:
            updates = True
        except pkg_resources.VersionConflict as ex:
            updates = True

        if self.useui:
            if updates:
                self.lbl_info.setText("<b>Updates required.</b>")
            else:
                self.lbl_info.setText("<b>No updates required.</b>")
