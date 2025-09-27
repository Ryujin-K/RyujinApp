import os
from dulwich import porcelain
from packaging import version
from .paths import paths

def update_providers():
    paths.ensure_dirs()
    
    if not paths.repo_dir.exists() or not any(paths.repo_dir.iterdir()):
        print(f"Clonando repositório para: {paths.repo_dir}")
        porcelain.clone('https://github.com/Ryujin-K/RyujinApp', str(paths.repo_dir))
    else:
        print(f"Atualizando repositório em: {paths.repo_dir}")
        porcelain.pull(str(paths.repo_dir))

def get_last_version():
    if not paths.repo_dir.exists():
        return "0.0.0"
    
    try:
        tags = porcelain.tag_list(str(paths.repo_dir))
        versions_str = [v.decode('utf-8')[1:] for v in tags if v.decode('utf-8').startswith('v')]
        if not versions_str:
            return "0.0.0"
        ordered_versions = sorted(versions_str, key=version.parse)
        return ordered_versions[-1]
    except Exception as e:
        print(f"Erro ao obter versão: {e}")
        return "0.0.0"
