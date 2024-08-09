import os
import random
import asyncio
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v2 as translate

# Initialize clients
translate_client = translate.Client()
speech_client = speech.SpeechClient()

def check_file_existence(func):
    def wrapper(file_path, *args, **kwargs):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        return func(file_path, *args, **kwargs)
    return wrapper

def supported_format(func):
    def wrapper(file_path, *args, **kwargs):
        _, file_extension = os.path.splitext(file_path)
        supported_formats = ['.txt', '.mp3', '.wav', '.docx']
        if file_extension.lower() not in supported_formats:
            print("Unsupported file format.")
            return None
        return func(file_path, *args, **kwargs)
    return wrapper

def detect_language(text):
    return translate_client.detect_language(text)['language']

async def transcribe_audio(file_path):
    try:
        with open(file_path, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code='en-US',
        )

        response = await speech_client.recognize(config=config, audio=audio)
        return ''.join(result.alternatives[0].transcript for result in response.results)
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

async def translate_file(file_path, target_language='ja'):
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        text_to_translate = content
    else:
        text_to_translate = await transcribe_audio(file_path)

    if not text_to_translate:
        return None

    source_language = detect_language(text_to_translate)
    if source_language == target_language:
        print("Input text is already in the target language.")
        return None

    return translate_text(text_to_translate, target_language)

def save_translation(translated_content, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(translated_content)
    print(f"Translated content saved to {output_file_path}")

async def batch_translate(file_paths, output_dir, progress_callback, target_language='ja'):
    translations = await asyncio.gather(
        *[translate_file(file_path, target_language) for file_path in file_paths]
    )
    for i, (file_path, translation) in enumerate(zip(file_paths, translations)):
        if translation:
            output_file_path = os.path.join(output_dir, f"translated_{os.path.basename(file_path)}")
            save_translation(translation, output_file_path)
        progress_callback(i + 1, len(file_paths))

def translate_text(text, target_language='ja'):
    return translate_client.translate(text, target_language=target_language)['translatedText']

def get_daily_challenge():
    challenges = [
        "Write a short paragraph about your day in Japanese.",
        "Translate the following sentence to Japanese: 'I am learning Japanese to improve my skills.'",
        "Read a Japanese article and summarize it in English.",
        "Listen to a Japanese podcast or song and write down what you understand.",
        "Have a conversation with a digital pen pal about your hobbies in Japanese.",
        "Write a forum post in Japanese about your favorite book.",
        "Translate a cooking recipe from English to Japanese.",
        "Practice speaking by recording yourself introducing your family in Japanese."
    ]
    return random.choice(challenges)

class TranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Japanese Translation and Learning App")
        self.geometry("700x700")
        
        self.default_output_dir = os.path.expanduser("~")
        self.default_target_language = 'ja'
        
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Welcome! Here's your daily challenge:").pack(pady=10)
        tk.Label(self, text=get_daily_challenge(), wraplength=600).pack(pady=10)
        
        tk.Label(self, text="Choose an option:").pack(pady=10)

        self.file_translate_frame = tk.Frame(self)
        self.file_translate_frame.pack(pady=5)
        tk.Button(self.file_translate_frame, text="Translate Files", command=self.translate_files).pack(side=tk.LEFT, padx=5)

        tk.Button(self, text="Translate Conversation", command=self.translate_conversation).pack(pady=5)
        tk.Button(self, text="Translate Forum Post", command=self.translate_forum_post).pack(pady=5)
        tk.Button(self, text="Settings", command=self.open_settings).pack(pady=5)
        tk.Button(self, text="Quit", command=self.quit).pack(pady=10)

        self.progress = tk.DoubleVar()
        ttk.Progressbar(self, variable=self.progress, maximum=100).pack(pady=10, fill=tk.X)

        self.output_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=10)
        self.output_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.status_bar = tk.Label(self, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message):
        self.status_bar.config(text=message)
        self.status_bar.update_idletasks()

    def translate_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select files to translate", 
            filetypes=[("Text files", "*.txt"), ("Audio files", "*.mp3 *.wav")]
        )
        if not file_paths:
            return

        output_dir = filedialog.askdirectory(
            title="Select output directory", 
            initialdir=self.default_output_dir
        )
        if not output_dir:
            return

        self.progress.set(0)
        self.output_text.delete(1.0, tk.END)

        def progress_callback(current, total):
            self.progress.set((current / total) * 100)
            self.set_status(f"Translating file {current} of {total}")

        def run_translation():
            asyncio.run(batch_translate(file_paths, output_dir, progress_callback, self.default_target_language))
            self.set_status("Translation complete")
            messagebox.showinfo("Info", "Translation complete")

        threading.Thread(target=run_translation).start()

    def translate_conversation(self):
        input_text = tk.simpledialog.askstring("Input", "Enter the text for your conversation:")
        if input_text:
            translated_content = translate_text(input_text, self.default_target_language)
            if translated_content:
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(tk.END, translated_content)
                messagebox.showinfo("Translated Text", translated_content)

    def translate_forum_post(self):
        input_text = tk.simpledialog.askstring("Input", "Enter the text for your forum post:")
        if input_text:
            translated_content = translate_text(input_text, self.default_target_language)
            if translated_content:
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(tk.END, translated_content)
                messagebox.showinfo("Translated Text", translated_content)

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x200")

        tk.Label(settings_window, text="Default Output Directory:").pack(pady=5)
        self.output_dir_entry = tk.Entry(settings_window, width=50)
        self.output_dir_entry.pack(pady=5)
        self.output_dir_entry.insert(0, self.default_output_dir)
        tk.Button(settings_window, text="Browse", command=self.set_output_dir).pack(pady=5)

        tk.Label(settings_window, text="Default Target Language:").pack(pady=5)
        self.language_entry = tk.Entry(settings_window, width=5)
        self.language_entry.pack(pady=5)
        self.language_entry.insert(0, self.default_target_language)

        tk.Button(settings_window, text="Save", command=self.save_settings).pack(pady=10)

    def set_output_dir(self):
        directory = filedialog.askdirectory(
            title="Select default output directory", 
            initialdir=self.default_output_dir
        )
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)

    def save_settings(self):
        self.default_output_dir = self.output_dir_entry.get()
        self.default_target_language = self.language_entry.get()
        messagebox.showinfo("Settings", "Settings saved successfully")

if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()
