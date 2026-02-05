import sys
import threading
import speech_recognition as sr
import pyttsx3
import random
import time
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

class SignalsWrapper(QObject):
    status_change = pyqtSignal(str)
    def emit_status(self, text): self.status_change.emit(text)

class JarvisUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(300, 300)
        self.status_text = "READY"
        self.angle = 0
        self.old_pos = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(20)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event): self.old_pos = None

    def paintEvent(self, event):
        self.angle = (self.angle + 3) % 360
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(0, 210, 255, 200)
        painter.setPen(QPen(color, 4))
        rect = self.rect().adjusted(70, 70, -70, -70)
        painter.drawEllipse(rect)
        painter.drawArc(rect.adjusted(-10, -10, 10, 10), self.angle * 16, 90 * 16)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.status_text)

    def update_status(self, text):
        self.status_text = text

class JarvisBrain:
    def __init__(self, signals):
        self.signals = signals
        self.engine = pyttsx3.init()
        self.names = ["арай", "арайс", "райс", "арис", "джарвис", "эрайс", "arys"]
        self.stop_phrases = ["стоп", "спи", "выход", "отключись", "выключи систему", "пока"]
        self.shut_up_phrases = ["понял", "хватит", "тихо", "замолчи", "тсс", "хорош"]
        
        self.recognizer = sr.Recognizer()
        self.is_speaking = False

    def say(self, text):
        def speak():
            self.is_speaking = True
            self.signals.emit_status("SPEAKING")
            print(f"[ГОЛОС] {text}")
            self.engine.say(text)
            self.engine.runAndWait()
            self.is_speaking = False
            self.signals.emit_status("LISTENING")

        # Запускаем голос в отдельном потоке, чтобы микрофон не блокировался
        threading.Thread(target=speak, daemon=True).start()

    def stop_speaking(self):
        if self.is_speaking:
            # Принудительно останавливаем движок речи
            self.engine.stop()
            self.is_speaking = False
            self.signals.emit_status("LISTENING")
            print("[ЛОГИКА] Речь прервана пользователем")

    def handle_command(self, command):
        command = command.lower()
        
        # 1. Если Джарвис говорит и ты сказал "Понял" - затыкаем его
        if any(word in command for word in self.shut_up_phrases):
            if self.is_speaking:
                self.stop_speaking()
                responses = ["Принято", "Молчу", "Понял вас", "Хорошо", "Слушаю"]
                time.sleep(0.5) # Маленькая пауза перед подтверждением
                self.say(random.choice(responses))
                return

        # 2. Проверка на полное выключение
        if any(stop in command for stop in self.stop_phrases):
            self.say("Система Арайс уходит в спящий режим.")
            time.sleep(2)
            sys.exit()

        # 3. Обращение по имени
        found_name = any(name in command for name in self.names)
        if found_name:
            if "привет" in command:
                self.say(random.choice(["Приветствую!", "Я на связи.", "Система онлайн."]))
            elif "как дела" in command:
                self.say("Все системы работают на пике возможностей.")
            else:
                self.say("Да, слушаю вас.")

    def run(self):
        self.say("Система Арайс онлайн")
        while True:
            with sr.Microphone() as source:
                self.signals.emit_status("LISTENING")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    # phrase_time_limit=3 позволяет быстрее реагировать на короткие фразы типа "понял"
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=3)
                    query = self.recognizer.recognize_google(audio, language="ru-RU").lower()
                    print(f"[СЛУХ] {query}")
                    self.handle_command(query)
                except:
                    continue

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = JarvisUI()
    sig = SignalsWrapper()
    sig.status_change.connect(ui.update_status)
    brain = JarvisBrain(sig)
    ui.show()
    threading.Thread(target=brain.run, daemon=True).start()
    sys.exit(app.exec())
