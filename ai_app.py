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

class JarvisUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(300, 300)
        self.status_text = "SYSTEM OK"
        self.angle = 0
        self.old_pos = None
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.update())
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

class JarvisBrain:
    def __init__(self, signals):
        self.signals = signals
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 180)
            self.engine.setProperty('volume', 1.0)
        except Exception as e:
            print(f"[ОШИБКА ЗВУКА] {e}")
        
        self.recognizer = sr.Recognizer()
        self.names = ["арайс", "джарвис", "эрайс", "arys", "jarvis", "арис"]

    def say(self, text):
        print(f"[ГОЛОС] {text}")
        self.signals.emit_status("ГОВОРИТ")
        self.engine.say(text)
        self.engine.runAndWait()
        self.signals.emit_status("СЛУШАЕТ")

    def handle_command(self, command):
        command = command.strip().lower()
        # Проверяем наличие любого имени из списка в строке
        found_name = any(name in command for name in self.names)
        
        if found_name:
            print(f"[ЛОГИКА] Имя найдено в фразе!")
            if any(x in command for x in ["стоп", "выключись", "спи", "завершить"]):
                self.say("Система Арайс отключается. До связи.")
                sys.exit()
            elif any(x in command for x in ["привет", "здравствуй", "ты тут"]):
                self.say(random.choice(["Приветствую! Слушаю вас.", "Я здесь. Чем могу помочь?", "Система онлайн."]))
            elif "как дела" in command:
                self.say("Все системы работают штатно. Готов к выполнению задач.")
            else:
                self.say("Да, я вас слушаю.")
        else:
            print(f"[ЛОГИКА] Имя не найдено в: {command}")

    def run(self):
        print("[СИСТЕМА] Попытка первого запуска голоса...")
        self.say("Система Арайс готова.")
        
        while True:
            with sr.Microphone() as source:
                self.signals.emit_status("СЛУШАЕТ")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                try:
                    print("[СЛУХ] Слушаю...")
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
                    query = self.recognizer.recognize_google(audio, language="ru-RU").lower()
                    print(f"[СЛУХ] Распознано: {query}")
                    self.handle_command(query)
                except Exception as e:
                    continue

# Вспомогательный класс для сигналов
class SignalsWrapper(QObject):
    status_change = pyqtSignal(str)
    def emit_status(self, text): self.status_change.emit(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = JarvisUI()
    sig = SignalsWrapper()
    sig.status_change.connect(ui.update_status)
    brain = JarvisBrain(sig)
    ui.show()
    threading.Thread(target=brain.run, daemon=True).start()
    sys.exit(app.exec())
