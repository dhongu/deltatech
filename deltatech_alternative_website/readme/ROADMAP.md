# Roadmap

## Planificat

### Introducerea indexului HNSW și căutarea cu AI

- Adăugarea unui index **HNSW** (Hierarchical Navigable Small World) pe vectorii de embeddings ai produselor,
  folosind extensia `pgvector` din PostgreSQL, pentru căutare aproximativă rapidă (ANN).
- Generarea de embeddings pentru codurile alternative și descrierile produselor folosind un model AI
  (ex. OpenAI `text-embedding-ada-002` sau un model local compatibil).
- Integrarea unui endpoint de căutare semantică în website: utilizatorul introduce o descriere liberă,
  se calculează embedding-ul interogării și se returnează produsele cele mai similare via indexul HNSW.
- Fallback la căutarea exactică actuală (după cod echivalent) când nu există rezultate semantice relevante.
- Configurare parametrizabilă (cheie API, model, prag similaritate, număr rezultate) din setările Odoo.

### Arhitectura Pâlniei de Căutare (Search Pipeline)

În controlerul magazinului online Odoo (ruta `/shop`), logica de căutare este împărțită în **3 pași consecutivi**.
Sistemul trece la pasul următor doar dacă pasul anterior a returnat 0 rezultate.

```
[ Utilizatorul caută pe site: "DIN933" sau "40012893" ]
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│ PASUL 1: Căutare exactă în SQL (Index B-Tree)          │
│ Caută match 100% în default_code, barcode, alt_codes  │
└────────────────────────┬───────────────────────────────┘
                         │
                         ├─► [Găsit 1 sau mai multe] ──► Afișează instant (0ms AI consumat)
                         │
                         ▼ [0 Rezultate]
┌────────────────────────────────────────────────────────┐
│ PASUL 2: Căutare parțială / RegEx (SQL `ILIKE`)       │
│ Caută dacă codul introdus este conținut în coduri      │
│ (Ex: utilizatorul a scris doar "933" în loc de "DIN933")│
└────────────────────────┬───────────────────────────────┘
                         │
                         ├─► [Găsit] ──► Afișează rezultatele
                         │
                         ▼ [0 Rezultate]
┌────────────────────────────────────────────────────────┐
│ PASUL 3: Vector Search (Ollama / OpenAI + HNSW)        │
│ Rulează doar dacă codul nu a fost găsit deloc sau     │
│ dacă utilizatorul a combinat codul cu text             │
│ (Ex: "surub DIN933 m8")                                │
└────────────────────────────────────────────────────────┘
```

#### Configurarea PostgreSQL pentru Pasul 1 și Pasul 2

Pentru ca primele două etape (care preiau ~90% din căutările după coduri) să răspundă în mai puțin de 5ms,
PostgreSQL are nevoie de indecși clasici B-Tree și Trigram:

```sql
-- Index clasic B-Tree pentru potriviri perfecte (Pasul 1)
CREATE INDEX IF NOT EXISTS product_default_code_btree_idx ON product_product (default_code);
CREATE INDEX IF NOT EXISTS product_barcode_btree_idx ON product_product (barcode);

-- Index Trigram pentru căutări parțiale de coduri (Pasul 2)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS product_alt_codes_trgm_idx ON product_product USING gin (default_code gin_trgm_ops);
```

#### Rolul AI-ului (Vector Search + HNSW)

AI-ul devine esențial în cazurile hibride în care căutarea SQL clasică eșuează:

- **Cod + Text (Căutare mixtă)**: Clientul scrie `"placute frana 21465"` — AI-ul înțelege contextul semantic
  și folosește numărul pentru a îngusta selecția exact pe modelul căutat.
- **Formate diferite de scriere**: Codul salvat ca `SRB-M8-20`, căutat ca `SRB M8 20` sau `SRBM820` —
  vectorii lor sunt aproape identici în spațiul geometric, deci Vector Search returnează produsul corect.

#### Recomandare practică

- Păstrează căutarea SQL exactă ca **primă barieră** — preia tot traficul greu fără RAM sau timp Ollama/OpenAI.
- Configurează modulul AI să acționeze exclusiv ca **plasă de siguranță (Fallback Search)**:
  în loc de pagina frustrantă „0 rezultate", indexul HNSW returnează cele mai apropiate potriviri.

### Pre-Normalizarea Căutării (Fără apeluri AI costisitoare)

Înainte ca string-ul introdus de utilizator să fie căutat în cache sau trimis la AI, el trece printr-o funcție
Python locală care execută 3 operațiuni de curățare în mai puțin de **0.1 milisecunde**:

1. **Curățarea de bază (Lower & Strip)** — transformă totul în litere mici și șterge spațiile accidentale:
   `DIN933 ` ➔ `din933`

2. **Standardizarea separatorilor de coduri (Regex)** — înlocuiește toate caracterele speciale (spații, puncte,
   underscore) cu un separator unic (cratima), forțând toate variațiile unui cod să devină un string identic în cache:
   - `SRB M8 20` ➔ `srb-m8-20`
   - `SRB_M8_20` ➔ `srb-m8-20`
   - `srb.m8.20` ➔ `srb-m8-20`

3. **Eliminarea „zgomotului" (Stop Words)** — cuvinte precum *„caut"*, *„magazin"*, *„vreau"* sunt eliminate
   dintr-o listă predefinită, păstrând doar termenii relevanți pentru identificarea produsului.

#### Implementare Python în Odoo 19

```python
import re

def pre_normalize_search(search_text):
    if not search_text:
        return ""

    # 1. Litere mici și eliminare spații capete
    text = search_text.strip().lower()

    # 2. Eliminare cuvinte de zgomot specifice e-commerce-ului
    stop_words = {'caut', 'vreau', 'magazin', 'pret', 'ieftin', 'oferta', 'cumpar'}
    words = text.split()
    filtered_words = [w for w in words if w not in stop_words]
    text = " ".join(filtered_words)

    # 3. Dacă textul seamănă cu o căutare de cod (conține litere și cifre amestecate),
    # înlocuim spațiile, punctele sau underscore-urile cu o cratimă standard
    if any(char.isdigit() for char in text) and any(char.isalpha() for char in text):
        text = re.sub(r'[\s._\-]+', '-', text)

    return text
```

#### Arhitectura Finală cu Pre-Normalizare

```
[Utilizatorul scrie: "  SRB M8 20  "]
                │
                ▼
      ┌──────────────────┐
      │ PRE-NORMALIZARE  │ ➔ Transformă textul în formatul unic: "srb-m8-20"
      └──────────────────┘
                │
                ▼
   ┌─────────────────────────┐
   │ Verificare CACHE Local  │ ➔ Caută în `ai.query.cache` după cheia "srb-m8-20"
   └─────────────────────────┘
                │
        ┌───────┴───────┐
 [Găsit în Cache] [NEGĂSIT în Cache]
        │               │
        │               ▼
        │    ┌──────────────────────┐
        │    │ Apel AI (OpenAI/Oll) │ ➔ Generează vectorul DOAR pentru "srb-m8-20"
        │    └──────────────────────┘
        │               │
        │               ▼
        │    ┌──────────────────────┐
        │    │ Salvare în Cache     │ ➔ Memorează rezultatul pentru viitor
        │    └──────────────────────┘
        │               │
        └───────┬───────┘
                │
                ▼
   ┌─────────────────────────┐
   │ Căutare Vector (HNSW)   │ ➔ Rulează query-ul în cele 100.000 de produse
   └─────────────────────────┘
```

#### Beneficiul pre-normalizării asupra cache-ului

Dacă 50 de clienți scriu același cod în 50 de formate diferite (`DIN 933`, `din.933`, `DIN_933`),
funcția de pre-normalizare le transformă pe toate în **`din-933`**. Primul client generează apelul AI
și salvează vectorul; toți ceilalți **iau vectorul direct din cache**, crescând eficiența cache-ului
de la ~70% la **peste 95%** și menținând latența sub 15–20 ms pentru utilizatorii de pe site.
