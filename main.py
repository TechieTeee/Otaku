import googletrans
from googletrans import Translator
import os

# Initialize translator
translator = Translator()

def translate_text(text, target_language='ja'):
    """
    Translate text to the target language.
    """
    translation = translator.translate(text, dest=target_language)
    return translation.text

def translate_file(file_path):
    """
    Translate the content of a file to the target language.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    translated_content = translate_text(content)
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
    print("\nTranslated Content:")
    print(translated_content)

if __name__ == "__main__":
    main()
