import pandas as pd
from WordOrSentence import WordOrSentence
from functions import PATH_TO_XLS


class PlWord(WordOrSentence):
    def __init__(self,row_nr):
        super().__init__(row_nr)
        self.row_nr= row_nr
        xls_data = pd.read_excel(PATH_TO_XLS)
        self.content = xls_data.iloc[row_nr - 2, 1]
        self._guiding_word = str(f"{self._guiding_word} - 1")
        self.my_language_code = 'pl-PL'
        self.my_name = 'pl-PL-Standard-F'

    def prepare_file_to_tts(self,new_folder_path):
        element_name = super().prepare_file_to_tts(new_folder_path)
        return element_name, self.my_name,self.my_language_code

