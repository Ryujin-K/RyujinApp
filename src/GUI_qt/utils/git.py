import os
from dulwich import porcelain
from packaging import version
from platformdirs import user_data_path

data_path = user_data_path('RyujinApp')

def update_providers():
    os.makedirs(data_path, exist_ok=True)
    if not os.path.isdir(data_path / 'RyujinApp'):
        porcelain.clone('https://github.com/Ryujin-K/RyujinApp', data_path / 'RyujinApp')
    else:
        porcelain.pull(data_path / 'RyujinApp')

def get_last_version():
    tags = porcelain.tag_list(data_path / 'RyujinApp')
    versions_str = [v.decode('utf-8')[1:] for v in tags]
    ordered_versions = sorted(versions_str, key=version.parse)
    return ordered_versions[-1]
