import os
import ssl
import urllib3
from dulwich import porcelain
from packaging import version
from .paths import paths

try:
    import certifi
    # Configurar urllib3 para usar os certificados do certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except ImportError:
    # Se certifi não estiver disponível, tentar usar certificados do sistema
    pass

def update_providers():
    paths.ensure_dirs()
    
    try:
        if not paths.repo_dir.exists() or not any(paths.repo_dir.iterdir()):
            print(f"Clonando repositório para: {paths.repo_dir}")
            porcelain.clone('https://github.com/Ryujin-K/RyujinApp', str(paths.repo_dir))
        else:
            print(f"Atualizando repositório em: {paths.repo_dir}")
            porcelain.pull(str(paths.repo_dir))
    except Exception as e:
        print(f"Erro ao atualizar provedores: {e}")
        print("Tentando sem verificação SSL...")
        # Em último caso, desabilitar verificação SSL (não recomendado, mas funcional)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Configurar para não verificar SSL
        os.environ['GIT_SSL_NO_VERIFY'] = '1'
        
        if not paths.repo_dir.exists() or not any(paths.repo_dir.iterdir()):
            porcelain.clone('https://github.com/Ryujin-K/RyujinApp', str(paths.repo_dir))
        else:
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
