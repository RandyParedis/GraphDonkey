"""
This file contains the IOHandler class, a static class that handles all
input/output functionality.

Author: Randy Paredis
Date:   12/14/2019
"""
from PyQt5 import QtCore
import xml.etree.ElementTree as ET
import os

class IOHandler:
    @staticmethod
    def pwd():
        return os.getcwd()

    @staticmethod
    def join(*path):
        return os.path.join(*path)

    @staticmethod
    def directory(path):
        return os.path.dirname(path)

    @staticmethod
    def dir_main():
        return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    @staticmethod
    def dir_root(*paths):
        return os.path.realpath(IOHandler.join(IOHandler.dir_main(), "..", *paths))

    @staticmethod
    def dir_vendor(*path):
        return os.path.realpath(IOHandler.join(IOHandler.dir_root(), "vendor", *path))

    @staticmethod
    def dir_ui(*paths):
        return os.path.realpath(IOHandler.join(IOHandler.dir_vendor(), "ui", *paths))

    @staticmethod
    def dir_styles(*styles):
        return os.path.realpath(IOHandler.join(IOHandler.dir_vendor(), "styles", *styles))

    @staticmethod
    def dir_icons(*icons):
        return os.path.realpath(IOHandler.join(IOHandler.dir_vendor(), "icons", *icons))

    @staticmethod
    def dir_grammars(*grammars):
        return os.path.realpath(IOHandler.join(IOHandler.dir_vendor(), "grammars", *grammars))

    @staticmethod
    def dir_plugins(*plugins):
        return os.path.realpath(IOHandler.join(IOHandler.dir_vendor(), "plugins", *plugins))

    @staticmethod
    def dir_lang(*lang):
        return os.path.realpath(IOHandler.join(IOHandler.dir_vendor(), "i18n", *lang))

    @staticmethod
    def langs():
        path = IOHandler.dir_lang()
        files = [f for f in os.listdir(path) if os.path.isfile(IOHandler.join(path, f)) and f.endswith(".ts")]
        res = [{
            "name": QtCore.QLocale("en_US").nativeLanguageName(),
            "value": "en_US"
        }]
        for file in files:
            root = ET.parse(IOHandler.join(path, file)).getroot()
            lang = root.attrib['language']
            res.append({"name": QtCore.QLocale(lang).nativeLanguageName(), "value": lang})
        return res

    @staticmethod
    def dir_config():
        return os.path.dirname(IOHandler.get_settings().fileName())

    @staticmethod
    def file_preferences():
        return os.path.realpath(IOHandler.join(IOHandler.dir_config(), "preferences.conf"))

    @staticmethod
    def get_settings():
        return QtCore.QSettings(Constants.APP_NAME, "MainWindow")

    @staticmethod
    def get_preferences():
        return QtCore.QSettings(Constants.APP_NAME, "Preferences")

    @staticmethod
    def delete(*files):
        for file in files:
            os.remove(file)

from main.extra import Constants
