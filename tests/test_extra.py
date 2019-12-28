"""This file tests the main.extra.__init__ functions for correctness.

Author: Randy Paredis
Date:   12/28/2019
"""

from .context import extra

def test_tabPathnames():
    lst = ['undefined', 'undefined', 'test/example.gv', 'other/example.gv', 'main.py',
           'other/test/oom-pah-pah.txt', 'other/test/bluh.txt', 'test/oof.gv', 'test/test/oof.gv']
    result = extra.tabPathnames(lst)
    assert result == ['undefined', 'undefined', 'test/example.gv', 'other/example.gv', 'main.py',
           'oom-pah-pah.txt', 'bluh.txt', 'test/oof.gv', 'test/test/oof.gv']
