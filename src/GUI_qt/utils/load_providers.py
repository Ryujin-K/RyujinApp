import os
import importlib.util
from typing import List
from pathlib import Path
from GUI_qt.utils.config import get_config
from platformdirs import user_data_path
from core.providers.domain.provider_repository import ProviderRepository

data_path = user_data_path('RyujinApp')

def base_path():
    """ Retorna o caminho absoluto para a pasta 'src' da aplicação. """
    import sys
    try:
        if getattr(sys, 'frozen', False):
            # When packaged, the data is in the same directory as the executable.
            application_path = os.path.dirname(sys.executable)
            # Check if there is a 'src' folder in the executable directory
            src_path = Path(application_path) / 'src'
            if src_path.exists():
                return src_path
            # If it doesn't exist, assume the executable is at the root of the project
            return Path(application_path)
        script_path = Path(__file__).resolve()
        src_folder = script_path.parent.parent.parent
        return src_folder
    except NameError:
        return Path('.')

def find_assets_path():
    """
    Find the path to the assets folder.
    Try different possible locations where the assets might be.
    """
    import sys
    
    possible_paths = []
    
    # Using base_path() (original method)
    try:
        current_dir = os.path.join(base_path(), 'GUI_qt')
        assets_path = os.path.join(current_dir, 'assets')
        possible_paths.append(assets_path)
    except:
        pass

    # Relative to the executable directory (for compiled versions)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        possible_paths.extend([
            os.path.join(exe_dir, 'GUI_qt', 'assets'),
            os.path.join(exe_dir, 'src', 'GUI_qt', 'assets'),
            os.path.join(exe_dir, 'assets'),
        ])

    # Relative to the current file
    try:
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths.extend([
            os.path.join(current_file_dir, '..', 'assets'),
            os.path.join(current_file_dir, '..', '..', 'GUI_qt', 'assets'),
        ])
    except:
        pass

    # Based on the current working directory
    cwd = os.getcwd()
    possible_paths.extend([
        os.path.join(cwd, 'GUI_qt', 'assets'),
        os.path.join(cwd, 'src', 'GUI_qt', 'assets'),
        os.path.join(cwd, 'assets'),
    ])

    # Find the first valid path that contains at least styles.qss or main.ui
    for path in possible_paths:
        normalized_path = os.path.normpath(path)
        if os.path.exists(normalized_path) and (
            os.path.exists(os.path.join(normalized_path, 'main.ui')) or
            os.path.exists(os.path.join(normalized_path, 'styles.qss'))
        ):
            return normalized_path

    # If no path was found, return the first one in the list and let the original error show
    return os.path.normpath(possible_paths[0]) if possible_paths else os.path.join(os.getcwd(), 'GUI_qt', 'assets')

package_path = os.path.join(base_path(), 'core', 'providers', 'infra')
ignore_folders = ['template', '__pycache__']

def _get_class(package_path, ignore_folders):
    classes = []

    for root, dirs, files in os.walk(package_path):
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        
        for file in files:
            if file.endswith('.py'):
                module_name = os.path.splitext(file)[0]
                module_path = os.path.join(root, file)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and name.endswith('Provider'):
                        classes.append(obj)
    
    return classes

def import_classes_recursively() -> List[ProviderRepository]:
    global ignore_folders, package_path
    classes = []

    config = get_config()

    classes += _get_class(package_path, ignore_folders)

    if config.external_provider:
        external = _get_class(config.external_provider_path, ignore_folders)

        for c in classes:
            for ex in external:
                if c.domain == ex.domain:
                    classes.remove(c)
        
        classes += external

    return classes
