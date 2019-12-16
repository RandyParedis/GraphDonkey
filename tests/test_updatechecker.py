"""This file tests if the pkg_resources is installed

Author: Randy Paredis
Date:   12/16/2019
"""
from .context import IOHandler
import pkg_resources

def test_constructor():
    deps = []
    with open(IOHandler.dir_root("requirements.txt")) as f:
        deps = f.read().replace("\r", "").split("\n")
    deps = [x.split("#")[0].strip() for x in deps]
    deps = [x for x in deps if x != ""]

    updates = False
    try:
        pkg_resources.require(deps)
    except pkg_resources.DistributionNotFound as ex:
        updates = True
    except pkg_resources.VersionConflict as ex:
        updates = True