import os
import asyncio
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v2 as translate

# Initialize clients globally to avoid reinitialization
translate_client = translate.Client()
speech_client = speech.SpeechClient()

# Wrappers to improve data flow and efficiency
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

async def transcribe_audio(file_path):
    """Asynchronous audio transcription with error handling."""
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

async def translate_text_async(text, target_language='ja'):
    """Async translation using Google Translate API."""
    try:
        return translate_client.translate(text, target_language=target_language)['translatedText']
    except Exception as e:
        print(f"Error during translation: {e}")
        return None

async def translate_file(file_path, target_language='ja'):
    """Transcribes and translates file contents asynchronously."""
    _, file_extension = os.path.splitext(file_path)
    
     Either read or transcribe audio
    if file_extension.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    else:
        content = await transcribe_audio(file_path)

    if not content:
        return None
    
     Only translate if the language is different
    source_language = translate_client.detect_language(content)['language']
    if source_language == target_language:
        print("Input text is already in the target language.")
        return None
    
    return await translate_text_async(content, target_language)

async def batch_process_files(file_paths, output_dir, target_language, progress_callback):
    """Batch transcribe and translate files concurrently."""
    tasks = []
    for file_path in file_paths:
        tasks.append(translate_file(file_path, target_language))
    
    translations = await asyncio.gather(*tasks)
    
    for i, translation in enumerate(translations):
        if translation:
            output_file_path = os.path.join(output_dir, f"translated_{os.path.basename(file_paths[i])}")
            save_translation(translation, output_file_path)
        progress_callback(i + 1, len(file_paths))

def save_translation(translated_content, output_file_path):
    """Save the translation to a file."""
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(translated_content)
    print(f"Translated content saved to {output_file_path}")

class TranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Japanese Translation and Learning App")
        self.geometry("700x700")
        
        self.default_output_dir = os.path.expanduser("~")
        self.default_target_language = 'ja'
        
        self.create_widgets()

    def create_widgets(self):
        """Create the main UI layout."""
        tk.Label(self, text="Choose an option:").pack(pady=10)

        self.file_translate_frame = tk.Frame(self)
        self.file_translate_frame.pack(pady=5)
        tk.Button(self.file_translate_frame, text="Translate Files", command=self.translate_files).pack(side=tk.LEFT, padx=5)
        tk.Button(self.file_translate_frame, text="Transcribe Podcast", command=self.transcribe_podcast).pack(side=tk.LEFT, padx=5)

        self.progress = tk.DoubleVar()
        ttk.Progressbar(self, variable=self.progress, maximum=100).pack(pady=10, fill=tk.X)

        self.output_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=10)
        self.output_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.status_bar = tk.Label(self, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message):
        """Update status bar."""
        self.status_bar.config(text=message)
        self.status_bar.update_idletasks()

    def translate_files(self):
        """Open file dialog for translation."""
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
            self.set_status(f"Processing file {current} of {total}")

        def run_translation():
            asyncio.run(batch_process_files(file_paths, output_dir, self.default_target_language, progress_callback))
            self.set_status("Translation complete")
            messagebox.showinfo("Info", "Translation complete")

        threading.Thread(target=run_translation).start()

    def transcribe_podcast(self):
        """Handle podcast transcription."""
        file_paths = filedialog.askopenfilenames(
            title="Select podcast files", 
            filetypes=[("Audio files", "*.mp3 *.wav")]
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
            self.set_status(f"Transcribing podcast {current} of {total}")

        def run_transcription():
            asyncio.run(batch_process_files(file_paths, output_dir, self.default_target_language, progress_callback))
            self.set_status("Transcription complete")
            messagebox.showinfo("Info", "Transcription complete")

        threading.Thread(target=run_transcription).start()

if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()
