import sys
import threading
import speech_recognition as sr
import pyttsx3
import random
import time
from groq import Groq
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

# --- НАСТРОЙКА ИИ (GROQ) ---
API_KEY = "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"
client = Groq(api_key=API_KEY)

AI_MODELS = ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]

class SignalsWrapper(QObject):
    status_change = pyqtSignal(str)
    def emit_status(self, text): self.status_change.emit(text)

class JarvisUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(300, 300)
        self.status_text = "JARVIS"
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
        # ТЕПЕРЬ РАЗДЕЛЯЕМ:
        self.activation_names = ["арай", "арайс", "райс", "арис", "эрайс"] # Команды активации
        self.bot_name = "Джарвис" 
        
        self.stop_phrases = ["стоп", "спи", "выход", "отключись"]
        self.shut_up_phrases = ["понял", "хватит", "тихо", "замолчи"]
        self.recognizer = sr.Recognizer()
        self.is_speaking = False

    def say(self, text):
        def speak_task():
            try:
                self.is_speaking = True
                self.signals.emit_status("SPEAK")
                engine = pyttsx3.init()
                engine.setProperty('rate', 190)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                self.is_speaking = False
                self.signals.emit_status("LISTEN")
            except:
                self.is_speaking = False
        threading.Thread(target=speak_task, daemon=True).start()

    def ask_ai(self, prompt):
        self.signals.emit_status("THINK")
        for model in AI_MODELS:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": f"Ты — {self.bot_name}, продвинутый ИИ. Твой создатель из Украины. Отвечай кратко, преданно и с легким сарказмом. Ты знаешь, что команда 'Арайс' тебя активирует."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return completion.choices[0].message.content
            except Exception as e:
                print(f"[ОШИБКА] {model}: {e}")
                continue
        return "Сэр, все системы перегружены."

    def handle_command(self, command):
        command = command.lower()
        
        if any(word in command for word in self.shut_up_phrases) and self.is_speaking:
            return
            
        if any(stop in command for stop in self.stop_phrases):
            self.say(f"Протоколы завершены. До связи.")
            time.sleep(2)
            sys.exit()
            
        # ПРОВЕРКА КОМАНДЫ АКТИВАЦИИ
        if any(name in command for name in self.activation_names):
            clean_command = command
            for name in self.activation_names:
                clean_command = clean_command.replace(name, "").strip()
            
            if not clean_command:
                self.say("Да, слушаю вас.")
            else:
                answer = self.ask_ai(clean_command)
                self.say(answer)

    def run(self):
        time.sleep(1)
        self.say(f"{self.bot_name} в сети.")
        while True:
            with sr.Microphone() as source:
                self.signals.emit_status("LISTEN")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
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
