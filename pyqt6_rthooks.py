import sys
from PyQt6.QtCore import QCoreApplication

if getattr(sys, 'frozen', False):
    # Adiciona caminho para plugins Qt
    base_path = sys._MEIPASS
    plugin_path = os.path.join(base_path, 'PyQt6', 'Qt6', 'plugins')
    QCoreApplication.addLibraryPath(plugin_path)
    
    # Configura variáveis de ambiente para Qt
    os.environ['QT_PLUGIN_PATH'] = plugin_path