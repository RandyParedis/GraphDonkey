"""This file handles all additional installation/uninstall and update features.

Maybe, it can be extended to a generic installer in the future.

Author: Randy Paredis
Date:   02/05/2020
"""

from PyQt5 import QtWidgets, QtCore, uic, QtNetwork
from main.extra.IOHandler import IOHandler
from main.extra import Constants
from urllib.request import urlretrieve
from zipfile import ZipFile
import sys, glob, os, json, time

UPDATE_URL = "https://api.github.com/repos/RandyParedis/GraphDonkey/releases/latest"

def version_lt(v1, v2):
    # TODO: write a test for this method call
    M1, m1, s1 = [int(x) for x in v1.split(".")]
    M2, m2, s2 = [int(x) for x in v2.split(".")]
    return (s1 < s2 and m1 <= m2 and M1 <= M2) or (m1 < m2 and M1 <= M2) or (M1 < M2)

class UpdateWizard(QtWidgets.QWizard):
    class Pages:
        START = 0
        UNINSTALL = 1
        CLEAR = 2
        UPDATES = 3

    def __init__(self, parent = None):
        super(UpdateWizard, self).__init__(parent, QtCore.Qt.Dialog)
        uic.loadUi(IOHandler.dir_ui("UpdateWizard.ui"), self)

        self.uninstallPage.isComplete = lambda: self.prog_uninstall.value() == 100
        self.clearPage.isComplete = lambda: self.prog_clear.value() == 100
        self.updatesPage.isComplete = lambda: self.prog_updates.value() == 100

        self.nwm = QtNetwork.QNetworkAccessManager(self)
        self.nwm.finished.connect(self.do_update)

        self.pb_clear.clicked.connect(self.clear)
        self.prog_clear.valueChanged.connect(lambda _: self.clearPage.completeChanged.emit())
        self.pb_uninstall.clicked.connect(self.uninstall)
        self.prog_uninstall.valueChanged.connect(lambda _: self.uninstallPage.completeChanged.emit())
        self.pb_update.clicked.connect(self.updateGD)
        self.prog_updates.valueChanged.connect(lambda _: self.updatesPage.completeChanged.emit())


    def nextId(self):
        cid = self.currentId()
        if cid == UpdateWizard.Pages.START:
            if self.rd_updates.isChecked():
                return UpdateWizard.Pages.UPDATES
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

    def updateGD(self):
        self.prog_updates.reset()
        self.lbl_updates_info.setText("Obtaining available updates...")
        if not (getattr(sys, 'frozen', None) and hasattr(sys, '_MEIPASS')):
            # PREVENTS UPDATING FROM SOURCE
            QtWidgets.QMessageBox.warning(self, "Updates Not Available",
                                          "You cannot update GraphDonkey when running from source.\n"
                                          "If you really want to do this, please pull the latest version of the"
                                          " repository.")
            self.lbl_updates_info.setText("Updates not available.")
            return
        self.nwm.get(QtNetwork.QNetworkRequest(QtCore.QUrl(UPDATE_URL)))

    def do_update(self, reply: QtNetwork.QNetworkReply):
        error = reply.error()
        if error != QtNetwork.QNetworkReply.NoError:
            QtWidgets.QMessageBox.warning(self, "Network Error", reply.errorString())
            self.lbl_updates_info.setText("Network Error.")
            return
        self.lbl_updates_info.setText("Checking versions...")
        self.prog_updates.setValue(0)
        resp = reply.readAll().data()
        rjson = json.loads(resp)
        target = IOHandler.dir_root()
        if version_lt(Constants.APP_VERSION, rjson["tag_name"][1:]):
            assets = rjson["assets"]
            durl = None
            size = 0
            name = ""
            for asset in assets:
                if (sys.platform == "win32" and "windows" in asset["name"]) or \
                        (sys.platform == "linux" and "linux" in asset["name"]):
                    durl = asset["browser_download_url"]
                    size = asset["size"]
                    name = asset["name"]
                    break
            if durl is None:
                QtWidgets.QMessageBox.warning(self, "Update Error", "There is no new version available for your system.")
                self.lbl_updates_info.setText("No update available.")
                self.prog_updates.setValue(100)
                return

            # Remove all files and folders except the 'vendor' dir
            self.lbl_updates_info.setText("Clearing existing installation...")
            self.prog_updates.setValue(1)
            files = QtCore.QDir(target).entryList()
            for file in files:
                if file in [".", "..", "vendor"]: continue
                path = IOHandler.join(target, file)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    QtCore.QDir(path).removeRecursively()

            self.lbl_updates_info.setText("Fetching archive...")
            self.prog_updates.setValue(5)
            time.sleep(0.01)
            zipf = IOHandler.join(target, name)
            def reph(bcnt, bsz, _):
                self.prog_updates.setValue(5 + ((bcnt * bsz * 25) // size))
            urlretrieve(durl, zipf, reph)

            self.lbl_updates_info.setText("Extracting archive...")
            self.prog_updates.setValue(30)
            time.sleep(0.01)
            baseName = "GraphDonkey/"
            with ZipFile(zipf) as zf:
                amount = len(zf.namelist())
                i = 0
                for member in zf.infolist():
                    name = member.filename.replace(baseName, "", 1)
                    if name == "": continue
                    loc = IOHandler.join(target, name)
                    if loc.endswith(os.sep):
                        os.mkdir(loc)
                    else:
                        with open(loc, "wb") as outfile:
                            outfile.write(zf.read(member))
                    self.prog_updates.setValue(30 + ((i * 60) // amount))
                    i += 1

            self.lbl_updates_info.setText("Update complete!")
            self.prog_updates.setValue(100)
        else:
            self.lbl_updates_info.setText("You already have the latest version!")
            self.prog_updates.setValue(100)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    wizard = UpdateWizard()
    wizard.show()
    app.exec_()
