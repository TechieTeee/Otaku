import os
import random
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v2 as translate

# Initialize Translation client
translate_client = translate.Client()

# Initialize Speech-to-Text client
client = speech.SpeechClient()

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
        supported_formats = ['.txt', '.mp3', '.wav']
        if file_extension.lower() not in supported_formats:
            print("Unsupported file format.")
            return None
        return func(file_path, *args, **kwargs)
    return wrapper

def detect_language(text):
    """
    Detect the language of the text.
    """
    response = translate_client.detect_language(text)
    return response['language']

def translate_text(text, target_language='ja', glossary=None, context=None):
    """
    Translate text to the target language with contextual information.
    """
    translation = translate_client.translate(text, target_language=target_language)
    return translation['translatedText']

@check_file_existence
@supported_format
def transcribe_audio(file_path):
    """
    Transcribe audio file to text.
    """
    with open(file_path, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code='en-US',  
    )

    response = client.recognize(config=config, audio=audio)
    
    transcript = ''.join(result.alternatives[0].transcript for result in response.results)
    return transcript

@check_file_existence
@supported_format
def translate_file(file_path, glossary=None, context=None):
    """
    Translate the content of a file to Japanese.
    """
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        source_language = detect_language(content)
        if source_language != 'ja':
            translated_content = translate_text(content)
        else:
            print("Input text is already in Japanese.")
            return None
    else:
        transcript = transcribe_audio(file_path)
        if not transcript:
            return None
        
        source_language = detect_language(transcript)
        if source_language != 'ja':
            translated_content = translate_text(transcript)
        else:
            print("Input audio is already in Japanese.")
            return None
    
    return translated_content

def save_translation(translated_content, output_file_path):
    """
    Save the translated content to a file.
    """
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(translated_content)
    print(f"Translated content saved to {output_file_path}")

def batch_translate(file_paths, output_dir):
    """
    Translate multiple files and save the translations to an output directory.
    """
    for file_path in file_paths:
        translated_content = translate_file(file_path)
        if translated_content:
            file_name = os.path.basename(file_path)
            output_file_path = os.path.join(output_dir, f"translated_{file_name}")
            save_translation(translated_content, output_file_path)

def translate_conversation(input_text, target_language='ja'):
    """
    Translate conversational text for a digital pen pal.
    """
    source_language = detect_language(input_text)
    if source_language != target_language:
        translated_content = translate_text(input_text, target_language)
        return translated_content
    else:
        print("Input text is already in the target language.")
        return None

def translate_forum_post(input_text, target_language='ja'):
    """
    Translate text intended for forum posts.
    """
    source_language = detect_language(input_text)
    if source_language != target_language:
        translated_content = translate_text(input_text, target_language)
        return translated_content
    else:
        print("Input text is already in the target language.")
        return None

def get_daily_challenge():
    """
    Provide a daily challenge for the user.
    """
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
    challenge = random.choice(challenges)
    return challenge

def main():
    print("Welcome! Here's your daily challenge:")
    daily_challenge = get_daily_challenge()
    print(daily_challenge)
    
    choice = input("Choose an option: (1) Translate files, (2) Translate conversation, (3) Translate forum post: ").strip()
    
    if choice == '1':
        file_paths = input("Enter the paths to the files you want to translate, separated by commas: ").split(',')
        file_paths = [file_path.strip() for file_path in file_paths]

        output_dir = input("Enter the path to the directory to save translated content: ")
        
        if not os.path.exists(output_dir):
            print("Output directory not found.")
            return

        batch_translate(file_paths, output_dir)
    elif choice == '2':
        input_text = input("Enter the text for your conversation: ").strip()
        translated_content = translate_conversation(input_text)
        if translated_content:
            print(f"Translated Text: {translated_content}")
    elif choice == '3':
        input_text = input("Enter the text for your forum post: ").strip()
        translated_content = translate_forum_post(input_text)
        if translated_content:
            print(f"Translated Text: {translated_content}")
    else:
        print("Invalid option.")

if __name__ == "__main__":
    main()
