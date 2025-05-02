import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from ui.interface import MainWindow
from ui.splash_screen import SplashScreen
from update.auto_updater import AutoUpdater  # Importando o módulo de atualização

def resource_path(relative_path):
    """Retorna o caminho absoluto, compatível com cx_Freeze"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def setup_environment():
    """Configura o ambiente, garantindo que os diretórios necessários existam."""
    os.makedirs("assets/poster_images", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Verifica se o arquivo catalog.json existe, se não, cria um vazio
    if not os.path.exists("data/catalog.json"):
        with open("data/catalog.json", "w") as f:
            f.write('{"movies": []}')
    
    # Verifica se o arquivo version.json existe, se não, cria um com versão padrão
    if not os.path.exists("version.json"):
        with open("version.json", "w") as f:
            f.write('{"version": "1.0.0"}')

def get_current_version():
    """Obtém a versão atual do programa a partir do arquivo version.json"""
    try:
        with open("version.json", "r") as f:
            version_data = json.load(f)
            return version_data.get("version", "1.0.0")
    except (FileNotFoundError, json.JSONDecodeError):
        return "1.0.0"

def check_for_updates(parent_widget=None):
    """Verifica se há atualizações disponíveis e pergunta ao usuário se deseja atualizar"""
    current_version = get_current_version()
    updater = AutoUpdater(
        repo_owner="gabrieloliveira64",
        repo_name="PipocaApp",
        current_version=current_version,
        ignore_patterns=["data/catalog.json", "assets/poster_images/*"]
    )
    
    release = updater.check_for_updates()
    
    if release:
        if parent_widget:
            reply = QMessageBox.question(
                parent_widget,
                "Atualização Disponível",
                f"Uma nova versão ({release['tag_name']}) está disponível. Deseja atualizar agora?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                msg = QMessageBox(parent_widget)
                msg.setWindowTitle("Atualizando")
                msg.setText("Baixando e instalando atualização. O programa será reiniciado automaticamente.")
                msg.setStandardButtons(QMessageBox.NoButton)
                msg.show()
                QApplication.processEvents()
                
                zip_path = updater.download_update(release)
                if zip_path and updater.install_update(zip_path):
                    QMessageBox.information(
                        parent_widget,
                        "Atualização Concluída",
                        "A atualização foi instalada com sucesso. O programa será reiniciado."
                    )
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
                else:
                    QMessageBox.warning(
                        parent_widget,
                        "Falha na Atualização",
                        "Não foi possível instalar a atualização."
                    )
        else:
            print(f"Nova versão disponível: {release['tag_name']}. Execute novamente para atualizar.")

if __name__ == "__main__":
    setup_environment()
    
    app = QApplication(sys.argv)

    # Define o ícone da aplicação (barra de tarefas)
    app.setWindowIcon(QIcon(resource_path("icon/pipocaplus.ico")))

    splash = SplashScreen()
    main_window = MainWindow()
    
    def check_updates_after_splash():
        check_for_updates(main_window)
    
    def open_main_window():
        main_window.showFullScreen()
        QTimer.singleShot(500, check_updates_after_splash)
    
    splash.animation_finished.connect(open_main_window)
    splash.show()
    
    sys.exit(app.exec_())
