import pandas
from functions import PATH_TO_XLS
import os
from google.cloud import texttospeech


class WordOrSentence:

    def __init__(self, row_nr):
        self.row_nr = row_nr
        xls_data = pandas.read_excel(PATH_TO_XLS)
        self._guiding_word = xls_data.iloc[row_nr - 2,2]
        self.content = xls_data.iloc[row_nr-2,2]

    def __len__(self):
        duration_lenght = int(1+len(self.content)/6)
        return duration_lenght

    def pouse_duration(self, duration):
        self.pouse_duration = duration



    def prepare_file_to_tts(self, new_folder_path):

        element_name = str(self._guiding_word) + ".wav"
        json_file_path = r"C:\Users\admin\PycharmProjects\pythonProject\naukaangielskiegotts-ebcb0b922743.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_file_path
        client = texttospeech.TextToSpeechClient()

        text_block = self.content

        synthesis_input = texttospeech.SynthesisInput(text=text_block)

        voice = texttospeech.VoiceSelectionParams(
            language_code=self.my_language_code,
            name=self.my_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            effects_profile_id=['small-bluetooth-speaker-class-device'],
            speaking_rate=0.8,
            pitch=1
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        output_folder = new_folder_path
        output_file_path = os.path.join(output_folder, element_name)

        with open(output_file_path, "wb") as output:
            output.write(response.audio_content)
            self.audio_file_path = output_file_path


