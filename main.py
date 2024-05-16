import os
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v2 as translate

# Initialize Translation client
translate_client = translate.Client()

# Initialize Speech-to-Text client
client = speech.SpeechClient()

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

def transcribe_audio(audio_file):
    """
    Transcribe audio file to text.
    """
    with open(audio_file, 'rb') as audio_file:
        content = audio_file.read()

    # For English inputs
    audio = speech.RecognitionAudio(content=content)
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

def translate_file(file_path, glossary=None, context=None):
    """
    Translate the content of a file to Japanese.
    """
    _, file_extension = os.path.splitext(file_path)
    supported_formats = ['.txt', '.mp3', '.wav']
    
    if file_extension.lower() not in supported_formats:
        print("Unsupported file format.")
        return None
    
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
        # Transcribe audio file to text
        transcript = transcribe_audio(file_path)
        
        # Detect language of the transcription
        source_language = detect_language(transcript)
        if source_language != 'ja':
            translated_content = translate_text(transcript)
        else:
            print("Input audio is already in Japanese.")
            return None
    
    return translated_content

def main():
    # Prompt user for file path
    file_path = input("Enter the path to the file you want to translate: ")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print("File not found.")
        return
    
    # Translate the file
    translated_content = translate_file(file_path)
    
    # Output the translated content
    if translated_content:
        print("\nTranslated Content:")
        print(translated_content)

if __name__ == "__main__":
    main()
