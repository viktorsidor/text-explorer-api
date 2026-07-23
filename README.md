# Search File and Text Analytics 🔍📊

**Bilingvní vyhledávač lokálních souborů a lingvistický textový analyzátor**

Aplikace slouží jako lehký a vysoce optimalizovaný nástroj pro pokročilé prohledávání textových dokumentů (podpora formátů `.txt`, `.pdf`, `.docx`) a základní kvantitativní analýzu textu. Projekt kombinuje moderní asynchronní webový backend v Pythonu s lingvistickým zpracováním přirozeného jazyka (NLP).

---

## Architektura systému

Projekt je striktně rozdělen na klientskou část (Frontend) a serverovou část (REST API Backend). Komunikace probíhá asynchronně pomocí formátu JSON.

```mermaid
graph TD
    UI[Klientské rozhraní: HTML5 / JS / Bootstrap 5] <-->|Asynchronní REST API / JSON| API[Server: Sanic Web Framework]
    API -->|Pravidlová tokenizace a segmentace| NLP[spaCy: cs_core_news_sm]
    API -->|Bilingvní expanze konceptů| Trans[deep-translator]
    API -->|I/O Extrakce textu| Ext[pypdf / python-docx]
```

---

## Uživatelská dokumentace

### Pokročilé vyhledávání v dokumentech

Uživatel zadá absolutní cestu k adresáři (nebo využije systémový průzkumník přes tlačítko "Procházet") a do vyhledávacího pole napíše dotaz. Vyhledávač pracuje ve dvou režimech:

1. **Konceptuální mód (Výchozí):** Uživatel zadá slovo (např. `soldier`). Systém automaticky provede bilingvní expanzi (přeloží dotaz do češtiny i angličtiny) a vyhledá v dokumentech nejen přesné slovo, ale i jeho gramatické tvary (díky lemmatizaci kořenů slov přes spaCy a odstranění diakritiky). Najde tedy i tvary jako *vojáci*, *vojákem*, *soldiers*.
2. **Exaktní mód (Uvozovky):** Pokud uživatel zadá dotaz do uvozovek (např. `"dobrý voják"`), systém vypne lingvistické ohýbání a hledá v textu pouze tento exaktní řetězec.

Výsledky se zobrazí v přehledných kartách s dynamicky vyříznutým kontextem (snippetem), kde je hledané slovo zvýrazněno žlutým HTML tagem `<mark>`.

### Lingvistická analýza textu

Uživatel v pravé části rozhraní nahraje jakýkoliv lokální soubor formátu `.txt`. Po kliknutí na tlačítko "Analyzovat soubor" backend provede kompletní zpracování textu a okamžitě zobrazí základní kvantitativní metriky:

* **Počet slov:** Celkový objem textu po očištění o interpunkci.
* **Velikost slovníku:** Počet unikátních slovních forem (bohatost slovní zásoby).
* **Počet vět:** Determinován pomocí spolehlivého pravidlového segmentátoru vět (`sentencizer`).

---

## Programátorská dokumentace

### Požadavky a závislosti

Aplikace je postavena na **Pythonu 3.12**. Všechny externí knihovny jsou definovány v souboru `requirements.txt`:

* `sanic` (v23.12.0) - Vysoce výkonný, asynchronní webový framework.
* `spacy` (>=3.8.14) - Průmyslový standard pro NLP úlohy.
* `cs-core-news-sm` - Český statistický model pro spaCy.
* `pypdf` & `python-docx` - Nástroje pro nízkoúrovňovou extrakci textu z binárních formátů.
* `deep-translator` - Zajištění překladů pro bilingvní vyhledávání.
* `click` - Podpora vnitřního CLI rozhraní pro spaCy v odlehčeném Linuxu.

### Lokální instalace a spuštění (Vývojové prostředí)

1. Nainstalujte závislosti:
```bash
pip install -r requirements.txt
```

2. Spusťte server:
```bash
python app/app.py
```

3. Otevřete prohlížeč na adrese: `http://localhost:8000`

---

## Popis REST API Protokolu

Aplikace plně implementuje specifikaci REST API. Všechny endpointy vrací data s hlavičkou `Content-Type: application/json`.

### 1. `GET /api/browse-folder`

Vyvolá na hostitelském počítači nativní grafické okno pro výběr složky.

* **Vstup:** Žádný
* **Úspěšná odpověď (200 OK):**
```json
{ "folder": "C:\\Data\\projekt" }
```

* **Poznámka:** V headless prostředích (např. Docker bez grafického rozhraní) funkce bezpečně selže a vrátí prázdný řetězec `""`.

### 2. `GET /api/search`

Prohledá zadaný adresář na základě lingvistických pravidel.

* **Query parametry:**
  * `query` (povinný) - Hledaný výraz (v uvozovkách pro exaktní shodu).
  * `folder` (nepovinný) - Absolutní cesta k adresáři. Pokud chybí, prohledává se interní složka `data`.

* **Úspěšná odpověď (200 OK):**
```json
[
  {
    "filename": "kapitola1.txt",
    "path": "C:\\data\\kapitola1.txt",
    "preview": "[Koncept: 'soldier']: ...byl to dobrý <mark class='bg-warning text-dark px-1 rounded'><strong>voják</strong></mark> Švejk..."
  }
]
```

### 3. `POST /api/analyze`

Provede rychlou statistickou analýzu nahraného souboru.

* **Vstup:** `Multipart/Form-Data` obsahující soubor v klíči `file`.
* **Úspěšná odpověď (200 OK):**
```json
{
  "word_count": 1452,
  "vocabulary_size": 412,
  "sentence_count": 89
}
```

---

## Deployment (Distribuce pomocí Dockeru)

Projekt je kompletně virtualizován a připraven pro okamžité nasazení na jakýkoliv server bez nutnosti ruční instalace Pythonu nebo jazykových modelů.

### Sestavení Docker obrazu

```bash
docker build -t text-explorer-api .
```

### Spuštění kontejneru (Jediný požadovaný příkaz)

Aplikaci nastartujete na standardním portu `8000` spuštěním tohoto příkazu v terminálu:

```bash
docker run -d -p 8000:8000 --name text-explorer text-explorer-api
```

Aplikace je následně okamžitě dostupná na adrese `http://localhost:8000`. Správu kontejneru (vypnutí, zapnutí, sledování využití RAM a procesoru) lze pohodlně provádět graficky v aplikaci **Docker Desktop**.
