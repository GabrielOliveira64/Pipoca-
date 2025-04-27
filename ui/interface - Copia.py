import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QScrollArea, QGridLayout, QPushButton, QMessageBox, QAction, 
                            QMenuBar, QMenu, QFileDialog, QInputDialog, QFrame, QDialog,
                            QDesktopWidget, QSizePolicy)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPalette, QColor, QCursor
from PyQt5.QtCore import Qt, QSize, QEvent, pyqtSignal, QPoint, QTimer
import webbrowser
from core.movie_manager import MovieManager
from PyQt5.QtWidgets import (QCheckBox, QLineEdit, QToolButton, QSizePolicy, 
                            QVBoxLayout, QHBoxLayout, QWidget, QFrame, QLabel,
                            QScrollArea, QGroupBox, QApplication)
from PyQt5.QtSvg import QSvgWidget
from ui.movie_card import MovieCard
from ui.add_movie_dialog import AddMovieDialog
from ui.delete_movie_dialog import DeleteMovieDialog

class MainWindow(QMainWindow):
    """Janela principal do aplicativo."""
    
    def __init__(self):
        super().__init__()
        self.movie_manager = MovieManager()
        self.resize_timer = QTimer()  # Adicionar um timer para o redimensionamento
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.load_movies)

        # Adicionar variável para controlar o estado do menu
        self.menu_open = False
        
        # Largura do menu lateral
        self.menu_width = 250
        
        # Lista de gêneros selecionados para filtrar
        self.selected_genres = []
        
        # Termo de pesquisa
        self.search_term = ""

        self.init_ui()
        self.load_movies()
        
        # Inicia em modo tela cheia
        self.showFullScreen()
        
    def init_ui(self):
        self.setWindowTitle("Pipoca+")
        
        # Barra de menu
        menubar = self.menuBar()
        
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #141414;
                color: white;
                border: none;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
            }
            QMenuBar::item:selected {
                background-color: #333;
                border-radius: 4px;
            }
            QMenu {
                background-color: #1f1f1f;
                color: white;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 25px 6px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #E50914;
            }
        """)
        
        # CORREÇÃO: Criar um único widget central e definir o layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal para todo o conteúdo
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Menu Arquivo
        file_menu = menubar.addMenu("Arquivo")
        
        add_action = QAction("Adicionar Filme", self)
        add_action.triggered.connect(self.add_movie)
        file_menu.addAction(add_action)
        
        refresh_action = QAction("Atualizar Biblioteca", self)
        refresh_action.triggered.connect(self.load_movies)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        # Opção para alternar entre tela cheia e janela
        toggle_fullscreen_action = QAction("Alternar Tela Cheia", self)
        toggle_fullscreen_action.setShortcut("F11")
        toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        file_menu.addAction(toggle_fullscreen_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Visualização
        view_menu = menubar.addMenu("Visualização")
        
        sort_menu = QMenu("Ordenar Por", self)
        view_menu.addMenu(sort_menu)
        
        sort_by_title = QAction("Título", self)
        sort_by_title.triggered.connect(lambda: self.sort_movies("title"))
        sort_menu.addAction(sort_by_title)
        
        sort_by_date_added = QAction("Data de Adição", self)
        sort_by_date_added.triggered.connect(lambda: self.sort_movies("date_added"))
        sort_menu.addAction(sort_by_date_added)
        
        sort_by_rating = QAction("Avaliação", self)
        sort_by_rating.triggered.connect(lambda: self.sort_movies("vote_average"))
        sort_menu.addAction(sort_by_rating)
        
        sort_by_year = QAction("Ano de Lançamento", self)
        sort_by_year.triggered.connect(lambda: self.sort_movies("release_date"))
        sort_menu.addAction(sort_by_year)
        
        # Criando o menu lateral (inicialmente oculto)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(0)  # Inicialmente com largura zero (oculto)
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(15, 20, 15, 20)
        self.sidebar_layout.setSpacing(15)
        # CORREÇÃO: Use self.sidebar_layout em vez de sidebar_layout
        self.sidebar.setLayout(self.sidebar_layout)
        
        # Campo de pesquisa
        search_label = QLabel("Pesquisar Filmes")
        search_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        self.sidebar_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para pesquisar...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                background-color: #444;
            }
        """)
        self.search_input.textChanged.connect(self.filter_movies)
        self.sidebar_layout.addWidget(self.search_input)
        
        # Categorias (Gêneros)
        genres_label = QLabel("Filtrar por Gênero")
        genres_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-top: 10px;")
        self.sidebar_layout.addWidget(genres_label)
        
        # Área de rolagem para as categorias
        genres_scroll = QScrollArea()
        genres_scroll.setWidgetResizable(True)
        genres_scroll.setStyleSheet("background-color: transparent; border: none;")
        
        self.genres_container = QWidget()
        self.genres_container.setStyleSheet("background-color: transparent;")
        self.genres_layout = QVBoxLayout(self.genres_container)
        self.genres_layout.setContentsMargins(0, 0, 0, 0)
        self.genres_layout.setSpacing(8)
        
        # Vamos adicionar os gêneros dinamicamente após carregar os filmes
        genres_scroll.setWidget(self.genres_container)
        self.sidebar_layout.addWidget(genres_scroll)
        
        self.sidebar_layout.addStretch()
        
        # Adicionar o sidebar ao layout principal
        self.main_layout.addWidget(self.sidebar)
        
        # Container para o conteúdo principal
        self.content_container = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_container.setLayout(content_layout)
        
        # Cabeçalho com título, botão de menu e botão de adicionar
        header_layout = QHBoxLayout()
        
        # Botão do menu
        self.menu_button = QToolButton()
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setFixedSize(36, 36)
        self.menu_button.clicked.connect(self.toggle_menu)
        
        # Usar o SVG para o ícone do menu
        self.menu_svg = QSvgWidget("ui/icons/menu_bars_close.svg")
        self.menu_svg.setFixedSize(20, 20)
        
        # Adicionar o SVG ao botão
        menu_button_layout = QVBoxLayout(self.menu_button)
        menu_button_layout.setContentsMargins(8, 8, 8, 8)
        menu_button_layout.addWidget(self.menu_svg)
        
        header_layout.addWidget(self.menu_button)
        
        # Título
        title_label = QLabel("Minha Biblioteca")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()

        # Botão para adicionar filme
        self.add_button = QPushButton("+ Filme")
        self.add_button.setObjectName("addButton")
        self.add_button.setFixedSize(100, 36)
        self.add_button.clicked.connect(self.add_movie)
        header_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("- Filme")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setFixedSize(100, 36)
        self.delete_button.setStyleSheet("""
            QPushButton#deleteButton {
                background-color: #333;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#deleteButton:hover {
                background-color: #555;
            }
        """)
        self.delete_button.clicked.connect(self.delete_movie)
        header_layout.addWidget(self.delete_button)
        
        content_layout.addLayout(header_layout)

        # Área de rolagem para os filmes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        # Configuração do grid layout com espaçamento mínimo
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(4)  # Zero espaçamento base
        self.grid_layout.setHorizontalSpacing(4)  # Espaçamento horizontal mínimo
        self.grid_layout.setVerticalSpacing(4)    # Espaçamento vertical mínimo
        self.grid_layout.setContentsMargins(0, 0, 0, 0)  # Sem margens no grid
        
        scroll_area.setWidget(scroll_content)
        content_layout.addWidget(scroll_area)

        # Adicionar o conteúdo ao layout principal
        self.main_layout.addWidget(self.content_container)
        
        # Atalho de teclado Esc para sair do modo tela cheia
        self.shortcut_escape = QAction("Sair da Tela Cheia", self)
        self.shortcut_escape.setShortcut("Esc")
        self.shortcut_escape.triggered.connect(self.exit_fullscreen)
        self.addAction(self.shortcut_escape)
        
        # Estilo geral
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f0f0f;
            }
            QWidget {
                background-color: #0f0f0f;
                color: white;
            }
            QPushButton#addButton {
                background-color: #E50914;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#addButton:hover {
                background-color: #F40D12;
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
                background: #1a1a1a;  /* Mesmo que o fundo da barra */
            }
            QScrollBar:horizontal {
                background: #1a1a1a;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #444;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
                border: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: #1a1a1a;  /* Mesmo que o fundo da barra */
            }
        """)
    def delete_movie(self):
        """Abre o diálogo para deletar filmes do catálogo."""
        dialog = DeleteMovieDialog(self.movie_manager, self)
        
        # Conecta o sinal emitido quando um filme é deletado
        dialog.movie_deleted.connect(self.load_movies)
        
        # Exibe o diálogo
        dialog.exec_()
    def init_sidebar(self):
        """Inicializa a barra lateral com um visual moderno."""
        # Estilização moderna para o sidebar
        self.sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #141414;
                border-right: 1px solid #333;
            }
        """)
        
        # Título principal do sidebar
        sidebar_title = QLabel("FILTROS")
        sidebar_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #E50914;
        """)
        self.sidebar_layout.insertWidget(0, sidebar_title)
        
        # Estiliza o campo de pesquisa para ficar mais moderno
        search_container = QFrame()
        search_container.setStyleSheet("""
            background-color: transparent;
            margin-bottom: 15px;
        """)
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)
        
        search_label = QLabel("PESQUISAR")
        search_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #E50914;
            letter-spacing: 1px;
        """)
        
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
        self.search_input.textChanged.connect(self.filter_movies)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        # Remover o widget de label de pesquisa antigo e o search_input antigo
        # Vamos substituí-los pelo novo container de pesquisa
        for i in range(self.sidebar_layout.count()):
            item = self.sidebar_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QLabel) and widget.text() == "Pesquisar Filmes":
                widget.deleteLater()
                self.sidebar_layout.removeItem(item)
                break
        
        for i in range(self.sidebar_layout.count()):
            item = self.sidebar_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QLineEdit):
                widget.deleteLater()
                self.sidebar_layout.removeItem(item)
                break
        
        # Inserir o novo container de pesquisa após o título principal
        self.sidebar_layout.insertWidget(1, search_container)
        
        # Remover o label de gêneros antigo para ser substituído no método populate_genres
        for i in range(self.sidebar_layout.count()):
            item = self.sidebar_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QLabel) and widget.text() == "Filtrar por Gênero":
                widget.deleteLater()
                self.sidebar_layout.removeItem(item)
                break
        
    def load_movies(self):
        """Carrega os filmes do catálogo para a interface."""
        # Limpa o layout de grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Importante: Restaurar configurações fixas de espaçamento após limpar o layout
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        movies = self.movie_manager.get_all_movies()
        
        # Popula a lista de gêneros no menu lateral
        self.populate_genres(movies)
        
        # Aplica filtros se houver
        filtered_movies = self.apply_filters(movies)
        
        if not filtered_movies:
            empty_message = "Sua biblioteca está vazia. Adicione filmes usando o botão acima."
            if movies and (self.search_term or self.selected_genres):
                empty_message = "Nenhum filme encontrado com os critérios selecionados."
                
            empty_label = QLabel(empty_message)
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #888; font-size: 16px; padding: 40px;")
            self.grid_layout.addWidget(empty_label, 0, 0)
            return
        
        # Determina o número de colunas com base na largura da janela
        available_width = self.content_container.width() - 40  # Subtrai margens
        
        # Ajusta a largura disponível considerando o estado do menu lateral
        if self.menu_open:
            available_width -= self.menu_width  # Reduz a largura disponível quando o menu está aberto
        
        card_width = 160  # Largura de cada cartão de filme
        card_margin = 2   # Margem fixa entre cards
        
        # Calcula o número ideal de colunas com base na largura disponível
        # Incluindo explicitamente a margem no cálculo
        cols_with_margin = max(1, int(available_width / (card_width + 2*card_margin)))
        
        # Adiciona os filmes ao grid
        row, col = 0, 0
        
        # Usando um dicionário para garantir que filmes com mesmo arquivo não sejam adicionados mais de uma vez
        unique_movies = {}
        
        for movie in filtered_movies:
            # Usar uma combinação de ID e caminho do arquivo como chave única
            movie_key = f"{movie.get('id', '')}-{movie.get('file_path', '')}"
            
            # Se já adicionamos esse filme, pular
            if movie_key in unique_movies:
                continue
                
            unique_movies[movie_key] = True
            
            movie_card = MovieCard(movie)
            # Definir tamanho fixo para o cartão
            movie_card.setFixedSize(card_width, movie_card.sizeHint().height())
            self.grid_layout.addWidget(movie_card, row, col)
            
            col += 1
            if col >= cols_with_margin:
                col = 0
                row += 1
        
        # Adicionar um widget vazio no final para empurrar os cartões para o topo quando houver espaço sobrando
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addWidget(spacer, row + 1, 0, 1, cols_with_margin)

    def toggle_menu(self):
        """Alterna a exibição do menu lateral."""
        if self.menu_open:
            # Fechar o menu
            self.menu_open = False
            self.sidebar.setFixedWidth(0)
            # Mudar o ícone para menu_bars
            self.menu_svg.load("ui/icons/menu_bars_close.svg")
        else:
            # Abrir o menu
            self.menu_open = True
            self.sidebar.setFixedWidth(self.menu_width)
            # Mudar o ícone para menu_bars_close
            self.menu_svg.load("ui/icons/menu_bars_open.svg")
        
        # Forçar recálculo do layout imediatamente após a mudança de visibilidade
        # Tempo reduzido para minimizar percepção de atraso
        QTimer.singleShot(50, self.force_layout_update)
    
    def populate_genres(self, movies):
        """Popula a lista de gêneros no menu lateral com estilo moderno."""
        # Limpar o layout de gêneros
        while self.genres_layout.count():
            item = self.genres_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Coletar todos os gêneros únicos dos filmes
        all_genres = set()
        for movie in movies:
            genres = movie.get("genres", [])
            for genre in genres:
                all_genres.add(genre)
        
        # Título de seção com estilo moderno
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
        self.genres_layout.addWidget(genres_title)
        
        # Se não houver gêneros, adicionar uma mensagem com estilo moderno
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
        
        # Cria um frame para conter os checkboxes com estilo moderno
        filter_container = QFrame()
        filter_container.setStyleSheet("""
            background-color: #1a1a1a;
            border-radius: 8px;
            padding: 2px;
        """)
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setSpacing(2)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        
        # Adicionar cada gênero como um checkbox estilizado
        for genre in sorted(all_genres):
            # Criar um widget para cada checkbox com layout horizontal
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
            
            # Checkbox personalizado
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
            
            # Conectar o sinal usando uma função lambda com captura do gênero
            checkbox.stateChanged.connect(lambda state, g=genre: self.handle_genre_filter(g, state))
            
            # Label do gênero com contador (quantidade de filmes)
            genre_count = sum(1 for movie in movies if genre in movie.get("genres", []))
            genre_label = QLabel(f"{genre} <span style='color: #888; font-size: 11px;'>({genre_count})</span>")
            genre_label.setStyleSheet("""
                color: #ddd;
                font-size: 13px;
            """)
            
            # Adiciona o checkbox e o label ao layout
            genre_layout.addWidget(checkbox)
            genre_layout.addWidget(genre_label, 1)  # 1 = stretch factor para expandir
            
            # Adiciona o widget do gênero ao container principal
            filter_layout.addWidget(genre_widget)
        
        # Botão para limpar todos os filtros
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
        
        # Adiciona o container de filtros ao layout principal
        self.genres_layout.addWidget(filter_container)
        self.genres_layout.addWidget(clear_filters_btn)
        self.genres_layout.addStretch()

    def clear_genre_filters(self):
        """Limpa todos os filtros de gênero selecionados."""
        if not self.selected_genres:
            return  # Já está limpo
            
        # Limpa a lista de gêneros selecionados
        self.selected_genres = []
        
        # Preserva o estado do menu
        was_menu_open = self.menu_open
        
        # Atualiza a interface
        QTimer.singleShot(50, lambda: self.safe_force_layout_update(was_menu_open))
        
        # Atualiza os checkboxes para o estado desmarcado
        for i in range(self.genres_layout.count()):
            item = self.genres_layout.itemAt(i)
            widget = item.widget()
            
            # Procura checkboxes dentro dos widgets do layout
            if isinstance(widget, QFrame):
                for child in widget.findChildren(QCheckBox):
                    child.setChecked(False)

    def handle_genre_filter(self, genre, state):
        """Gerencia a alteração de estado dos filtros de gênero."""
        # Atualizar a lista de gêneros selecionados
        if state == Qt.Checked:
            if genre not in self.selected_genres:
                self.selected_genres.append(genre)
        else:
            if genre in self.selected_genres:
                self.selected_genres.remove(genre)
        
        # Lembrar o estado do menu
        was_menu_open = self.menu_open
        
        # Atualizar os filmes
        self.search_term = self.search_input.text().lower()
        
        # Usar um QTimer para atualizar o layout após processamento dos eventos
        QTimer.singleShot(50, lambda: self.safe_force_layout_update(was_menu_open))
    
    def toggle_genre_filter(self, genre, state):
        """Alterna a exibição do menu lateral."""
        self.handle_genre_filter(genre, state)
        if self.menu_open:
            # Fechar o menu
            self.menu_open = False
            self.sidebar.setFixedWidth(0)
            # Mudar o ícone para menu_bars
            self.menu_svg.load("ui/icons/menu_bars_close.svg")
        else:
            # Abrir o menu
            self.menu_open = True
            self.sidebar.setFixedWidth(self.menu_width)
            # Mudar o ícone para menu_bars_close
            self.menu_svg.load("ui/icons/menu_bars_open.svg")
    
        # Forçar recálculo do layout após um breve atraso
        QTimer.singleShot(100, self.load_movies)
    
    def filter_movies(self):
        """Filtra os filmes com base nos critérios selecionados."""
        # Atualiza o termo de pesquisa
        self.search_term = self.search_input.text().lower()
        
        # Preservar o estado do menu
        was_menu_open = self.menu_open
        
        # Recarrega os filmes com os filtros aplicados
        QTimer.singleShot(50, lambda: self.safe_force_layout_update(was_menu_open))

    def force_layout_update(self):
        """Força uma atualização completa do layout."""
        # Redefine explicitamente as propriedades do grid
        self.grid_layout.setSpacing(2)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Força o recálculo do layout
        self.load_movies()  # Não chame a si mesmo aqui!
        
        # Atualiza explicitamente a interface
        self.content_container.update()
        QApplication.processEvents()  # Processamento imediato dos eventos pendentes

    def safe_force_layout_update(self, should_keep_menu_open):
        """Força uma atualização do layout preservando o estado do menu."""
        # Redefine explicitamente as propriedades do grid
        self.grid_layout.setSpacing(2)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Força o recálculo do layout
        self.load_movies()
        
        # Atualiza explicitamente a interface
        self.content_container.update()
        QApplication.processEvents()
        
        # Restaura o estado do menu se necessário
        if should_keep_menu_open and not self.menu_open:
            # Restaura o menu sem chamar toggle_menu para evitar ciclos
            self.menu_open = True
            self.sidebar.setFixedWidth(self.menu_width)
            self.menu_svg.load("ui/icons/menu_bars_open.svg")
    
    def apply_filters(self, movies):
        """Aplica os filtros de pesquisa e gênero aos filmes."""
        filtered_movies = []
        
        for movie in movies:
            # Verificar se o filme corresponde ao termo de pesquisa
            match_search = True
            if self.search_term:
                title = movie.get("title", "").lower()
                original_title = movie.get("original_title", "").lower()
                overview = movie.get("overview", "").lower()
                
                match_search = (self.search_term in title or 
                               self.search_term in original_title or 
                               self.search_term in overview)
            
            # Verificar se o filme corresponde aos gêneros selecionados
            match_genre = True
            if self.selected_genres:
                movie_genres = movie.get("genres", [])
                # Verifica se pelo menos um dos gêneros selecionados está no filme
                match_genre = any(genre in movie_genres for genre in self.selected_genres)
            
            # Adicionar o filme à lista filtrada se corresponder a ambos os critérios
            if match_search and match_genre:
                filtered_movies.append(movie)
        
        return filtered_movies
    
    def add_movie(self):
        """Abre o diálogo para adicionar um novo filme."""
        dialog = AddMovieDialog(self.movie_manager, self)
        if dialog.exec_():
            self.load_movies()
    
    def sort_movies(self, sort_key):
        """Ordena os filmes com base no critério especificado."""
        movies = self.movie_manager.get_all_movies()
        
        if sort_key == "title":
            sorted_movies = sorted(movies, key=lambda x: x.get("title", "").lower())
        elif sort_key == "date_added":
            sorted_movies = sorted(movies, key=lambda x: x.get("date_added", ""), reverse=True)
        elif sort_key == "vote_average":
            # Garantir que filmes sem avaliação não causem erros
            sorted_movies = sorted(
                movies, 
                key=lambda x: float(x.get("vote_average", 0)) if x.get("vote_average") not in (None, "") else 0, 
                reverse=True
            )
        elif sort_key == "release_date":
            sorted_movies = sorted(movies, key=lambda x: x.get("release_date", ""), reverse=True)
        else:
            return
        
        self.movie_manager.catalog["movies"] = sorted_movies
        self.movie_manager.save_catalog()
        self.load_movies()
    
    def toggle_fullscreen(self):
        """Alterna entre modo tela cheia e janela."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def exit_fullscreen(self):
        """Sai do modo tela cheia."""
        if self.isFullScreen():
            self.showNormal()
    
    def resizeEvent(self, event):
        """Evento disparado quando a janela é redimensionada."""
        super().resizeEvent(event)
        # Cancelar qualquer timer pendente e iniciar um novo
        self.resize_timer.stop()
        self.resize_timer.start(200)  # Reduzido para 200ms para resposta mais rápida
