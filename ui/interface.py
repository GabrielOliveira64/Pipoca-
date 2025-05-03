import os
import sys
from utils import resource_path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QScrollArea, QGridLayout, QPushButton, QMessageBox, QAction, 
                            QMenuBar, QMenu, QFileDialog, QInputDialog, QFrame, QDialog,
                            QDesktopWidget, QSizePolicy, QApplication)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPalette, QColor, QCursor
from PyQt5.QtCore import Qt, QSize, QEvent, pyqtSignal, QPoint, QTimer
import webbrowser
from core.movie_manager import MovieManager
from PyQt5.QtWidgets import (QCheckBox, QLineEdit, QToolButton, QSizePolicy, 
                            QVBoxLayout, QHBoxLayout, QWidget, QFrame, QLabel,
                            QScrollArea, QGroupBox)
from PyQt5.QtSvg import QSvgWidget
from ui.movie_card import MovieCard
from ui.add_movie_dialog import AddMovieDialog
from ui.delete_movie_dialog import DeleteMovieDialog
from ui.splash_screen import SplashScreen
import json

def get_version():
    try:
        version_path = os.path.join("./", "version.json")
        if os.path.exists(version_path):
            with open(version_path, 'r') as f:
                version_data = json.load(f)
                return version_data.get("version", "Desconhecida")
        return "Desconhecida"
    except Exception:
        return "Desconhecida"

class MainWindow(QMainWindow):
    """Janela principal do aplicativo."""
    
    def __init__(self):
        super().__init__()
        self.movie_manager = MovieManager()
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.load_movies)
        self.menu_open = False
        self.menu_width = 250
        self.selected_genres = []
        self.search_term = ""
        self.init_ui()
        self.load_movies()
        self.showFullScreen()  # Restaurado para comportamento original
    
    def init_ui(self):
        self.setWindowTitle("Pipoca+")
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        file_menu = menubar.addMenu("Arquivo")
        add_action = QAction("Adicionar Filme", self)
        add_action.triggered.connect(self.add_movie)
        file_menu.addAction(add_action)
        refresh_action = QAction("Atualizar Biblioteca", self)
        refresh_action.triggered.connect(self.load_movies)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        toggle_fullscreen_action = QAction("Alternar Tela Cheia", self)
        toggle_fullscreen_action.setShortcut("F11")
        toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        file_menu.addAction(toggle_fullscreen_action)
        file_menu.addSeparator()
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
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
        about_menu = menubar.addMenu("Sobre")
        app_info_action = QAction("Informações do App", self)
        app_info_action.triggered.connect(self.show_about_info)
        about_menu.addAction(app_info_action)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(0)
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(15, 20, 15, 20)
        self.sidebar_layout.setSpacing(15)
        self.sidebar.setLayout(self.sidebar_layout)
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
        genres_label = QLabel("Filtrar por Gênero")
        genres_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-top: 10px;")
        self.sidebar_layout.addWidget(genres_label)
        genres_scroll = QScrollArea()
        genres_scroll.setWidgetResizable(True)
        genres_scroll.setStyleSheet("background-color: transparent; border: none;")
        self.genres_container = QWidget()
        self.genres_container.setStyleSheet("background-color: transparent;")
        self.genres_layout = QVBoxLayout(self.genres_container)
        self.genres_layout.setContentsMargins(0, 0, 0, 0)
        self.genres_layout.setSpacing(8)
        genres_scroll.setWidget(self.genres_container)
        self.sidebar_layout.addWidget(genres_scroll)
        self.sidebar_layout.addStretch()
        self.main_layout.addWidget(self.sidebar)
        self.content_container = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_container.setLayout(content_layout)
        header_layout = QHBoxLayout()
        self.menu_button = QToolButton()
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setFixedSize(36, 36)
        self.menu_button.clicked.connect(self.toggle_menu)
        self.menu_svg = QSvgWidget(resource_path("ui/icons/menu_bars_close.svg"))
        self.menu_svg.setFixedSize(20, 20)
        menu_button_layout = QVBoxLayout(self.menu_button)
        menu_button_layout.setContentsMargins(8, 8, 8, 8)
        menu_button_layout.addWidget(self.menu_svg)
        header_layout.addWidget(self.menu_button)
        title_label = QLabel("Minha Biblioteca")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.add_button = QPushButton("+ Filme ")
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
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setHorizontalSpacing(4)
        self.grid_layout.setVerticalSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area.setWidget(scroll_content)
        content_layout.addWidget(scroll_area)
        self.main_layout.addWidget(self.content_container)
        self.shortcut_escape = QAction("Sair da Tela Cheia", self)
        self.shortcut_escape.setShortcut("Esc")
        self.shortcut_escape.triggered.connect(self.exit_fullscreen)
        self.addAction(self.shortcut_escape)
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
                background: #1a1a1a;
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
                background: #1a1a1a;
            }
        """)
    
    def delete_movie(self):
        dialog = DeleteMovieDialog(self.movie_manager, self)
        dialog.movie_deleted.connect(self.load_movies)
        dialog.exec_()
    
    def init_sidebar(self):
        self.sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #141414;
                border-right: 1px solid #333;
            }
        """)
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
        self.sidebar_layout.insertWidget(1, search_container)
        for i in range(self.sidebar_layout.count()):
            item = self.sidebar_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QLabel) and widget.text() == "Filtrar por Gênero":
                widget.deleteLater()
                self.sidebar_layout.removeItem(item)
                break
    
    def load_movies(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        movies = self.movie_manager.get_all_movies()
        self.populate_genres(movies)
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
        available_width = self.content_container.width() - 40
        if self.menu_open:
            available_width -= self.menu_width
        card_width = 160
        card_margin = 2
        cols_with_margin = max(1, int(available_width / (card_width + 2*card_margin)))
        row, col = 0, 0
        unique_movies = {}
        for movie in filtered_movies:
            movie_key = f"{movie.get('id', '')}-{movie.get('file_path', '')}"
            if movie_key in unique_movies:
                continue
            unique_movies[movie_key] = True
            movie_card = MovieCard(movie)
            movie_card.setFixedSize(card_width, movie_card.sizeHint().height())
            self.grid_layout.addWidget(movie_card, row, col)
            col += 1
            if col >= cols_with_margin:
                col = 0
                row += 1
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addWidget(spacer, row + 1, 0, 1, cols_with_margin)

    def toggle_menu(self):
        if self.menu_open:
            self.menu_open = False
            self.sidebar.setFixedWidth(0)
            self.menu_svg.load(resource_path("ui/icons/menu_bars_close.svg"))
        else:
            self.menu_open = True
            self.sidebar.setFixedWidth(self.menu_width)
            self.menu_svg.load(resource_path("ui/icons/menu_bars_open.svg"))
        QTimer.singleShot(50, self.force_layout_update)
    
    def populate_genres(self, movies):
        while self.genres_layout.count():
            item = self.genres_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        all_genres = set()
        for movie in movies:
            genres = movie.get("genres", [])
            for genre in genres:
                all_genres.add(genre)
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
        filter_container = QFrame()
        filter_container.setStyleSheet("""
            background-color: #1a1a1a;
            border-radius: 8px;
            padding: 2px;
        """)
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setSpacing(2)
        filter_layout.setContentsMargins(8, 8, 8, 8)
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
            genre_count = sum(1 for movie in movies if genre in movie.get("genres", []))
            genre_label = QLabel(f"{genre} <span style='color: #888; font-size: 11px;'>({genre_count})</span>")
            genre_label.setStyleSheet("""
                color: #ddd;
                font-size: 13px;
            """)
            genre_layout.addWidget(checkbox)
            genre_layout.addWidget(genre_label, 1)
            filter_layout.addWidget(genre_widget)
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
        self.genres_layout.addWidget(filter_container)
        self.genres_layout.addWidget(clear_filters_btn)
        self.genres_layout.addStretch()

    def clear_genre_filters(self):
        if not self.selected_genres:
            return
        self.selected_genres = []
        was_menu_open = self.menu_open
        QTimer.singleShot(50, lambda: self.safe_force_layout_update(was_menu_open))
        for i in range(self.genres_layout.count()):
            item = self.genres_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QFrame):
                for child in widget.findChildren(QCheckBox):
                    child.setChecked(False)

    def handle_genre_filter(self, genre, state):
        if state == Qt.Checked:
            if genre not in self.selected_genres:
                self.selected_genres.append(genre)
        else:
            if genre in self.selected_genres:
                self.selected_genres.remove(genre)
        was_menu_open = self.menu_open
        self.search_term = self.search_input.text().lower()
        QTimer.singleShot(50, lambda: self.safe_force_layout_update(was_menu_open))
    
    def toggle_genre_filter(self, genre, state):
        self.handle_genre_filter(genre, state)
        if self.menu_open:
            self.menu_open = False
            self.sidebar.setFixedWidth(0)
            self.menu_svg.load(resource_path("ui/icons/menu_bars_close.svg"))
        else:
            self.menu_open = True
            self.sidebar.setFixedWidth(self.menu_width)
            self.menu_svg.load(resource_path("ui/icons/menu_bars_open.svg"))
        QTimer.singleShot(100, self.load_movies)
    
    def filter_movies(self):
        self.search_term = self.search_input.text().lower()
        was_menu_open = self.menu_open
        QTimer.singleShot(50, lambda: self.safe_force_layout_update(was_menu_open))

    def force_layout_update(self):
        self.grid_layout.setSpacing(2)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.load_movies()
        self.content_container.update()
        QApplication.processEvents()

    def safe_force_layout_update(self, should_keep_menu_open):
        self.grid_layout.setSpacing(2)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.load_movies()
        self.content_container.update()
        QApplication.processEvents()
        if should_keep_menu_open and not self.menu_open:
            self.menu_open = True
            self.sidebar.setFixedWidth(self.menu_width)
            self.menu_svg.load(resource_path("ui/icons/menu_bars_open.svg"))
    
    def apply_filters(self, movies):
        filtered_movies = []
        for movie in movies:
            match_search = True
            if self.search_term:
                title = movie.get("title", "").lower()
                original_title = movie.get("original_title", "").lower()
                overview = movie.get("overview", "").lower()
                match_search = (self.search_term in title or 
                               self.search_term in original_title or 
                               self.search_term in overview)
            match_genre = True
            if self.selected_genres:
                movie_genres = movie.get("genres", [])
                match_genre = any(genre in movie_genres for genre in self.selected_genres)
            if match_search and match_genre:
                filtered_movies.append(movie)
        return filtered_movies
    
    def add_movie(self):
        dialog = AddMovieDialog(self.movie_manager, self)
        if dialog.exec_():
            self.load_movies()
    
    def sort_movies(self, sort_key):
        movies = self.movie_manager.get_all_movies()
        if sort_key == "title":
            sorted_movies = sorted(movies, key=lambda x: x.get("title", "").lower())
        elif sort_key == "date_added":
            sorted_movies = sorted(movies, key=lambda x: x.get("date_added", ""), reverse=True)
        elif sort_key == "vote_average":
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
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            
    def show_about_info(self):
        version = get_version()
        QMessageBox.about(self, 
                        "Sobre Pipoca+", 
                        f"<h2>Pipoca+</h2>"
                        f"<p>Versão: {version}</p>"
                        f"<p>Desenvolvido por: GabrielOliveira64</p>"
                        f"<p>Um gerenciador de filmes para sua coleção pessoal.</p>")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.stop()
        self.resize_timer.start(200)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
