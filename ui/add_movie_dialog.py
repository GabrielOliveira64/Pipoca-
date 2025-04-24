import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QFileDialog, QListWidget, QListWidgetItem,
                            QMessageBox, QProgressDialog, QApplication)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from core.movie_fetcher import MovieFetcher
import time

class TMDBSearchThread(QThread):
    """Thread para buscar filmes na API do TMDB."""
    search_completed = pyqtSignal(list)
    
    def __init__(self, fetcher, title):
        super().__init__()
        self.fetcher = fetcher
        self.title = title
        
    def run(self):
        results = self.fetcher.search_movie(self.title)
        self.search_completed.emit(results)


class MovieDetailsFetchThread(QThread):
    """Thread para buscar detalhes completos de um filme."""
    fetch_completed = pyqtSignal(dict)
    
    def __init__(self, fetcher, movie_id):
        super().__init__()
        self.fetcher = fetcher
        self.movie_id = movie_id
        
    def run(self):
        movie_details = self.fetcher.get_movie_details(self.movie_id)
        if movie_details:
            # Baixar o poster
            local_poster_path = None
            if movie_details.get("poster_path"):
                local_poster_path = self.fetcher.download_poster(
                    movie_details["poster_path"], 
                    movie_details["id"]
                )
            
            # Extrair informações relevantes
            movie_info = self.fetcher.extract_movie_info(movie_details)
            movie_info["local_poster_path"] = local_poster_path
            
            self.fetch_completed.emit(movie_info)
        else:
            self.fetch_completed.emit({})


class AddMovieDialog(QDialog):
    """Diálogo para adicionar um novo filme."""
    
    def __init__(self, movie_manager, parent=None):
        super().__init__(parent)
        self.movie_manager = movie_manager
        self.movie_fetcher = MovieFetcher()
        self.selected_file_path = ""
        self.selected_movie_info = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Adicionar Filme")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Seção 1: Seleção de arquivo
        file_section = QVBoxLayout()
        
        file_label = QLabel("Passo 1: Selecione o arquivo de vídeo")
        file_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        file_section.addWidget(file_label)
        
        file_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("Selecione o arquivo de vídeo...")
        file_layout.addWidget(self.file_path_edit)
        
        browse_button = QPushButton("Procurar")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_button)
        
        file_section.addLayout(file_layout)
        layout.addLayout(file_section)
        
        # Linha separadora
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #333;")
        layout.addWidget(separator)
        
        # Seção 2: Busca de informações do filme
        search_section = QVBoxLayout()
        
        search_label = QLabel("Passo 2: Buscar informações do filme")
        search_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        search_section.addWidget(search_label)
        
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Digite o título do filme...")
        search_layout.addWidget(self.search_edit)
        
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.search_movie)
        search_layout.addWidget(search_button)
        
        search_section.addLayout(search_layout)
        
        # Lista de resultados
        results_layout = QHBoxLayout()
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("font-size: 14px;")
        self.results_list.itemClicked.connect(self.select_movie)
        results_layout.addWidget(self.results_list, 2)
        
        # Painel de detalhes do filme selecionado
        self.details_panel = QVBoxLayout()
        
        self.poster_label = QLabel()
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_label.setFixedSize(200, 300)
        self.poster_label.setStyleSheet("background-color: #333;")
        self.details_panel.addWidget(self.poster_label)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.details_panel.addWidget(self.title_label)
        
        self.year_label = QLabel()
        self.year_label.setAlignment(Qt.AlignCenter)
        self.details_panel.addWidget(self.year_label)
        
        self.overview_label = QLabel()
        self.overview_label.setWordWrap(True)
        self.overview_label.setAlignment(Qt.AlignTop)
        self.details_panel.addWidget(self.overview_label)
        
        self.details_panel.addStretch()
        results_layout.addLayout(self.details_panel, 1)
        
        search_section.addLayout(results_layout)
        layout.addLayout(search_section)
        
        # Linha separadora
        separator2 = QLabel()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet("background-color: #333;")
        layout.addWidget(separator2)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        buttons_layout.addStretch()
        
        self.add_button = QPushButton("Adicionar Filme")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self.add_movie)
        buttons_layout.addWidget(self.add_button)
        
        layout.addLayout(buttons_layout)
        
        # Estilo geral
        self.setStyleSheet("""
            QDialog {
                background-color: #141414;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #E50914;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #F40D12;
            }
            QPushButton:disabled {
                background-color: #5E5E5E;
            }
            QListWidget {
                background-color: #222;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #E50914;
            }
        """)
    
    def browse_file(self):
        """Abre um diálogo para selecionar um arquivo de vídeo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Selecionar Arquivo de Vídeo",
            "",
            "Arquivos de Vídeo (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;Todos os Arquivos (*.*)"
        )
        
        if file_path:
            # Verificar se é um arquivo de vídeo
            if not self.movie_manager.is_video_file(file_path):
                QMessageBox.warning(
                    self, 
                    "Arquivo Inválido", 
                    "O arquivo selecionado não parece ser um arquivo de vídeo válido."
                )
                return
                
            self.selected_file_path = file_path
            self.file_path_edit.setText(file_path)
            
            # Extrair o nome do arquivo (sem extensão) para usar como termo de busca
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Limpar caracteres especiais comuns em nomes de arquivos de filmes
            clean_name = name_without_ext.replace(".", " ")
            clean_name = clean_name.replace("_", " ")
            
            # Remover termos comuns de qualidade e codificação
            terms_to_remove = ["1080p", "720p", "480p", "HDTV", "BRRip", "WEBRip", 
                              "BluRay", "x264", "HEVC", "XviD", "AAC", "AC3", "DUAL"]
            for term in terms_to_remove:
                clean_name = clean_name.replace(term, "")
            
            # Preencher o campo de busca com o nome limpo
            self.search_edit.setText(clean_name.strip())
            
            # Realizar a busca automaticamente
            self.search_movie()
    
    def search_movie(self):
        """Busca filmes com base no título inserido."""
        search_term = self.search_edit.text().strip()
        if not search_term:
            QMessageBox.warning(self, "Campo Vazio", "Digite um título para buscar.")
            return
        
        # Mostrar diálogo de progresso
        progress = QProgressDialog("Buscando filmes...", "Cancelar", 0, 0, self)
        progress.setWindowTitle("Aguarde")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()
        
        # Iniciar thread de busca
        self.search_thread = TMDBSearchThread(self.movie_fetcher, search_term)
        self.search_thread.search_completed.connect(self.handle_search_results)
        self.search_thread.finished.connect(progress.close)
        self.search_thread.start()
    
    def handle_search_results(self, results):
        """Processa os resultados da busca."""
        self.results_list.clear()
        
        if not results:
            self.results_list.addItem("Nenhum resultado encontrado.")
            return
        
        for movie in results:
            title = movie.get("title", "Sem título")
            year = ""
            release_date = movie.get("release_date", "")
            if release_date:
                try:
                    year = f" ({release_date.split('-')[0]})"
                except:
                    pass
            
            item = QListWidgetItem(f"{title}{year}")
            item.setData(Qt.UserRole, movie)
            self.results_list.addItem(item)
    
    def select_movie(self, item):
        """Seleciona um filme da lista de resultados."""
        movie_data = item.data(Qt.UserRole)
        if not movie_data:
            return
        
        # Mostrar diálogo de progresso
        progress = QProgressDialog("Obtendo detalhes do filme...", "Cancelar", 0, 0, self)
        progress.setWindowTitle("Aguarde")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()
        
        # Iniciar thread para buscar detalhes completos
        self.details_thread = MovieDetailsFetchThread(self.movie_fetcher, movie_data["id"])
        self.details_thread.fetch_completed.connect(self.show_movie_details)
        self.details_thread.finished.connect(progress.close)
        self.details_thread.start()
    
    def show_movie_details(self, movie_info):
        """Exibe os detalhes do filme selecionado."""
        if not movie_info:
            QMessageBox.warning(self, "Erro", "Não foi possível obter detalhes do filme.")
            return
        
        self.selected_movie_info = movie_info
        
        # Exibir poster
        poster_path = movie_info.get("local_poster_path")
        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
            pixmap = pixmap.scaled(200, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.poster_label.setPixmap(pixmap)
        else:
            self.poster_label.setText("Sem Poster")
            self.poster_label.setAlignment(Qt.AlignCenter)
        
        # Exibir título
        self.title_label.setText(movie_info.get("title", "Sem Título"))
        
        # Exibir ano
        release_date = movie_info.get("release_date", "")
        if release_date:
            year = release_date.split("-")[0]
            self.year_label.setText(year)
        else:
            self.year_label.setText("")
        
        # Exibir sinopse
        overview = movie_info.get("overview", "Sinopse não disponível.")
        self.overview_label.setText(overview)
        
        # Habilitar botão de adicionar
        if self.selected_file_path and self.selected_movie_info:
            self.add_button.setEnabled(True)
    
    def add_movie(self):
        """Adiciona o filme selecionado ao catálogo."""
        if not self.selected_file_path or not self.selected_movie_info:
            QMessageBox.warning(self, "Informações Incompletas", "Selecione um arquivo e um filme para continuar.")
            return
        
        # Adicionar filme ao catálogo
        new_movie = self.movie_manager.add_movie(self.selected_movie_info, self.selected_file_path)
        
        if new_movie:
            QMessageBox.information(self, "Sucesso", f"Filme '{new_movie['title']}' adicionado com sucesso!")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível adicionar o filme ao catálogo.")
