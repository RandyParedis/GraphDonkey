"""
This file is the entrypoint of the GUI for grapher.
It reads the commandline arguments and launches the
MainWindow in maximized modus.
"""

from PyQt5 import QtWidgets
from main.extra import Constants
from main.MainWindow import MainWindow
import sys, graphviz

print("LAUNCING APP...")
print("GraphViz Version:", graphviz.__version__)
app = QtWidgets.QApplication(sys.argv)
app.setApplicationName(Constants.APP_NAME + " " + Constants.APP_VERSION)
mainwindow = MainWindow()
mainwindow.showMaximized()
code = app.exec_()