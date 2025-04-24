import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.interface import MainWindow

def setup_environment():
    """Configura o ambiente, garantindo que os diretórios necessários existam."""
    os.makedirs("assets/poster_images", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Verifica se o arquivo catalog.json existe, se não, cria um vazio
    if not os.path.exists("data/catalog.json"):
        with open("data/catalog.json", "w") as f:
            f.write('{"movies": []}')

if __name__ == "__main__":
    setup_environment()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    