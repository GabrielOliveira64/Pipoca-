import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMessageBox, QFrame, QDialog)
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import Qt
import webbrowser
from PyQt5.QtWidgets import QDesktopWidget


class MovieCard(QWidget):
    """Widget para exibir um cartão de filme com efeito hover."""
    
    def __init__(self, movie, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.setMouseTracking(True)  # Ativa o rastreamento do mouse
        self.hovered = False
        self.init_ui()
        
    def init_ui(self):
        self.layout = QVBoxLayout()
        # Reduzir ainda mais as margens do cartão
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        
        # Container principal
        self.container = QFrame()
        self.container.setObjectName("movieCard")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        # Poster
        self.poster_frame = QFrame()
        self.poster_frame.setObjectName("posterFrame")
        self.poster_layout = QVBoxLayout(self.poster_frame)
        self.poster_layout.setContentsMargins(0, 0, 0, 0)
        self.poster_layout.setSpacing(0)
        
        self.poster_label = QLabel()
        poster_path = self.movie.get("local_poster_path")
        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
            pixmap = pixmap.scaled(160, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.poster_label.setPixmap(pixmap)
        else:
            self.poster_label.setText("")
            self.poster_label.setStyleSheet("background-color: #333;")
            self.poster_label.setFixedSize(160, 240)
        
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_layout.addWidget(self.poster_label)
        self.container_layout.addWidget(self.poster_frame)
        
        # Overlay (botões que aparecem no hover)
        self.overlay = QWidget(self.poster_frame)
        self.overlay.setObjectName("overlay")
        self.overlay.setFixedSize(160, 240)  # Tamanho fixo igual ao poster
        self.overlay.setStyleSheet("""
            QWidget#overlay {
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 8px;
            }
        """)
        
        # Layout de overlay com absoluto posicionamento centralizado
        self.overlay_layout = QVBoxLayout(self.overlay)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setAlignment(Qt.AlignCenter)
        
        # Container para botões em linha
        button_container = QHBoxLayout()
        button_container.setSpacing(10)
        button_container.setContentsMargins(0, 0, 0, 0)
        button_container.setAlignment(Qt.AlignCenter)
        
        # Botão Play
        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("playButton")
        self.play_btn.setFixedSize(50, 50)
        self.play_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.play_btn.clicked.connect(self.play_movie)
        button_container.addWidget(self.play_btn)
        
        # Botão Info
        self.info_btn = QPushButton("i")
        self.info_btn.setObjectName("infoButton")
        self.info_btn.setFixedSize(50, 50)
        self.info_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.info_btn.clicked.connect(self.show_info)
        button_container.addWidget(self.info_btn)
        
        self.overlay_layout.addLayout(button_container)
        
        self.overlay.hide()  # Esconde o overlay inicialmente
        
        self.layout.addWidget(self.container)
        
        # Estilo
        self.setStyleSheet("""
            QFrame#movieCard {
                background-color: transparent;
                border: none;
            }
            QFrame#posterFrame {
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }
            QLabel {
                border-radius: 8px;  /* Adiciona bordas arredondadas nas imagens */
            }
            QPushButton#playButton {
                background-color: #E50914;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 25px;
            }
            QPushButton#playButton:hover {
                background-color: #F40D12;
            }
            QPushButton#infoButton {
                background-color: #333;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid white;
                border-radius: 25px;
            }
            QPushButton#infoButton:hover {
                background-color: #555;
            }
        """)
        self.setFixedWidth(160)
        self.setFixedHeight(244)  # Apenas o suficiente para caber a imagem (240) + uma pequena margem
        
    def enterEvent(self, event):
        """Evento para quando o mouse entra no widget."""
        self.hovered = True
        self.overlay.show()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Evento para quando o mouse sai do widget."""
        self.hovered = False
        self.overlay.hide()
        super().leaveEvent(event)
        
    def play_movie(self):
        """Reproduz o filme."""
        file_path = self.movie.get("file_path")
        if file_path and os.path.exists(file_path):
            # Abrir o arquivo com o programa padrão do sistema
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open \"{file_path}\"")
            else:  # Linux
                os.system(f"xdg-open \"{file_path}\"")
        else:
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado!")
            
    def show_info(self):
        """Mostra informações detalhadas do filme."""
        dialog = MovieInfoDialog(self.movie, self)
        dialog.exec_()


class MovieInfoDialog(QDialog):
    """Diálogo para exibir informações detalhadas do filme."""
    
    def __init__(self, movie, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(self.movie.get("title", "Detalhes do Filme"))
        self.setMinimumSize(760, 520)
        
        # Centralizar o diálogo na tela
        screen_geometry = QDesktopWidget().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container principal com fundo semi-transparente e bordas arredondadas
        container = QFrame()
        container.setObjectName("infoContainer")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        
        # Coluna esquerda (poster)
        left_column = QVBoxLayout()
        
        # Poster com bordas arredondadas
        poster_frame = QFrame()
        poster_frame.setObjectName("posterFrame")
        poster_layout = QVBoxLayout(poster_frame)
        poster_layout.setContentsMargins(0, 0, 0, 0)
        
        poster_label = QLabel()
        poster_path = self.movie.get("local_poster_path")
        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
            pixmap = pixmap.scaled(240, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            poster_label.setPixmap(pixmap)
        else:
            poster_label.setText("Sem Poster")
            poster_label.setAlignment(Qt.AlignCenter)
            poster_label.setStyleSheet("color: white; font-size: 16px;")
            poster_label.setFixedSize(240, 360)
        
        poster_layout.addWidget(poster_label)
        left_column.addWidget(poster_frame)
        
        # Botão de assistir moderno
        play_btn = QPushButton("Assistir")
        play_btn.setObjectName("playButton")
        play_btn.clicked.connect(self.play_movie)
        left_column.addWidget(play_btn)
        
        if self.movie.get("trailer_key"):
            trailer_btn = QPushButton("Ver Trailer")
            trailer_btn.setObjectName("trailerButton")
            trailer_btn.clicked.connect(self.watch_trailer)
            left_column.addWidget(trailer_btn)
        
        left_column.addStretch()
        container_layout.addLayout(left_column)
        
        # Coluna direita (informações do filme)
        right_column = QVBoxLayout()
        
        # Título
        title_label = QLabel(self.movie.get("title", "Sem Título"))
        title_label.setObjectName("titleLabel")
        right_column.addWidget(title_label)
        
        # Título original (se for diferente)
        original_title = self.movie.get("original_title")
        if original_title and original_title != self.movie.get("title"):
            original_title_label = QLabel(f"Título Original: {original_title}")
            original_title_label.setObjectName("originalTitleLabel")
            right_column.addWidget(original_title_label)
        
        # Informações básicas
        info_layout = QHBoxLayout()
        
        # Ano
        release_date = self.movie.get("release_date", "")
        if release_date:
            year = release_date.split("-")[0]
            year_label = QLabel(year)
            year_label.setObjectName("infoLabel")
            info_layout.addWidget(year_label)
        
        # Duração
        runtime = self.movie.get("runtime")
        if runtime:
            hours, minutes = divmod(runtime, 60)
            duration_text = f"{hours}h {minutes}min" if hours else f"{minutes}min"
            duration_label = QLabel(" • " + duration_text)
            duration_label.setObjectName("infoLabel")
            info_layout.addWidget(duration_label)
        
        # Avaliação
        rating = self.movie.get("vote_average")
        if rating:
            rating_label = QLabel(f" • ⭐ {rating}/10")
            rating_label.setObjectName("infoLabel")
            info_layout.addWidget(rating_label)
        
        info_layout.addStretch()
        right_column.addLayout(info_layout)
        
        # Gêneros
        genres = self.movie.get("genres", [])
        if genres:
            genres_label = QLabel("Gêneros: " + ", ".join(genres))
            genres_label.setObjectName("detailLabel")
            right_column.addWidget(genres_label)
        
        # Diretor
        directors = self.movie.get("directors", [])
        if directors:
            directors_label = QLabel("Direção: " + ", ".join(directors))
            directors_label.setObjectName("detailLabel")
            right_column.addWidget(directors_label)
        
        # Elenco
        cast = self.movie.get("cast", [])
        if cast:
            cast_label = QLabel("Elenco: " + ", ".join(cast))
            cast_label.setObjectName("detailLabel")
            cast_label.setWordWrap(True)
            right_column.addWidget(cast_label)
        
        right_column.addSpacing(20)
        
        # Sinopse
        overview_title = QLabel("Sinopse")
        overview_title.setObjectName("sectionLabel")
        right_column.addWidget(overview_title)
        
        overview = self.movie.get("overview", "Sinopse não disponível.")
        overview_label = QLabel(overview)
        overview_label.setObjectName("overviewLabel")
        overview_label.setWordWrap(True)
        right_column.addWidget(overview_label)
        
        right_column.addStretch()
        
        # Data de adição
        date_added = self.movie.get("date_added", "")
        if date_added:
            try:
                formatted_date = date_added.split("T")[0]
                date_label = QLabel(f"Adicionado em: {formatted_date}")
                date_label.setObjectName("dateLabel")
                right_column.addWidget(date_label)
            except:
                pass
        
        container_layout.addLayout(right_column)
        main_layout.addWidget(container)
        
        # Estilo geral
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(15, 15, 15, 0.9);
            }
            QFrame#infoContainer {
                background-color: #141414;
                border-radius: 16px;
            }
            QFrame#posterFrame {
                border-radius: 15px;
                background-color: #333;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
                margin-bottom: 5px;
            }
            QLabel#originalTitleLabel {
                font-size: 16px;
                color: #aaa;
                margin-bottom: 10px;
            }
            QLabel#infoLabel {
                font-size: 14px;
                color: #ddd;
            }
            QLabel#detailLabel {
                font-size: 14px;
                color: #bbb;
                margin-top: 5px;
            }
            QLabel#sectionLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                margin-bottom: 5px;
            }
            QLabel#overviewLabel {
                font-size: 14px;
                color: #ccc;
                line-height: 1.4;
            }
            QLabel#dateLabel {
                font-size: 12px;
                color: #888;
            }
            QPushButton#playButton {
                background-color: #E50914;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                margin-top: 15px;
            }
            QPushButton#playButton:hover {
                background-color: #F40D12;
            }
            QPushButton#trailerButton {
                background-color: #333;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                margin-top: 10px;
            }
            QPushButton#trailerButton:hover {
                background-color: #444;
            }
        """)
        
    def play_movie(self):
        """Reproduz o filme."""
        file_path = self.movie.get("file_path")
        if file_path and os.path.exists(file_path):
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open \"{file_path}\"")
            else:  # Linux
                os.system(f"xdg-open \"{file_path}\"")
        else:
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado!")
    
    def watch_trailer(self):
        """Abre o trailer do filme no YouTube."""
        trailer_key = self.movie.get("trailer_key")
        if trailer_key:
            webbrowser.open(f"https://www.youtube.com/watch?v={trailer_key}")
