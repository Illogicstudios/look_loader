import importlib
from common import utils

utils.unload_packages(silent=True, package="look_loader")
importlib.import_module("look_loader")
from look_loader.LookLoader import LookLoader
try:
    look_loader.close()
except:
    pass
look_loader = LookLoader()
look_loader.show()
