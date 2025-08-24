from tkinter import ttk, messagebox
import customtkinter as ctk
from customtkinter import CTkEntry
from EnWord import EnWord
from PlWord import PlWord
from PlSentence import PlSentence
from EnSentence import EnSentence
#from Small_Programs.audio_file_path_to_excel import value
from functions import AUDIO_BASE,combine_audio, excel_save,create_dict_from_xls, generat_sentence_from_gpt,PATH_TO_XLS,update_excel_word ,add_points, restart_app, refresh_word_dicts_and_list
import pandas as pd
import locale
import os


selected_word = None
pl_word = None
en_word = None
polish_sentence = None
english_sentence = None
row_nr = None

pl_edit_entry = None
en_edit_entry = None
edit_mode = False

segment_vars = []     # lista 4x IntVar (1..4)
segment_paths = {}    # dict {1: path, 2: path, 3: path, 4: path}
segment_widgets = []  # żeby móc wyczyścić UI przy kolejnym słowie

labels = {}

def _get_saved_sentences(row_nr: int):
    """Zwraca (pl, en) z Excela dla danego wiersza. Puste stringi jeśli brak."""
    df = pd.read_excel(PATH_TO_XLS)
    r = df.iloc[row_nr - 2]             # -2 bo nagłówek + 1-based w Excelu
    pl_cell = r.iloc[3]                 # kolumna D (sentence_in_polish)
    en_cell = r.iloc[4]                 # kolumna E (sentence_in_english)

    def _clean(v):
        if isinstance(v, float):
            # NaN itp.
            return "" if pd.isna(v) else str(v).strip()
        return "" if pd.isna(v) else str(v).strip()

    return _clean(pl_cell), _clean(en_cell)


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

def clear_area(rows, columns=None):
    """
    Usuń wszystkie widgety w podanych wierszach (i opcjonalnie kolumnach).
    rows: iterable, np. range(9,13) lub [9,10,11,12]
    columns: iterable lub None -> usuń wszystko w danym wierszu
    """
    if columns is None:
        for r in rows:
            # usuń wszystko w wierszu r
            for w in app.grid_slaves(row=r):
                w.destroy()
    else:
        for r in rows:
            for c in columns:
                for w in app.grid_slaves(row=r, column=c):
                    w.destroy()


# def create_label(text, row, column, **kwargs):
#     ctk.CTkLabel(app, text=text).grid(row=row, column=column, **kwargs)
def create_label(text, row, column, **kwargs):
    # jeśli w tej komórce już coś jest → usuń
    if (row, column) in labels:
        labels[(row, column)].destroy()
    # nowy label
    lbl = ctk.CTkLabel(app, text=text)
    lbl.grid(row=row, column=column, **kwargs)
    labels[(row, column)] = lbl
    return lbl

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

    print(f"Słowo: {selected_word} | Punkty: {_points}")

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
        # DEBUG: co sprawdzamy / jaki wiersz?
        print(f"[DEBUG] WRONG. selected_word={selected_word!r}  row_nr={row_nr}  en_word={en_word.content!r}")

        # wczytaj zapisane zdania (Excel)
        pl_saved, en_saved = _get_saved_sentences(row_nr)

        print(f"[DEBUG] from Excel -> PL:{pl_saved!r}  EN:{en_saved!r}")

        if pl_saved:
            bar_for_polish_sentence.delete(0, "end")
            bar_for_polish_sentence.insert(0, pl_saved)
            print(f"[DEBUG] inserted into PL entry: {bar_for_polish_sentence.get()!r}")

        if en_saved:
            bar_for_english_sentence.delete(0, "end")
            bar_for_english_sentence.insert(0, en_saved)
            print(f"[DEBUG] inserted into EN entry: {bar_for_english_sentence.get()!r}")


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
    create_button("Zdania ok",approve_sentences,7,1, padx=5, pady=5)

bars_list = []
def create_pause_duration_bar(text, row, var_value):
    create_label(text, row, 0, padx=5, pady=5, sticky="w")
    duration_var = ctk.StringVar()
    duration_var.set(var_value)
    duration_bar = ctk.CTkEntry(app, textvariable=duration_var)
    duration_bar.grid(row=row, column=1, padx=10, pady=10, sticky="w")
    bars_list.append(duration_bar)

def approve_sentences():
    global english_sentence
    english_sentence = EnSentence(row_nr, bar_for_english_sentence.get())

    create_label("Tekst", 8, 0, padx=5, pady=5, sticky="w")
    create_label("Opóźnienie", 8, 1, padx=5, pady=5, sticky="w")

    # czyścimy cały blok 9..12 w kolumnach 0..2 (teksty, entry, checkboxy)
    clear_area(range(9, 13), columns=[0, 1, 2])

    create_pause_duration_bar(pl_word.content, 9, pl_word.pause_duration)
    create_pause_duration_bar(en_word.content, 10, en_word.pause_duration)
    create_pause_duration_bar(polish_sentence.content, 11, polish_sentence.pause_duration)
    create_pause_duration_bar(english_sentence.content, 12, english_sentence.pause_duration)

    # --- NOWE: segmenty z dysku + checkboxy
    _clear_segment_checkboxes()
    # wyszukaj gotowe pliki "<en> - 1.wav" ... "<en> - 4.wav"
    found = _find_segment_files_for_word(en_word.content)
    segment_paths.update(found)
    # narysuj checkboxy (kolumna 2, rząd od 8 w dół, obok 'Opóźnienie')
    _render_segment_checkboxes(start_row=8)

    create_button("Wyślij do Google TTS", lambda: send_to_tts(bars_list), 13, 1, padx=10, pady=10)


def send_to_tts(bars_list):
    try:
        # 1) czasy pauz (z GUI)
        pl_word.set_pause_duration(bars_list[0].get())
        en_word.set_pause_duration(bars_list[1].get())
        polish_sentence.set_pause_duration(bars_list[2].get())
        english_sentence.set_pause_duration(bars_list[3].get())



        # Celujemy w te obiekty, kolejność = indeksom 1..4
        targets = [pl_word, en_word, polish_sentence, english_sentence]

        # 2) Jeśli checkbox i plik istnieje -> użyj gotowego audio
        for idx, obj in enumerate(targets, start=1):
            try:
                use_it = (segment_vars[idx - 1].get() == 1)  # zaznaczony?
            except Exception:
                use_it = False
            path = segment_paths.get(idx)
            if use_it and path and os.path.isfile(path):
                obj.set_existing_audio(path)

        # 3) Dla tych, które wciąż nie mają pliku – robimy TTS
        for obj in targets:
            if not getattr(obj, "audio_file_path", None) or not os.path.isfile(obj.audio_file_path):
                folder = en_word.create_folder()
                obj.prepare_file_to_tts(folder)

        # 4) Składanie całości + zapis do Excela
        new_folder_path = en_word.create_folder()
        list_word_and_folder = [new_folder_path, pl_word, en_word, polish_sentence, english_sentence]
        file_path = combine_audio(list_word_and_folder)
        excel_save(en_word.row_nr, file_path, polish_sentence.content, english_sentence.content)

        _refresh_after_audio()
        next_word()

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

def _find_segment_files_for_word(en_word_text: str):
    """
    Szuka w AUDIO_BASE/<en_word>/ plików:
      "<en_word> - 1.wav" ... "<en_word> - 4.wav"
    Zwraca dict {1:path, 2:path, 3:path, 4:path} (tylko istniejące).
    """
    folder = os.path.join(AUDIO_BASE, en_word_text)
    found = {}
    if os.path.isdir(folder):
        for idx in (1, 2, 3, 4):
            cand = os.path.join(folder, f"{en_word_text} - {idx}.wav")
            if os.path.isfile(cand):
                found[idx] = cand
    return found


def _clear_segment_checkboxes():
    """Usuwa stare checkboxy i czyści zmienne."""
    global segment_vars, segment_paths, segment_widgets
    for w in segment_widgets:
        try:
            w.destroy()
        except:
            pass
    segment_widgets.clear()
    segment_vars.clear()
    segment_paths.clear()


def _render_segment_checkboxes(start_row: int):
    """
    Tworzy 4 checkboxy (1..4) po prawej od pól 'Opóźnienie'.
    Zaznaczone jeśli istnieje odpowiedni plik w segment_paths.
    """
    global segment_vars, segment_widgets
    labels = {
        1: "1. słowo PL",
        2: "2. słowo EN",
        3: "3. zdanie PL",
        4: "4. zdanie EN",
    }
    # Nagłówek
    hdr = ctk.CTkLabel(app, text="Użyj gotowych segmentów (z dysku):")
    hdr.grid(row=start_row, column=2, padx=12, pady=(6, 2), sticky="w")
    segment_widgets.append(hdr)

    for i in range(1, 5):
        v = ctk.IntVar(value=1 if i in segment_paths else 0)
        cb = ctk.CTkCheckBox(app, text=f"{labels[i]}",
                             variable=v, onvalue=1, offvalue=0)
        cb.grid(row=start_row + i, column=2, padx=12, pady=4, sticky="w")
        segment_vars.append(v)
        segment_widgets.append(cb)



def run_ui():
    load_word_by_index(0)
    # Enter działa tylko jak "Sprawdź"
    app.bind("<Return>", lambda event: check_answer())
    _bind_shortcuts()
    app.mainloop()





