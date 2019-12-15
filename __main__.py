"""
This file is the entrypoint of the GUI for grapher.
It reads the commandline arguments and launches the
MainWindow in maximized modus.
"""

import sys, graphviz
from PyQt5 import QtWidgets
from main.MainWindow import MainWindow
from main.extra import Constants

print("LAUNCING APP...")
print("GraphViz Version:", graphviz.__version__)
print("GraphDonkey Version:", Constants.APP_VERSION)
app = QtWidgets.QApplication(sys.argv)
app.setApplicationName(Constants.APP_NAME)
app.setApplicationVersion(Constants.APP_VERSION)
app.setApplicationDisplayName(Constants.APP_NAME + " v" + Constants.APP_VERSION)
app.setWindowIcon(Constants.APP_ICON)
mainwindow = MainWindow()
mainwindow.showMaximized()
code = app.exec_()
