\# Search File and Text Analytics 🔍📊



\*\*Bilingvní vyhledávač lokálních souborů a lingvistický textový analyzátor\*\*



Aplikace slouží jako lehký a vysoce optimalizovaný nástroj pro pokročilé prohledávání textových dokumentů (podpora formátů `.txt`, `.pdf`, `.docx`) a základní kvantitativní analýzu textu. Projekt kombinuje moderní asynchronní webový backend v Pythonu s lingvistickým zpracováním přirozeného jazyka (NLP).



\---



\## Architektura systému



Projekt je striktně rozdělen na klientskou část (Frontend) a serverovou část (REST API Backend). Komunikace probíhá asynchronně pomocí formátu JSON.



```mermaid

graph TD

&#x20;   UI\[Klientské rozhraní: HTML5 / JS / Bootstrap 5] <-->|Asynchronní REST API / JSON| API\[Server: Sanic Web Framework]

&#x20;   API -->|Pravidlová tokenizace a segmentace| NLP\[spaCy: cs\_core\_news\_sm]

&#x20;   API -->|Bilingvní expanze konceptů| Trans\[deep-translator]

&#x20;   API -->|I/O Extrakce textu| Ext\[pypdf / python-docx]



```



\---



\## Uživatelská dokumentace



\### Pokročilé vyhledávání v dokumentech



Uživatel zadá absolutní cestu k adresáři (nebo využije systémový průzkumník přes tlačítko "Procházet") a do vyhledávacího pole napíše dotaz. Vyhledávač pracuje ve dvou režimech:



1\. \*\*Konceptuální mód (Výchozí):\*\* Uživatel zadá slovo (např. `soldier`). Systém automaticky provede bilingvní expanzi (přeloží dotaz do češtiny i angličtiny) a vyhledá v dokumentech nejen přesné slovo, ale i jeho gramatické tvary (díky lemmatizaci kořenů slov přes spaCy a odstranění diakritiky). Najde tedy i tvary jako \*vojáci\*, \*vojákem\*, \*soldiers\*.

2\. \*\*Exaktní mód (Uvozovky):\*\* Pokud uživatel zadá dotaz do uvozovek (např. `"dobrý voják"`), systém vypne lingvistické ohýbání a hledá v textu pouze tento exaktní řetězec.



Výsledky se zobrazí v přehledných kartách s dynamicky vyříznutým kontextem (snippetem), kde je hledané slovo zvýrazněno žlutým HTML tagem `<mark>`.



```mermaid

sequenceDiagram

&#x20;   actor U as Uživatel (Prohlížeč)

&#x20;   participant B as Sanic Backend

&#x20;   participant T as Deep Translator

&#x20;   participant N as spaCy Engine



&#x20;   U->>B: GET /api/search?query=soldier

&#x20;   alt Konceptuální mód (bez uvozovek)

&#x20;       B->>T: Automatický překlad (EN/CS)

&#x20;       T-->>B: Vrátí bilingvní koncepty

&#x20;   end

&#x20;   B->>N: Načtení textu a ořezaná NLP analýza

&#x20;   N-->>B: Tokeny a kmeny slov

&#x20;   B->>B: Porovnání kmenů a vyříznutí snippetu

&#x20;   B-->>U: JSON výsledky se zvýrazněným HTML textem



```



\### Lingvistická analýza textu



Uživatel v pravé části rozhraní nahraje jakýkoliv lokální soubor formátu `.txt`. Po kliknutí na tlačítko "Analyzovat soubor" backend provede kompletní zpracování textu a okamžitě zobrazí základní kvantitativní metriky:



\* \*\*Počet slov:\*\* Celkový objem textu po očištění o interpunkci.

\* \*\*Velikost slovníku:\*\* Počet unikátních slovních forem (bohatost slovní zásoby).

\* \*\*Počet vět:\*\* Determinován pomocí spolehlivého pravidlového segmentátoru vět (`sentencizer`).



\---



\## Programátorská dokumentace



\### Požadavky a závislosti



Aplikace je postavena na \*\*Pythonu 3.12\*\*. Všechny externí knihovny jsou definovány v souboru `requirements.txt`:



\* `sanic` (v23.12.0) - Vysoce výkonný, asynchronní webový framework.

\* `spacy` (>=3.8.14) - Průmyslový standard pro NLP úlohy.

\* `cs-core-news-sm` - Český statistický model pro spaCy.

\* `pypdf` \& `python-docx` - Nástroje pro nízkoúrovňovou extrakci textu z binárních formátů.

\* `deep-translator` - Zajištění překladů pro bilingvní vyhledávání.

\* `click` - Podpora vnitřního CLI rozhraní pro spaCy v odlehčeném Linuxu.



\### Lokální instalace a spuštění (Vývojové prostředí)



1\. Nainstalujte závislosti:

```bash

pip install -r requirements.txt



```





2\. Spusťte server:

```bash

python app/app.py



```





3\. Otevřete prohlížeč na adrese: `http://localhost:8000`



\---



\## Popis REST API Protokolu



Aplikace plně implementuje specifikaci REST API. Všechny endpointy vrací data s hlavičkou `Content-Type: application/json`.



\### 1. `GET /api/browse-folder`



Vyvolá na hostitelském počítači nativní grafické okno pro výběr složky.



\* \*\*Vstup:\*\* Žádný

\* \*\*Úspěšná odpověď (200 OK):\*\*

```json

{ "folder": "C:\\\\Data\\\\PREDMETY\\\\ALG4\\\\data" }



```





\* \*\*Poznámka:\*\* V headless prostředích (např. Docker bez grafického rozhraní) funkce bezpečně selže a vrátí prázdný řetězec `""`.



\### 2. `GET /api/search`



Prohledá zadaný adresář na základě lingvistických pravidel.



\* \*\*Query parametry:\*\*

\* `query` (povinný) - Hledaný výraz (v uvozovkách pro exaktní shodu).

\* `folder` (nepovinný) - Absolutní cesta k adresáři. Pokud chybí, prohledává se interní složka `data`.





\* \*\*Úspěšná odpověď (200 OK):\*\*

```json

\[

&#x20; {

&#x20;   "filename": "kapitola1.txt",

&#x20;   "path": "C:\\\\data\\\\kapitola1.txt",

&#x20;   "preview": "\[Koncept: 'soldier']: ...byl to dobrý <mark class='bg-warning text-dark px-1 rounded'><strong>voják</strong></mark> Švejk..."

&#x20; }

]



```







\### 3. `POST /api/analyze`



Provede rychlou statistickou analýzu nahraného souboru.



\* \*\*Vstup:\*\* `Multipart/Form-Data` obsahující soubor v klíči `file`.

\* \*\*Úspěšná odpověď (200 OK):\*\*

```json

{

&#x20; "word\_count": 1452,

&#x20; "vocabulary\_size": 412,

&#x20; "sentence\_count": 89

}



```







\---



\## Deployment (Distribuce pomocí Dockeru)



Projekt je kompletně virtualizován a připraven pro okamžité nasazení na jakýkoliv server bez nutnosti ruční instalace Pythonu nebo jazykových modelů.



\### Sestavení Docker obrazu



```bash

docker build -t text-explorer-api .



```



\### Spuštění kontejneru (Jediný požadovaný příkaz)



Aplikaci nastartujete na standardním portu `8000` spuštěním tohoto příkazu v terminálu:



```bash

docker run -d -p 8000:8000 --name text-explorer text-explorer-api



```



Aplikace je následně okamžitě dostupná na adrese `http://localhost:8000`. Správu kontejneru (vypnutí, zapnutí, sledování využití RAM a procesoru) lze pohodlně provádět graficky v aplikaci \*\*Docker Desktop\*\*.



