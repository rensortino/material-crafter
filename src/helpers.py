import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import bpy

class PathManager(object):
    """
    Singleton class for path management
    """

    def __init__(self, paths_file_name: str = "paths.json"):
        self.named_paths = {
            "material_crafter": self.default_path,
            "model": Path.home() / ".cache/huggingface",
            "texture_output": Path.home() / ".tmp"
        }
        self.named_paths["venv"] = self.named_paths['material_crafter'] / "venv"
        directory = Path(__file__).parent
        self.paths_file = Path(directory.parent / paths_file_name)
        self.load_paths_file()
        self.named_paths["site-packages"] = self.named_paths['venv'] / "Lib" / "site-packages"

    def __new__(self):
        if not hasattr(self, "_instance"):
            self._instance = super(PathManager, self).__new__(self)
        return self._instance

    @property
    def default_path(self):
        return Path.home() / os.sep

    def paths_file_exists(self) -> bool:
        return self.paths_file.exists() and self.paths_file.is_file()

    def load_paths_file(self):
        if self.paths_file_exists():
            loaded_paths = json.load(open(self.paths_file))
            self.named_paths = {k: Path(v) for k, v in loaded_paths.items()}
    
    def add_venv_path_visibility(self):
        if not (self.named_paths['site-packages']).as_posix() in sys.path:
            sys.path.insert(0, self.named_paths['site-packages'].as_posix())

    def save_named_paths(self):
        paths_as_strings = {k: v.as_posix() for k, v in self.named_paths.items()}
        json_data = json.dumps(paths_as_strings, indent=1, ensure_ascii=True)

        with open(self.paths_file, "w") as outfile:
            outfile.write(json_data + "\n")

    def update_named_paths(self, path, path_name = str):
        self.named_paths[path_name] = Path(path)
        self.save_named_paths()

pm = PathManager()
# Dependencies

# Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
# set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
# of the arguments. DO NOT use this to import other parts of this Python add-on, see "Local modules" above for examples.

with open(pm.paths_file.parent / "requirements.json") as f:
    dependencies = json.load(f)

dependencies_installed = False


def set_dependencies_installed(are_installed):
    global dependencies_installed
    dependencies_installed = are_installed

def dependencies_installed() -> bool:
    try:
        for dependency in dependencies:
            import_module(dependency)
        return True
    except ImportError:
        # Don't register other panels, operators etc.
        return False
    
def is_installed(dependency):
    try:
        import_module(dependency)
        return True
    except ImportError:
        return False

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


def install_modules(
    venv_path: str,
    context
):
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

    print(f"Installing dependencies: {', '.join([i for i in dependencies])}")
    
    for i, (module_name, module_params) in enumerate(dependencies.items()):
        if "version" in module_params:
            module_name += f"=={module_params['version']}"
        extra_params = module_params['extra_params']

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
            venv_path / "Scripts" / "python",
            "-m",
            "pip",
            "install",
            module_name,
        ]

        if extra_params:
            install_commands_list.extend(extra_params)

        print(f"\nInstalling {module_name} to {venv_path}.\n")
        context.window_manager.progress = (i+1) / len(dependencies)
        context.window_manager.progress_text = f"Installing {module_name} [{i+1}/{len(dependencies)}]"
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1, time_limit=0.0)
        try:
            subprocess.run(install_commands_list, check=True, env=environ_copy)
        except subprocess.CalledProcessError as e:
            print(
                f"Exception occurred while installing {module_name}: \n\n{e}"
            )
            context.window_manager.progress_text = f"Error installing {module_name}"
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1, time_limit=0.0)
    context.window_manager.progress = 1


def execution_handler(
    venv_path: str, operation_function: str, user_input: dict, output: bool = True
):
    """
    In order for the Venv to work inside Blender, we must run the script as the Venv is activated
    inside the actual 'activate.bat' file that Venv generates. This means that for each interaction with Stable Diffusion
    we must input the commands into the activate.bat file, then run the file with Subprocess.

    This file controls the interactions with the activate.bat file, it opens, modifies, and runs the files depending on
    what functions are needed by Material Crafter. Each main function, when called, will activate Stable Diffusion with the
    appropriate input variables.
    """

    activate_bat_path = venv_path / "Scripts" / "activate.bat"
    activate_and_run_path = venv_path / "Scripts" / "activate_and_run.bat"
    python_exe_path = venv_path / "Scripts" / "python.exe"

    sd_interface_path = Path(__file__).parent / "sd_functions.py"

    # Get args from user_input:
    args_string = " "
    for (
        arg_name,
        arg_value,
    ) in user_input.items():  # user_input: {param_name: param_value}
        args_string += f"""--{arg_name} "{arg_value}" """

    commands = [
        f"""
            "{python_exe_path}" "{sd_interface_path}" {operation_function}{args_string} 
            """,  # NOTE: "operation_function" is the name of the function in sd_interface.py given to the command line.
    ]

    # Send commands to activate.bat
    with open(activate_bat_path, "rt") as bat_in:
        with open(activate_and_run_path, "wt") as bat_out:
            for line in bat_in:
                bat_out.write(line)

            for line in commands:
                bat_out.write(f"\n{line}")

    # Run activate.bat, activate Venv:
    # if output:
    try:
        output = subprocess.check_output(
            activate_and_run_path.as_posix(),
        )
    except subprocess.CalledProcessError as e:
        raise e


def import_modules(venv_path: str):
    for module_name in dependencies:
        import_module(module_name)


def import_module(module_name):
    """
    Import a module.
    :param module_name: Module to import.
    :raises: ImportError and ModuleNotFoundError
    """
    
    pm.add_venv_path_visibility()
    globals()[module_name] = importlib.import_module(module_name)

def check_drive_space(path: str = os.getcwd()):
    """
    Checks current drive if it has enough available space to store the Environment and Stable Diffusion weights.
    """
    total, used, free = shutil.disk_usage(path)
    required_space = 15 * 2**30 # Convert to GB
    free_after = free - required_space

    if free_after < 0:
        return False
    elif free_after > 5 * 2**30:
        print("WARNING: Less than 5GB will be left after completing installation")
    return True
