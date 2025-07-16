import os
import soundfile as sf
import numpy as np
import openpyxl
import pandas as pd
from tkinter import  ttk, messagebox
from openai import OpenAI


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_TO_XLS = os.path.join(BASE_DIR, "Text_Files", "słówka_ang_dane.xlsx")

if not os.path.exists(PATH_TO_XLS):
    error_message = ttk.Tk()
    error_message.withdraw()
    messagebox.showinfo("Błąd ścieżki", "Ścieżka nie istnieje")


def check_audio_file(english_word, file_path):


    if not os.path.isfile(file_path):
        return False

    elif not file_path.lower().endswith('.mp3'):
        return False
    else:
        min_size_kb = 10
        file_size_kb = os.path.getsize(file_path) / 1024
        if file_size_kb >= min_size_kb:

            return True
        else:
            print("Plik audio jest za mały.")
            return False

def create_dict_from_xls(PATH_TO_XLS):


    # Wczytanie danych z pliku xls
    xls_data = pd.read_excel(PATH_TO_XLS)

    # Inicjalizacja pustego słownika
    not_used_pl_word_dict = {}
    used_pl_word_dict = {}

    # Iteracja po wierszach danych
    for index, row in xls_data.iterrows():
        audio_file_path = str(row.iloc[5])
        row_number = index + 2


        if audio_file_path == "nan":

            # Pobranie słówka po polsku i angielsku
            polish_word = row.iloc[1]

            english_word = row.iloc[2]
            not_used_pl_word_dict[polish_word] = row_number
        else:
            english_word = row.iloc[2]
            if check_audio_file(english_word, audio_file_path) == False:
                print(f"Słowo {row.iloc[2]} ma nieprawidłowy plik audio.")
            polish_word = row.iloc[1]
            used_pl_word_dict[polish_word] = row_number
    return not_used_pl_word_dict, used_pl_word_dict


def excel_save(row_nr, file_path,*args):


    workbook = openpyxl.load_workbook(PATH_TO_XLS)
    sheet = workbook['Sheet']


    sheet[f'A{row_nr}'] = 'ok'
    sheet[f'F{row_nr}'] = file_path

    if args:
        sheet[f'D{row_nr}'] = args[0] if len(args) > 0 else None
        sheet[f'E{row_nr}'] = args[1] if len(args) > 1 else None


    # Zapisz zmiany
    workbook.save(PATH_TO_XLS)

# @staticmethod
def combine_audio(list_word_and_folder):




    combined_audio = np.array([], dtype=np.float32)

    for element in list_word_and_folder[1:]:
        path_to_file = element.audio_file_path

        audio, sample_rate = sf.read(path_to_file)
        pause_duration = int(element.pouse_duration) * sample_rate  # 0.1 sekundy przerwy
        final_pause = np.zeros(pause_duration)


        combined_audio = np.concatenate((combined_audio,audio,final_pause))



    output_folder = r"C:\Users\admin\Documents\ANGIELSKI\Angielski do słuchania"
    output_file = os.path.join(output_folder, list_word_and_folder[2].content + ".mp3")

    sf.write(output_file, combined_audio, samplerate=sample_rate)
    print(f"Tworzeni pliku zakończone: {output_file}")

    return output_file


def generat_sentence_from_gpt(question):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "Napisz proste wyrażenie po polsku z danym słowem. Od 2 do 4 słów. Nie dodawaj dodatkowych komentarzy. Wyrażenie musi być zgodne z polską gramatyką."},
            {"role": "user", "content": "okoliczności"},
            {"role": "assistant", "content": "w takich okolicznościach"},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content.strip()


