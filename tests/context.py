"""This file identifies the imports for all test suites.

Author: Randy Paredis
Date:   12/16/2019
"""

from __future__ import absolute_import

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main.extra.IOHandler import IOHandler
from main.editor.Intellisense import Trie
from main import extra
from main.wizards.UpdateWizard import version_lt

# Prevent the deletion of 'unused' imports
_ioh = IOHandler
_trie = Trie
_ex = extra
_vlt = version_lt
