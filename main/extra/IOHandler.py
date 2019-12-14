"""
This file contains the IOHandler class,
a Singleton class that handles all
input/output functionality.
"""
from PyQt5 import QtCore
from main.extra import Constants
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
    def dir_main():
        return os.path.dirname(os.path.realpath(__file__))

    @staticmethod
    def dir_root(*paths):
        return os.path.realpath(IOHandler.join(__file__, "..", "..", "..", "..", *paths))

    @staticmethod
    def dir_ui(*paths):
        return os.path.realpath(IOHandler.join(__file__, "..", "..", "..", "ui", *paths))

    @staticmethod
    def dir_vendor(*path):
        return os.path.realpath(IOHandler.join(__file__, "..", "..", "..", "..", "vendor", *path))

    @staticmethod
    def dir_styles(*styles):
        return os.path.realpath(IOHandler.join(IOHandler.dir_vendor(), "styles", *styles))

    @staticmethod
    def dir_gen(*styles):
        return os.path.realpath(IOHandler.join(IOHandler.dir_vendor(), "generate", *styles))

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
    def dir_workspace():
        return os.path.realpath(IOHandler.join(__file__, "..", "..", "..", "..", "files"))

    @staticmethod
    def dir_config():
        return os.path.dirname(IOHandler.get_settings().fileName())

    @staticmethod
    def file_preferences():
        return os.path.realpath(IOHandler.join(IOHandler.dir_config(), "preferences.conf"))

    @staticmethod
    def file_sim():
        return os.path.realpath(IOHandler.join(IOHandler.dir_config(), "siminit"))

    @staticmethod
    def get_settings():
        return QtCore.QSettings(Constants.APP_NAME, "MainWindow")

    @staticmethod
    def delete(*files):
        for file in files:
            os.remove(file)