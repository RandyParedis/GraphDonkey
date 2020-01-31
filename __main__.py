#!/usr/bin/env python3
"""
This file is the entrypoint of the GUI for GraphDonkey.
It launches the MainWindow in maximized modus and sets
all application information.

Author: Randy Paredis
Date:   12/14/2019
"""
import os, sys
from main.extra.IOHandler import IOHandler

depfol = IOHandler.dir_plugins(".dependencies")
if not os.path.isdir(depfol):
    os.mkdir(depfol)
sys.path.append(depfol)

from PyQt5 import QtWidgets
from main.extra import Constants
from main.MainWindow import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(Constants.APP_NAME)
    app.setApplicationVersion(Constants.APP_VERSION)
    app.setApplicationDisplayName(
        Constants.APP_NAME + " [" + Constants.APP_VERSION_NAME + "] v" + Constants.APP_VERSION)
    app.setWindowIcon(Constants.APP_ICON)

    print("LAUNCING APP...")
    print("GraphDonkey Version:", Constants.APP_VERSION_NAME, "(" + Constants.APP_VERSION + ")")

    mainwindow = MainWindow()
    mainwindow.show()
    code = app.exec_()
