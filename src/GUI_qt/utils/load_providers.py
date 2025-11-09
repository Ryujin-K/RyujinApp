import os
import sys
import importlib.util
from typing import List
from pathlib import Path
from GUI_qt.utils.config import get_config
from core.providers.domain.provider_repository import ProviderRepository
from .paths import paths

def base_path():
    return paths.base_dir

def get_providers_path() -> Path:
    """Resolve the directory that stores provider implementations."""
    if paths.is_executable:
        repo_providers = paths.repo_dir / 'src' / 'core' / 'providers' / 'infra'
        if repo_providers.exists():
            return repo_providers
    return paths.providers_dir

def get_assets_path():
    return paths.assets_dir

ignore_folders = ['template', '__pycache__']

def _get_class(package_path: Path, ignore_folders):
    classes = []

    if not package_path.exists():
        return classes

    for root, dirs, files in os.walk(package_path):
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        
        for file in files:
            if file.endswith('.py'):
                module_name = os.path.splitext(file)[0]
                module_path = os.path.join(root, file)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if not spec or not spec.loader:
                    continue

                sys.modules.pop(module_name, None)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and name.endswith('Provider'):
                        classes.append(obj)
    
    return classes

def import_classes_recursively() -> List[ProviderRepository]:
    classes = []

    config = get_config()

    providers_path = get_providers_path()
    classes += _get_class(providers_path, ignore_folders)

    if config and config.external_provider and config.external_provider_path:
        external = _get_class(Path(config.external_provider_path), ignore_folders)

        if external:
            classes = [c for c in classes if all(c.domain != ex.domain for ex in external)]
            classes.extend(external)

    return classes
