"""Find and Replace dialog for the GraphDonkey application.

Author: Randy Paredis
Date:   17/12/2019
"""
from PyQt5 import QtWidgets, uic
from main.extra.IOHandler import IOHandler
import json


class Snippets(QtWidgets.QDialog):
    def __init__(self, parent):
        super(Snippets, self).__init__(parent)
        uic.loadUi(IOHandler.dir_ui("Snippets.ui"), self)
        self.snipfile = IOHandler.dir_vendor("snippets.json")

        with open(self.snipfile, 'r') as f:
            self.snippets = json.load(f)

        self.pb_add.clicked.connect(self.add)
        self.pb_remove.clicked.connect(self.remove)
        self.le_filter.textChanged.connect(self.filter)

    def exec_(self):
        self.le_filter.setText("")
        self.clear()
        self.table.setSortingEnabled(False)
        for name in self.snippets:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.set(r, name, self.snippets[name])
        self.table.setSortingEnabled(True)
        QtWidgets.QDialog.exec_(self)

    def accept(self):
        self.snippets = {}
        for row in range(self.table.rowCount()):
            name, code = self.get(row)
            self.snippets[name] = code
        with open(self.snipfile, 'w') as f:
            json.dump(self.snippets, f)
        QtWidgets.QDialog.accept(self)

    def set(self, row, name, code):
        self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(name))
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(code))

    def get(self, row):
        name = self.table.item(row, 0).text()
        code = self.table.item(row, 1).text()
        return name, code

    def add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.set(row, "", "")
        self.table.setCurrentCell(row, 0)

    def remove(self):
        row = self.table.currentRow()
        self.table.removeRow(row)

    def clear(self):
        while self.table.rowCount() > 0:
            self.table.removeRow(0)

    def filter(self, text):
        for row in range(self.table.rowCount()):
            name, _ = self.get(row)
            self.table.setRowHidden(row, text.lower() not in name.lower())

