import googletrans
from googletrans import Translator
import os
from google.cloud import speech_v1p1beta1 as speech

# Initialize translator
translator = Translator()

# Initialize Speech-to-Text client
client = speech.SpeechClient()

def translate_text(text, target_language='ja', glossary=None):
    """
    Translate text to the target language.
    """
    translation = translator.translate(text, dest=target_language, glossary=glossary)
    return translation.text

def transcribe_audio(audio_file):
    """
    Transcribe audio file to text.
    """
    with open(audio_file, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    # For English audio input
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code='en-US',
    )

    response = client.recognize(config=config, audio=audio)
    
    # Extract and concatenate transcription from response
    transcript = ''
    for result in response.results:
        transcript += result.alternatives[0].transcript
    
    return transcript

def translate_file(file_path, glossary=None):
    """
    Translate the content of a file to the target language.
    """
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        translated_content = translate_text(content, glossary=glossary)
    elif file_extension.lower() in ['.mp3', '.wav']:
        # Transcribe audio file to text
        transcript = transcribe_audio(file_path)
        
        # Translate the transcription
        translated_content = translate_text(transcript, glossary=glossary)
    else:
        print("Unsupported file format.")
        return None
    
    return translated_content

def load_glossary(glossary_file):
    """
    Load custom glossary from file.
    """
    if not os.path.exists(glossary_file):
        print("Glossary file not found.")
        return None
    
    glossary = {}
    with open(glossary_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip():
                source, target = line.strip().split(',')
                glossary[source.strip()] = target.strip()
    
    return glossary

def main():
    # Prompt user for file path
    file_path = input("Enter the path to the file you want to translate: ")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print("File not found.")
        return
    
    # Prompt user for glossary file path (optional)
    glossary_file = input("Enter the path to the glossary file (optional): ")
    glossary = load_glossary(glossary_file)
    
    # Translate the file
    translated_content = translate_file(file_path, glossary=glossary)
    
    # Output the translated content
    print("\nTranslated Content:")
    print(translated_content)

if __name__ == "__main__":
    main()
