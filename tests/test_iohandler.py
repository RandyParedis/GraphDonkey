"""This file tests the main.extra.IOHandler for correct folder names.

Author: Randy Paredis
Date:   12/16/2019
"""

from .context import IOHandler

def test_dir_main():
    split = IOHandler.dir_main().split("/")
    assert split[-1] == "main"