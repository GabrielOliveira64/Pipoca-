from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QScrollArea, 
                            QVBoxLayout, QSizePolicy)
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint
import os

class FilmesCarrossel(QWidget):
    filmeSelecionado = pyqtSignal(dict)  # Sinal para quando um filme for selecionado
    
    def __init__(self, generos, filme_id_atual, parent=None):
        super().__init__(parent)
        self.generos = generos
        self.filme_id_atual = filme_id_atual
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de rolagem horizontal
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(180)  # Altura fixa para os posters
        
        # Widget para conter os filmes similares
        filmes_container = QWidget()
        filmes_layout = QHBoxLayout(filmes_container)
        filmes_layout.setContentsMargins(0, 0, 0, 0)
        filmes_layout.setSpacing(10)
        
        # Buscar filmes similares (implementar esta função)
        filmes_similares = self.buscar_filmes_similares()
        
        # Adicionar cada filme ao layout horizontal
        for filme in filmes_similares:
            filme_widget = self.criar_widget_filme(filme)
            filmes_layout.addWidget(filme_widget)
        
        # Adicionar espaçador para permitir rolar além do último item
        filmes_layout.addStretch()
        
        scroll_area.setWidget(filmes_container)
        main_layout.addWidget(scroll_area)
        
        # Implementar rolagem suave com o mouse
        self.setMouseTracking(True)
        self.last_pos = None
        
    def buscar_filmes_similares(self):
        # Aqui você deve implementar a lógica para buscar filmes com gêneros similares
        # Este é apenas um exemplo - você deve integrar com seu sistema de dados
        filmes_exemplo = [
            {"id": 1, "title": "Filme Similar 1", "poster_path": "assets/poster_images/1.jpg"},
            {"id": 2, "title": "Filme Similar 2", "poster_path": "assets/poster_images/2.jpg"},
            # Adicione mais exemplos conforme necessário
        ]
        return filmes_exemplo
        
    def criar_widget_filme(self, filme):
        # Cria um widget para representar um filme no carrossel
        filme_widget = QWidget()
        filme_widget.setObjectName("similarMovie")
        filme_widget.setCursor(Qt.PointingHandCursor)
        filme_widget.setProperty("filme_id", filme["id"])
        
        layout = QVBoxLayout(filme_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Poster do filme
        poster_label = QLabel()
        poster_label.setFixedSize(110, 150)  # Tamanho fixo para o poster
        
        # Carregar imagem do poster
        poster_path = filme.get("poster_path")
        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
            poster_label.setPixmap(pixmap.scaled(poster_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            poster_label.setText("Sem Imagem")
            poster_label.setAlignment(Qt.AlignCenter)
            poster_label.setStyleSheet("background-color: #333; color: #999;")
            
        layout.addWidget(poster_label)
        
        # Título do filme
        titulo_label = QLabel(filme.get("title", ""))
        titulo_label.setAlignment(Qt.AlignCenter)
        titulo_label.setWordWrap(True)
        titulo_label.setStyleSheet("font-size: 12px; color: white;")
        layout.addWidget(titulo_label)
        
        # Conectar clique para abrir detalhes do filme
        filme_widget.mousePressEvent = lambda e, f=filme: self.abrir_filme_detalhes(f)
        
        return filme_widget
        
    def abrir_filme_detalhes(self, filme):
        # Emitir sinal com informações do filme selecionado
        self.filmeSelecionado.emit(filme)
        
    def mousePressEvent(self, event):
        self.last_pos = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.last_pos and event.buttons() == Qt.LeftButton:
            scroll_area = self.findChild(QScrollArea)
            if scroll_area:
                delta = self.last_pos.x() - event.pos().x()
                scroll_bar = scroll_area.horizontalScrollBar()
                scroll_bar.setValue(scroll_bar.value() + delta)
                self.last_pos = event.pos()
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.last_pos = None
        super().mouseReleaseEvent(event)