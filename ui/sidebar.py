from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                            QCheckBox, QLineEdit, QScrollArea, QPushButton, 
                            QWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCursor
from utils import resource_path

class Sidebar(QFrame):
    """Sidebar para filtros e pesquisa na aplicação PipocaZ."""
    
    # Sinais para comunicação com a janela principal
    searchChanged = pyqtSignal(str)
    genreFilterChanged = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.selected_genres = []
        self.search_term = ""
        self.init_ui()
        
    def init_ui(self):
        # Estilo da sidebar
        self.setStyleSheet("""
            QFrame#sidebar {
                background-color: #141414;
                border-right: 1px solid #333;
            }
        """)
        
        # Layout principal
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(15, 20, 15, 20)
        self.sidebar_layout.setSpacing(15)
        self.setLayout(self.sidebar_layout)
        
        # Container de pesquisa
        search_container = QFrame()
        search_container.setStyleSheet("""
            background-color: transparent;
            margin-bottom: 15px;
        """)
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)
        
        # Label de pesquisa
        search_label = QLabel("PESQUISAR")
        search_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #E50914;
            letter-spacing: 1px;
        """)
        
        # Input de pesquisa
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para pesquisar...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1f1f1f;
                color: white;
                border: 2px solid #333;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #E50914;
                background-color: #252525;
            }
        """)
        self.search_input.textChanged.connect(self._handle_search)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        self.sidebar_layout.addWidget(search_container)
        
        # Título de gêneros
        genres_title = QLabel("GÊNEROS")
        genres_title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #E50914;
            letter-spacing: 1px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
            margin-bottom: 12px;
        """)
        self.sidebar_layout.addWidget(genres_title)
        
        # Área de rolagem para gêneros
        genres_scroll = QScrollArea()
        genres_scroll.setWidgetResizable(True)
        genres_scroll.setStyleSheet("background-color: transparent; border: none;")
        
        # Container de gêneros
        self.genres_container = QWidget()
        self.genres_container.setStyleSheet("background-color: transparent;")
        self.genres_layout = QVBoxLayout(self.genres_container)
        self.genres_layout.setContentsMargins(0, 0, 0, 0)
        self.genres_layout.setSpacing(8)
        
        genres_scroll.setWidget(self.genres_container)
        self.sidebar_layout.addWidget(genres_scroll)
        
        # Adiciona espaço em branco no final
        self.sidebar_layout.addStretch()
    
    def _handle_search(self):
        """Manipula alterações no campo de pesquisa"""
        self.search_term = self.search_input.text().lower()
        self.searchChanged.emit(self.search_term)
    
    def handle_genre_filter(self, genre, state):
        """Manipula alterações nos filtros de gênero"""
        if state == Qt.Checked:
            if genre not in self.selected_genres:
                self.selected_genres.append(genre)
        else:
            if genre in self.selected_genres:
                self.selected_genres.remove(genre)
        
        self.genreFilterChanged.emit(self.selected_genres)
    
    def clear_genre_filters(self):
        """Limpa todos os filtros de gênero selecionados"""
        if not self.selected_genres:
            return
            
        self.selected_genres = []
        
        # Desmarca todas as checkboxes
        for i in range(self.genres_layout.count()):
            item = self.genres_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QFrame):
                for child in widget.findChildren(QCheckBox):
                    child.setChecked(False)
        
        self.genreFilterChanged.emit(self.selected_genres)
    
    def populate_genres(self, movies):
        """Preenche a barra lateral com os gêneros disponíveis"""
        # Limpa o layout atual
        while self.genres_layout.count():
            item = self.genres_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Coleta todos os gêneros únicos
        all_genres = set()
        for movie in movies:
            genres = movie.get("genres", [])
            for genre in genres:
                all_genres.add(genre)
        
        # Se não houver gêneros, mostra uma mensagem
        if not all_genres:
            no_genres_container = QFrame()
            no_genres_container.setStyleSheet("""
                background-color: #1f1f1f;
                border-radius: 6px;
                padding: 10px;
            """)
            no_genres_layout = QVBoxLayout(no_genres_container)
            no_genres_label = QLabel("Nenhum gênero disponível")
            no_genres_label.setStyleSheet("""
                color: #888;
                font-size: 13px;
                font-style: italic;
                padding: 5px;
            """)
            no_genres_label.setAlignment(Qt.AlignCenter)
            no_genres_layout.addWidget(no_genres_label)
            self.genres_layout.addWidget(no_genres_container)
            return
        
        # Container para filtros
        filter_container = QFrame()
        filter_container.setStyleSheet("""
            background-color: #1a1a1a;
            border-radius: 8px;
            padding: 2px;
        """)
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setSpacing(2)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        
        # Adiciona cada gênero com checkbox
        for genre in sorted(all_genres):
            genre_widget = QFrame()
            genre_widget.setStyleSheet("""
                QFrame {
                    border-radius: 6px;
                    padding: 2px;
                }
                QFrame:hover {
                    background-color: #252525;
                }
            """)
            genre_layout = QHBoxLayout(genre_widget)
            genre_layout.setContentsMargins(5, 5, 5, 5)
            genre_layout.setSpacing(8)
            
            checkbox = QCheckBox()
            checkbox.setChecked(genre in self.selected_genres)
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 3px;
                    border: 2px solid #555;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #2a2a2a;
                }
                QCheckBox::indicator:checked {
                    background-color: #E50914;
                    border: 2px solid #E50914;
                    image: url(ui/icons/check.svg);
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #888;
                }
            """)
            checkbox.stateChanged.connect(lambda state, g=genre: self.handle_genre_filter(g, state))
            
            # Conta quantos filmes têm este gênero
            genre_count = sum(1 for movie in movies if genre in movie.get("genres", []))
            genre_label = QLabel(f"{genre} <span style='color: #888; font-size: 11px;'>({genre_count})</span>")
            genre_label.setStyleSheet("""
                color: #ddd;
                font-size: 13px;
            """)
            
            genre_layout.addWidget(checkbox)
            genre_layout.addWidget(genre_label, 1)
            filter_layout.addWidget(genre_widget)
        
        # Botão para limpar filtros
        clear_filters_btn = QPushButton("Limpar Filtros")
        clear_filters_btn.setCursor(QCursor(Qt.PointingHandCursor))
        clear_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
                margin-top: 10px;
                font-size: 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #252525;
                color: white;
                border: 1px solid #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        clear_filters_btn.clicked.connect(self.clear_genre_filters)
        
        # Adiciona o container e o botão ao layout
        self.genres_layout.addWidget(filter_container)
        self.genres_layout.addWidget(clear_filters_btn)
        self.genres_layout.addStretch()
    
    def get_search_term(self):
        """Retorna o termo de pesquisa atual"""
        return self.search_term
    
    def get_selected_genres(self):
        """Retorna a lista de gêneros selecionados"""
        return self.selected_genres