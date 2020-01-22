"""Find and Replace dialog for the GraphDonkey application.

Author: Randy Paredis
Date:   17/12/2019
"""
from PyQt5 import QtWidgets, uic
from main.extra.IOHandler import IOHandler
from main.plugins import PluginLoader
import json

pluginloader = PluginLoader.instance()

class Snippets(QtWidgets.QDialog):
    def __init__(self, parent):
        super(Snippets, self).__init__(parent)
        uic.loadUi(IOHandler.dir_ui("Snippets.ui"), self)
        self.snipfile = IOHandler.dir_vendor("snippets.json")

        with open(self.snipfile, 'r') as f:
            self.snippets = json.load(f)

        self.pb_add.clicked.connect(self.add)
        self.pb_remove.clicked.connect(self.remove)
        self.pb_duplicate.clicked.connect(self.duplicate)
        self.le_filter.textChanged.connect(self.filter)

    def exec_(self):
        self.le_filter.setText("")
        self.clear()
        self.table.setSortingEnabled(False)
        for type in self.snippets:
            for name in self.snippets[type]:
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.set(r, name, self.snippets[type][name], type=type)
        self.table.setSortingEnabled(True)
        QtWidgets.QDialog.exec_(self)

    def accept(self):
        self.snippets = {}
        for row in range(self.table.rowCount()):
            type, name, code = self.get(row)
            if type not in self.snippets:
                self.snippets[type] = {}
            self.snippets[type][name] = code
        with open(self.snipfile, 'w') as f:
            json.dump(self.snippets, f)
        QtWidgets.QDialog.accept(self)

    def set(self, row, name, code, type=""):
        combo = QtWidgets.QComboBox(self.table)
        for it in pluginloader.getFileTypes():
            if len(it) > 0:
                combo.addItem(it)
        combo.setCurrentText(type)
        self.table.setCellWidget(row, 0, combo)
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(name))
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(code))

    def get(self, row):
        combo = self.table.cellWidget(row, 0).currentText()
        name = self.table.item(row, 1).text()
        code = self.table.item(row, 2).text()
        return combo, name, code

    def add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.set(row, "", "")
        self.table.setCurrentCell(row, 0)

    def remove(self):
        row = self.table.currentRow()
        self.table.removeRow(row)

    def duplicate(self):
        row = self.table.currentRow()
        t, n, c = self.get(row)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.set(row, n, c, t)

    def clear(self):
        while self.table.rowCount() > 0:
            self.table.removeRow(0)

    def filter(self, text):
        for row in range(self.table.rowCount()):
            _, name, _ = self.get(row)
            self.table.setRowHidden(row, text.lower() not in name.lower())

