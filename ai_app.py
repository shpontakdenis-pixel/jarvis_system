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
        self.status_text = "ONLINE"
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
        self.names = ["арай", "арайс", "райс", "арис", "джарвис", "эрайс"]
        self.stop_phrases = ["стоп", "спи", "выход", "отключись", "пока"]
        self.shut_up_phrases = ["понял", "хватит", "тихо", "замолчи", "хорош"]
        self.recognizer = sr.Recognizer()
        self.is_speaking = False

    def say(self, text):
        def speak_task():
            try:
                self.is_speaking = True
                self.signals.emit_status("SPEAK")
                print(f"[ГОЛОС] {text}")
                
                # Локальная инициализация движка (решает проблему зависания)
                engine = pyttsx3.init()
                engine.setProperty('rate', 190)
                engine.setProperty('volume', 1.0)
                
                engine.say(text)
                engine.runAndWait()
                engine.stop() # Обязательно освобождаем ресурс
                
                self.is_speaking = False
                self.signals.emit_status("LISTEN")
            except Exception as e:
                print(f"[ОШИБКА ГОЛОСА] {e}")
                self.is_speaking = False

        threading.Thread(target=speak_task, daemon=True).start()

    def handle_command(self, command):
        command = command.lower()
        
        # Если нужно заткнуть
        if any(word in command for word in self.shut_up_phrases) and self.is_speaking:
            print("[ЛОГИКА] Прерывание")
            # В текущей реализации pyttsx3 сложно убить поток мгновенно, 
            # но мы хотя бы не будем начинать новые фразы.
            return

        # Если команда стоп
        if any(stop in command for stop in self.stop_phrases):
            self.say("Выключаюсь. До связи.")
            time.sleep(2)
            sys.exit()

        # Поиск имени
        if any(name in command for name in self.names):
            if "привет" in command or "здравствуй" in command:
                self.say(random.choice(["Приветствую!", "Я тут. Что нужно?", "Система онлайн."]))
            elif "как дела" in command:
                self.say("Все системы в норме. Готов к работе.")
            elif "понял" in command:
                self.say(random.choice(["Принято.", "Хорошо.", "Понял вас."]))
            else:
                self.say("Слушаю.")

    def run(self):
        # Даем понять, что программа вообще жива при старте
        time.sleep(1)
        self.say("Арайс запущен")
        
        while True:
            with sr.Microphone() as source:
                self.signals.emit_status("LISTEN")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=4)
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
