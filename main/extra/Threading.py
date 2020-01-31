"""Handles all threading functionality

Author: Randy Paredis
Date:   01/27/2020
"""

import time
from PyQt5 import QtCore


class WorkerThread(QtCore.QThread):
    def __init__(self, func):
        QtCore.QThread.__init__(self)
        self.func = func

    def __del__(self):
        self.wait()

    def run(self):
        time.sleep(0.01)  # << Make sure the thread is at least this amount of time active
        self.func()
