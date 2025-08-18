from tkinter import ttk, messagebox
import customtkinter as ctk
from customtkinter import CTkEntry
from EnWord import EnWord
from PlWord import PlWord
from PlSentence import PlSentence
from EnSentence import EnSentence
#from Small_Programs.audio_file_path_to_excel import value
from functions import combine_audio, excel_save,create_dict_from_xls, generat_sentence_from_gpt,PATH_TO_XLS,update_excel_word ,add_points, restart_app, refresh_word_dicts_and_list
import pandas as pd
import locale


dict_with_polishword_key, dict_with_used_word = create_dict_from_xls(PATH_TO_XLS)

locale.setlocale(locale.LC_COLLATE, "pl_PL.UTF-8")  # opcjonalnie: sortowanie po polsku

# zbuduj posortowany słownik (klucz=PL, wartość=(row_nr, points))
_all_words = dict(sorted(
    {**dict_with_polishword_key, **dict_with_used_word}.items(),
    key=lambda kv: (kv[1][1], locale.strxfrm(kv[0]))  # (punkty, polskie A→Z)
    # jeśli bez polskiej lokalizacji: key=lambda kv: (kv[1][1], kv[0].lower())
))

print(_all_words)
# teraz ta kolejność jest “permanentna” dla tego obiektu
pl_word_list = list(_all_words.keys())

#Ogólne ustawienia okna
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Nauka angielskiego")

def create_label(text, row, column, **kwargs):
    ctk.CTkLabel(app, text=text).grid(row=row, column=column, **kwargs)

last_button = None  # globalna zmienna

def create_button(text, command, row, column, **kwargs):
    global last_button
    btn = ctk.CTkButton(app, text=text, command=command)
    btn.grid(row=row, column=column, **kwargs)
    last_button = btn
    return btn

def reset_ui():
    global current_idx
    answer_entry.delete(0, "end")
    bar_for_polish_sentence.delete(0, "end")
    bar_for_english_sentence.delete(0, "end")
    pl_word_display.configure(text="")
    load_word_by_index(current_idx)

# Możesz zmienić tekst, ale zostawiam jak było
create_label("Wybierz słówko do tłumaczenia",1,0, padx=10, pady=10)
# create_button("Następne słówko", lambda: load_word_by_index(current_idx + 1), 1, 1, padx=10, pady=10)
def next_word():
    global current_idx
    if not pl_word_list:
        return
    nxt = (current_idx + 1) % len(pl_word_list)
    load_word_by_index(nxt)

create_button("Następne słówko", next_word, 1, 1, padx=10, pady=10)

create_button("Wyczyść", reset_ui, 1,3,padx=10, pady=10)


selected_word = None
pl_word = None
en_word = None
polish_sentence = None
english_sentence = None
row_nr = None

pl_edit_entry = None
en_edit_entry = None
edit_mode = False

bar_for_polish_sentence = CTkEntry(app, width=450)
# Python
translate_btn = None  # globalnie


# TO JEST DO WYRZUCENIA
def show_translate_button(event=None):
    global translate_btn
    if bar_for_polish_sentence.get().strip():
        if not translate_btn:
            translate_btn = create_button("Przetłumacz", create_polish_sentence, 5, 1, padx=5, pady=5)
    else:
        if translate_btn:
            translate_btn.destroy()
            translate_btn = None

bar_for_polish_sentence.bind("<KeyRelease>", show_translate_button)

bar_for_english_sentence = CTkEntry(app, width=450)

# >>> DODANE: label ze słówkiem PL + pole odpowiedzi EN + przycisk Sprawdź
pl_word_display = ctk.CTkLabel(app, text="")
pl_word_display.grid(row=2, column=0, padx=10, pady=10, sticky="w")

answer_entry = CTkEntry(app, width=300)
answer_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())

def _show_original_ui():
    global en_word, pl_word, bar_for_polish_sentence
    pl_and_en_word_label = ctk.CTkLabel(app, text=" " * 130)
    pl_and_en_word_label.grid(row=3, column=0)
    create_label(f"Słówko po polsku: {pl_word.content}     Słówko po angielsku: {en_word.content} ",3, 0)
    create_label("Wprowadź zdanie po polsku do wybranego słowa",4,0,padx=5,pady =5,sticky="nsew")
    bar_for_polish_sentence.grid(row=5, column=0, padx=5, pady =5, sticky="nsew")
    df = pd.read_excel(PATH_TO_XLS)
    create_button("Przetłumacz",create_polish_sentence,5,1,padx=5,pady=5)
    create_button("Generuj wyrażenie", insert_sentence_to_bar, 3, 1, padx=5,pady=5)
    bar_for_polish_sentence.delete(0, "end")

# >>> NOWE: indeks i ładowanie słowa po indeksie (zamiast comboboxa)
current_idx = 0
def load_word_by_index(idx: int):
    global selected_word, row_nr, en_word, pl_word, current_idx
    current_idx = idx  # <<< aktualizuj bieżący indeks
    selected_word = pl_word_list[idx]
    if selected_word in dict_with_polishword_key:
        row_nr, _points = dict_with_polishword_key[selected_word]

    elif selected_word in dict_with_used_word:
        row_nr, _points = dict_with_used_word[selected_word]

    else:
        print("Coś nie tak z wybranym słowem")
        return
    en_word = EnWord(row_nr)
    pl_word = PlWord(row_nr)
    pl_word_display.configure(text=f"{pl_word.content}")
    answer_entry.delete(0, "end")

# >>> ZMIANA: „Sprawdź” bez comboboxa – przejście do kolejnego indeksu
def check_answer():
    global current_idx
    if not en_word:
        return
    ok = (_normalize(answer_entry.get()) == _normalize(en_word.content))
    # dodanie punktów do Excela
    if selected_word in dict_with_polishword_key:
        row_nr, _points = dict_with_polishword_key[selected_word]
    elif selected_word in dict_with_used_word:
        row_nr, _points = dict_with_used_word[selected_word]
    else:
        return

    if ok:

        add_points(row_nr, 3)

        current_idx += 1
        if current_idx >= len(pl_word_list):
            current_idx = 0  # lub możesz zakończyć: return
        load_word_by_index(current_idx)
    else:
        add_points(row_nr, 1)
        _show_original_ui()
        # answer_entry.delete(0, "end")
        # answer_entry.insert(0, en_word.content)


def toggle_edit_mode():
    global edit_mode, pl_edit_entry, en_edit_entry
    edit_mode = not edit_mode
    if edit_mode:
        create_label("PL ↴", 3, 0, padx=5, pady=2, sticky="w")
        create_label("EN ↴", 4, 0, padx=5, pady=2, sticky="w")
        for w in [pl_edit_entry, en_edit_entry]:
            try:
                if w: w.destroy()
            except:
                pass
        init_pl = pl_word.content if pl_word else ""
        init_en = en_word.content if en_word else ""
        globals()['pl_edit_entry'] = ctk.CTkEntry(app, width=450)
        globals()['en_edit_entry'] = ctk.CTkEntry(app, width=450)
        pl_edit_entry.insert(0, init_pl)
        en_edit_entry.insert(0, init_en)
        pl_edit_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        en_edit_entry.grid(row=4, column=1, padx=5, pady=2, sticky="ew")
    else:
        try:
            if pl_edit_entry: pl_edit_entry.destroy()
            if en_edit_entry: en_edit_entry.destroy()
        except:
            pass

def save_word_edits():
    global dict_with_polishword_key, dict_with_used_word, pl_word_list, current_idx, selected_word
    if not (pl_edit_entry and en_edit_entry and pl_word and en_word):
        return
    new_pl = pl_edit_entry.get().strip()
    new_en = en_edit_entry.get().strip()
    if not new_pl or not new_en:
        messagebox.showwarning("Edycja", "PL i EN nie mogą być puste.")
        return

    update_excel_word(en_word.row_nr, new_pl, new_en)
    dict_with_polishword_key, dict_with_used_word = create_dict_from_xls(PATH_TO_XLS)
    pl_word_list = sorted(
        dict_with_polishword_key.keys(),
        key=lambda w: (dict_with_polishword_key[w][1], w.lower())
    )
    if new_pl in pl_word_list:
        current_idx = pl_word_list.index(new_pl)
    else:
        current_idx = 0
    toggle_edit_mode()
    load_word_by_index(current_idx)
    # messagebox.showinfo("Edycja", "Zapisano zmiany.")

create_button("Sprawdź", check_answer, 2, 3, padx=10, pady=10)
create_button("Edytuj słowo", toggle_edit_mode, 2, 4, padx=6, pady=10)
create_button("Zapisz zmiany", save_word_edits, 2, 5, padx=6, pady=10)

# >>> USUNIĘTE: combobox + on_select_polish_word (niepotrzebne)
# (pozostawiam definicję on_select_polish_word, jeśli chcesz – ale nie jest wywoływana)
def on_select_polish_word(event):
    pass

# --- Twoja sekcja tłumaczeń / audio niezmieniona ---
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
    try:
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
        # <<< odśwież słowniki i listę po zapisie ścieżki audio do Excela
        _refresh_after_audio()
        next_word()

        # # sukces → restart po chwili (żeby UI zdążyło dokończyć event)
        # app.after(100, do_restart)
    except Exception as e:
        messagebox.showerror("Błąd TTS", f"Wystąpił błąd podczas generowania: {e}")


def _refresh_after_audio():
    global dict_with_polishword_key, dict_with_used_word, pl_word_list, current_idx
    dict_with_polishword_key, dict_with_used_word, pl_word_list = refresh_word_dicts_and_list()
    if pl_word_list:
        current_idx = min(current_idx, len(pl_word_list) - 1)
    else:
        current_idx = 0
# Python
def do_restart():
    restart_app()  # uruchamia program od nowa
    app.destroy()  # zamyka okno Tkinter

        
def insert_sentence_to_bar():
    global selected_word, bar_for_polish_sentence
    if selected_word:
        generated_sentence = generat_sentence_from_gpt(
            pl_word.content,  # polskie hasło
            en_word.content,  # angielskie słowo
            cefr="A2",  # możesz podbić na "B1"
            mode="phrase"  # albo "sentence"
        )

        bar_for_polish_sentence.delete(0, "end")
        bar_for_polish_sentence.insert(0, generated_sentence)
    else:
        print("Nie wybrano słowa.")


def _bind_shortcuts():
    app.bind("<F2>", lambda e: toggle_edit_mode())
    app.bind("<Control-s>", lambda e: save_word_edits())

def run_ui():
    load_word_by_index(0)
    # Enter działa tylko jak "Sprawdź"
    app.bind("<Return>", lambda event: check_answer())
    _bind_shortcuts()
    app.mainloop()





