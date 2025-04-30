import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.interface import MainWindow
from ui.splash_screen import SplashScreen

def setup_environment():
    """Configura o ambiente, garantindo que os diretórios necessários existam."""
    os.makedirs("assets/poster_images", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Verifica se o arquivo catalog.json existe, se não, cria um vazio
    if not os.path.exists("data/catalog.json"):
        with open("data/catalog.json", "w") as f:
            f.write('{"movies": []}')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Criar a splash screen
    splash = SplashScreen()
    # Criar a janela principal, mas não exibi-la ainda
    main_window = MainWindow()
    
    # Função para abrir a janela principal
    def open_main_window():
        main_window.showFullScreen()  # Exibir em tela cheia
        splash.close()  # Fechar a splash screen
    
    # Conectar o sinal de animação concluída à abertura da MainWindow
    splash.animation_finished.connect(open_main_window)
    
    # Exibir a splash screen
    splash.show()
    
    sys.exit(app.exec_())
    
