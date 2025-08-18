import os
from WordOrSentence import WordOrSentence
class EnWord(WordOrSentence):
    def __init__(self, row_nr):

        super().__init__(row_nr)
        self.content = self.content
        self._guiding_word = str(f"{self._guiding_word} - 2")
        self.my_language_code = 'en-US'
        self.my_name = 'en-US-Standard-E'


    def prepare_file_to_tts(self,new_folder_path):
        element_name = super().prepare_file_to_tts(new_folder_path)
        return element_name, self.my_name,self.my_language_code

    def create_folder(self):
        location = r"C:\Users\admin\Documents\ANGIELSKI\Angielski do słuchania"

        folder_name = self.content

        new_folder_path = os.path.join(location, folder_name)


        if not os.path.exists(new_folder_path):


            os.makedirs(new_folder_path)


        return new_folder_path
