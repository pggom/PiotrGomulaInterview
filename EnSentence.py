from WordOrSentence import WordOrSentence
class EnSentence(WordOrSentence):

    def __init__(self, row_nr, content):
        super().__init__(row_nr)
        self.content = content
        self._guiding_word = str(f"{self._guiding_word} - 4")
        self.my_language_code = 'en-US'
        self.my_name = 'en-US-Standard-A'
    def prepare_file_to_tts(self,new_folder_path):
        element_name = super().prepare_file_to_tts(new_folder_path)
        return element_name, self.my_name,self.my_language_code


