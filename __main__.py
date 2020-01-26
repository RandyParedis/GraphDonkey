#!/usr/bin/env python3
"""
This file is the entrypoint of the GUI for GraphDonkey.
It launches the MainWindow in maximized modus and sets
all application information.

Author: Randy Paredis
Date:   12/14/2019
"""
import sys, subprocess
from pathlib import Path
from PyQt5 import QtWidgets
from main.extra.IOHandler import IOHandler

def startup():
    # TODO: check which are installed already and ignore those
    # Create the requirements for all the plugins
    pathlist = Path(IOHandler.dir_plugins()).glob('**/requirements.txt')
    reqs = set()
    for path in pathlist:
        data = path.open().read()
        reqs = reqs.union(data.split("\n"))
    reqfile = IOHandler.dir_plugins(".requirements.txt")
    with open(reqfile, 'w') as file:
        file.write("\n".join([
            "################################################################################",
            "#                   AUTOMATIC FILE CREATED FROM GRAPHDONKEY.                   #",
            "#         ANY CHANGES MADE TO THIS FILE WILL BE OVERWRITTEN ON STARTUP         #",
            "#  IF YOU WANT TO ADD REQUIREMENTS FOR YOUR OWN PLUGIN, PLEASE CREATE A VALID  #",
            "#          requirements.txt FILE IN THE ROOT DIRECTORY OF YOUR PLUGIN          #",
            "################################################################################", "\n"]))
        file.write("\n".join(reqs))

    # Install the plugin requirements locally
    depfol = ".dependencies"
    subprocess.check_call(['python3', '-m', 'pip', 'install', '-t', IOHandler.dir_plugins(depfol), '-r', reqfile,
                           '--upgrade'])

    # Alter the system path
    sys.path.append(IOHandler.dir_plugins(depfol))

if __name__ == '__main__':
    startup()

    from main.MainWindow import MainWindow
    from main.extra import Constants

    print("LAUNCING APP...")
    print("GraphDonkey Version:", Constants.APP_VERSION_NAME, "(" + Constants.APP_VERSION + ")")

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(Constants.APP_NAME)
    app.setApplicationVersion(Constants.APP_VERSION)
    app.setApplicationDisplayName(Constants.APP_NAME + " [" + Constants.APP_VERSION_NAME + "] v" + Constants.APP_VERSION)
    app.setWindowIcon(Constants.APP_ICON)

    mainwindow = MainWindow()
    mainwindow.show()
    code = app.exec_()
