import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QMessageBox, QDesktopWidget,
                            QScrollArea, QGridLayout, QFrame)
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QBrush, QColor
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QSize
import webbrowser


class MovieInfoPage(QWidget):
    """Página para exibir informações detalhadas do filme com animações."""
    
    def __init__(self, movie, parent=None, base_path=None):
        super().__init__(parent)
        self.movie = movie
        self.parent = parent
        self.base_path = base_path or os.getcwd()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()
        self.setup_animations()
        
    def init_ui(self):
        # Obter tamanho da tela para animações e dimensionamento
        self.screen_size = QDesktopWidget().screenGeometry()
        self.setGeometry(0, -self.screen_size.height(), self.screen_size.width(), self.screen_size.height())
        
        # Container principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Container do backdrop full screen com gradiente
        self.backdrop_container = QWidget()
        self.backdrop_container.setObjectName("backdropContainer")
        backdrop_layout = QVBoxLayout(self.backdrop_container)
        backdrop_layout.setContentsMargins(0, 0, 0, 0)
        
        # Backdrop de fundo
        self.backdrop_label = QLabel()
        self.backdrop_label.setObjectName("backdropImage")
        self.setup_backdrop()
        backdrop_layout.addWidget(self.backdrop_label)
        
        # Container para o conteúdo com gradiente por cima do backdrop
        self.content_container = QWidget()
        self.content_container.setObjectName("contentOverlay")
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        # Botão de voltar no canto superior esquerdo
        back_btn = QPushButton()
        back_btn.setIcon(QIcon("assets/icons/back_arrow.png"))
        back_btn.setObjectName("backButton")
        back_btn.setToolTip("Voltar")
        back_btn.clicked.connect(self.close_animation)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(back_btn, 0, Qt.AlignLeft | Qt.AlignTop)
        header_layout.addStretch()
        content_layout.addLayout(header_layout)
        
        # Layout principal dividido em duas partes (1/3 esquerda para info, 2/3 direita vazia)
        main_content_layout = QHBoxLayout()
        
        # Área de rolagem para o conteúdo principal (1/3 esquerda)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setObjectName("transparentScroll")
        scroll_area.setMaximumWidth(self.screen_size.width() // 3)
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 20, 0, 20)
        scroll_layout.setSpacing(30)
        
        # Container único com efeito de vidro para todas as informações
        main_info_container = QFrame()
        main_info_container.setObjectName("glassContainer")
        main_info_layout = QVBoxLayout(main_info_container)
        main_info_layout.setContentsMargins(20, 20, 20, 20)
        main_info_layout.setSpacing(15)
        
        # GRID 1: Informações básicas do filme
        info_grid = QGridLayout()
        info_grid.setSpacing(8)
        
        # Título do filme
        title_label = QLabel(self.movie.get("title", "Sem Título"))
        title_label.setObjectName("titleLabel")
        info_grid.addWidget(title_label, 0, 0, 1, 3, Qt.AlignLeft)  # Expandido para 3 colunas
        
        # Título original (se for diferente)
        original_title = self.movie.get("original_title")
        if original_title and original_title != self.movie.get("title"):
            original_title_label = QLabel(f"Título Original: {original_title}")
            original_title_label.setObjectName("originalTitleLabel")
            info_grid.addWidget(original_title_label, 1, 0, 1, 3, Qt.AlignLeft)  # Expandido para 3 colunas
        
        # Informações básicas em linha (agora todas na mesma linha)
        info_row = 2
        
        # Layout horizontal para ano, duração e avaliação
        basic_info_layout = QHBoxLayout()
        basic_info_layout.setSpacing(15)  # Espaçamento uniforme entre os elementos
        
        # Ano
        release_date = self.movie.get("release_date", "")
        if release_date:
            year = release_date.split("-")[0]
            year_label = QLabel(year)
            year_label.setObjectName("infoLabel")
            basic_info_layout.addWidget(year_label)
        
        # Duração
        runtime = self.movie.get("runtime")
        if runtime:
            hours, minutes = divmod(runtime, 60)
            duration_text = f"{hours}h {minutes}min" if hours else f"{minutes}min"
            duration_label = QLabel(duration_text)
            duration_label.setObjectName("infoLabel")
            basic_info_layout.addWidget(duration_label)
        
        # Avaliação com uma casa decimal
        rating = self.movie.get("vote_average")
        if rating:
            # Formatação com uma casa decimal
            formatted_rating = f"{rating:.1f}" if isinstance(rating, (int, float)) else rating
            rating_label = QLabel(f"⭐ {formatted_rating}/10")
            rating_label.setObjectName("infoLabel")
            basic_info_layout.addWidget(rating_label)
        
        # Adiciona espaçador para que os elementos se alinhem à esquerda
        basic_info_layout.addStretch()
        
        # Adiciona o layout horizontal à grid
        info_grid.addLayout(basic_info_layout, info_row, 0, 1, 3)
        info_row += 1
        
        # Gêneros
        genres = self.movie.get("genres", [])
        if genres:
            genres_label = QLabel("Gêneros: " + ", ".join(genres))
            genres_label.setObjectName("detailLabel")
            info_grid.addWidget(genres_label, info_row, 0, 1, 3, Qt.AlignLeft)
            info_row += 1
        
        main_info_layout.addLayout(info_grid)
        
        # Sinopse com título
        sinopse_container = QFrame()
        sinopse_container.setObjectName("sinopseContainer")
        sinopse_layout = QVBoxLayout(sinopse_container)
        sinopse_layout.setContentsMargins(0, 10, 0, 10)  # Margens consistentes
        
        overview_title = QLabel("Sinopse")
        overview_title.setObjectName("sectionLabel")
        overview_title.setAlignment(Qt.AlignLeft)
        sinopse_layout.addWidget(overview_title)
        
        overview = self.movie.get("overview", "Sinopse não disponível.")
        overview_label = QLabel(overview)
        overview_label.setObjectName("overviewLabel")
        overview_label.setWordWrap(True)
        overview_label.setAlignment(Qt.AlignJustify)
        sinopse_layout.addWidget(overview_label)
        
        main_info_layout.addWidget(sinopse_container)
        
        # GRID 2: Seção de diretores
        directors = self.movie.get("directors", [])
        if directors:
            directors_container = QFrame()
            directors_container.setObjectName("directorsContainer")
            directors_layout = QVBoxLayout(directors_container)
            directors_layout.setContentsMargins(0, 10, 0, 10)  # Margens consistentes
            
            director_title = QLabel("Direção")
            director_title.setObjectName("sectionLabel")
            director_title.setAlignment(Qt.AlignLeft)
            directors_layout.addWidget(director_title)
            
            directors_grid = QGridLayout()
            directors_grid.setHorizontalSpacing(25)  # Espaçamento horizontal entre os diretores
            directors_grid.setVerticalSpacing(15)
            
            for i, person in enumerate(directors):
                # Verifica se person é uma string ou um dicionário
                if isinstance(person, str):
                    person_name = person
                    person_id = None
                    profile_path = None
                else:
                    person_name = person.get("name", "")
                    person_id = person.get("id")
                    profile_path = person.get("profile_path")
                    
                if not person_name:
                    continue
                    
                person_frame = QWidget()  # Alterado para QWidget sem background
                person_frame.setObjectName("personCard")
                person_layout = QVBoxLayout(person_frame)
                person_layout.setContentsMargins(0, 0, 0, 0)  # Sem margens
                person_layout.setSpacing(6)  # Menor espaço entre foto e nome
                person_layout.setAlignment(Qt.AlignCenter)
                
                # Foto da pessoa com recorte circular
                person_photo_label = QLabel()
                person_photo_label.setObjectName("personPhoto")
                
                # Verifica se temos ID da pessoa e um caminho de foto
                if person_id and profile_path:
                    person_photo_path = f"assets/profile_images/director_{person_id}.jpg"
                    
                    # Convertemos para caminho absoluto se for relativo
                    if not os.path.isabs(person_photo_path):
                        person_photo_path = os.path.join(self.base_path, person_photo_path)
                    
                    if os.path.exists(person_photo_path):
                        # Criar um pixmap circular com borda suavizada
                        original_pixmap = QPixmap(person_photo_path)
                        size = 60
                        rounded_pixmap = QPixmap(size, size)
                        rounded_pixmap.fill(Qt.transparent)
                        
                        painter = QPainter(rounded_pixmap)
                        painter.setRenderHint(QPainter.Antialiasing)
                        painter.setBrush(QBrush(original_pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
                        painter.setPen(Qt.NoPen)
                        painter.drawEllipse(0, 0, size, size)
                        painter.end()
                        
                        person_photo_label.setPixmap(rounded_pixmap)
                        person_photo_label.setFixedSize(size, size)
                    else:
                        person_photo_label.setText("Sem Foto")
                        person_photo_label.setAlignment(Qt.AlignCenter)
                        person_photo_label.setFixedSize(120, 120)
                else:
                    person_photo_label.setText("Sem Foto")
                    person_photo_label.setAlignment(Qt.AlignCenter)
                    person_photo_label.setFixedSize(120, 120)
                
                person_layout.addWidget(person_photo_label, 0, Qt.AlignHCenter)
                
                # Nome da pessoa
                person_name_label = QLabel(person_name)
                person_name_label.setObjectName("personName")
                person_name_label.setAlignment(Qt.AlignHCenter)
                person_layout.addWidget(person_name_label, 0, Qt.AlignHCenter)
                
                # Adiciona ao grid - 3 colunas
                row = i // 3
                col = i % 3
                directors_grid.addWidget(person_frame, row, col, Qt.AlignCenter)
            
            directors_layout.addLayout(directors_grid)
            directors_container.setMaximumWidth(self.screen_size.width() // 9)  # 1/3 do container principal
        
        # GRID 3: Seção de elenco
        cast = self.movie.get("cast", [])
        if cast:
            cast_container = QFrame()
            cast_container.setObjectName("castContainer")
            cast_layout = QVBoxLayout(cast_container)
            cast_layout.setContentsMargins(0, 10, 0, 10)  # Margens consistentes
            
            cast_title = QLabel("Elenco Principal")
            cast_title.setObjectName("sectionLabel")
            cast_title.setAlignment(Qt.AlignLeft)
            cast_layout.addWidget(cast_title)
            
            cast_grid = QGridLayout()
            cast_grid.setHorizontalSpacing(5)  # Reduzido o espaçamento horizontal
            cast_grid.setVerticalSpacing(15)
            
            max_actors = min(6, len(cast))  # Limite de 6 atores para manter compacto
            for i in range(max_actors):
                actor_info = cast[i]
                
                # Verifica se actor_info é uma string ou um dicionário
                if isinstance(actor_info, str):
                    actor_name = actor_info
                    actor_id = None
                    profile_path = None
                    character = None
                else:
                    actor_name = actor_info.get("name", "")
                    actor_id = actor_info.get("id")
                    profile_path = actor_info.get("profile_path")
                    character = actor_info.get("character", "")
                    
                if not actor_name:
                    continue
                
                actor_frame = QWidget()  # Alterado para QWidget sem background
                actor_frame.setObjectName("actorCard")
                actor_layout = QVBoxLayout(actor_frame)
                actor_layout.setContentsMargins(0, 0, 0, 0)  # Sem margens
                actor_layout.setSpacing(6)  # Menor espaço entre foto e nome
                actor_layout.setAlignment(Qt.AlignCenter)
                
                # Foto do ator com recorte circular
                actor_photo_label = QLabel()
                actor_photo_label.setObjectName("personPhoto")
                
                # Verifica se temos ID do ator e um caminho de foto
                if actor_id and profile_path:
                    actor_photo_path = f"assets/profile_images/cast_{actor_id}.jpg"
                    
                    # Convertemos para caminho absoluto se for relativo
                    if not os.path.isabs(actor_photo_path):
                        actor_photo_path = os.path.join(self.base_path, actor_photo_path)
                    
                    if os.path.exists(actor_photo_path):
                        # Criar um pixmap circular com borda suavizada
                        original_pixmap = QPixmap(actor_photo_path)
                        size = 60
                        rounded_pixmap = QPixmap(size, size)
                        rounded_pixmap.fill(Qt.transparent)
                        
                        painter = QPainter(rounded_pixmap)
                        painter.setRenderHint(QPainter.Antialiasing)
                        painter.setBrush(QBrush(original_pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
                        painter.setPen(Qt.NoPen)
                        painter.drawEllipse(0, 0, size, size)
                        painter.end()
                        
                        actor_photo_label.setPixmap(rounded_pixmap)
                        actor_photo_label.setFixedSize(size, size)
                    else:
                        actor_photo_label.setText("Sem Foto")
                        actor_photo_label.setAlignment(Qt.AlignCenter)
                        actor_photo_label.setFixedSize(120, 120)
                else:
                    actor_photo_label.setText("Sem Foto")
                    actor_photo_label.setAlignment(Qt.AlignCenter)
                    actor_photo_label.setFixedSize(120, 120)
                
                actor_layout.addWidget(actor_photo_label, 0, Qt.AlignHCenter)
                
                # Nome do ator
                actor_name_label = QLabel(actor_name)
                actor_name_label.setObjectName("personName")
                actor_name_label.setAlignment(Qt.AlignHCenter)
                actor_layout.addWidget(actor_name_label, 0, Qt.AlignHCenter)
                
                # Personagem (se disponível)
                if character:
                    character_label = QLabel(f"como {character}")
                    character_label.setObjectName("characterName")
                    character_label.setAlignment(Qt.AlignHCenter)
                    actor_layout.addWidget(character_label, 0, Qt.AlignHCenter)
                
                # Adiciona ao grid - 3 colunas para aproximar horizontalmente
                row = i // 3
                col = i % 3
                cast_grid.addWidget(actor_frame, row, col, Qt.AlignCenter)
            
            cast_layout.addLayout(cast_grid)
            cast_container.setMinimumWidth(self.screen_size.width() // 5)  # 2/3 do container principal
        
        # Layout horizontal para diretores e elenco lado a lado
        if directors or cast:
            directors_cast_layout = QHBoxLayout()
            directors_cast_layout.setSpacing(0)  # Sem espaçamento entre os containers
            
            # Adiciona diretores se existirem
            if directors:
                directors_cast_layout.addWidget(directors_container)
                
                # Adiciona separador vertical se tiver ambos
                if cast:
                    separator = QFrame()
                    separator.setObjectName("verticalSeparator")
                    separator.setFrameShape(QFrame.VLine)
                    separator.setFrameShadow(QFrame.Sunken)
                    separator.setMaximumWidth(1)
                    directors_cast_layout.addWidget(separator)
            
            # Adiciona elenco se existir
            if cast:
                directors_cast_layout.addWidget(cast_container)
            
            main_info_layout.addLayout(directors_cast_layout)
        
        # Seção de filmes similares
        similares_container = QFrame()
        similares_container.setObjectName("similaresContainer")
        similares_layout = QVBoxLayout(similares_container)
        similares_layout.setContentsMargins(0, 10, 0, 10)
        
        similares_title = QLabel("Similares")
        similares_title.setObjectName("sectionLabel")
        similares_title.setAlignment(Qt.AlignLeft)
        similares_layout.addWidget(similares_title)
        
        # Placeholder para o carrossel (será implementado em outro módulo)
        similares_placeholder = QLabel("Carrossel de filmes similares será carregado aqui.")
        similares_placeholder.setObjectName("placeholderLabel")
        similares_placeholder.setAlignment(Qt.AlignCenter)
        similares_layout.addWidget(similares_placeholder)
        
        main_info_layout.addWidget(similares_container)
        
        # Data de adição
        date_added = self.movie.get("date_added", "")
        if date_added:
            try:
                formatted_date = date_added.split("T")[0]
                date_label = QLabel(f"Adicionado em: {formatted_date}")
                date_label.setObjectName("dateLabel")
                date_label.setAlignment(Qt.AlignRight)
                main_info_layout.addWidget(date_label)
            except:
                pass
        
        scroll_layout.addWidget(main_info_container)
        
        scroll_area.setWidget(scroll_content)
        main_content_layout.addWidget(scroll_area)
        
        # Área vazia à direita (2/3 da tela)
        empty_space = QWidget()
        empty_space.setObjectName("emptySpace")
        main_content_layout.addWidget(empty_space)
        
        content_layout.addLayout(main_content_layout)
        
        # Botões de ação na parte inferior centralizada
        buttons_container = QFrame()
        buttons_container.setObjectName("buttonsContainer")
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 20, 0, 20)
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignLeft)  # Alinhando à esquerda para acompanhar o conteúdo
        
        play_btn = QPushButton("Assistir")
        play_btn.setObjectName("playButton")
        play_btn.clicked.connect(self.play_movie)
        buttons_layout.addWidget(play_btn)
        
        if self.movie.get("trailer_key"):
            trailer_btn = QPushButton("Ver Trailer")
            trailer_btn.setObjectName("trailerButton")
            trailer_btn.clicked.connect(self.watch_trailer)
            buttons_layout.addWidget(trailer_btn)
        
        content_layout.addWidget(buttons_container)
        
        # Adicionar os containers ao layout principal
        self.backdrop_container.setParent(None)  # Remove do layout anterior se houver
        self.main_layout.addWidget(self.backdrop_container)
        
        # O content_container será posicionado por cima do backdrop via stacking
        self.content_container.setParent(self)
        self.content_container.setGeometry(0, 0, self.screen_size.width(), self.screen_size.height())
        
        self.apply_stylesheet()
        
        # Lista de widgets para animação fade-in
        self.fade_widgets = [main_info_container]
        if directors:
            self.fade_widgets.append(directors_container)
        if cast:
            self.fade_widgets.append(cast_container)
        self.fade_widgets.append(similares_container)
        
    def setup_backdrop(self):
        """Configura a imagem de fundo (backdrop) em tela cheia."""
        backdrop_path = None
        if "backdrop_local_path" in self.movie and self.movie["backdrop_local_path"]:
            backdrop_path = self.movie["backdrop_local_path"]
        else:
            # Tenta construir o caminho baseado no tmdb_id
            tmdb_id = self.movie.get("tmdb_id")
            if tmdb_id:
                backdrop_path = f"assets/backdrop_images/{tmdb_id}_backdrop.jpg"
            # Se não tiver tmdb_id, tentar com o id local
            elif "id" in self.movie:
                backdrop_path = f"assets/backdrop_images/{self.movie['id']}_backdrop.jpg"
        
        if backdrop_path:
            # Convertemos para caminho absoluto se for relativo
            if not os.path.isabs(backdrop_path):
                backdrop_path = os.path.join(self.base_path, backdrop_path)
            
            if os.path.exists(backdrop_path):
                pixmap = QPixmap(backdrop_path)
                # Redimensiona para cobrir toda a tela mantendo a proporção
                screen_size = self.screen_size
                scaled_pixmap = pixmap.scaled(screen_size.width(), screen_size.height(), 
                                            Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                
                # Crop centralizado se a imagem for maior que a tela
                if scaled_pixmap.width() > screen_size.width() or scaled_pixmap.height() > screen_size.height():
                    x = (scaled_pixmap.width() - screen_size.width()) // 2 if scaled_pixmap.width() > screen_size.width() else 0
                    y = (scaled_pixmap.height() - screen_size.height()) // 2 if scaled_pixmap.height() > screen_size.height() else 0
                    scaled_pixmap = scaled_pixmap.copy(x, y, 
                                                    min(scaled_pixmap.width(), screen_size.width()), 
                                                    min(scaled_pixmap.height(), screen_size.height()))
                
                self.backdrop_label.setPixmap(scaled_pixmap)
            else:
                print(f"Backdrop não encontrado: {backdrop_path}")
                self.backdrop_label.setText("Imagem não disponível")
                self.backdrop_label.setAlignment(Qt.AlignCenter)
                self.backdrop_label.setStyleSheet("color: white; font-size: 18px; background-color: #141414;")
        else:
            self.backdrop_label.setText("Imagem não disponível")
            self.backdrop_label.setAlignment(Qt.AlignCenter)
            self.backdrop_label.setStyleSheet("color: white; font-size: 18px; background-color: #141414;")
    
    def setup_animations(self):
        """Configura as animações de entrada e saída."""
        # Animação de entrada (do topo para o centro)
        self.open_animation = QPropertyAnimation(self, b"geometry")
        self.open_animation.setDuration(500)
        self.open_animation.setStartValue(QRect(0, -self.screen_size.height(), 
                                             self.screen_size.width(), self.screen_size.height()))
        self.open_animation.setEndValue(QRect(0, 0, self.screen_size.width(), self.screen_size.height()))
        self.open_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.open_animation.finished.connect(self.start_fade_animations)
        
        # Animação de saída (do centro para o topo)
        self.close_anim = QPropertyAnimation(self, b"geometry")
        self.close_anim.setDuration(500)
        self.close_anim.setStartValue(QRect(0, 0, self.screen_size.width(), self.screen_size.height()))
        self.close_anim.setEndValue(QRect(0, -self.screen_size.height(), 
                                       self.screen_size.width(), self.screen_size.height()))
        self.close_anim.setEasingCurve(QEasingCurve.InCubic)
        self.close_anim.finished.connect(self.hide)
        
        # Preparar os widgets para aparecerem com fade
        for widget in self.fade_widgets:
            widget.setStyleSheet(widget.styleSheet() + "opacity: 0;")
            
    def start_fade_animations(self):
        """Inicia as animações de fade-in para os widgets."""
        # Grupo sequencial para animar os elementos um após o outro
        self.seq_group = QSequentialAnimationGroup()
        
        # Duração base do fade
        fade_duration = 400
        
        # Cria animações de fade-in para cada widget
        for i, widget in enumerate(self.fade_widgets):
            fade_anim = QPropertyAnimation(widget, b"windowOpacity")
            fade_anim.setDuration(fade_duration)
            fade_anim.setStartValue(0.0)
            fade_anim.setEndValue(1.0)
            fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
            
            # Adiciona à animação sequencial
            self.seq_group.addAnimation(fade_anim)
        
        # Inicia o grupo de animações
        self.seq_group.start()
        
    def showEvent(self, event):
        """Executa a animação quando o widget é mostrado."""
        super().showEvent(event)
        self.open_animation.start()
        
    def close_animation(self):
        """Inicia a animação de fechamento da página."""
        self.close_anim.start()
        
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
            
    def apply_stylesheet(self):
        """Aplica estilos à página de informações do filme."""
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QLabel#backdropImage {
                background-color: #000;
            }
            
            QWidget#contentOverlay {
                background-color: transparent;
            }
            
            QWidget#scrollContent {
                background-color: transparent;
            }
            
            QScrollArea#transparentScroll {
                background-color: transparent;
                border: none;
            }
            
            QScrollBar:vertical {
                background: rgba(30, 30, 30, 0.3);
                width: 6px;
                border-radius: 3px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(150, 150, 150, 0.4);
                border-radius: 3px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(180, 180, 180, 0.6);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            #backdropContainer {
                background-color: black;
            }
            
            QFrame#glassContainer {
                background: rgba(20, 20, 20, 0.55);
                border-radius: 12px;
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 18px;
            }
            
            QFrame#sinopseContainer, QFrame#directorsContainer, QFrame#castContainer {
                padding: 10px 0px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
            
            QLabel#personPhoto {
                border-radius: 100px;
            }
            
            QLabel#titleLabel {
                font-size: 28px;
                font-weight: bold;
                color: white;
                margin-bottom: 3px;
            }
            
            QLabel#originalTitleLabel {
                font-size: 16px;
                color: #cccccc;
                margin-bottom: 10px;
            }
            
            QLabel#infoLabel {
                font-size: 15px;
                color: #dddddd;
            }
            
            QLabel#detailLabel {
                font-size: 15px;
                color: #bbbbbb;
                margin-top: 8px;
            }
            
            QLabel#sectionLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                margin-top: 5px;
                margin-bottom: 12px;
            }
            
            QLabel#overviewLabel {
                font-size: 15px;
                color: #dddddd;
                line-height: 1.5;
            }
            
            QLabel#personName {
                font-size: 14px;
                font-weight: bold;
                color: white;
                margin-top: 6px;
            }
            
            QLabel#characterName {
                font-size: 13px;
                color: #aaaaaa;
                margin-top: 2px;
            }
            
            QLabel#dateLabel {
                font-size: 13px;
                color: #999999;
                margin-right: 10px;
                margin-top: 10px;
            }
            
            QFrame#buttonsContainer {
                background: transparent;
                margin-bottom: 40px;
            }
            
            QPushButton#playButton {
                background-color: #E50914;
                color: white;
                border: 2px solid white;
                border-radius: 4px;
                padding: 10px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            
            QPushButton#playButton:hover {
                background-color: #F40D12;
                box-shadow: 0 0 12px rgba(229, 9, 20, 0.9);
                transform: scale(1.05);
            }
            
            QPushButton#trailerButton {
                background-color: rgba(60, 60, 60, 0.7);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                padding: 10px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            
            QPushButton#trailerButton:hover {
                background-color: rgba(80, 80, 80, 0.8);
                box-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
            }
            
            QPushButton#backButton {
                background-color: rgba(30, 30, 30, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                min-width: 40px;
                min-height: 40px;
                icon-size: 20px;
            }
            
            QPushButton#backButton:hover {
                background-color: rgba(50, 50, 50, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            QFrame#verticalSeparator {
                background-color: rgba(255, 255, 255, 0.1);
                width: 1px;
                margin: 10px 15px;
            }
            
            QWidget#similaresContainer {
                padding: 10px 0px;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                margin-top: 15px;
            }
            
            QLabel#placeholderLabel {
                color: #999999;
                font-size: 14px;
                padding: 20px;
            }
            
            .similar-movie-container {
                background-color: rgba(20, 20, 20, 0.6);
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            
            .similar-movie-container:hover {
                background-color: rgba(40, 40, 40, 0.8);
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
            }
        """)