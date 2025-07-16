from WordOrSentence import WordOrSentence
from deep_translator import GoogleTranslator

class PlSentence(WordOrSentence):

    def __init__(self, row_nr, content):
        super().__init__(row_nr)
        self.content = content

        self._guiding_word = str(f"{self._guiding_word} - 3")
        self.my_language_code = 'pl-PL'
        self.my_name = 'pl-PL-Standard-B'


    def translate_sentance(self):


        english_sentence = GoogleTranslator(source='auto', target='en').translate(text=self.content)

        return english_sentence

    def prepare_file_to_tts(self,new_folder_path):
        element_name = super().prepare_file_to_tts(new_folder_path)
        return element_name, self.my_name,self.my_language_code



