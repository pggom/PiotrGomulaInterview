from tkinter import ttk
import customtkinter as ctk
from customtkinter import CTkEntry
from EnWord import EnWord
from PlWord import PlWord
from PlSentence import PlSentence
from EnSentence import EnSentence
#from Small_Programs.audio_file_path_to_excel import value
from functions import combine_audio, excel_save,create_dict_from_xls, generat_sentence_from_gpt,PATH_TO_XLS
import pandas as pd



dict_with_polishword_key, dict_with_used_word = create_dict_from_xls(PATH_TO_XLS)


pl_word_list = [str(key) for key in dict_with_polishword_key.keys()]
pl_word_list.sort(key=str.lower)

# english_tenses = [
#     "Present Simple",
#     "Present Continuous",
#     "Present Perfect Simple",
#     "Past Simple",
#     "Past Continuous",
#     "Past Perfect Simple",
#     "Future Simple (will)",
#     "Be going to",
#     "Zero Conditional",
#     "First Conditional",
#     "Second Conditional",
#     "Third Conditional",
#     "Reported Speech",
#     "Passive voice",
#     "Can, could, be able to",
#     "Must, have to, need to",
#     "Should",
#     "May, might",
#     "Gerund",
#     "Infinitive",
#     "Defining Relative Clauses",
#     "Non-defining Relative Clauses",
#     "Comparative Structures",
#     "Used to"
# ]
#
# pl_word_list += english_tenses




#Ogólne ustawienia okna
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Nauka angielskiego")


def create_label(text, row, column, **kwargs):
    ctk.CTkLabel(app, text=text).grid(row=row, column=column, **kwargs)

def create_button(text, command, row, column, **kwargs):
    ctk.CTkButton(app, text=text, command=command).grid(row=row, column=column, **kwargs)


create_label("Wybierz słówko do tłumaczenia",1,0, padx=10, pady=10)

selected_word = None
pl_word = None
en_word = None
polish_sentence = None
english_sentence = None
row_nr = None


bar_for_polish_sentence = CTkEntry(app, width=450)
bar_for_english_sentence = CTkEntry(app, width=450)


def on_select_polish_word(event):
    global selected_word
    global bar_for_polish_sentence
    global row_nr
    global en_word
    global pl_word

    selected_word = polisch_word_combo.get()
    if selected_word in dict_with_polishword_key:
        row_nr = dict_with_polishword_key[selected_word]
    elif selected_word in dict_with_used_word:
        row_nr = dict_with_used_word[selected_word]
    else:
        print("Coś nie tak z wybranym słowem")

    en_word = EnWord(row_nr)
    pl_word = PlWord(row_nr)
    pl_and_en_word_label = ctk.CTkLabel(app, text="                                                                                                                                          ")
    pl_and_en_word_label.grid(row=3, column=0)
    pl_and_en_word_label = create_label(f"Słówko po polsku: {pl_word.content}     Słówko po angielsku: {en_word.content} ",3, 0)
    create_label("Wprowadź zdanie po polsku do wybranego słowa",4,0,padx=5,pady =5,sticky="nsew")
    bar_for_polish_sentence.grid(row=5, column=0, padx=5, pady =5, sticky="nsew")
    df = pd.read_excel(PATH_TO_XLS)

    create_button("Przetłumacz",create_polish_sentence,5,1,padx=5,pady=5)
    create_button("Generuj wyrażenie", insert_sentence_to_bar, 3, 1, padx=5,pady=5)
    bar_for_polish_sentence.delete(0, "end")



polisch_word_combo = ttk.Combobox(app, values=pl_word_list ,width=90)
polisch_word_combo.grid(row=2, column=0,padx=15, pady=15, sticky="nsew")
polisch_word_combo.bind("<<ComboboxSelected>>", on_select_polish_word)


def create_polish_sentence():


    global row_nr
    global polish_sentence
    polish_sentence = PlSentence(row_nr, bar_for_polish_sentence.get())

    english_sentence = polish_sentence.translate_sentance()
    create_label("Wprowadź zdanie po angielsku",6,0,padx=5,pady =5,sticky="nsew")
    bar_for_english_sentence.delete(0, "end")
    bar_for_english_sentence.insert(0, string=english_sentence)
    bar_for_english_sentence.grid(row=7, column=0, padx=5, pady =5, sticky="nsew")
    create_button("Zadnia ok",approve_sentences,7,1, padx=5, pady=5)

bars_list = []
def create_pouse_duration(text, row, var_value):
    create_label(text, row, 0, padx=5, pady=5, sticky="w")
    duration_var = ctk.StringVar()
    duration_var.set(var_value)
    duration_bar = ctk.CTkEntry(app, textvariable=duration_var)
    duration_bar.grid(row=row, column=1, padx=10, pady=10, sticky="w")
    bars_list.append(duration_bar)

def approve_sentences():
    global english_sentence
    english_sentence = EnSentence(row_nr,bar_for_english_sentence.get())

    create_label("Tekst",8,0,padx=5,pady =5,sticky="w")
    create_label("Opóźnienie",8,1,padx=5,pady =5,sticky="w")


    create_pouse_duration(pl_word.content, 9, len(en_word)+4)
    create_pouse_duration(en_word.content, 10, len(en_word)+4)
    create_pouse_duration(polish_sentence.content, 11, len(english_sentence)+4)
    create_pouse_duration(english_sentence.content, 12, len(english_sentence)+4)


    create_button("Wyślij do Google TTS", lambda: send_to_tts(bars_list), 13, 1, padx=10,pady=10)




def send_to_tts(bars_list):
    pl_word.pouse_duration(bars_list[0].get())
    en_word.pouse_duration(bars_list[1].get())
    polish_sentence.pouse_duration(bars_list[2].get())
    english_sentence.pouse_duration(bars_list[3].get())

    new_folder_path = en_word.create_folder()
    pl_word.prepare_file_to_tts(new_folder_path)
    en_word.prepare_file_to_tts(new_folder_path)
    polish_sentence.prepare_file_to_tts(new_folder_path)
    english_sentence.prepare_file_to_tts(new_folder_path)

    list_word_and_folder = [new_folder_path, pl_word, en_word, polish_sentence, english_sentence]
    file_path = combine_audio(list_word_and_folder)
    excel_save(en_word.row_nr, file_path, polish_sentence.content, english_sentence.content)
    create_button("Wyślij do Google TTS", send_to_tts,13,1, padx = 10, pady = 10)


def insert_sentence_to_bar():
    global selected_word, bar_for_polish_sentence
    if selected_word:
        generated_sentence = generat_sentence_from_gpt(selected_word)
        bar_for_polish_sentence.delete(0, "end")
        bar_for_polish_sentence.insert(0, generated_sentence)

    else:
        print("Nie wybrano słowa.")



def run_ui():

    app.mainloop()

