import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QListWidget, QListWidgetItem,
                            QMessageBox, QFrame, QSizePolicy, QToolButton)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont, QCursor

class MovieListItem(QListWidgetItem):
    """Item personalizado para a lista de filmes."""
    def __init__(self, movie):
        super().__init__()
        self.movie = movie
        self.setup_item()
    
    def setup_item(self):
        """Configura o texto e dados do item."""
        title = self.movie.get('title', 'Sem título')
        
        # Adicionar o ano de lançamento se disponível
        year = ''
        if self.movie.get('release_date'):
            release_year = self.movie.get('release_date', '').split('-')[0]
            if release_year:
                year = f" ({release_year})"
        
        # Adicionar o título original se for diferente do título principal
        original = ''
        if (self.movie.get('original_title') and 
            self.movie.get('original_title') != self.movie.get('title')):
            original = f"\nTítulo original: {self.movie.get('original_title')}"
        
        # Adicionar gêneros se disponíveis
        genres = ''
        if self.movie.get('genres'):
            genres_text = ", ".join(self.movie.get('genres'))
            if len(genres_text) > 50:
                genres_text = genres_text[:47] + "..."
            genres = f"\nGêneros: {genres_text}"
        
        # Configurar o texto do item
        self.setText(f"{title}{year}{original}{genres}")
        
        # Armazenar os dados do filme no item
        self.setData(Qt.UserRole, self.movie)
        
        # Ajustar a altura do item para mostrar todas as informações
        # Calcula a altura necessária com base no número de linhas de texto
        lines = self.text().count('\n') + 1
        height = max(60, lines * 20)  # Altura mínima de 60px ou 20px por linha
        self.setSizeHint(QSize(0, height))


class DeleteMovieDialog(QDialog):
    """Janela de diálogo para pesquisar e deletar filmes do catálogo."""
    
    movie_deleted = pyqtSignal()  # Sinal emitido quando um filme é deletado
    
    def __init__(self, movie_manager, parent=None):
        super().__init__(parent)
        self.movie_manager = movie_manager
        self.deleted_count = 0
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface da janela de diálogo."""
        self.setWindowTitle("Deletar Filmes")
        self.setFixedSize(500, 500)
        
        # Estilo geral
        self.setStyleSheet("""
            QDialog {
                background-color: #141414;
                color: white;
                border-radius: 8px;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #E50914;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F40D12;
            }
            QPushButton:disabled {
                background-color: #5c5c5c;
                color: #aaa;
            }
            QPushButton#cancelButton {
                background-color: #333;
                color: white;
            }
            QPushButton#cancelButton:hover {
                background-color: #444;
            }
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
            QListWidget {
                background-color: #1f1f1f;
                color: white;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
                outline: none;
                font-size: 13px;
            }
            QListWidget::item {
                background-color: #1f1f1f;
                border-bottom: 1px solid #333;
                padding: 8px;
                border-radius: 0px;
            }
            QListWidget::item:selected {
                background-color: #252525;
                color: white;
                border-left: 3px solid #E50914;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
                border: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #1a1a1a;
            }
        """)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Deletar Filmes do Catálogo")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            padding-bottom: 10px;
            border-bottom: 2px solid #E50914;
        """)
        main_layout.addWidget(title_label)
        
        # Campo de pesquisa
        search_label = QLabel("Pesquisar filme para deletar:")
        search_label.setStyleSheet("font-size: 14px; color: #ddd; margin-top: 10px;")
        main_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o nome do filme...")
        self.search_input.textChanged.connect(self.filter_movies)
        main_layout.addWidget(self.search_input)
        
        # Lista de filmes
        self.movies_list = QListWidget()
        self.movies_list.setAlternatingRowColors(True)
        self.movies_list.setSelectionMode(QListWidget.SingleSelection)
        self.movies_list.itemClicked.connect(self.enable_delete_button)
        main_layout.addWidget(self.movies_list)
        
        # Barra de status para mostrar quantidade de filmes encontrados
        self.status_label = QLabel("Nenhum filme encontrado")
        self.status_label.setStyleSheet("color: #888; font-size: 12px; margin-top: 5px;")
        main_layout.addWidget(self.status_label)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        # Botão de cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # Espaçador
        buttons_layout.addStretch()
        
        # Botão para deletar filme
        self.delete_button = QPushButton("Deletar Filme")
        self.delete_button.setEnabled(False)  # Desabilitado até que um filme seja selecionado
        self.delete_button.clicked.connect(self.delete_selected_movie)
        buttons_layout.addWidget(self.delete_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Carrega os filmes iniciais
        self.load_movies()
        
    def load_movies(self):
        """Carrega todos os filmes do catálogo na lista."""
        self.movies_list.clear()
        
        movies = self.movie_manager.get_all_movies()
        if not movies:
            self.status_label.setText("O catálogo está vazio")
            return
        
        for movie in movies:
            self.add_movie_to_list(movie)
        
        self.status_label.setText(f"{len(movies)} filmes encontrados no catálogo")
    
    def add_movie_to_list(self, movie):
        """Adiciona um filme à lista com formato mais simples e confiável."""
        item = MovieListItem(movie)
        self.movies_list.addItem(item)
    
    def filter_movies(self):
        """Filtra os filmes com base no texto de pesquisa."""
        search_text = self.search_input.text().lower()
        self.movies_list.clear()
        
        # Recarrega os filmes atuais do catálogo para ter certeza de ter a lista mais recente
        movies = self.movie_manager.get_all_movies()
        filtered_movies = []
        
        for movie in movies:
            title = movie.get('title', '').lower()
            original_title = movie.get('original_title', '').lower()
            
            if search_text in title or search_text in original_title:
                filtered_movies.append(movie)
                self.add_movie_to_list(movie)
        
        if filtered_movies:
            self.status_label.setText(f"{len(filtered_movies)} filmes encontrados")
        else:
            self.status_label.setText("Nenhum filme encontrado com esse termo")
    
    def enable_delete_button(self):
        """Habilita o botão de deletar quando um filme é selecionado."""
        self.delete_button.setEnabled(True)
    
    def delete_selected_movie(self):
        """Deleta o filme selecionado do catálogo."""
        current_item = self.movies_list.currentItem()
        if not current_item:
            return
        
        movie = current_item.data(Qt.UserRole)
        title = movie.get('title', 'Sem título')
        movie_id = movie.get('id')
        
        # Verificação adicional para garantir que temos o ID correto
        if movie_id is None:
            QMessageBox.warning(
                self, 
                "Erro ao Deletar", 
                f'Não foi possível identificar o ID do filme "{title}".'
            )
            return
        
        # Mensagem de confirmação
        reply = QMessageBox.question(
            self, 
            'Confirmar Exclusão',
            f'Tem certeza que deseja deletar o filme "{title}" (ID: {movie_id}) do catálogo?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Tenta deletar o filme
            success = self.movie_manager.delete_movie(movie_id)
            
            if success:
                self.deleted_count += 1
                self.movie_deleted.emit()  # Emite o sinal para atualizar a lista principal
                
                # Remove o item da lista
                row = self.movies_list.row(current_item)
                self.movies_list.takeItem(row)
                
                # Atualiza o status
                remaining = self.movies_list.count()
                self.status_label.setText(f"{remaining} filmes restantes | {self.deleted_count} deletados nesta sessão")
                
                # Desabilita o botão novamente
                self.delete_button.setEnabled(False)
                
                # Mostra confirmação
                QMessageBox.information(
                    self, 
                    "Filme Deletado", 
                    f'O filme "{title}" (ID: {movie_id}) foi removido do catálogo.'
                )
                
                # Recarrega a lista para garantir que esteja atualizada
                # Isso garante que a lista reflita o estado atual do catálogo
                self.load_movies()
                
                # Reaplica o filtro se houver texto de pesquisa
                if self.search_input.text():
                    self.filter_movies()
            else:
                QMessageBox.warning(
                    self, 
                    "Erro ao Deletar", 
                    f'Não foi possível deletar o filme "{title}" (ID: {movie_id}).'
                )
