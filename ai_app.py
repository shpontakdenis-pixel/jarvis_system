import customtkinter as ctk
import mss, io, threading, sys, base64, requests, os, time, asyncio
import edge_tts, pygame, speech_recognition as sr
from PIL import Image
from datetime import datetime
from duckduckgo_search import DDGS
import numpy as np

# Скрываем лишние логи в консоли
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

OPENROUTER_API_KEY = "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"

class AriseJarvis(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS ARISE v41.9")
        self.geometry("1100x650")
        self.configure(fg_color="#0a0510")
        
        self.is_active = False 
        self.is_speaking = False 
        pygame.mixer.init()

        # UI
        self.status_label = ctk.CTkLabel(self, text="СИСТЕМА ГОТОВА", font=("Arial", 16), text_color="#555555")
        self.status_label.place(x=550, y=20)
        self.chat_display = ctk.CTkTextbox(self, width=500, height=500, font=("Segoe UI", 15), fg_color="#150a25")
        self.chat_display.place(x=550, y=70)

        threading.Thread(target=self.background_listener, daemon=True).start()

    def play_beep(self):
        try:
            sample_rate = 44100
            t = np.linspace(0, 0.1, int(sample_rate * 0.1), False)
            wave = (np.sin(2 * np.pi * 1000 * t) * 32767).astype(np.int16)
            pygame.sndarray.make_sound(wave).play()
        except: pass

    def say(self, text):
        def _run():
            self.is_speaking = True # МИКРОФОН В ИГНОР
            try:
                fname = f"temp_v.mp3"
                asyncio.run(edge_tts.Communicate(text, "ru-RU-DmitryNeural").save(fname))
                pygame.mixer.music.load(fname)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    if not self.is_speaking: break
                    time.sleep(0.05)
                pygame.mixer.music.unload()
                if os.path.exists(fname): os.remove(fname)
            finally:
                time.sleep(0.4) # Даем эху затихнуть
                self.is_speaking = False
        threading.Thread(target=_run, daemon=True).start()

    def get_info(self, query):
        try:
            with DDGS() as ddgs:
                results = [r['body'] for r in ddgs.text(query, max_results=2)]
                return " ".join(results)
        except: return "Нет данных в сети."

    def background_listener(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            while True:
                try:
                    audio = r.listen(source, timeout=None, phrase_time_limit=4)
                    if self.is_speaking: continue # Полный игнор, если ИИ говорит

                    text = r.recognize_google(audio, language="ru-RU").lower()
                    print(f"> {text}")

                    if "понял" in text:
                        self.is_speaking = False
                        pygame.mixer.music.stop()
                        continue

                    if any(w in text for w in ["ара", "арай", "арис"]):
                        self.is_active = True
                        self.play_beep()
                        self.status_label.configure(text="● СЛУШАЮ", text_color="#00FFCC")
                    elif self.is_active:
                        self.status_label.configure(text="● ПОИСК...", text_color="#FFFF00")
                        threading.Thread(target=self.process, args=(text,), daemon=True).start()
                except: continue

    def process(self, text):
        info = self.get_info(text)
        prompt = f"Ты Джарвис. Твои знания: {info}. Ответь на вопрос: {text}. Будь краток, не извиняйся."
        
        try:
            res = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]},
                timeout=12
            )
            if res.status_code == 200:
                ans = res.json()['choices'][0]['message']['content']
                self.chat_display.insert("end", f"ДЖАРВИС: {ans}\n\n")
                self.say(ans)
        except: pass

if __name__ == "__main__":
    AriseJarvis().mainloop()