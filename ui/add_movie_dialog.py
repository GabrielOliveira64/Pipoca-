import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QFileDialog, QListWidget, QListWidgetItem,
                            QMessageBox, QProgressDialog, QApplication, QCheckBox)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from core.movie_fetcher import MovieFetcher
import time
import re
import subprocess
from pathlib import Path
from difflib import SequenceMatcher


class BatchScanThread(QThread):
    """Thread para escanear pastas e encontrar filmes."""
    progress_updated = pyqtSignal(int, int)
    movie_found = pyqtSignal(str, str)
    scan_completed = pyqtSignal(list)
    
    def __init__(self, root_folder, movie_manager):
        super().__init__()
        self.root_folder = root_folder
        self.movie_manager = movie_manager
        
    def run(self):
        video_files = []
        
        # Lista de extensões de vídeo suportadas
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        
        total_files = 0
        processed_files = 0
        
        # Contar arquivos primeiro para a barra de progresso
        for root, dirs, files in os.walk(self.root_folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    total_files += 1
        
        # Escanear pasta recursivamente
        for root, dirs, files in os.walk(self.root_folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    file_path = os.path.join(root, file)
                    processed_files += 1
                    self.progress_updated.emit(processed_files, total_files)
                    
                    # Verificar se é um filme (mais de 60 minutos)
                    if self.is_movie_file(file_path):
                        # Limpar o título
                        clean_title = self.clean_movie_title(file)
                        video_files.append((clean_title, file_path))
                        self.movie_found.emit(clean_title, file_path)
        
        # Emitir resultados
        self.scan_completed.emit(video_files)
    
    def is_movie_file(self, file_path):
        """Verifica se o arquivo é um filme com base na duração (mais de 60 minutos)."""
        try:
            # Verificar se ffprobe está disponível
            try:
                # Verifica se o ffprobe está disponível no sistema
                subprocess.run(['ffprobe', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except FileNotFoundError:
                # Se ffprobe não estiver disponível, assumir que é um filme
                print("FFprobe não encontrado no sistema. Assumindo que é um filme.")
                return True
            
            # Usar ffprobe para obter a duração
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                file_path
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                print(f"Erro ao executar ffprobe: {result.stderr}")
                return True  # Se falhar, assumir que é um filme
                
            duration = float(result.stdout.strip())
            
            # Considerar um filme se tiver mais de 60 minutos (3600 segundos)
            return duration > 3600
        except Exception as e:
            print(f"Erro ao verificar duração: {e}")
            # Se não conseguir verificar, assumir que é um filme
            return True
    
    def clean_movie_title(self, filename):
        """Remove termos técnicos do nome do arquivo para obter o título do filme."""
        # Obter nome sem extensão
        name = os.path.splitext(filename)[0]
        
        # Substituir separadores comuns por espaços
        name = name.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        
        # Remover termos técnicos comuns
        patterns = [
            r'\b\d{4}\b',  # Anos (ex: 2022)
            r'\b(1080p|720p|480p|4K|UHD|HD|FHD)\b',  # Resoluções
            r'\b(BluRay|BRRip|WEBRip|HDTV|DVDRip|WEB-DL|HDRIP|WEB |DL |SF|Acesse|ORIGINAL|Dublagem|BKS|by|GmV|Pirate|Filmes|The|LAPUMiaAFiLMES|COM|By|jmsmarcelo|COMANDO LA|LA|LapumiaFilmes|TorrentDosFilmes|SE|NET|)\b',  # Fontes
            r'\b(x264|x265|HEVC|XviD|h264|h265)\b',  # Codecs de vídeo
            r'\b(AAC|AC3|DTS|MP3|FLAC|DDP5.1|DDP|DD5.1|ÁUDIO|AUDIO|EAC3|6CH|CH|TDF|DL)\b',  # Codecs de áudio
            r'\b(DUAL|DUBLADO|LEGENDADO|DUB|PT-BR|PT|BR|EN|ENG|PTBR)\b',  # Idiomas
            r'\b(5.1|7.1|2.0)\b',  # Canais de áudio
            r'\bwww\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',  # URLs
            r'\b(EXTENDED|DIRECTORS.CUT|UNRATED|REMASTERED|REMUX |SF|BLUDV|BY|LUAHARP|LuaHarper|JefPsB|LAPUMiA|CAMPRip|THEPIRATEFILMES|RICKSZ|COMANDOTORRENTS|WOLVERDONFILMES|NACIONAL|VERSAO|ESTENDIDA|STARCKFILMES|remasterizado|CAMPRip|VERSÃO|ToTTI9|jeffpsb|portugues|WWW|-)\b',  # Versões
            r'\[.*?\]|\(.*?\)',  # Qualquer coisa entre colchetes ou parênteses
        ]
        
        for pattern in patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Remover múltiplos espaços e espaços no início/fim
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name


class AutomaticMovieAddThread(QThread):
    """Thread para adicionar filmes automaticamente."""
    progress_updated = pyqtSignal(int, int)
    movie_processed = pyqtSignal(str, bool, str)
    processing_completed = pyqtSignal()
    
    def __init__(self, movie_files, movie_manager, movie_fetcher):
        super().__init__()
        self.movie_files = movie_files
        self.movie_manager = movie_manager
        self.movie_fetcher = movie_fetcher
        self.catalog = self.load_catalog()
        
    def load_catalog(self):
        """Carrega o catálogo existente para verificar duplicatas."""
        catalog_path = os.path.join("data", "catalog.json")
        if os.path.exists(catalog_path):
            try:
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar catálogo: {e}")
                return {"movies": []}
        return {"movies": []}
        
    def run(self):
        total = len(self.movie_files)
        for index, (clean_title, file_path) in enumerate(self.movie_files):
            try:
                # Atualizar progresso
                self.progress_updated.emit(index + 1, total)
                
                # Verificar se o filme já existe no catálogo (pelo caminho do arquivo)
                if self.movie_exists_in_catalog(file_path):
                    self.movie_processed.emit(clean_title, False, "Filme já existe no catálogo")
                    continue
                
                # Buscar filme na API
                results = self.movie_fetcher.search_movie(clean_title)
                
                if not results:
                    # Tentar termos alternativos
                    alternative_title = self.get_alternative_search_term(clean_title)
                    if alternative_title and alternative_title != clean_title:
                        results = self.movie_fetcher.search_movie(alternative_title)
                
                if not results:
                    self.movie_processed.emit(clean_title, False, "Nenhum resultado encontrado")
                    continue
                
                # Ordenar resultados pelo melhor match
                best_match = self.find_best_title_match(clean_title, results)
                
                if not best_match:
                    self.movie_processed.emit(clean_title, False, "Nenhum resultado compatível")
                    continue
                
                # Buscar detalhes completos
                movie_details = self.movie_fetcher.get_movie_details(best_match['id'])
                
                if not movie_details:
                    self.movie_processed.emit(clean_title, False, "Falha ao obter detalhes")
                    continue
                
                # Baixar poster
                local_poster_path = None
                if movie_details.get("poster_path"):
                    local_poster_path = self.movie_fetcher.download_poster(
                        movie_details["poster_path"], 
                        movie_details["id"]
                    )
                
                # Extrair informações
                movie_info = self.movie_fetcher.extract_movie_info(movie_details)
                movie_info["local_poster_path"] = local_poster_path
                
                # Adicionar filme ao catálogo
                new_movie = self.movie_manager.add_movie(movie_info, file_path)
                
                if new_movie:
                    self.movie_processed.emit(clean_title, True, new_movie['title'])
                else:
                    self.movie_processed.emit(clean_title, False, "Falha ao adicionar ao catálogo")
                    
            except Exception as e:
                self.movie_processed.emit(clean_title, False, str(e))
        
        self.processing_completed.emit()
    
    def movie_exists_in_catalog(self, file_path):
        """Verifica se o filme já existe no catálogo pelo caminho do arquivo."""
        for movie in self.catalog.get("movies", []):
            if movie.get("file_path") == file_path:
                return True
        return False
    
    def find_best_title_match(self, search_title, results):
        """Encontra o melhor match de título entre os resultados."""
        best_match = None
        best_score = 0
        
        for movie in results:
            # Comparar os títulos
            title = movie.get("title", "").lower()
            search = search_title.lower()
            
            # Usar algoritmo de similaridade
            ratio = SequenceMatcher(None, search, title).ratio()
            
            # Considerar ano de lançamento se estiver no título de busca
            year_match = 0
            release_date = movie.get("release_date", "")
            if release_date:
                year = release_date.split("-")[0]
                if year in search_title:
                    year_match = 0.2  # Bônus por ano correspondente
            
            score = ratio + year_match
            
            if score > best_score:
                best_score = score
                best_match = movie
        
        # Exigir pontuação mínima de 0.5 (50% similar)
        if best_score < 0.5:
            return None
            
        return best_match
    
    def get_alternative_search_term(self, title):
        """Cria termos de busca alternativos para melhorar a pesquisa."""
        # Remover parte após : ou - que geralmente são subtítulos
        alt_title = re.sub(r'[:;]-.*$', '', title).strip()
        
        # Remover palavras muito comuns para focar em palavras-chave
        common_words = ['o', 'a', 'os', 'as', 'e', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas']
        words = alt_title.split()
        if len(words) > 2:  # Se tiver mais de 2 palavras, tenta remover as comuns
            filtered_words = [w for w in words if w.lower() not in common_words]
            if filtered_words:  # Se ainda sobrou algo
                alt_title = ' '.join(filtered_words)
        
        return alt_title if alt_title != title else None


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
        self.found_movies = []
        self.catalog = self.load_catalog()
        self.init_ui()
        
    def load_catalog(self):
        """Carrega o catálogo existente para verificar duplicatas."""
        catalog_path = os.path.join("data", "catalog.json")
        if os.path.exists(catalog_path):
            try:
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar catálogo: {e}")
                return {"movies": []}
        return {"movies": []}
        
    def init_ui(self):
        self.setWindowTitle("Adicionar Filme")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Seção 1: Seleção de arquivo ou pasta
        file_section = QVBoxLayout()
        
        file_label = QLabel("Passo 1: Selecione o arquivo de vídeo ou uma pasta com filmes")
        file_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        file_section.addWidget(file_label)
        
        file_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("Selecione o arquivo de vídeo ou pasta...")
        file_layout.addWidget(self.file_path_edit)
        
        browse_button = QPushButton("Procurar Arquivo")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_button)
        
        browse_folder_button = QPushButton("Procurar Pasta")
        browse_folder_button.clicked.connect(self.browse_folder)
        file_layout.addWidget(browse_folder_button)
        
        file_section.addLayout(file_layout)
        
        # Opção para processamento automático
        auto_process_layout = QHBoxLayout()
        self.auto_process_checkbox = QCheckBox("Processar filmes automaticamente")
        self.auto_process_checkbox.setChecked(True)
        auto_process_layout.addWidget(self.auto_process_checkbox)
        auto_process_layout.addStretch()
        file_section.addLayout(auto_process_layout)
        
        # Opção para pular verificação de duplicatas
        skip_duplicates_layout = QHBoxLayout()
        self.skip_duplicates_checkbox = QCheckBox("Pular filmes já existentes no catálogo")
        self.skip_duplicates_checkbox.setChecked(True)
        skip_duplicates_layout.addWidget(self.skip_duplicates_checkbox)
        skip_duplicates_layout.addStretch()
        file_section.addLayout(skip_duplicates_layout)
        
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
        
        # Log de processamento
        log_section = QVBoxLayout()
        log_label = QLabel("Log de Processamento")
        log_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        log_section.addWidget(log_label)
        
        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(100)
        log_section.addWidget(self.log_list)
        
        layout.addLayout(log_section)
        
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
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid #555;
                background-color: #333;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #E50914;
                border: 1px solid #E50914;
            }
        """)
    
    def add_log_message(self, message, success=True):
        """Adiciona uma mensagem ao log de processamento."""
        item = QListWidgetItem(message)
        item.setForeground(Qt.green if success else Qt.red)
        self.log_list.addItem(item)
        self.log_list.scrollToBottom()
    
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
            
            # Verificar se o filme já existe no catálogo
            if self.skip_duplicates_checkbox.isChecked() and self.movie_exists_in_catalog(file_path):
                QMessageBox.information(
                    self,
                    "Filme já existe",
                    "Este filme já existe no catálogo."
                )
                return
            
            # Extrair o nome do arquivo (sem extensão) para usar como termo de busca
            filename = os.path.basename(file_path)
            basename = os.path.splitext(filename)[0]
            
            # Limpar o nome
            clean_title = self.clean_movie_title(basename)
            
            # Preencher o campo de busca com o nome limpo
            self.search_edit.setText(clean_title.strip())
            
            # Realizar a busca automaticamente
            self.search_movie()
    
    def clean_movie_title(self, filename):
        """Remove termos técnicos do nome do arquivo para obter o título do filme."""
        # Substituir separadores comuns por espaços
        name = filename.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        
        # Remover termos técnicos comuns
        patterns = [
            r'\b\d{4}\b',  # Anos (ex: 2022)
            r'\b(1080p|720p|480p|4K|UHD|HD|FHD)\b',  # Resoluções
            r'\b(BluRay|BRRip|WEBRip|HDTV|DVDRip|WEB-DL|HDRIP)\b',  # Fontes
            r'\b(x264|x265|HEVC|XviD|h264|h265)\b',  # Codecs de vídeo
            r'\b(AAC|AC3|DTS|MP3|FLAC|DDP5.1|DDP|DD5.1)\b',  # Codecs de áudio
            r'\b(DUAL|DUBLADO|LEGENDADO|DUB|PT-BR|PT|BR|EN|ENG|PTBR)\b',  # Idiomas
            r'\b(5.1|7.1|2.0)\b',  # Canais de áudio
            r'\bwww\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',  # URLs
            r'\b(EXTENDED|DIRECTORS.CUT|UNRATED|REMASTERED|REMUX)\b',  # Versões
            r'\[.*?\]|\(.*?\)',  # Qualquer coisa entre colchetes ou parênteses
        ]
        
        for pattern in patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Remover múltiplos espaços e espaços no início/fim
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def movie_exists_in_catalog(self, file_path):
        """Verifica se o filme já existe no catálogo pelo caminho do arquivo."""
        for movie in self.catalog.get("movies", []):
            if movie.get("file_path") == file_path:
                return True
        return False
    
    def browse_folder(self):
        """Abre um diálogo para selecionar uma pasta contendo filmes."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta com Filmes",
            ""
        )
        
        if folder_path:
            self.file_path_edit.setText(folder_path)
            
            # Iniciar o escaneamento da pasta
            self.scan_folder_for_movies(folder_path)
    
    def scan_folder_for_movies(self, folder_path):
        """Escaneia a pasta em busca de arquivos de vídeo que possam ser filmes."""
        # Criar e mostrar diálogo de progresso
        self.scan_progress = QProgressDialog("Escaneando pasta por filmes...", "Cancelar", 0, 0, self)
        self.scan_progress.setWindowTitle("Escaneando")
        self.scan_progress.setWindowModality(Qt.WindowModal)
        self.scan_progress.setMinimumDuration(0)
        self.scan_progress.show()
        QApplication.processEvents()
        
        # Limpar log
        self.log_list.clear()
        self.add_log_message("Iniciando escaneamento da pasta...")
        
        # Iniciar thread de escaneamento
        self.scan_thread = BatchScanThread(folder_path, self.movie_manager)
        self.scan_thread.progress_updated.connect(self.update_scan_progress)
        self.scan_thread.movie_found.connect(self.on_movie_found)
        self.scan_thread.scan_completed.connect(self.on_scan_completed)
        self.scan_thread.start()
    
    def update_scan_progress(self, current, total):
        """Atualiza a barra de progresso do escaneamento."""
        if self.scan_progress.wasCanceled():
            self.scan_thread.terminate()
            return
        
        self.scan_progress.setMaximum(total)
        self.scan_progress.setValue(current)
        self.scan_progress.setLabelText(f"Escaneando filmes... ({current}/{total})")
    
    def on_movie_found(self, clean_title, file_path):
        """Manipula o evento quando um filme é encontrado durante o escaneamento."""
        self.add_log_message(f"Filme encontrado: {clean_title}")
    
    def on_scan_completed(self, found_movies):
        """Manipula o evento quando o escaneamento é concluído."""
        self.found_movies = []
        
        # Filtrar duplicatas se necessário
        if self.skip_duplicates_checkbox.isChecked():
            for title, file_path in found_movies:
                if not self.movie_exists_in_catalog(file_path):
                    self.found_movies.append((title, file_path))
                else:
                    self.add_log_message(f"Pulando filme duplicado: {title}", success=False)
        else:
            self.found_movies = found_movies
        
        self.scan_progress.close()
        
        if not self.found_movies:
            QMessageBox.information(self, "Escaneamento Concluído", 
                                   "Nenhum filme novo encontrado na pasta selecionada.")
            return
        
        # Mostrar resultado
        QMessageBox.information(
            self, 
            "Escaneamento Concluído", 
            f"Foram encontrados {len(self.found_movies)} novos filmes."
        )
        
        self.add_log_message(f"Escaneamento concluído: {len(self.found_movies)} filmes encontrados")
        
        # Se o processamento automático estiver ativado, começar a adicionar filmes
        if self.auto_process_checkbox.isChecked():
            self.process_found_movies()
    
    def process_found_movies(self):
        """Processa os filmes encontrados automaticamente."""
        if not self.found_movies:
            return
        
        # Criar e mostrar diálogo de progresso
        self.processing_progress = QProgressDialog("Processando filmes...", "Cancelar", 0, len(self.found_movies), self)
        self.processing_progress.setWindowTitle("Adicionando Filmes")
        self.processing_progress.setWindowModality(Qt.WindowModal)
        self.processing_progress.setMinimumDuration(0)
        self.processing_progress.show()
        QApplication.processEvents()
        
        # Iniciar thread de processamento
        self.auto_add_thread = AutomaticMovieAddThread(
            self.found_movies,
            self.movie_manager,
            self.movie_fetcher
        )
        self.auto_add_thread.progress_updated.connect(self.update_processing_progress)
        self.auto_add_thread.movie_processed.connect(self.on_movie_processed)
        self.auto_add_thread.processing_completed.connect(self.on_processing_completed)
        self.auto_add_thread.start()
    
    def update_processing_progress(self, current, total):
        """Atualiza a barra de progresso do processamento."""
        if self.processing_progress.wasCanceled():
            self.auto_add_thread.terminate()
            return
        
        self.processing_progress.setValue(current)
        self.processing_progress.setLabelText(f"Processando filmes... ({current}/{total})")
    
    def on_movie_processed(self, movie_title, success, message):
        """Manipula o evento quando um filme é processado."""
        status = "Adicionado" if success else "Falha"
        log_message = f"{status}: {movie_title} - {message}"
        self.add_log_message(log_message, success)
    
    def on_processing_completed(self):
        """Manipula o evento quando o processamento é concluído."""
        self.processing_progress.close()
        QMessageBox.information(
            self, 
            "Processamento Concluído", 
            "O processamento dos filmes foi concluído. Os filmes foram adicionados ao catálogo."
        )
        self.add_log_message("Processamento de filmes concluído")
        self.accept()
    
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
            # Tentar busca alternativa se não encontrar resultados
            search_term = self.search_edit.text().strip()
            alternative_term = self.get_alternative_search_term(search_term)
            
            if alternative_term and alternative_term != search_term:
                # Mostrar diálogo de progresso
                progress = QProgressDialog(f"Tentando busca alternativa: {alternative_term}", "Cancelar", 0, 0, self)
                progress.setWindowTitle("Aguarde")
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                QApplication.processEvents()
                
                # Iniciar thread de busca alternativa
                self.alt_search_thread = TMDBSearchThread(self.movie_fetcher, alternative_term)
                self.alt_search_thread.search_completed.connect(self.handle_alternative_search_results)
                self.alt_search_thread.finished.connect(progress.close)
                self.alt_search_thread.start()
                return
            else:
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
            
            # Se houver apenas um resultado e for muito similar ao termo de busca, selecionar automaticamente
            if len(results) == 1:
                search_term = self.search_edit.text().strip().lower()
                movie_title = title.lower()
                if search_term in movie_title or movie_title in search_term:
                    self.results_list.setCurrentItem(item)
                    self.select_movie(item)
    
    def handle_alternative_search_results(self, results):
        """Processa os resultados da busca alternativa."""
        if not results:
            self.results_list.addItem("Nenhum resultado encontrado com busca alternativa.")
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
            
            item = QListWidgetItem(f"{title}{year} [busca alternativa]")
            item.setData(Qt.UserRole, movie)
            self.results_list.addItem(item)
    
    def get_alternative_search_term(self, title):
        """Cria termos de busca alternativos para melhorar a pesquisa."""
        # Remover parte após : ou - que geralmente são subtítulos
        alt_title = re.sub(r'[:;]-.*$', '', title).strip()
        
        # Remover palavras muito comuns para focar em palavras-chave
        common_words = ['o', 'a', 'os', 'as', 'e', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas']
        words = alt_title.split()
        if len(words) > 2:  # Se tiver mais de 2 palavras, tenta remover as comuns
            filtered_words = [w for w in words if w.lower() not in common_words]
            if filtered_words:  # Se ainda sobrou algo
                alt_title = ' '.join(filtered_words)
        
        return alt_title if alt_title != title else None
    
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
        self.add_button.setEnabled(True if self.selected_file_path else False)
    
    def add_movie(self):
        """Adiciona o filme selecionado ao catálogo."""
        if not self.selected_file_path or not self.selected_movie_info:
            QMessageBox.warning(self, "Informações Incompletas", "Selecione um arquivo e um filme para continuar.")
            return
        
        # Verificar se já existe no catálogo
        if self.skip_duplicates_checkbox.isChecked() and self.movie_exists_in_catalog(self.selected_file_path):
            QMessageBox.information(
                self,
                "Filme já existe",
                "Este filme já existe no catálogo."
            )
            return
        
        # Adicionar filme ao catálogo
        new_movie = self.movie_manager.add_movie(self.selected_movie_info, self.selected_file_path)
        
        if new_movie:
            QMessageBox.information(self, "Sucesso", f"Filme '{new_movie['title']}' adicionado com sucesso!")
            self.add_log_message(f"Filme adicionado manualmente: {new_movie['title']}")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível adicionar o filme ao catálogo.")
            self.add_log_message(f"Falha ao adicionar filme: {self.selected_movie_info.get('title', 'Desconhecido')}", success=False)
