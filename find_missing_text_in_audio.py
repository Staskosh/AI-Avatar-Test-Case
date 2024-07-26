import logging
import os

import assemblyai as aai
import re

from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def transcribe_audio(file_path):
    """
    Распознаем текст при помощи AssemblyAI.
    """
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(language_code='ru', punctuate=True)
    transcript = transcriber.transcribe(file_path, config=config)

    if transcript.status == "completed":
        return transcript
    else:
        raise Exception("Не распознал текст в аудио")


def preprocess_text(text):
    """
    Не учитываем пробелы и знаки препнания для сравнения текстов
    """
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def find_differences(given_text, transcribed_text):
    """
    Сравниваем тексты и находим отличия
    """
    given_words = preprocess_text(given_text).split()
    transcribed_words = preprocess_text(transcribed_text).split()

    differences = []
    given_index, transcribed_index = 0, 0

    while given_index < len(given_words) and transcribed_index < len(transcribed_words):
        if given_words[given_index] != transcribed_words[transcribed_index]:
            differences.append((given_index, given_words[given_index]))
            given_index += 1
        else:
            given_index += 1
            transcribed_index += 1

    while given_index < len(given_words):
        differences.append((given_index, given_words[given_index]))
        given_index += 1

    return differences


def save_results_to_file(filename, differences, transcript):
    """
    Сохраняем результат в файл
    """
    with open(filename, 'w', encoding='utf-8') as file:
        if not differences:
            file.write("Отличий в тексте нет.\n")
        else:
            file.write("Отличия в тексте найдены:\n")
            word_timings = {re.sub(r'[^\w\s]', '', word.text.lower()): word for word in
                            transcript.words}  # Map words to their timings

            for index, word in differences:
                word_info = word_timings.get(word.lower())
                if word_info:
                    file.write(
                        f"Пропущено: {word} | Время начала: {word_info.start / 1000} сек | Время окончания: {word_info.end / 1000} сек\n")
                else:
                    file.write(f"Пропущено: {word} | Время недоступно\n")


if __name__ == "__main__":
    load_dotenv()

    aai.settings.api_key = os.getenv("AAI_API_KEY")

    text_filename = os.getenv("TEXT")
    given_text_file_path = f"source/{text_filename}"

    try:
        with open(given_text_file_path, 'r', encoding='utf-8') as file:
            given_text = file.read()
    except FileNotFoundError:
        logger.error(f"Файл {given_text_file_path} с текстом не найден ")

    audio_filename = os.getenv("AUDIO")

    audio_file_path = f"source/{audio_filename}"

    transcript = transcribe_audio(audio_file_path)
    transcribed_text = transcript.text

    differences = find_differences(given_text, transcribed_text)

    output_file = f"source/comparison_results_for_{audio_filename}.txt"
    save_results_to_file(output_file, differences, transcript)

    logger.info(f"Результат сохранен в {output_file}")
