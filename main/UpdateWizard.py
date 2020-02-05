"""This file handles all additional installation/uninstall and update features.

Maybe, it can be extended to a generic installer in the future.

Author: Randy Paredis
Date:   02/05/2020
"""

from PyQt5 import QtWidgets, QtCore, uic
from main.extra.IOHandler import IOHandler
import sys, glob, os

class UpdateWizard(QtWidgets.QWizard):
    class Pages:
        START = 0
        UNINSTALL = 1
        CLEAR = 2
        UPDATES = 3
        PLUGIN = 4

    def __init__(self, parent = None):
        super(UpdateWizard, self).__init__(parent, QtCore.Qt.Dialog)
        uic.loadUi(IOHandler.dir_ui("UpdateWizard.ui"), self)

        self.pb_clear.clicked.connect(self.clear)
        self.pb_uninstall.clicked.connect(self.uninstall)

    def nextId(self):
        cid = self.currentId()
        if cid == UpdateWizard.Pages.START:
            if self.rd_updates.isChecked():
                return UpdateWizard.Pages.UPDATES
            if self.rd_plugin.isChecked():
                return UpdateWizard.Pages.PLUGIN
            if self.rd_uninstall.isChecked():
                return UpdateWizard.Pages.UNINSTALL
            if self.rd_clear.isChecked():
                return UpdateWizard.Pages.CLEAR
        elif cid == UpdateWizard.Pages.UNINSTALL:
            return UpdateWizard.Pages.CLEAR
        return -1

    def uninstall(self):
        if not (getattr(sys, 'frozen', None) and hasattr(sys, '_MEIPASS')):
            # PREVENTS REMOVING ALL CODE DURING DEVELOPMENT
            QtWidgets.QMessageBox.warning(self, "Uninstallation Not Possible",
                                          "You cannot uninstall GraphDonkey when running from source.\n"
                                          "If you really want to do this, clear the configuration files and "
                                          "remove the GraphDonkey repository locally.")
            return

        self.prog_uninstall.reset()
        self.lbl_uninstall_info.setText("Locating GraphDonkey files...")
        dr = IOHandler.dir_root("*")
        files = [f for f in glob.glob(dr, recursive=True)]
        dirs = []
        lf = len(files)
        for fix in range(lf - 1, -1, -1):
            file = files[fix]
            if file == __file__:
                continue
            if os.path.isdir(file):
                dirs.append(file)
            else:
                self.lbl_uninstall_info.setText("Removing %s..." % file.replace(dr[:-1], "GraphDonkey/"))
                QtCore.QFile.remove(file)
            self.prog_uninstall.setValue(((lf - fix - len(dirs)) // lf) * 100)
        QtCore.QDir(dr[:-1]).removeRecursively()
        self.lbl_uninstall_info.setText("Uninstalled GraphDonkey!")
        self.prog_uninstall.setValue(100)

    def clear(self):
        self.prog_clear.reset()

        self.lbl_clear_info.setText("Obtaining Settings...")
        sett = IOHandler.get_settings()
        self.prog_clear.setValue(10)

        self.lbl_clear_info.setText("Clearing Settings...")
        sett.clear()
        sett.sync()
        self.prog_clear.setValue(30)
        fmt = sett.format()
        rmpath = sys.platform == "win32" and fmt == QtCore.QSettings.NativeFormat
        if not rmpath:
            QtCore.QFile.remove(sett.fileName())
        self.prog_clear.setValue(50)

        self.lbl_clear_info.setText("Obtaining Preferences...")
        prefs = IOHandler.get_preferences()
        self.prog_clear.setValue(60)

        self.lbl_clear_info.setText("Clearing Preferences...")
        prefs.clear()
        prefs.sync()
        self.prog_clear.setValue(80)
        fmt = prefs.format()
        rmpath = sys.platform == "win32" and fmt == QtCore.QSettings.NativeFormat
        if not rmpath:
            QtCore.QFile.remove(prefs.fileName())
        self.prog_clear.setValue(100)
        self.lbl_clear_info.setText("Finished")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    wizard = UpdateWizard()
    wizard.show()
    app.exec_()
