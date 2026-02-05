import sys
import threading
import speech_recognition as sr
import pyttsx3
import random
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

class JarvisSignals(QObject):
    status_change = pyqtSignal(str)

# --- ГРАФИЧЕСКИЙ ИНТЕРФЕЙС (ПЕРЕМЕЩАЕМЫЙ) ---
class JarvisUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(300, 300)
        self.status_text = "ARYS"
        self.angle = 0
        self.old_pos = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_anim)
        self.timer.start(20)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def update_anim(self):
        self.angle = (self.angle + 3) % 360
        self.update()

    def update_status(self, text):
        self.status_text = text.upper()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(0, 210, 255, 200)
        painter.setPen(QPen(color, 4))
        rect = self.rect().adjusted(70, 70, -70, -70)
        painter.drawEllipse(rect)
        painter.setPen(QPen(color, 2))
        painter.drawArc(rect.adjusted(-10, -10, 10, 10), self.angle * 16, 90 * 16)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.status_text)

# --- УЛУЧШЕННЫЙ МОЗГ ---
class JarvisBrain:
    def __init__(self, signals):
        self.signals = signals
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180) 
        self.recognizer = sr.Recognizer()
        
        # Настройки имен и команд
        self.names = ["джарвис", "арайс", "эрайс", "jarvis", "arys"]
        self.stop_commands = ["стоп", "выход", "отключись", "выключи систему", "спи", "завершить работу"]

    def say(self, text):
        self.signals.status_change.emit("ГОВОРИТ")
        self.engine.say(text)
        self.engine.runAndWait()

    def handle_command(self, command):
        # Проверяем, позвали ли его по имени
        called = any(name in command for name in self.names)
        
        if called:
            # Логика остановки
            if any(stop in command for stop in self.stop_commands):
                responses = ["Завершаю сеанс. До встречи", "Система Арайс переходит в спящий режим", "Выключаюсь."]
                self.say(random.choice(responses))
                sys.exit()
            
            # Приветствия
            elif "привет" in command or "здравствуй" in command:
                responses = ["Приветствую! Чем могу помочь?", "Система онлайн. Слушаю вас.", "Здравствуйте! Все системы в норме."]
                self.say(random.choice(responses))
            
            # Как дела
            elif "как дела" in command or "статус" in command:
                self.say("Проверка систем завершена. Все модули работают в штатном режиме.")
            
            # Если позвал по имени, но команду не распознал
            else:
                self.say("Да, я вас слушаю.")

    def run(self):
        self.say("Система Арайс запущена и готова к работе.")
        while True:
            with sr.Microphone() as source:
                self.signals.status_change.emit("СЛУШАЕТ")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
                    query = self.recognizer.recognize_google(audio, language="ru-RU").lower()
                    print(f"Распознано: {query}")
                    self.handle_command(query)
                except Exception as e:
                    continue

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
