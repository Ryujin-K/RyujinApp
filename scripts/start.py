import os
import sys
import subprocess
from pathlib import Path
from sys import platform

is_posix = platform.startswith(("darwin", "cygwin", "linux", "linux2"))

def run():
    # Caminho raiz do projeto
    base_path = Path(__file__).resolve().parent.parent
    src_path = base_path / 'src'
    app_path = src_path / 'GUI_qt' / '__init__.py'

    # Variável de ambiente do app
    os.environ['RYUJINAPPENV'] = 'dev'

    # Se estiver rodando empacotado (PyInstaller)
    if getattr(sys, 'frozen', False):
        try:
            # Importa e executa diretamente a função principal do GUI_qt
            from src.GUI_qt import main
            main()
        except ImportError as e:
            print("Erro ao iniciar GUI_qt no exe:", e)
        return

    # Modo desenvolvimento com jurigged
    if is_posix:
        os.environ['PYTHONPATH'] = str(src_path)
        result = subprocess.run(["jurigged", str(app_path)], capture_output=True, text=True, env=os.environ)
    else:
        script = f"set PYTHONPATH={str(src_path)} && jurigged {str(app_path)}"
        result = subprocess.run(script, capture_output=True, text=True, shell=True)

    # Exibe saída do subprocess
    print("Output App:")
    print(result.stdout)
    if result.stderr:
        print("Errors app:")
        print(result.stderr)

if __name__ == "__main__":
    run()
