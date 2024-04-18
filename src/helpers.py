import pathlib
import os
import json
import sys
import subprocess
import importlib
import site
from collections import namedtuple



model_id = "gvecchio/MatForger"

directory = os.path.dirname(os.path.realpath(__file__))
path_log = os.path.join(directory, "..", "path_log.json")

def path_log_exists() -> bool:
    return os.path.exists(path_log) and os.path.isfile(path_log)

current_drive = path_log if path_log_exists() else os.path.join(pathlib.Path.home().drive, os.sep)
# Dependencies

# Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
# set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
# of the arguments. DO NOT use this to import other parts of this Python add-on, see "Local modules" above for examples.

dependence_dict = {
        "pywin32": [],
        "fire": [],
        "numpy": [],
        "diffusers": [],
        "transformers": [],
        "accelerate": [],
        "torch==2.2.2+cu121": ["--index-url", "https://download.pytorch.org/whl/cu121"],
}

Dependency = namedtuple("Dependency", ["module", "name", "extra_params"])
dependencies = [Dependency(module=i, name=None, extra_params=j) for i, j in dependence_dict.items()]
dependencies_installed = False



def set_dependencies_installed(are_installed):
    global dependencies_installed
    dependencies_installed = are_installed

def create_path_log(path: str, path_name=str):
    print(f"\n{path_log}\n")
    json_data = json.dumps({path_name: path}, indent=1, ensure_ascii=True)

    with open(path_log, 'w') as outfile:
        outfile.write(json_data + '\n')

    return path_log

# Returns true if dependency has been installed.
def is_installed(dependency: str) -> bool:
    try:
        # Blender does not add the user's site-packages/ directory by default.
        sys.path.append(site.getusersitepackages())
        if "==" in dependency:
            dependency = dependency.split("==")[0]
        return importlib.util.find_spec(dependency) is not None
    finally:
        sys.path.remove(site.getusersitepackages())

def install_pip():
    """
    Installs pip if not already present. Please note that ensurepip.bootstrap() also calls pip, which adds the
    environment variable PIP_REQ_TRACKER. After ensurepip.bootstrap() finishes execution, the directory doesn't exist
    anymore. However, when subprocess is used to call pip, in order to install a package, the environment variables
    still contain PIP_REQ_TRACKER with the now nonexistent path. This is a problem since pip checks if PIP_REQ_TRACKER
    is set and if it is, attempts to use it as temp directory. This would result in an error because the
    directory can't be found. Therefore, PIP_REQ_TRACKER needs to be removed from environment variables.
    :return:
    """

    try:
        # Check if pip is already installed
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        import ensurepip

        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)

def install_modules(venv_path: str, ):
    """
    Installs the package through pip and will attempt to import modules into the Venv, or if make_global = True import
    them globally.
    :param import_global: Makes installed modules global if True, will not install imports to Venv. If false, modules
        will only be installed to the Venv to be used with the Stable Diffusion libraries.
    :raises: subprocess.CalledProcessError and ImportError

    Deprecated:
    module_name: Module to import.
    package_name: (Optional) Name of the package that needs to be installed. If None it is assumed to be equal
       to the module_name.
    global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    """

    print(f"Installing dependencies: {''.join([i.module for i in dependencies])}")

    for dependency in dependencies:
        module_name = dependency.module
        extra_params = dependency.extra_params
        make_global = False

        if "make_global" in extra_params:
            extra_params.remove("make_global")
            make_global = True

        # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
        # if a dependency is already installed. This can cause problems if the packages is installed in the user
        # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
        # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
        # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
        # The paths used by pip can be checked with the following:
        # `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

        # Create a copy of the environment variables and modify them for the subprocess call

        environ_copy = dict(os.environ)
        environ_copy["PYTHONNOUSERSITE"] = "1"

        install_commands_list = [
                os.path.join(venv_path, "Scripts", "python"),
                "-m",
                "pip",
                "install",
                module_name
        ]

        if extra_params:
            install_commands_list.extend(extra_params)

        if not make_global:
            print(f"\nInstalling {module_name} to {venv_path}.\n")
            if is_installed(module_name):
                print(f"Module {module_name} already installed.")
            else: 
                try:
                    subprocess.run(
                            install_commands_list,
                            check=True,
                            env=environ_copy
                    )
                except subprocess.CalledProcessError as e:
                    print(f"Exception occurred while installing {dependency.module_name}: \n\n{e}")


def read_path_log():
    if path_log_exists():
        return json.load(open(path_log))
    

def import_modules(venv_path: str):
    site_packages_path = os.path.join(venv_path, "Lib", "site-packages")
    sys.path.insert(0, site_packages_path) #HACK Ugly but working way to import installed packages


def show_blender_system_console():
    import win32gui

    def enum_windows_callback(hwnd, results):
        class_name = win32gui.GetClassName(hwnd)
        if class_name == "ConsoleWindowClass":
            results.append((hwnd, win32gui.GetWindowText(hwnd)))

    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)

    for hwnd, title in windows:
        if title=="":
            break

    print(f"The Blender console window is {hwnd}")

    # Check if the window is visible or hidden
    is_visible = win32gui.IsWindowVisible(hwnd)

    if is_visible:
        print("The window is visible.")
        win32gui.SetForegroundWindow(hwnd)
    else:
        print("The window is hidden.")
        bpy.ops.wm.console_toggle()