import os
import sys
from pathlib import Path
from platformdirs import user_data_path

class PathManager:
    
    def __init__(self):
        self._app_data_dir = Path(user_data_path('RyujinApp'))
        self._is_dev = os.environ.get('RYUJINAPPENV') == 'dev'
        self._is_frozen = getattr(sys, 'frozen', False)
        
    @property
    def is_executable(self) -> bool:
        """Retorna True se rodando como executável PyInstaller."""
        return self._is_frozen and hasattr(sys, '_MEIPASS')
    
    @property
    def is_development(self) -> bool:
        """Retorna True se em modo desenvolvimento."""
        return self._is_dev
    
    @property
    def app_data_dir(self) -> Path:
        """Diretório de dados da aplicação do usuário."""
        return self._app_data_dir
    
    @property
    def repo_dir(self) -> Path:
        """Diretório onde o repositório é clonado."""
        return self.app_data_dir / 'source'
    
    @property
    def base_dir(self) -> Path:
        """Diretório base da aplicação (src)."""
        if self.is_executable:
            # No executável, usa a pasta temporária do PyInstaller
            return Path(sys._MEIPASS)
        elif self.is_development:
            # Em desenvolvimento, usa o diretório atual
            return Path('.') / 'src'
        else:
            # Em produção (não executável), usa o repo clonado
            return self.repo_dir / 'src'
    
    @property
    def gui_dir(self) -> Path:
        """Diretório GUI_qt."""
        return self.base_dir / 'GUI_qt'
    
    @property
    def assets_dir(self) -> Path:
        """Diretório de assets GUI."""
        return self.gui_dir / 'assets'
    
    @property
    def providers_dir(self) -> Path:
        """Diretório de providers."""
        return self.base_dir / 'core' / 'providers' / 'infra'
    
    def get_asset_path(self, filename: str) -> Path:
        """Retorna o caminho completo para um arquivo de asset."""
        return self.assets_dir / filename
    
    def ensure_dirs(self):
        """Cria os diretórios necessários se não existirem."""
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        if not self.is_executable and not self.is_development:
            self.repo_dir.mkdir(parents=True, exist_ok=True)

# Instância global do gerenciador de paths
paths = PathManager()