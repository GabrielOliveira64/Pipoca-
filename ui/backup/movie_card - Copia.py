import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMessageBox, QFrame)
from PyQt5.QtGui import QPixmap, QCursor, QPainter, QPainterPath, QBrush
from PyQt5.QtCore import Qt

# Importar a classe MovieInfoDialog do outro arquivo
from ui.movie_info_dialog import MovieInfoDialog


class RoundedLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 8
        
    def paintEvent(self, event):
        if not self.pixmap():
            return super().paintEvent(event)
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self.radius, self.radius)
        
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, self.pixmap())


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
        
        self.poster_label = RoundedLabel()
        poster_path = self.movie.get("local_poster_path")
        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
            pixmap = pixmap.scaled(200, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.poster_label.setPixmap(pixmap)
        else:
            self.poster_label.setText("")
            self.poster_label.setStyleSheet("background-color: #333;")
            self.poster_label.setFixedSize(200, 300)
        
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_layout.addWidget(self.poster_label)
        self.container_layout.addWidget(self.poster_frame)
        
        # Overlay (botões que aparecem no hover)
        self.overlay = QWidget(self.poster_frame)
        self.overlay.setObjectName("overlay")
        self.overlay.setFixedSize(200, 300)  # Tamanho fixo igual ao poster
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
        self.setFixedWidth(200)
        self.setFixedHeight(304)  # Apenas o suficiente para caber a imagem (240) + uma pequena margem
        
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
