import os
import spacy
import asyncio
from sanic import Sanic
from sanic.response import json, file
import unicodedata
import re
import pypdf
import docx
from deep_translator import GoogleTranslator
try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None
    filedialog = None

app = Sanic("SearchApp")
nlp = spacy.load("cs_core_news_sm", disable=["parser", "ner"])
nlp.add_pipe("sentencizer")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
HTML_PATH = os.path.join(BASE_DIR, "static", "index.html")

app.static("/static", os.path.join(BASE_DIR, "static"))

# --- LINGVISTICKÉ POMOCNÉ FUNKCE ---

def remove_diacritics(text):
    """Převede text na malá písmena a odstraní diakritiku se zachováním délky 1:1."""
    if not text:
        return ""
    accented = "áčďéěíňóřšťúůýmžÁČĎÉĚÍŇÓŘŠŤÚŮÝMŽ"
    unaccented = "acdeeinorstuuymzACDEEINORSTUUYMZ"
    mapping = str.maketrans(accented, unaccented)
    return text.translate(mapping).lower()

def clean_extracted_text(text):
    """Odstraňuje z textu zalomení řádků a spojuje slova rozdělená pomlčkou (častý problém PDF)."""
    if not text:
        return ""
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    return text

# --- EXTRAKTORY TEXTU ---
def extract_text_from_pdf(file_path):
    text = ""
    try:
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception:
        pass
    return text

def extract_text_from_docx(file_path):
    text = ""
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text += paragraph.text + "\n"
    except Exception:
        pass
    return text

def ask_directory_sync():
    # Pokud jsme v Dockeru a tkinter se nenačetl, okno neotevíráme
    if tk is None or filedialog is None:
        return ""
        
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_path = filedialog.askdirectory()
        root.destroy()
        return folder_path
    except Exception:
        return ""

# --- LOGIKA VYHLEDÁVÁNÍ ---

def search_files(query, directory):
    results = []
    if not os.path.exists(directory):
        return [{"filename": "Chyba", "path": directory, "preview": "Zadaná složka neexistuje!"}]

    # Detekce exaktního módu pomocí uvozovek
    stripped_query = query.strip('"\'“”')
    is_exact_mode = len(stripped_query) < len(query)

    if is_exact_mode:
        target_exact = stripped_query.lower()
    else:
        # Konceptuální vyhledávání s bilingvní expanzí
        try:
            query_en = GoogleTranslator(source='auto', target='en').translate(stripped_query).lower()
            query_cs = GoogleTranslator(source='auto', target='cs').translate(stripped_query).lower()
        except Exception:
            query_en = stripped_query.lower()
            query_cs = stripped_query.lower()

        target_en = remove_diacritics(query_en)
        target_cs = remove_diacritics(query_cs)

        stem_en = target_en
        
        if len(target_cs) > 4 and target_cs[-1] in "oae":
            stem_cs = target_cs[:-1]
        else:
            stem_cs = target_cs

    # Procházení souborů
    for root_dir, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root_dir, file_name)
            file_text = ""
            
            if file_name.endswith(".txt"):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_text = f.read()
                except Exception:
                    continue
            elif file_name.endswith(".pdf"):
                file_text = clean_extracted_text(extract_text_from_pdf(file_path))
            elif file_name.endswith(".docx"):
                file_text = clean_extracted_text(extract_text_from_docx(file_path))
            else:
                continue

            if not file_text.strip():
                continue

            matched_snippet = None
            match_label = ""

            # --- PRVNÍ KROK: EXAKTNÍ HLEDÁNÍ ---
            if is_exact_mode:
                file_text_lower = file_text.lower()
                if target_exact in file_text_lower:
                    start_idx = file_text_lower.find(target_exact)
                    crop_start = max(0, start_idx - 50)
                    crop_end = min(len(file_text), start_idx + len(target_exact) + 60)
                    
                    snippet = file_text[crop_start:crop_end].strip().replace("\n", " ").replace("\r", " ")
                    snippet_lower = snippet.lower()
                    
                    word_pos = snippet_lower.find(target_exact)
                    if word_pos != -1:
                        before = snippet[:word_pos]
                        actual = snippet[word_pos:word_pos + len(target_exact)]
                        after = snippet[word_pos + len(target_exact):]
                        snippet = f"{before}<mark class='bg-warning text-dark px-1 rounded'><strong>{actual}</strong></mark>{after}"
                    
                    if crop_start > 0: snippet = "..." + snippet
                    if crop_end < len(file_text): snippet = snippet + "..."
                    matched_snippet = snippet
                    match_label = f"Přesná shoda"

            # --- DRUHÝ KROK: LINGVISTICKÉ HLEDÁNING ---
            else:
                doc = nlp(file_text)
                for sent in doc.sents:
                    sent_text = sent.text.strip().replace("\n", " ").replace("\r", " ")
                    
                    original_words = re.findall(r'\b\w+\b', sent_text)
                    matched_word = None

                    for word in original_words:
                        word_norm = remove_diacritics(word)
                        cleaned_word = word_norm[2:] if word_norm.startswith("ne") and len(word_norm) > 4 else word_norm
                        
                        if (stem_cs and cleaned_word.startswith(stem_cs)) or (stem_en and cleaned_word.startswith(stem_en)):
                            matched_word = word
                            break

                    if matched_word:
                        match_label = f"Koncept: '{stripped_query}'"
                        start_idx = sent_text.lower().find(matched_word.lower())
                        
                        if start_idx != -1:
                            crop_start = max(0, start_idx - 50)
                            crop_end = min(len(sent_text), start_idx + len(matched_word) + 60)
                            snippet = sent_text[crop_start:crop_end].strip()
                            
                            word_idx = snippet.lower().find(matched_word.lower())
                            if word_idx != -1:
                                before = snippet[:word_idx]
                                actual = snippet[word_idx:word_idx + len(matched_word)]
                                after = snippet[word_idx + len(matched_word):]
                                snippet = f"{before}<mark class='bg-warning text-dark px-1 rounded'><strong>{actual}</strong></mark>{after}"
                            
                            if crop_start > 0: snippet = "..." + snippet
                            if crop_end < len(sent_text): snippet = snippet + "..."
                            matched_snippet = snippet
                            break

            if matched_snippet:
                results.append({
                    "filename": file_name,
                    "path": file_path,
                    "preview": f"[{match_label}]: {matched_snippet}"
                })
                
    return results

# --- API ENDPOINTY ---

@app.get("/api/browse-folder")
async def api_browse_folder(request):
    loop = asyncio.get_event_loop()
    selected_path = await loop.run_in_executor(None, ask_directory_sync)
    return json({"folder": selected_path})

@app.get("/api/search")
async def api_search(request):
    query = request.args.get("query")
    chosen_folder = request.args.get("folder")
    if not query:
        return json({"error": "Missing query parameter"}, status=400)
    search_directory = chosen_folder if chosen_folder else DEFAULT_PATH
    results = search_files(query, search_directory)
    return json(results)

@app.post("/api/analyze")
async def api_analyze(request):
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return json({"error": "Nebyl nahrán žádný soubor"}, status=400)
    
    text_content = uploaded_file.body.decode("utf-8", errors="ignore")
    doc = nlp(text_content)
    
    words = [token.text.lower() for token in doc if not token.is_punct and not token.is_space]
    word_count = len(words)
    vocabulary_size = len(set(words))

    sentences = list(doc.sents)
    sentence_count = len(sentences)
            
    return json({
        "word_count": word_count,
        "vocabulary_size": vocabulary_size,
        "sentence_count": sentence_count
    })

@app.get("/")
async def index_page(request):
    return await file(HTML_PATH)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)