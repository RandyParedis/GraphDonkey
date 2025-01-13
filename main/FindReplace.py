"""Find and Replace dialog for the GraphDonkey application.

Author: Randy Paredis
Date:   17/12/2019
"""
from PyQt6 import QtWidgets, QtGui, QtCore, uic
from main.extra.IOHandler import IOHandler
import re


class FindReplace(QtWidgets.QDialog):
    def __init__(self, parent, editor):
        super(FindReplace, self).__init__(parent)
        uic.loadUi(IOHandler.dir_ui("FindReplace.ui"), self)
        self.editor = editor

        self.pb_find.clicked.connect(self.findText)
        self.pb_close.clicked.connect(self.close)
        self.pb_replace.clicked.connect(self.replace)
        self.pb_replaceAll.clicked.connect(self.replaceAll)

        self.le_find.textChanged.connect(self.findChanged)
        self.le_replace.textChanged.connect(self.replaceTextChanged)

        self.check_case.clicked.connect(self.findChanged)
        self.check_words.clicked.connect(self.findChanged)
        self.check_regex.clicked.connect(self.findChanged)

        self.replaceTextChanged("")
        self.setError("")

        self.idx = -1

    def findChanged(self, text=None):
        self.get()  #< Check validity
        self.idx = -1
        self.editor.matches = []
        self.editor.highlightMatches()

    def replaceTextChanged(self, text):
        self.pb_replace.setEnabled(text != "")
        self.pb_replaceAll.setEnabled(text != "")

    def caseSensitive(self):
        return self.check_case.isChecked()

    def wholeWords(self):
        return self.check_words.isChecked()

    def useRegEx(self):
        return self.check_regex.isChecked()

    def up(self):
        return self.radio_dir_up.isChecked()

    def down(self):
        return self.radio_dir_down.isChecked()

    def close(self):
        self.findChanged()
        QtWidgets.QDialog.close(self)

    def get(self):
        text = self.le_find.text()
        if not self.useRegEx():
            text = QtCore.QRegularExpression.escape(text)
        if self.wholeWords():
            text = r"\b" + text.replace(" ", r"\b") + r"\b"
        options = QtCore.QRegularExpression.PatternOption.NoPatternOption
        if not self.caseSensitive():
            options |= QtCore.QRegularExpression.PatternOption.CaseInsensitiveOption
        reg = QtCore.QRegularExpression(text, options)
        if reg.isValid():
            self.setInfo("")
        else:
            self.setError(reg.errorString())
        return reg

    def findText(self):
        cursor = self.editor.textCursor()
        if self.idx == -1:
            start = cursor.selectionStart()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End, QtGui.QTextCursor.MoveMode.KeepAnchor)
            text = cursor.selectedText()

            self.editor.matches = []
            regex = self.get()
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                if match.hasMatch():
                    self.editor.matches.append((match.capturedStart(), match.capturedEnd(), match))

            l = len(self.editor.matches)

            for i in range(l):
                if start <= self.editor.matches[i][0]:
                    self.idx = i
                    break
            if self.up():
                self.idx -= 1
            if l > 0:
                self.idx %= l

            if l == 0:
                self.setInfo("No matches found.")
            elif l == 1:
                self.setInfo("1 match found.")
            else:
                self.setInfo("%i matches found." % l)

        l = len(self.editor.matches)

        if self.idx != -1:
            if self.down():
                self.idx = (self.idx + 1) % l
            else:
                self.idx = (self.idx - 1) % l

        if l > 0:
            cursor.setPosition(self.editor.matches[self.idx][0])
            cursor.setPosition(self.editor.matches[self.idx][1], QtGui.QTextCursor.MoveMode.KeepAnchor)
            self.editor.setTextCursor(cursor)
        self.editor.highlightMatches()

    def replaceMatch(self, match):
        start, end, rem = match
        cursor = self.editor.textCursor()

        text = self.le_replace.text()
        if self.useRegEx():
            capregex = QtCore.QRegularExpression(r"(?<![\\])\$(\d+)")
            iter = capregex.globalMatch(text)
            ms = []
            while iter.hasNext():
                match = iter.next()
                if match.hasMatch():
                    ms.append(match)
            for m in range(len(ms), 0, -1):
                match = ms[m-1]
                group = int(match.captured(1))
                st = rem.capturedStart(group)
                if st != -1:
                    cursor.setPosition(st)
                    cursor.setPosition(rem.capturedEnd(group), QtGui.QTextCursor.MoveMode.KeepAnchor)
                    mtxt = cursor.selectedText()
                    text = text[:match.capturedStart()] + mtxt + text[match.capturedEnd():]
            text = text.replace(r"\$", "$")

        cursor.setPosition(start)
        cursor.setPosition(end, QtGui.QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(text)

    def replace(self):
        self.findText()
        if len(self.editor.matches) > 0:
            self.replaceMatch(self.editor.matches[self.idx])
        self.findChanged()
        self.findText()
        self.editor.updateLineNumberArea()

    def replaceAll(self):
        self.findText()
        while len(self.editor.matches) > 0:
            self.replace()

    def setInfo(self, msg):
        if msg == "":
            self.label_error.setText("")
        else:
            self.label_error.setText(msg)

    def setError(self, msg):
        if msg == "":
            self.label_error.setText("")
        else:
            self.label_error.setText("<span style='color: red'><b>Error:</b> %s</span>" % msg)
