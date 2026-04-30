# GraphRAG Lifecycle — Znalostní graf nad technickou dokumentací

Implementace životního cyklu znalostního grafu nad technickou dokumentací s využitím malých lokálních jazykových modelů. Systém kombinuje grafové a vektorové vyhledávání (GraphRAG) a je provozovatelný zcela lokálně bez závislosti na komerčních cloudových API.

---

## Architektura

![Architektura systému](docs/architecture.png)

**Integrační vrstva:** LangChain (`LLMGraphTransformer`, `Neo4jVector`, `ChatPromptTemplate`)  
**Lokální LLM:** Llama 3.1 8B přes Ollama  
**Inkrementální správa:** MD5 hashování chunků + PKL cache

---

## Instalace

### 1. Klonování repozitáře

```bash
git clone https://github.com/<tvuj-username>/graphrag-lifecycle-local.git
cd graphrag-lifecycle-local
```

### 2. Instalace závislostí

```bash
pip install -r requirements.txt
```

### 3. Konfigurace prostředí

Zkopíruj šablonu a vyplň přihlašovací údaje k Neo4j:

```bash
cp .env.example .env
```

Obsah `.env`:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### 4. Spuštění Neo4j

```bash
docker-compose up -d
```

### 5. Spuštění Ollama modelu

```bash
ollama pull llama3.1:8b
ollama serve
```

---

## Použití

### Konverze PDF na Markdown

Otevři a spusť `notebooks/md_converter.ipynb`.
Výstupní `.md` soubory ulož do složky `documents/`.

### Sestavení znalostního grafu a evaluace

Otevři `notebooks/graphrag_pipeline_eval_SF.ipynb` nebo `graphrag_pipeline_eval_PA.ipynb`.

Notebook obsahuje dvě části:

1. **Pipeline** (buňky 1–12) — načtení dokumentu, build grafu, indexy, retrievery, RAG chain
2. **Evaluace** (buňky 13+) — testovací sady, metriky (BERTScore, ROUGE-L, RAGAS)

### Streamlit aplikace

```bash
streamlit run app/app.py
```

Aplikace zpřístupňuje záložky:

- **PDF na Markdown** — konverze zdrojových dokumentů
- **Sestavení grafu** — inkrementální extrakce entit a vztahů
- **Dotazování** — hybridní GraphRAG pipeline s logem retrievalu

---

## Struktura projektu

```
graphrag-lifecycle-local/
├── app/
│   └── app.py                            # Streamlit aplikace
├── notebooks/
│   ├── md_converter.ipynb                # PDF -> Markdown konverze
│   ├── graphrag_pipeline_eval_SF.ipynb   # Pipeline + evaluace (Strojirenska firma)
│   └── graphrag_pipeline_eval_PA.ipynb   # Pipeline + evaluace (Planovani a analytika)
├── documents/                            # Zdrojove Markdown dokumenty
├── evaluation/
│   ├── evaluation_strojirenska_firma.csv
│   └── evaluation_planovani_pa.csv
├── neo4j/                                # Docker konfigurace Neo4j
├── docker-compose.yaml
├── requirements.txt
├── .env.example                          # Sablona konfigurace (bez hesel)
└── .gitignore
```

---

## Evaluace

Systém byl evaluován na dvou dokumentech z oblasti řízení výrobních podniků pomocí metrik:

| Metrika                | Popis                                      |
| ---------------------- | ------------------------------------------ |
| ROUGE-L                | Lexikální překryv s referenční odpovědí    |
| BERTScore              | Sémantická podobnost s referenční odpovědí |
| RAGAS Faithfulness     | Faktické ukotvení odpovědi v kontextu      |
| RAGAS Answer Relevancy | Relevance odpovědi vůči dotazu             |

Výsledky evaluace jsou dostupné ve složce `evaluation/`.

---

## Technologický stack

| Komponenta            | Technologie                          |
| --------------------- | ------------------------------------ |
| Lokální LLM           | Llama 3.1 8B (Ollama)                |
| Orchestrace           | LangChain                            |
| Grafová databáze      | Neo4j (Docker)                       |
| Extrakce grafu        | LLMGraphTransformer                  |
| Vektorové vyhledávání | Neo4jVector                          |
| Reranking             | CrossEncoder (sentence-transformers) |
| UI                    | Streamlit                            |
| PDF konverze          | Docling                              |
