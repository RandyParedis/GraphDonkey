"""This file tests if the version checking can be done correctly.

Author: Randy Paredis
Date:   12/16/2019
"""
from .context import version_lt

def test_version_lt():
    assert version_lt("0.0.0", "0.0.1")
    assert version_lt("0.0.0", "0.0.123")
    assert version_lt("0.0.0", "0.1.0")
    assert version_lt("0.0.0", "1.0.0")

    assert version_lt("0.0.9", "0.1.0")
    assert version_lt("0.1.9", "0.1.10")
    assert version_lt("0.1.9", "1.0.0")

    assert not version_lt("0.5.3", "0.1.2")
    assert not version_lt("0.5.3", "0.5.3")
