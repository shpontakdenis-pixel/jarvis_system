import sys
import threading
import speech_recognition as sr
import pyttsx3
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

# Сигналы для связи логики и графики
class JarvisSignals(QObject):
    status_change = pyqtSignal(str)

# --- ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ---
class JarvisUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 400)
        
        self.status_text = "СИСТЕМА ОЖИДАНИЯ"
        self.angle = 0
        self.pulse = 0
        self.growing = True
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_anim)
        self.timer.start(20)

    def update_anim(self):
        self.angle = (self.angle + 4) % 360
        self.pulse = (self.pulse + 1) % 50
        self.update()

    def update_status(self, text):
        self.status_text = text.upper()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Рисуем кольцо
        color = QColor(0, 255, 255, 180)
        painter.setPen(QPen(color, 3))
        rect = self.rect().adjusted(100, 100, -100, -100)
        painter.drawEllipse(rect)
        
        # Вращающиеся элементы
        painter.drawArc(rect.adjusted(-15, -15, 15, 15), self.angle * 16, 100 * 16)
        
        # Текст статуса
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.status_text)

# --- МОЗГИ ДЖАРВИСА ---
class JarvisBrain:
    def __init__(self, signals):
        self.signals = signals
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        
    def say(self, text):
        self.signals.status_change.emit("ГОВОРИТ")
        self.engine.say(text)
        self.engine.runAndWait()
        self.signals.status_change.emit("СЛУШАЕТ")

    def listen(self):
        with sr.Microphone() as source:
            self.signals.status_change.emit("СЛУШАЕТ")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                query = self.recognizer.recognize_google(audio, language="ru-RU")
                return query.lower()
            except:
                return ""

    def run(self):
        self.say("Система запущена. Я к вашим услугам.")
        while True:
            request = self.listen()
            if "джарвис" in request:
                if "выход" in request or "отключись" in request:
                    self.say("Завершаю работу.")
                    sys.exit()
                else:
                    self.say("Да, я вас слушаю")
                    # Тут можно добавить логику ответов или ChatGPT

# --- ЗАПУСК ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = JarvisUI()
    signals = JarvisSignals()
    signals.status_change.connect(ui.update_status)
    
    brain = JarvisBrain(signals)
    
    ui.show()
    
    thread = threading.Thread(target=brain.run, daemon=True)
    thread.start()
    
    sys.exit(app.exec())
