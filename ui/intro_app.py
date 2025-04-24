import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt5.QtGui import QColor, QPainter, QFont

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        # Configurações da janela principal
        self.setWindowTitle("Pipoca+")
        self.setFixedSize(1920, 1080)  # Tamanho para tela cheia
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Cores do tema
        self.bg_color = QColor(0, 0, 0)  # Fundo preto
        self.text_color = QColor(229, 9, 20)  # Vermelho característico
        
        # Configuração do layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        # Label para o texto
        self.text_label = QLabel("pipoca+", self)
        font = QFont("Arial", 120, QFont.Bold)
        self.text_label.setFont(font)
        self.text_label.setStyleSheet("color: rgb(229, 9, 20);")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.text_label)
        
        # Posicionamento inicial fora da tela
        self.text_label.setGeometry(0, self.height() // 2 - 100, self.width(), 200)
        self.text_label.hide()
        
        # Timer para sequência de animações
        self.timer = QTimer()
        self.timer.singleShot(500, self.start_animation)
        
        # Contagem para encerrar splash screen
        self.counter = 0
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())
    
    def start_animation(self):
        # Mostrar o texto
        self.text_label.show()
        
        # Animação de zoom do texto
        self.zoom_animation = QPropertyAnimation(self.text_label, b"geometry")
        self.zoom_animation.setDuration(1000)
        start_rect = QRect(
            self.width() // 2 - 100, 
            self.height() // 2 - 50, 
            200, 
            100
        )
        end_rect = QRect(
            self.width() // 2 - 400, 
            self.height() // 2 - 150, 
            800, 
            300
        )
        self.zoom_animation.setStartValue(start_rect)
        self.zoom_animation.setEndValue(end_rect)
        self.zoom_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.zoom_animation.finished.connect(self.start_shine_effect)
        self.zoom_animation.start()
    
    def start_shine_effect(self):
        # Efeito de brilho
        self.counter = 0
        self.shine_timer = QTimer()
        self.shine_timer.timeout.connect(self.update_shine)
        self.shine_timer.start(150)  # Aumentado de 50 para 150ms (mais lento)
    
    def update_shine(self):
        self.counter += 1
        
        # Alternar entre um vermelho levemente mais claro e vermelho padrão
        # Diminuído o contraste para um efeito mais sutil
        if self.counter % 2 == 0:
            self.text_label.setStyleSheet("color: rgb(250, 100, 100);")  # Vermelho mais claro/suave
        else:
            self.text_label.setStyleSheet("color: rgb(229, 9, 20);")  # Vermelho padrão
        
        # Finalizar animação de brilho após 6 alterações (reduzido de 10)
        if self.counter >= 6:
            self.shine_timer.stop()
            self.text_label.setStyleSheet("color: rgb(229, 9, 20);")
            self.start_final_animation()
    
    def start_final_animation(self):
        # Animação final - Contração e desaparecimento
        self.final_animation = QPropertyAnimation(self.text_label, b"geometry")
        self.final_animation.setDuration(800)
        
        current_rect = self.text_label.geometry()
        end_rect = QRect(
            self.width() // 2 - 20, 
            self.height() // 2 - 10, 
            40, 
            20
        )
        
        self.final_animation.setStartValue(current_rect)
        self.final_animation.setEndValue(end_rect)
        self.final_animation.setEasingCurve(QEasingCurve.InCubic)
        self.final_animation.finished.connect(self.close_splash)
        self.final_animation.start()
    
    def close_splash(self):
        # Aqui você pode iniciar seu aplicativo principal
        # Para fins de demonstração, vamos apenas fechar após 1 segundo
        QTimer.singleShot(1000, self.close)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SplashScreen()
    window.show()
    sys.exit(app.exec_())
