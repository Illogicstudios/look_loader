import sys
import importlib

if __name__ == '__main__':
    # TODO specify the right path
    install_dir = 'PATH/TO/look_loader'
    if not sys.path.__contains__(install_dir):
        sys.path.append(install_dir)

    modules = [
        "LookStandin",
        "LookLoader"
    ]

    from utils import *
    unload_packages(silent=True, packages=modules)

    for module in modules:
        importlib.import_module(module)

    from LookLoader import *

    try:
        look_loader.close()
    except:
        pass
    look_loader = LookLoader()
    look_loader.show()
