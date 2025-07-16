import nltk
from nltk.corpus import wordnet
import random
from deep_translator import GoogleTranslator

# Pobranie zasobów WordNet
nltk.download('wordnet')

class SentenceGenerator:
    def __init__(self, word):
        self.__word = word
        self.__translated_word = self.__translate_to_english(word)
        self.__examples = self.__fetch_examples()

    @property
    def word(self):
        return self.__word

    @word.setter
    def word(self, word):
        self.__word = word
        self.__translated_word = self.__translate_to_english(word)
        self.__examples = self.__fetch_examples()

    @property
    def examples(self):
        return self.__examples

    def __translate_to_english(self, word):
        return GoogleTranslator(source='auto', target='en').translate(word)

    def __translate_to_polish(self, text):
        return GoogleTranslator(source='auto', target='pl').translate(text)

    def __fetch_examples(self):
        synsets = wordnet.synsets(self.__translated_word)
        examples = []
        for synset in synsets:
            examples.extend(synset.examples())
        translated_examples = [self.__translate_to_polish(example) for example in examples]
        return translated_examples if translated_examples else ["Nie znaleziono przykładowych zdań."]

    def get_random_example(self):
        return random.choice(self.__examples)

# Funkcja do uruchomienia programu
def run_sentence_generator():
    while True:
        word = input("Wpisz słowo (lub 'exit', aby zakończyć): ").strip()
        if word.lower() == 'exit':
            break
        generator = SentenceGenerator(word)
        print(f"Przykładowe zdania z użyciem słowa '{generator.word}':")
        for example in generator.examples:
            print(f"- {example}")
        print(f"Losowy przykład: {generator.get_random_example()}\n")

if __name__ == "__main__":
    run_sentence_generator()
