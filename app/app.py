"""
GraphRAG Streamlit App
==========================================
Kombinuje:
  1. md_converter.ipynb  → PDF → MD konverze (záložka "PDF → Markdown")
  2. prototype_rankingV2 → MD → PKL → Neo4j → RAG dotazování + yFiles graf
"""

import os
import sys
import re
import io
import time
import hashlib
import pickle
import tempfile
import traceback
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st

# Load environment variables from .env file
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GraphRAG | Znalostní graf",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS  (industrial / dark-steel aesthetic)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ── BACKGROUND ── */
.stApp { background: #0d0f14; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #111318 !important;
    border-right: 1px solid #2a2d36;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: #8b9ab0 !important; font-size: 0.75rem; letter-spacing: .08em; text-transform: uppercase; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #111318;
    border-bottom: 1px solid #2a2d36;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #5a6478;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: .06em;
    padding: 0.7rem 1.6rem;
    border-radius: 0 !important;
    border-right: 1px solid #2a2d36;
}
.stTabs [aria-selected="true"] {
    color: #e8c840 !important;
    background: #0d0f14 !important;
    border-bottom: 2px solid #e8c840 !important;
}

/* ── CARDS / CONTAINERS ── */
.card {
    background: #13161d;
    border: 1px solid #252830;
    border-radius: 4px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.card-title {
    color: #e8c840;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: .12em;
    text-transform: uppercase;
    margin-bottom: .6rem;
}

/* ── STATUS BADGES ── */
.badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: .05em;
    padding: 2px 10px;
    border-radius: 2px;
    margin-right: 6px;
}
.badge-ok   { background: #1a3a1e; color: #4caf50; border: 1px solid #2e5e32; }
.badge-warn { background: #3a2e0a; color: #e8c840; border: 1px solid #5e4e12; }
.badge-err  { background: #3a0a0a; color: #f44336; border: 1px solid #5e1e1e; }
.badge-info { background: #0a1f3a; color: #42a5f5; border: 1px solid #1a3a5e; }

/* ── BUTTONS ── */
.stButton > button {
    background: #1c1f28 !important;
    color: #e8c840 !important;
    border: 1px solid #e8c840 !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: .06em !important;
    transition: all .15s ease;
}
.stButton > button:hover {
    background: #e8c840 !important;
    color: #0d0f14 !important;
}

/* ── TEXT AREAS / INPUTS ── */
.stTextArea textarea, .stTextInput input {
    background: #13161d !important;
    color: #c8d0e0 !important;
    border: 1px solid #2a2d36 !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #e8c840 !important;
    box-shadow: 0 0 0 1px #e8c840 !important;
}

/* ── PROGRESS / EXPANDERS ── */
.stExpander { border: 1px solid #252830 !important; border-radius: 4px !important; }
.stExpander header { background: #13161d !important; color: #8b9ab0 !important; }

/* ── LOG BOX ── */
.log-box {
    background: #080a0d;
    border: 1px solid #1e2128;
    border-radius: 3px;
    padding: 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.74rem;
    color: #6a7a8a;
    max-height: 380px;
    overflow-y: auto;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
.log-box .ok   { color: #4caf50; }
.log-box .warn { color: #e8c840; }
.log-box .err  { color: #f44336; }
.log-box .info { color: #42a5f5; }

/* ── ANSWER BOX ── */
.answer-box {
    background: #0f1520;
    border-left: 3px solid #e8c840;
    padding: 1.2rem 1.4rem;
    border-radius: 0 4px 4px 0;
    color: #d0dcea;
    font-size: 0.9rem;
    line-height: 1.75;
    white-space: pre-wrap;
}

/* ── METRICS ── */
[data-testid="metric-container"] {
    background: #13161d;
    border: 1px solid #252830;
    border-radius: 4px;
    padding: .7rem 1rem;
}
[data-testid="metric-container"] label { color: #5a6478 !important; font-size: 0.7rem !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e8c840 !important; font-family: 'IBM Plex Mono', monospace !important; }

/* ── HEADERS ── */
h1 { color: #e8c840 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 1.4rem !important; letter-spacing: .04em; }
h2 { color: #c8d0e0 !important; font-size: 1.1rem !important; }
h3 { color: #8b9ab0 !important; font-size: 0.95rem !important; }
p, li { color: #8b9ab0; }

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: #13161d;
    border: 1px dashed #2a2d36;
    border-radius: 4px;
}

/* ── SELECTBOX ── */
.stSelectbox [data-baseweb="select"] > div {
    background: #13161d !important;
    border: 1px solid #2a2d36 !important;
    color: #c8d0e0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ── DIVIDER ── */
hr { border-color: #1e2128 !important; }

/* ── GRAPH IFRAME ── */
.graph-frame {
    border: 1px solid #252830;
    border-radius: 4px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## GraphRAG")
    st.markdown("<p style='color:#5a6478;font-size:.75rem;letter-spacing:.08em;'>Znalostní graf nad technickou dokumentací</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("<p class='badge badge-info'>NEO4J</p>", unsafe_allow_html=True)
    neo4j_uri  = st.text_input("URI",      value=os.getenv("NEO4J_URI",      "bolt://localhost:7687"), key="neo4j_uri")
    neo4j_user = st.text_input("Username", value=os.getenv("NEO4J_USERNAME", "neo4j"),                 key="neo4j_user")
    neo4j_pass = st.text_input("Password", value=os.getenv("NEO4J_PASSWORD", "your_password"),         type="password", key="neo4j_pass")

    st.divider()
    st.markdown("<p class='badge badge-info'>OLLAMA</p>", unsafe_allow_html=True)
    ollama_model    = st.text_input("LLM model",       value="llama3.1:8b",       key="llm_model")
    embedding_model = st.text_input("Embedding model", value="nomic-embed-text",  key="emb_model")

    st.divider()
    cache_file = st.text_input(
        "PKL cache soubor (optional)",
        value="",
        placeholder="strojirenska_firma.pkl - pokud prázdné, auto z MD",
        key="cache_file",
        help="Pokud necháš prázdné, automaticky se vygeneruje z názvu MD souboru"
    )
    
    st.divider()
    st.markdown("<p class='badge badge-info'>PERFORMANCE</p>", unsafe_allow_html=True)
    
    # ── RAM check ─────────────────────────────────────────────────────────────
    available_ram_gb = None
    try:
        import psutil
        available_ram_gb = psutil.virtual_memory().available / (1024**3)
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        
        if available_ram_gb > 10:
            ram_badge = "badge-ok"
            ram_color = "✅"
        elif available_ram_gb > 8:
            ram_badge = "badge-warn"
            ram_color = "⚠️"
        else:
            ram_badge = "badge-err"
            ram_color = "❌"
        
        st.markdown(
            f'<div class="card">'
            f'<span class="badge {ram_badge}">{ram_color} RAM: {available_ram_gb:.1f}GB / {total_ram_gb:.1f}GB</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    except ImportError:
        st.markdown('<span class="badge badge-warn">⚠️ psutil chybí — install pro RAM monitoring</span>', unsafe_allow_html=True)
    
    max_workers_override = st.slider(
        "Max Workers (LLM extraction)",
        min_value=1,
        max_value=4,
        value=1,
        step=1,
        help="Paralelní workers pro LLM extrakci chunků. 1=sekvenčně (bezpečné), 2=paralelně (2x rychleji, více RAM). Default: auto-detect dle dostupné RAM.",
        key="max_workers_slider"
    )
    st.caption("1 worker — sekvenční zpracování | 2+ workers — 2–3× rychlejší, vyšší nároky na RAM")

    st.divider()
    if st.button("🧹 Vymazat Neo4j DB", use_container_width=True, key="clear_db"):
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            driver.close()
            st.sidebar.success("✅ Neo4j DB vymazána!")
        except Exception as e:
            st.sidebar.error(f"❌ Chyba: {e}")

    st.divider()
    st.markdown("<p style='color:#2a2d36;font-size:.68rem;text-align:center'>IBM Plex · Neo4j · Ollama · yFiles</p>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: stream log messages to a st.empty placeholder
# ─────────────────────────────────────────────────────────────────────────────
class StreamlitLogger:
    """Collects log lines and renders them in a styled box."""
    def __init__(self, placeholder):
        self._ph = placeholder
        self._lines: list[str] = []

    def _colorize(self, msg: str) -> str:
        if msg.startswith("✅") or msg.startswith("🟢"):
            return f'<span class="ok">{msg}</span>'
        if msg.startswith("⚠️") or msg.startswith("🟡"):
            return f'<span class="warn">{msg}</span>'
        if msg.startswith("❌") or msg.startswith("🔴"):
            return f'<span class="err">{msg}</span>'
        if msg.startswith("🔍") or msg.startswith("ℹ️") or msg.startswith("📊"):
            return f'<span class="info">{msg}</span>'
        return msg

    def log(self, msg: str):
        self._lines.append(self._colorize(str(msg)))
        html = "<br>".join(self._lines[-120:])
        self._ph.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)

    def clear(self):
        self._lines = []
        self._ph.empty()


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_pdf, tab_graph, tab_query, tab_viz = st.tabs([
    "Konverze dokumentu",
    "Sestavení grafu",
    "Dotazování",
    "Vizualizace grafu",
])


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 1 — PDF → MARKDOWN  (md_converter.ipynb logic)
# ═══════════════════════════════════════════════════════════════════════════
with tab_pdf:
    st.markdown("### Konverze dokumentu")
    st.markdown("<p>Konverze zdrojového PDF dokumentu do strukturovaného formátu Markdown zachovávající hierarchii nadpisů a pořadí čtení.</p>", unsafe_allow_html=True)

    col_up, col_opt = st.columns([3, 2])
    with col_up:
        uploaded_pdf = st.file_uploader("Nahraj PDF dokument", type=["pdf"], key="pdf_upload")
    with col_opt:
        do_ocr   = st.checkbox("OCR",          value=False)
        do_table = st.checkbox("Extrakce tabulek",      value=True)
        st.markdown("")
        run_convert = st.button("▶  Spustit konverzi", use_container_width=True)

    log_ph_pdf = st.empty()
    logger_pdf = StreamlitLogger(log_ph_pdf)

    if run_convert:
        if uploaded_pdf is None:
            st.warning("Nejprve nahraj PDF soubor.")
        else:
            logger_pdf.clear()
            try:
                from docling.document_converter import DocumentConverter, PdfFormatOption
                from docling.datamodel.base_models import InputFormat
                from docling.datamodel.pipeline_options import PdfPipelineOptions
            except ImportError:
                st.error("❌  `docling` není nainstalováno. Spusť: `pip install docling`")
                st.stop()

            logger_pdf.log(f"Zahajuji konverzi: {uploaded_pdf.name}")

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(uploaded_pdf.read())
                tmp_path = tmp.name

            with st.spinner("Konvertuji PDF…  (může trvat minuty)"):
                try:
                    pipeline_options = PdfPipelineOptions()
                    pipeline_options.do_ocr             = do_ocr
                    pipeline_options.do_table_structure = do_table
                    pipeline_options.generate_page_images = False

                    converter = DocumentConverter(
                        format_options={
                            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                        }
                    )
                    result = converter.convert(tmp_path)
                    logger_pdf.log("✅ Docling konverze dokončena.")
                except Exception as e:
                    logger_pdf.log(f"❌ Chyba při konverzi: {e}")
                    st.stop()
                finally:
                    os.unlink(tmp_path)

            # ── Reading order export ──────────────────────────────────────────
            logger_pdf.log("Sestavuji markdown ve fyzickém pořadí čtení…")

            SKIP_LABELS = {'page_header', 'page_footer', 'page_number', 'footnote'}

            def export_with_reading_order(document):
                items = []
                for idx, (item, _level) in enumerate(document.iterate_items()):
                    if not (hasattr(item, 'prov') and item.prov):
                        continue
                    prov = item.prov[0]
                    label_val = item.label.value if hasattr(item.label, 'value') else str(item.label)
                    sort_y = -prov.bbox.b if label_val == 'figure' else -prov.bbox.t
                    items.append((prov.page_no, sort_y, idx, item))
                items.sort(key=lambda x: (x[0], x[1], x[2]))
                lines = []
                for _page, _y, _idx, item in items:
                    label_val = item.label.value if hasattr(item.label, 'value') else str(item.label)
                    if label_val in SKIP_LABELS:
                        continue
                    text = getattr(item, 'text', '').strip()
                    if label_val == 'section_header':
                        raw_level = getattr(item, 'level', 2)
                        try:
                            h = max(1, min(int(raw_level), 6))
                        except (TypeError, ValueError):
                            h = 2
                        if lines and lines[-1].strip() != '':
                            lines.append('')
                        lines.append(f"{'#' * h} {text}")
                        lines.append('')
                    elif label_val == 'title':
                        if lines and lines[-1].strip() != '':
                            lines.append('')
                        lines.append(f"# {text}")
                        lines.append('')
                    elif label_val == 'text':
                        if text:
                            lines.append(text)
                            lines.append('')
                    elif label_val == 'list_item':
                        if text:
                            lines.append(f"- {text}")
                    elif label_val == 'figure':
                        lines.append('<!-- image -->')
                        lines.append('')
                    elif label_val == 'table':
                        try:
                            lines.append(item.export_to_markdown(doc=document))
                        except Exception:
                            lines.append('<!-- table -->')
                        lines.append('')
                    elif label_val == 'caption':
                        if text:
                            lines.append(f"*{text}*")
                            lines.append('')
                    else:
                        if text:
                            lines.append(text)
                            lines.append('')
                return '\n'.join(lines)

            def fix_headers(text):
                lines = text.split('\n')
                fixed = []
                for line in lines:
                    if re.match(r'^\s*-\s+\d+\s+-\s*$', line):
                        continue
                    m_sub = re.match(r'^\s*-\s*[oO]\s+(.*)', line)
                    if m_sub:
                        fixed.append(f"    - {m_sub.group(1)}")
                        continue
                    m_hdr = re.match(r'^\s*(#+)\s+(.*)', line)
                    if m_hdr:
                        content = m_hdr.group(2).strip()
                        m_num = re.match(r'^((?:\d+\.)*\d+\.?)\s+(.*)', content)
                        m_let = re.match(r'^([A-Z]\.)\s+(.*)', content)
                        m_spc = re.match(r'^(Obsah|Závěr|Zdroje|Úvodní poznámky|Poznámky)', content, re.IGNORECASE)
                        if fixed and fixed[-1].strip() != '':
                            fixed.append('')
                        if m_num:
                            num = m_num.group(1)
                            title = m_num.group(2)
                            parts = [p for p in num.split('.') if p.strip()]
                            level = max(1, min(len(parts), 6))
                            fixed.append(f"{'#' * level} {num} {title}")
                        elif m_let or m_spc:
                            fixed.append(f"# {content}")
                        else:
                            fixed.append(f"**{content.strip('*')}**")
                        fixed.append('')
                    else:
                        fixed.append(line)
                joined = '\n'.join(fixed)
                return re.sub(r'\n{3,}', '\n\n', joined)

            def reorder_sections(text):
                heading_re = re.compile(r'^(#{1,6}\s+)((?:\d+\.)*\d+\.?)\s+', re.MULTILINE)
                positions = [(m.start(), m.group(2)) for m in heading_re.finditer(text)]
                if not positions:
                    return text
                preamble = text[:positions[0][0]]
                chunks = []
                for i, (start, num_str) in enumerate(positions):
                    end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
                    key = tuple(int(x) for x in num_str.rstrip('.').split('.') if x.strip())
                    chunks.append((key, text[start:end]))
                chunks.sort(key=lambda x: x[0])
                return preamble + ''.join(c for _, c in chunks)

            md_output = export_with_reading_order(result.document)
            logger_pdf.log("Opravuji úrovně hlaviček…")
            md_output = fix_headers(md_output)
            logger_pdf.log("Seřazuji případné přeskočené kapitoly…")
            md_output = reorder_sections(md_output)

            lines_count = len(md_output.splitlines())
            logger_pdf.log(f"✅ Hotovo!  {lines_count} řádků markdownu.")

            st.session_state["md_output"]   = md_output
            st.session_state["md_filename"] = Path(uploaded_pdf.name).stem + ".md"

    # ── Show result ──────────────────────────────────────────────────────────
    if "md_output" in st.session_state:
        md_text = st.session_state["md_output"]
        fname   = st.session_state["md_filename"]

        col_dl, col_stats = st.columns([1, 3])
        with col_dl:
            st.download_button(
                "⬇  Stáhnout Markdown",
                data=md_text.encode("utf-8"),
                file_name=fname,
                mime="text/markdown",
                use_container_width=True,
            )
        with col_stats:
            c1, c2, c3 = st.columns(3)
            c1.metric("Řádků",   len(md_text.splitlines()))
            c2.metric("Znaků",   f"{len(md_text):,}")
            c3.metric("Nadpisů", len(re.findall(r'^#+\s', md_text, re.MULTILINE)))

        with st.expander("📖 Náhled Markdownu (prvních 200 řádků)"):
            st.code("\n".join(md_text.splitlines()[:200]), language="markdown")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 2 — MD → GRAPH (prototype_rankingV2 cells 2-6)
# ═══════════════════════════════════════════════════════════════════════════
with tab_graph:
    st.markdown("### Sestavení znalostního grafu")
    st.markdown("<p>Upload existujícího <code>.md</code> souboru nebo použij výsledek z předchozí záložky.</p>", unsafe_allow_html=True)

    # Source selection — 3 options
    src_choice = st.radio(
        "Zdroj Markdownu",
        ["Cesta na disku", "Nahrát .md soubor", "Výsledek ze záložky Konverze dokumentu"],
        horizontal=False,
        key="md_source",
    )

    md_for_graph: str | None = None

    if src_choice.startswith("Cesta"):
        md_disk_path = st.text_input(
            "Absolutní nebo relativní cesta k .md souboru",
            placeholder="documents/md/AF_III_02_01__Strojirenska_Firma.md",
            key="md_disk_path",
        )
        if md_disk_path:
            if os.path.exists(md_disk_path):
                with open(md_disk_path, "r", encoding="utf-8") as _f:
                    md_for_graph = _f.read()
                st.session_state["md_output"]   = md_for_graph
                st.session_state["md_filename"] = Path(md_disk_path).name
                st.markdown(
                    f'<span class="badge badge-ok">✅ MD načten z disku — {len(md_for_graph):,} znaků, '
                    f'{len(md_for_graph.splitlines())} řádků</span>',
                    unsafe_allow_html=True,
                )
                # Show hash preview so user can verify alignment with PKL
                import hashlib as _hl
                sample_hash = _hl.md5(md_for_graph[:500].encode("utf-8")).hexdigest()
                st.markdown(
                    f'<span class="badge badge-info">MD5 prvních 500 B: <code>{sample_hash}</code></span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<span class="badge badge-err">❌ Soubor nenalezen: {md_disk_path}</span>',
                    unsafe_allow_html=True,
                )

    elif src_choice.startswith("Nahrát"):
        up_md = st.file_uploader("Nahraj .md soubor", type=["md"], key="md_upload_graph")
        if up_md:
            # Read raw bytes and decode — preserve original line endings
            raw_bytes = up_md.read()
            md_for_graph = raw_bytes.decode("utf-8")
            st.session_state["md_output"]   = md_for_graph
            st.session_state["md_filename"] = up_md.name
            st.markdown(
                f'<span class="badge badge-ok">✅ {len(md_for_graph):,} znaků načteno</span>',
                unsafe_allow_html=True,
            )

    else:  # záložka 1
        if "md_output" in st.session_state:
            md_for_graph = st.session_state["md_output"]
            st.markdown(
                f'<span class="badge badge-ok">✅ MD připraven z záložky Konverze dokumentu ({len(md_for_graph):,} znaků)</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="badge badge-warn">⚠️ Nejprve proveď konverzi v záložce 1</span>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Chunk params — MUST match notebook values for PKL cache hits ──────────
    st.markdown(
        '<div class="card"><span class="card-title">Shoda parametrů: </span>'
        'Chunk size a overlap musí odpovídat hodnotám použitým při generování PKL '
        '(výchozí hodnoty: chunk_size=4000, chunk_overlap=400). '
        'Při nesouladu dojde k cache miss a LLM extrakce se spustí znovu.</div>',
        unsafe_allow_html=True,
    )
    col_cs, col_co = st.columns(2)
    with col_cs:
        chunk_size    = st.number_input("Chunk size (znaky)",    min_value=500,  max_value=16000, value=4000, step=100, key="chunk_size")
    with col_co:
        chunk_overlap = st.number_input("Chunk overlap (znaky)", min_value=0,    max_value=4000,  value=400,  step=50,  key="chunk_overlap")

    # Show PKL stats before running so user can verify
    _cache_path_preview = cache_file if "cache_file" in st.session_state else "strojirenska_firma.pkl"
    if os.path.exists(_cache_path_preview):
        try:
            with open(_cache_path_preview, "rb") as _pf:
                _preview_cache = pickle.load(_pf)
            st.markdown(
                f'<span class="badge badge-ok">📁 PKL nalezen: <b>{len(_preview_cache)}</b> chunků v cache</span>',
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown('<span class="badge badge-warn">⚠️ PKL soubor nelze načíst</span>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<span class="badge badge-warn">📁 PKL nenalezen na cestě: <code>{_cache_path_preview}</code> — bude vytvořen</span>',
            unsafe_allow_html=True,
        )

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        run_graph = st.button("▶  Spustit zpracování grafu", use_container_width=True, key="run_graph")
    
    if "graph_paused" not in st.session_state:
        st.session_state["graph_paused"] = False
    if "graph_running" not in st.session_state:
        st.session_state["graph_running"] = False
    
    with col_btn2:
        if st.session_state.get("graph_running", False):
            if st.session_state.get("graph_paused", False):
                if st.button("▶️  Pokračovat", use_container_width=True, key="resume_graph"):
                    st.session_state["graph_paused"] = False
                    st.rerun()
            else:
                if st.button("⏸️  Pauza", use_container_width=True, key="pause_graph"):
                    st.session_state["graph_paused"] = True
                    st.rerun()

    log_ph_g = st.empty()
    logger_g = StreamlitLogger(log_ph_g)

    if run_graph:
        if md_for_graph is None:
            st.warning("Nejprve připrav Markdown (záložka 1 nebo upload).")
        else:
            st.session_state["graph_running"] = True
            logger_g.clear()

            # ── imports ──────────────────────────────────────────────────────
            try:
                from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
                from langchain_community.graphs import Neo4jGraph
                from langchain_experimental.llms.ollama_functions import OllamaFunctions
                from langchain_experimental.graph_transformers import LLMGraphTransformer
                from langchain_ollama import OllamaEmbeddings
                from langchain_community.vectorstores import Neo4jVector
                from neo4j import GraphDatabase
            except ImportError as e:
                st.error(f"❌ Chybí závislost: {e}")
                st.stop()

            # ── 1. SPLIT ─────────────────────────────────────────────────────
            logger_g.log("Dělím Markdown na chunky…")
            headers_to_split_on = [
                ("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3"),
                ("####", "Header 4"), ("#####", "Header 5"), ("######", "Header 6"),
            ]
            markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            md_header_splits  = markdown_splitter.split_text(md_for_graph)
            text_splitter     = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            all_documents     = text_splitter.split_documents(md_header_splits)

            documents = []
            for doc in all_documents:
                h1 = doc.metadata.get("Header 1", "").strip().lower()
                if "obsah" in h1 or "zdroje" in h1 or "literatura" in h1:
                    continue
                documents.append(doc)

            logger_g.log(f"Chunků celkem: {len(all_documents)} → po filtraci: {len(documents)}")

            # ── 2. HASH + NEO4J SYNC ─────────────────────────────────────────
            logger_g.log("Počítám hashe chunků…")
            def get_chunk_hash(text):
                return hashlib.md5(text.encode('utf-8')).hexdigest()

            for doc in documents:
                doc.metadata["hash"] = get_chunk_hash(doc.page_content)

            try:
                driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_pass)
                )
                with driver.session() as session:
                    result_neo = session.run("MATCH (d:Document) RETURN d.text AS text, d.hash AS hash")
                    records = list(result_neo)
                    neo4j_hashes = set()
                    updates = []
                    for record in records:
                        if record["hash"]:
                            neo4j_hashes.add(record["hash"])
                        elif record["text"]:
                            computed = get_chunk_hash(record["text"])
                            neo4j_hashes.add(computed)
                            updates.append({"text": record["text"], "hash": computed})
                    if updates:
                        logger_g.log(f"🔧 Opravuji {len(updates)} chybějících hashů v Neo4j…")
                        session.run("""
                        UNWIND $updates AS up
                        MATCH (d:Document {text: up.text})
                        SET d.hash = up.hash
                        """, {"updates": updates})

                current_hashes  = {doc.metadata["hash"] for doc in documents}
                obsolete_hashes = neo4j_hashes - current_hashes
                if obsolete_hashes:
                    logger_g.log(f"🗑️ Odstraňuji {len(obsolete_hashes)} zastaralých chunků z Neo4j…")
                    with driver.session() as session:
                        for h in obsolete_hashes:
                            session.run("MATCH (d:Document {hash: $hash}) DETACH DELETE d", {"hash": h})
                        session.run("""
                        MATCH (e)
                        WHERE (e:Hlavni_Pojem OR e:Proces_Cinnost OR e:Nastroj_System OR
                               e:Metrika_Parametr OR e:Subjekt_Role OR e:Kapitola OR e:Podkapitola)
                          AND NOT (e)--()
                        DELETE e
                        """)
                    neo4j_hashes -= obsolete_hashes
                driver.close()
                logger_g.log("✅ Neo4j synchronizace hotova.")
            except Exception as e:
                logger_g.log(f"⚠️ Neo4j nedostupné: {e}  — pokračuji s PKL only.")
                neo4j_hashes = set()

            # ── 3. PKL CACHE ─────────────────────────────────────────────────
            # Pokud sidebar PKL je prázdný → auto-generate z MD jména
            md_filename = st.session_state.get("md_filename", "")
            
            if not cache_file and md_filename:
                # Prázdný sidebar + máme MD jméno → auto-generate
                _cache_file = Path(md_filename).stem + ".pkl"
                logger_g.log(f"Auto-generated PKL: {_cache_file}")
            elif cache_file:
                # Uživatel zadal jméno → použij to
                _cache_file = cache_file
                logger_g.log(f"PKL z sidebaru: {_cache_file}")
            else:
                # Fallback - nejde generovat
                _cache_file = "default.pkl"
                logger_g.log(f"⚠️ Fallback PKL: {_cache_file}")
            
            local_cache: dict = {}
            if os.path.exists(_cache_file):
                with open(_cache_file, "rb") as f:
                    local_cache = pickle.load(f)

            obsolete_pkl = set(local_cache.keys()) - current_hashes
            if obsolete_pkl:
                logger_g.log(f"🧹 Čistím PKL cache: {len(obsolete_pkl)} starých záznamů…")
                for h in obsolete_pkl:
                    del local_cache[h]
                with open(_cache_file, "wb") as f:
                    pickle.dump(local_cache, f)

            missing_in_neo4j = [doc for doc in documents if doc.metadata.get("hash") not in neo4j_hashes]
            docs_for_llm     = [doc for doc in missing_in_neo4j if doc.metadata.get("hash") not in local_cache]

            logger_g.log(f"Celkem chunků v textu: {len(documents)}")
            logger_g.log(f"Z toho už je v Neo4j: {len(neo4j_hashes)}")
            logger_g.log(f"Z toho už předpočítáno v PKL: {len(local_cache)}")
            logger_g.log(f"Bude se přes LLM reálně počítat: {len(docs_for_llm)} chunků")

            # ── 4. LLM extraction — PARALELNÍ S FALLBACK NA SEKVENČNÍ ────────────
            # PKL se ukládá PO KAŽDÉM chunku → při pádu/restartu pokračuje tam kde skončilo
            if docs_for_llm:
                logger_g.log(f"Spouštím LLM extrakci pro {len(docs_for_llm)} chunků…")
                try:
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    import psutil
                    
                    llm_ex = OllamaFunctions(model=ollama_model, temperature=0, format="json", num_predict=4096)
                    universal_nodes = ["Hlavni_Pojem", "Proces_Cinnost", "Nastroj_System", "Metrika_Parametr", "Subjekt_Role"]
                    universal_rels  = ["SKLADA_SE_Z", "VYUZIVA", "MA_VLASTNOST", "PROVADI", "SOUVISI_S"]
                    llm_transformer = LLMGraphTransformer(llm=llm_ex, allowed_nodes=universal_nodes, allowed_relationships=universal_rels)

                    # ── Detekce max_workers dle RAM (nebo override ze slideru) ─────────
                    process = psutil.Process()
                    available_ram_gb = psutil.virtual_memory().available / (1024**3)
                    
                    # Pokud je nastavený slider na >1, použij to; jinak auto-detect
                    if st.session_state.get("max_workers_slider", 1) > 1:
                        max_workers = st.session_state.get("max_workers_slider", 1)
                        logger_g.log(f"RAM dostupné: {available_ram_gb:.1f}GB → override z slideru: {max_workers} workers")
                    else:
                        # Auto-detect (konzervativní: 10GB threshold místo 12GB)
                        if available_ram_gb > 10:
                            max_workers = 2
                            logger_g.log(f"RAM dostupné: {available_ram_gb:.1f}GB → auto-detect: 2 workers")
                        else:
                            max_workers = 1
                            logger_g.log(f"RAM dostupné: {available_ram_gb:.1f}GB → auto-detect: 1 worker (sekvenčně)")

                    # ── Worker function pro jeden chunk ────────────────────────────────────
                    def process_chunk(doc_idx_tuple):
                        doc, idx = doc_idx_tuple
                        doc_hash = doc.metadata["hash"]
                        try:
                            extracted = llm_transformer.convert_to_graph_documents([doc])
                            return (doc_hash, extracted[0] if extracted else None, None)
                        except Exception as ex:
                            return (doc_hash, None, str(ex))

                    # ── Paralelní processing s futures ──────────────────────────────────
                    prog_bar = st.progress(0, text="LLM extrakce…")
                    time_ph = st.empty()  # Pro ETA
                    completed = 0
                    start_time = time.time()
                    
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Odeslat všechny tasty
                        futures = {
                            executor.submit(process_chunk, (doc, i)): i 
                            for i, doc in enumerate(docs_for_llm)
                        }
                        
                        # Zpracovávat výsledky jak se vracejí
                        for future in as_completed(futures):
                            idx = futures[future]
                            doc_hash, result, error = future.result()
                            
                            if result is not None:
                                local_cache[doc_hash] = result
                                logger_g.log(f"  ✅ {idx+1}/{len(docs_for_llm)} (Hash: {doc_hash[:8]})")
                            elif error:
                                logger_g.log(f"  ❌ {idx+1}/{len(docs_for_llm)} - Chyba: {error[:100]}")
                            
                            # ✅ Uložit PKL po KAŽDÉM completním chunku
                            completed += 1
                            with open(_cache_file, "wb") as f:
                                pickle.dump(local_cache, f)
                            
                            # Update progress + ETA
                            progress_pct = completed / len(docs_for_llm)
                            elapsed = time.time() - start_time
                            if completed > 0:
                                rate = completed / elapsed  # chunks per second
                                remaining_chunks = len(docs_for_llm) - completed
                                eta_seconds = remaining_chunks / rate if rate > 0 else 0
                                eta_minutes = eta_seconds / 60
                                time_ph.markdown(f"⏱️ Elapsed: {elapsed/60:.1f}m | ETA: {eta_minutes:.1f}m | Rate: {rate:.2f} chunks/sec")
                            
                            prog_bar.progress(progress_pct, text=f"LLM: {completed}/{len(docs_for_llm)} ({progress_pct*100:.0f}%)")
                    
                    time_ph.empty()
                    prog_bar.empty()
                    total_time = time.time() - start_time
                    logger_g.log(f"✅ Extrakce dokončena ({len(local_cache)} v cache) za {total_time/60:.1f} minut. Paralelní mode: {max_workers} worker(s)")
                except ImportError:
                    logger_g.log("⚠️ psutil chybí — fallback na sekvenční mode")
                    # Fallback — existující sekvenční logika
                    try:
                        llm_ex = OllamaFunctions(model=ollama_model, temperature=0, format="json", num_predict=4096)
                        universal_nodes = ["Hlavni_Pojem", "Proces_Cinnost", "Nastroj_System", "Metrika_Parametr", "Subjekt_Role"]
                        universal_rels  = ["SKLADA_SE_Z", "VYUZIVA", "MA_VLASTNOST", "PROVADI", "SOUVISI_S"]
                        llm_transformer = LLMGraphTransformer(llm=llm_ex, allowed_nodes=universal_nodes, allowed_relationships=universal_rels)

                        prog = st.progress(0, text="LLM extrakce (sekvenční)…")
                        for i, doc in enumerate(docs_for_llm):
                            doc_hash = doc.metadata["hash"]
                            try:
                                extracted = llm_transformer.convert_to_graph_documents([doc])
                                if extracted:
                                    local_cache[doc_hash] = extracted[0]
                                    with open(_cache_file, "wb") as f:
                                        pickle.dump(local_cache, f)
                            except Exception as ex:
                                logger_g.log(f"    ❌ Chyba při zpracování chunku {i+1}: {ex}")
                            prog.progress((i + 1) / len(docs_for_llm), text=f"LLM: {i+1}/{len(docs_for_llm)}")
                        prog.empty()
                        logger_g.log("✅ Extrakce dokončena (sekvenční).")
                    except Exception as e:
                        logger_g.log(f"⚠️ Ollama nedostupná: {e}")
                except Exception as e:
                    logger_g.log(f"⚠️ Chyba paralelního modu: {e} — fallback na sekvenční…")
            else:
                # Identické else větve jako v notebooku
                if missing_in_neo4j:
                    logger_g.log("✅ LLM není potřeba, všechna chybějící data načtena z lokálního PKL souboru!")
                else:
                    logger_g.log("✅ LLM není potřeba, všechna data už jsou v Neo4j.")

            # ── 5. Upload to Neo4j ────────────────────────────────────────────
            new_graph_docs = [local_cache[doc.metadata["hash"]] for doc in missing_in_neo4j if doc.metadata.get("hash") in local_cache]
            if new_graph_docs:
                logger_g.log(f"Nahrávání {len(new_graph_docs)} dokumentů do Neo4j…")
                try:
                    graph = Neo4jGraph(url=neo4j_uri, username=neo4j_user, password=neo4j_pass)
                    graph.add_graph_documents(new_graph_docs, baseEntityLabel=True, include_source=True)
                    logger_g.log("✅ Dokumenty nahrány do Neo4j.")
                except Exception as e:
                    logger_g.log(f"⚠️ Nahrání do Neo4j selhalo: {e}")

            # ── 6. Chapter hierarchy ──────────────────────────────────────────
            logger_g.log("📖 Buduji hierarchii kapitol v Neo4j…")
            try:
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                with driver.session() as session:
                    for doc in documents:
                        chunk_hash = doc.metadata.get("hash")
                        path_nodes = []
                        current_path_id = ""
                        for i in range(1, 7):
                            h = doc.metadata.get(f"Header {i}")
                            if h:
                                current_path_id = f"{current_path_id} | {h}" if current_path_id else h
                                path_nodes.append({"id": current_path_id, "name": h, "level": i})
                        if not path_nodes:
                            path_nodes = [{"id": "Obecné", "name": "Obecné", "level": 1}]
                        for i, item in enumerate(path_nodes):
                            session.run("MERGE (k:Kapitola {id: $id}) SET k.nazev = $name, k.uroven = $level",
                                        {"id": item["id"], "name": item["name"], "level": item["level"]})
                            if i > 0:
                                parent_item = path_nodes[i - 1]
                                session.run("""
                                MATCH (parent:Kapitola {id: $parent_id})
                                MATCH (child:Kapitola {id: $child_id})
                                MERGE (parent)-[:OBSAHUJE_PODKAPITOLU]->(child)
                                """, {"parent_id": parent_item["id"], "child_id": item["id"]})
                        leaf_item = path_nodes[-1]
                        session.run("""
                        MATCH (d:Document {hash: $hash})
                        MATCH (k:Kapitola {id: $leaf_id})
                        MERGE (k)-[:OBSAHUJE_TEXT]->(d)
                        """, {"hash": chunk_hash, "leaf_id": leaf_item["id"]})
                driver.close()
                logger_g.log("✅ Hierarchie kapitol vytvořena.")
            except Exception as e:
                logger_g.log(f"⚠️ Hierarchie kapitol selhala: {e}")

            # ── 7. Vector + Fulltext index ────────────────────────────────────
            logger_g.log("🔢 Vytvářím vektorový index (embeddings)…")
            try:
                from langchain_ollama import OllamaEmbeddings
                from langchain_community.vectorstores import Neo4jVector

                embeddings = OllamaEmbeddings(model=embedding_model, num_ctx=8192)

                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                with driver.session() as session:
                    result_emb = session.run("MATCH (d:Document) WHERE d.embedding IS NULL RETURN d.id as id, d.text as text")
                    nodes_emb = [{"id": r["id"], "text": r["text"]} for r in result_emb]

                if nodes_emb:
                    logger_g.log(f"  Počítám embeddingy pro {len(nodes_emb)} uzlů…")
                    prog2 = st.progress(0, text="Embeddingy…")
                    prog_ph = st.empty()
                    with driver.session() as session:
                        for i, node in enumerate(nodes_emb):
                            if st.session_state.get("graph_paused", False):
                                logger_g.log("⏸️ Zpracování pozastaveno…")
                                prog_ph.markdown('<span style="color:#e8c840;font-weight:bold">⏳ Čeká se na obnovení...</span>')
                                while st.session_state.get("graph_paused", False):
                                    time.sleep(0.5)
                                logger_g.log("▶️ Zpracování pokračuje…")
                                prog_ph.empty()
                            try:
                                vector = embeddings.embed_query(node["text"][:8000])
                                session.run("MATCH (d:Document {id: $id}) SET d.embedding = $vector",
                                            {"id": node["id"], "vector": vector})
                            except Exception as ex:
                                logger_g.log(f"  ⚠️ Embedding chyba u {node['id']}: {ex}")
                            prog2.progress((i + 1) / len(nodes_emb), text=f"Embedding {i+1}/{len(nodes_emb)}")
                        session.run("""
                            CREATE VECTOR INDEX vector IF NOT EXISTS
                            FOR (m:Document) ON (m.embedding)
                            OPTIONS {indexConfig: {
                              `vector.dimensions`: 768,
                              `vector.similarity_function`: 'cosine'
                            }}
                        """)
                    prog2.empty()
                    logger_g.log("✅ Vektorový index vytvořen.")
                else:
                    logger_g.log("✅ Všechny embeddingy už existují.")
                driver.close()

                # Fulltext index
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                with driver.session() as session:
                    # IDENTICKÉ s notebookem buňka 5:
                    # Index je nad __Entity__|Kapitola|Podkapitola, NIKOLI nad Document
                    # a pouze nad [id, nazev] — ne nad [text]!
                    session.run("DROP INDEX fulltext_entity_id IF EXISTS")
                    session.run("""
                    CREATE FULLTEXT INDEX fulltext_entity_id IF NOT EXISTS
                    FOR (n:__Entity__|Kapitola|Podkapitola)
                    ON EACH [n.id, n.nazev]
                    """)
                    # "keyword" fulltext index nad Document.text — nutný pro hybrid vector search
                    # Notebook ho vytváří implicitně přes Neo4jVector.from_existing_graph()
                    # My ho musíme vytvořit explicitně protože nepoužíváme from_existing_graph
                    session.run("DROP INDEX keyword IF EXISTS")
                    session.run("""
                    CREATE FULLTEXT INDEX keyword IF NOT EXISTS
                    FOR (n:Document)
                    ON EACH [n.text]
                    """)
                driver.close()
                logger_g.log("✅ Fulltextový index (fulltext_entity_id + keyword) vytvořen.")
            except Exception as e:
                logger_g.log(f"⚠️ Indexování selhalo: {e}")

            st.session_state["graph_ready"] = True
            st.session_state["graph_running"] = False
            logger_g.log("Zpracování dokončeno. Přejdi na záložku Dotazování.")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 3 — RAG DOTAZOVÁNÍ
# ═══════════════════════════════════════════════════════════════════════════
with tab_query:
    st.markdown("### Dotazování")
    st.markdown("<p>Dotazování nad znalostním grafem s volbou retrieval strategie.</p>", unsafe_allow_html=True)

    retrieval_mode = st.selectbox(
        "Retrieval strategie",
        ["3. Hybrid GraphRAG", "1. Naive RAG", "2. Graph RAG"],
        key="retrieval_mode",
    )

    question = st.text_area("Dotaz", placeholder="Jaké jsou klíčové aktivity v evidenci TPV?", height=80, key="question")
    
    if "query_paused" not in st.session_state:
        st.session_state["query_paused"] = False
    if "query_running" not in st.session_state:
        st.session_state["query_running"] = False
    
    col_query_btn, col_query_pause = st.columns([2, 1])
    with col_query_btn:
        run_query = st.button("🔍  Odeslat dotaz", use_container_width=True, key="run_query")
    
    with col_query_pause:
        if st.session_state.get("query_running", False):
            if st.session_state.get("query_paused", False):
                if st.button("▶️  Pokračovat", use_container_width=True, key="resume_query"):
                    st.session_state["query_paused"] = False
                    st.rerun()
            else:
                if st.button("⏸️  Pauza", use_container_width=True, key="pause_query"):
                    st.session_state["query_paused"] = True

    log_ph_q = st.empty()
    logger_q  = StreamlitLogger(log_ph_q)

    if run_query:
        if not question.strip():
            st.warning("Zadej dotaz.")
        else:
            st.session_state["query_running"] = True
            logger_q.clear()
            try:
                from langchain_community.graphs import Neo4jGraph
                from langchain_experimental.llms.ollama_functions import OllamaFunctions
                from langchain_ollama import OllamaEmbeddings, ChatOllama
                from langchain_community.vectorstores import Neo4jVector
                from langchain_core.runnables import RunnablePassthrough
                from langchain_core.output_parsers import StrOutputParser
                from langchain_core.prompts import ChatPromptTemplate
                from pydantic import BaseModel, Field
                from neo4j import GraphDatabase
                import re as _re
            except ImportError as e:
                st.error(f"❌ Chybí závislost: {e}")
                st.stop()

            # ── Init ─────────────────────────────────────────────────────────
            graph = Neo4jGraph(url=neo4j_uri, username=neo4j_user, password=neo4j_pass)
            embeddings = OllamaEmbeddings(model=embedding_model, num_ctx=8192)
            llm_rag    = ChatOllama(model=ollama_model, temperature=0, num_ctx=32768)
            # IDENTICKÉ s notebookem buňka 8:
            # llm_extraction = OllamaFunctions(model=..., temperature=0, format="json")
            # BEZ num_predict — to je pouze pro LLM transformer v záložce 2
            llm_ex  = OllamaFunctions(model=ollama_model, temperature=0, format="json")

            # ── Cross-encoder ────────────────────────────────────────────────
            try:
                from sentence_transformers import CrossEncoder
                reranker = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
                RERANKER_AVAILABLE = True
                logger_q.log("✅ Cross-encoder načten.")
            except ImportError:
                RERANKER_AVAILABLE = False
                logger_q.log("⚠️ sentence-transformers chybí — reranking přeskočen.")

            def rerank_docs(q, docs, top_k=10):
                if not docs or not RERANKER_AVAILABLE:
                    return docs[:top_k]
                texts  = [d.page_content if hasattr(d, "page_content") else d for d in docs]
                scores = reranker.predict([(q, t) for t in texts])
                ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
                
                # Debug logging (identické jako v notebooku)
                logger_q.log(f"  Reranking ({len(docs)} docs → top {top_k}):")
                for rank_i, (score, doc) in enumerate(ranked, 1):
                    text = doc.page_content if hasattr(doc, "page_content") else doc
                    preview = text[:120].replace("\n", " ")
                    marker = "✅" if rank_i <= top_k else "❌"
                    logger_q.log(f"  {marker} #{rank_i:<3} {score:>7.3f}  {preview}...")
                
                return [d for _, d in ranked[:top_k]]

            # ── Vector index ─────────────────────────────────────────────────
            vector_retriever = None
            try:
                logger_q.log("Inicializuji vektorový index…")
                neo4j_dense_index = Neo4jVector.from_existing_index(
                    embeddings,
                    index_name="vector",
                    search_type="vector",
                    node_label="Document",
                    text_node_property="text",
                )
                dense_retriever = neo4j_dense_index.as_retriever(search_kwargs={"k": 20})
                vector_retriever = dense_retriever  # alias — zbytek kódu funguje beze změny

                # 2. Hybrid Retriever — pro Hybrid GraphRAG
                neo4j_hybrid_index = Neo4jVector.from_existing_index(
                    embeddings,
                    index_name="vector",
                    search_type="hybrid",
                    keyword_index_name="keyword",
                    node_label="Document",
                    text_node_property="text",
                )
                hybrid_retriever = neo4j_hybrid_index.as_retriever(search_kwargs={"k": 20})
                logger_q.log("✅ Vektorový index inicializován.")
            except Exception as e:
                logger_q.log(f"⚠️ Neo4jVector selhání: {str(e)[:300]}")
                # Ultra fallback: manual vector search via Cypher
                # This is slower but works if index is completely broken
                logger_q.log("Používám manuální vektorové vyhledávání (fallback)…")
                
                class ManualVectorRetriever:
                    def __init__(self, embeddings, driver, k=20):
                        self.embeddings = embeddings
                        self.driver = driver
                        self.k = k
                    
                    def invoke(self, question):
                        try:
                            q_vec = self.embeddings.embed_query(question)
                            query = """
                            MATCH (d:Document) WHERE d.embedding IS NOT NULL
                            WITH d, vector.similarity.cosine(d.embedding, $q_vec) as score
                            RETURN d.text as text, score
                            ORDER BY score DESC LIMIT $k
                            """
                            with self.driver.session() as session:
                                result = session.run(query, {"q_vec": q_vec, "k": self.k})
                                docs = []
                                for rec in result:
                                    # Return as simple objects with page_content attribute
                                    class SimpleDoc:
                                        def __init__(self, text):
                                            self.page_content = text
                                    docs.append(SimpleDoc(rec['text']))
                                return docs
                        except Exception as ex:
                            logger_q.log(f"  ❌ Manuální vyhledávání chyba: {ex}")
                            return []
                
                try:
                    driver_dbg = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                    vector_retriever = ManualVectorRetriever(embeddings, driver_dbg, k=20)
                    logger_q.log("✅ Manuální retriever inicializován.")
                except Exception as manual_err:
                    logger_q.log(f"⚠️ Manuální retriever také selhal: {manual_err}")
                    vector_retriever = None
                
                # Debug info
                try:
                    driver_dbg = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                    with driver_dbg.session() as sess_dbg:
                        idx_result = sess_dbg.run("SHOW INDEXES")
                        idx_list = list(idx_result)
                        logger_q.log(f"  Indexy v Neo4j: {[r.get('name') for r in idx_list]}")
                        
                        doc_result = sess_dbg.run("MATCH (d:Document) RETURN count(*) as cnt, sum(CASE WHEN d.embedding IS NOT NULL THEN 1 ELSE 0 END) as with_emb")
                        for rec in doc_result:
                            logger_q.log(f"  Dokumentů: {rec['cnt']}, s embeddingy: {rec['with_emb']}")
                    driver_dbg.close()
                except Exception as dbg_e:
                    logger_q.log(f"  ❌ Debug check selhal: {dbg_e}")

            # ── Entity extraction ────────────────────────────────────────────
            class Entities(BaseModel):
                names: list[str] = Field(
                    ...,
                    description="Všechny klíčové pojmy, technické termíny, procesy a funkce. ZÁSADNÍ: Nesekej víceslovná spojení (např. 'funkce prediktivní analytiky', 'řízení dopravy') na jednotlivá slova!",
                )

            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", """Jsi expert na extrakci klíčových pojmů z odborných dotazů pro vyhledávání v databázi.
Tvým úkolem je z uživatelské otázky vyextrahovat hlavní entity.

ZÁSADNÍ PRAVIDLO: Odborné pojmy, víceslovné názvy, vlastnosti, metriky nebo procesy ponechávej v celku! Nesekej ustálená spojení na jednotlivá slova.

PŘÍKLADY SPRÁVNÉHO CHOVÁNÍ:
Otázka: "Co je to sekvenční diagram?"
Entity: ["sekvenční diagram"]

Otázka: "Jaké jsou fáze buněčného dělení v biologii?"
Entity: ["fáze buněčného dělení", "biologie"]

Otázka: "Co patří pod funkce prediktivní analytiky v marketingu?"
Entity: ["funkce prediktivní analytiky v marketingu"]

Otázka: "Jaké jsou výhody agilního řízení projektů?"
Entity: ["výhody agilního řízení projektů"]
"""),
                ("human", "{question}")
            ])
            entity_chain = extraction_prompt | llm_ex.with_structured_output(Entities)

            # ── Graph retriever ───────────────────────────────────────────────
            def graph_enhanced_retriever(q):
                try:
                    entities = entity_chain.invoke({"question": q})
                    logger_q.log(f"Entity: {entities.names}")
                    all_documents = []
                    seen_docs = set()
                    relations_text = ""
                    seen_relations = set()
                    search_queries = []

                    for entity in entities.names:
                        words = [w.lower() for w in entity.split() if len(w) >= 3]
                        if words:
                            search_queries.append(" AND ".join([f"*{w[:5]}*" for w in words]))

                    q_words = [w.lower() for w in _re.findall(r'\w+', q) if len(w) >= 3]
                    if q_words:
                        search_queries.append(" OR ".join([f"*{w[:5]}*" for w in q_words]))

                    search_queries = list(set(search_queries))

                    for lq in search_queries:
                        printed_nodes = set()
                        response = graph.query("""
                        CALL db.index.fulltext.queryNodes('fulltext_entity_id', $lucene_query, {limit: 5})
                        YIELD node
                        // Pokud je node rodič (má podkapitoly), NEjdi dolů — vezmi ho samotného
                        // Tím zamezíme přidání všech sourozeneckých podkapitol (8.8.6.1, 8.8.6.4...)
                        OPTIONAL MATCH (node)-[:OBSAHUJE_PODKAPITOLU]->(direct_child)
                        WITH node, count(direct_child) AS child_count
                        OPTIONAL MATCH (node)-[:OBSAHUJE_PODKAPITOLU*1..5]->(sub_k)
                            WHERE child_count = 0
                        OPTIONAL MATCH (parent_k:Kapitola)-[:OBSAHUJE_PODKAPITOLU*1..3]->(node)
                        WITH node,
                             collect(DISTINCT sub_k) + [node] + collect(DISTINCT parent_k) AS all_nodes
                        UNWIND all_nodes AS search_node
                        MATCH (doc:Document)
                        WHERE (doc)-[:MENTIONS]->(search_node) OR (search_node)-[:OBSAHUJE_TEXT]->(doc)
                        OPTIONAL MATCH (doc)-[:MENTIONS]->(kapitola_entity:__Entity__)
                        WHERE labels(node)[0] = 'Kapitola'
                        OPTIONAL MATCH (node)-[r]-(neighbor)
                        WHERE type(r) <> 'MENTIONS' AND type(r) <> 'OBSAHUJE_TEXT' AND type(r) <> 'OBSAHUJE_PODKAPITOLU'
                        RETURN DISTINCT
                            node.id AS entity_name,
                            labels(node)[0] AS node_type,
                            type(r) AS relation,
                            neighbor.id AS related_entity,
                            kapitola_entity.id AS podrizena_entita,
                            doc.text AS source_doc
                        LIMIT 50
                        """, {"lucene_query": lq})

                        for r in response:
                            node_name = r.get('entity_name')
                            node_type = r.get('node_type', 'Neznámý uzel')
                            rel = r.get('relation')
                            neighbor = r.get('related_entity')
                            podrizena_entita = r.get('podrizena_entita')
                            
                            if node_name not in printed_nodes:
                                logger_q.log(f"  Nalezen uzel [{node_type}]: '{node_name}'")
                                printed_nodes.add(node_name)
                            
                            if rel and neighbor:
                                rel_str = f"Položka '{neighbor}' (vztah ke '{node_name}': {rel})"
                                if rel_str not in seen_relations:
                                    relations_text += f"- {rel_str}\n"
                                    seen_relations.add(rel_str)
                            
                            if podrizena_entita:
                                sub_ent_str = f"Kapitola '{node_name}' obsahuje detailní pojem: '{podrizena_entita}'"
                                if sub_ent_str not in seen_relations:
                                    relations_text += f"- {sub_ent_str}\n"
                                    seen_relations.add(sub_ent_str)
                            
                            doc_text = r.get('source_doc')
                            if doc_text and doc_text not in seen_docs and len(doc_text) > 100:
                                all_documents.append(doc_text)
                                seen_docs.add(doc_text)

                    logger_q.log(f"✅ Graf: {len(all_documents)} dokumentů.")
                    return relations_text, all_documents
                except Exception as e:
                    logger_q.log(f"❌ Graf chyba: {e}")
                    return "", []

            # ── Retrieval strategy ────────────────────────────────────────────
            mode = retrieval_mode[0]  # "1", "2", or "3"

            with st.spinner("Vyhledávám a generuji odpověď…"):
                if mode == "1":
                    logger_q.log("Naive RAG — vektorové vyhledávání…")
                    docs = dense_retriever.invoke(question) if dense_retriever else []
                    context = "\n\n".join(d.page_content for d in docs[:25])

                elif mode == "2":
                    logger_q.log("Graph RAG…")
                    relations_text, graph_docs = graph_enhanced_retriever(question)
                    ranked = rerank_docs(question, graph_docs, top_k=10)
                    graph_text = "\n\n".join(d if isinstance(d, str) else d.page_content for d in ranked)
                    graph_text_pg   = graph_text[:8000]
                    relations_pg    = relations_text[:1500]
                    context = (f"### 1. DOKUMENTY Z GRAFU (PRIMÁRNÍ ZDROJ):\n{graph_text_pg}"
                            f"\n\n### 2. VZTAHY Z GRAFU:\n{relations_pg}")

                else:
                    logger_q.log("🔀 Hybrid GraphRAG…")
                    
                    # Vector retrieval
                    logger_q.log(f"Vektorové vyhledávání — dotaz: '{question[:80]}...'")
                    try:
                        if vector_retriever:
                            vector_docs = hybrid_retriever.invoke(question)
                            logger_q.log(f"  ✅ Vektor vrátil {len(vector_docs)} dokumentů")
                        else:
                            vector_docs = []
                            logger_q.log(f"  ⚠️ Vektor není dostupný (je None)")
                    except Exception as e:
                        logger_q.log(f"  ❌ Vektorové vyhledávání chyba: {str(e)[:300]}")
                        vector_docs = []
                    
                    # Graph retrieval
                    graph_rel, graph_docs = graph_enhanced_retriever(question)
                    
                    logger_q.log(f"Vektorové: {len(vector_docs)} dokumentů → reranking na 10…")
                    logger_q.log(f"Grafové: {len(graph_docs)} dokumentů → reranking na 10…")
                    
                    reranked_v = rerank_docs(question, vector_docs, top_k=10)
                    reranked_g = rerank_docs(question, graph_docs, top_k=10) if graph_docs else []
                    
                    logger_q.log(f"✅ Po rerankingu → vektor: {len(reranked_v)}, graf: {len(reranked_g)}")
                    
                    vector_text = "\n\n".join(d.page_content if hasattr(d, "page_content") else d for d in reranked_v)
                    graph_text  = "\n\n".join(d.page_content if hasattr(d, "page_content") else d for d in reranked_g)
                    graph_text_trimmed  = graph_text[:8000]
                    vector_text_trimmed = vector_text[:3000]
                    graph_rel_trimmed   = graph_rel[:1500]
                    
                    context = (f"### 1. DOKUMENTY Z GRAFU (PRIMÁRNÍ ZDROJ - ČTĚTE CELÉ, ODPOVĚĎ JE ZDE):\n{graph_text_trimmed}"
                               f"\n\n### 2. VEKTOROVÉ DOKUMENTY (Doplňující textový kontext):\n{vector_text_trimmed}"
                               f"\n\n### 3. VZTAHY Z GRAFU (Strukturální kontext):\n{graph_rel_trimmed}")
                    
                    logger_q.log(f"Context velikost: {len(context)} chars (graf_rel: {len(graph_rel)}, vektor: {len(vector_text)}, graf: {len(graph_text)})")

                # ── LLM answer ────────────────────────────────────────────────
                template = """

Jsi expertní analytický systém pracující s technickou dokumentací.

### KRITICKÁ PRAVIDLA:
1. ODPOVÍDEJ POUZE NA ZÁKLADĚ DODANÉHO KONTEXTU.
2. Pro výčty použij odrážkový seznam, pro definice odstavce.
3. KOMPLETNÍ VÝČET BEZ ZKRACOVÁNÍ — žádné "a další", "apod.", "atd.".

### KONTEXT:
{context}

### OTÁZKA:
{question}


### ODPOVĚĎ:"""

                try:
                    # Check pause before generating answer
                    if st.session_state.get("query_paused", False):
                        logger_q.log("⏸️ Generování pozastaveno…")
                        while st.session_state.get("query_paused", False):
                            time.sleep(0.5)
                        logger_q.log("▶️ Generování pokračuje…")
                    
                    final_prompt = template.format(context=context, question=question)
                    answer = llm_rag.invoke(final_prompt).content
                    st.session_state["last_answer"] = answer
                    logger_q.log("✅ Odpověď vygenerována.")
                except Exception as e:
                    logger_q.log(f"❌ LLM chyba: {e}")
                    answer = f"Chyba: {e}"
                finally:
                    st.session_state["query_running"] = False

    if "last_answer" in st.session_state:
        st.markdown("#### Odpověď")
        st.markdown(f'<div class="answer-box">{st.session_state["last_answer"]}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 4 — GRAPH VISUALIZATION (yFiles / fallback Plotly)
# ═══════════════════════════════════════════════════════════════════════════
with tab_viz:
    st.markdown("### Vizualizace grafu")

    col_q, col_lim = st.columns([4, 1])
    with col_q:
        cypher_query = st.text_area(
            "Cypher dotaz",
            value="MATCH (s)-[r]->(t) RETURN s, r, t LIMIT 200",
            height=90,
            key="cypher",
        )
    with col_lim:
        st.markdown("")
        run_viz = st.button("Vizualizovat", use_container_width=True, key="run_viz")

    log_ph_v = st.empty()
    logger_v  = StreamlitLogger(log_ph_v)

    if run_viz:
        logger_v.clear()
        try:
            from neo4j import GraphDatabase as _GD
            driver = _GD.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
            logger_v.log("Připojeno k Neo4j.")

            with driver.session() as session:
                result_viz = session.run(cypher_query)
                records = list(result_viz)

            driver.close()
            logger_v.log(f"✅ Načteno {len(records)} záznamů.")

            # ── Parse nodes + edges ──────────────────────────────────────────
            nodes_dict: dict = {}
            edges_list: list = {}
            edges_list = []

            for record in records:
                for key in record.keys():
                    val = record[key]
                    # Nodes
                    if hasattr(val, 'element_id') and hasattr(val, 'labels'):
                        nid = val.element_id
                        if nid not in nodes_dict:
                            props = dict(val.items())
                            label = list(val.labels)[0] if val.labels else "Node"
                            display = (
                                props.get("id") or
                                props.get("nazev") or
                                ("📄 " + props.get("text", "")[:35] + "…" if "text" in props else None) or
                                label
                            )
                            nodes_dict[nid] = {
                                "id":      nid,
                                "label":   str(display),
                                "type":    label,
                                "props":   props,
                            }
                    # Relationships
                    if hasattr(val, 'element_id') and hasattr(val, 'type'):
                        edges_list.append({
                            "source": val.start_node.element_id,
                            "target": val.end_node.element_id,
                            "label":  val.type,
                        })

            nodes_list = list(nodes_dict.values())
            logger_v.log(f"Uzlů: {len(nodes_list)}, hran: {len(edges_list)}")

            # ── yFiles Streamlit component (if available) ───────────────────
            yfiles_available = False
            try:
                from yfiles_graphs_for_streamlit import StreamlitGraphWidget, Node, Edge
                yfiles_available = True
            except ImportError:
                pass

            if yfiles_available:
                logger_v.log("✅ yFiles for Streamlit načten.")

                TYPE_COLORS = {
                    "Document":         "#4a90d9",
                    "Kapitola":         "#e8c840",
                    "Hlavni_Pojem":     "#4caf50",
                    "Proces_Cinnost":   "#f06292",
                    "Nastroj_System":   "#26c6da",
                    "Metrika_Parametr": "#ab47bc",
                    "Subjekt_Role":     "#ff7043",
                    "__Entity__":       "#78909c",
                }

                # Node objekty — label = lidsky čitelný, type uložen do properties
                nodes = [
                    Node(
                        id=n["id"],
                        properties={
                            "label": n["label"],
                            "type":  n["type"],
                        }
                    )
                    for n in nodes_list
                ]
                edges = [
                    Edge(start=e["source"], end=e["target"], properties={"label": e["label"]})
                    for e in edges_list
                ]

                # node_color_mapping — lambda dostane node dict s properties
                # properties["type"] obsahuje Neo4j label (Document, Kapitola, ...)
                node_color_mapping = lambda node: TYPE_COLORS.get(
                    node.get("properties", {}).get("type", ""), "#78909c"
                )

                # node_label_mapping — stejná logika jako notebook
                node_label_mapping = lambda node: node.get("properties", {}).get("label", "?")

                try:
                    StreamlitGraphWidget(
                        nodes,
                        edges,
                        node_color_mapping=node_color_mapping,
                        node_label_mapping=node_label_mapping,
                    ).show()
                    logger_v.log("✅ Graf zobrazován pomocí yFiles (s barvami).")
                except Exception as e:
                    logger_v.log(f"⚠️ yFiles render chyba: {e} — fallback na Plotly")
                    yfiles_available = False

            if not yfiles_available:
                import plotly.graph_objects as go
                import math, random

                # Simple force-like layout via circular + random
                random.seed(42)
                n = len(nodes_list)
                pos = {}
                for i, node in enumerate(nodes_list):
                    angle = 2 * math.pi * i / max(n, 1)
                    r = 1 + random.uniform(-0.3, 0.3)
                    pos[node["id"]] = (r * math.cos(angle), r * math.sin(angle))

                TYPE_COLORS_PLOTLY = {
                    "Document":        "#42a5f5",
                    "Kapitola":        "#e8c840",
                    "Hlavni_Pojem":    "#4caf50",
                    "Proces_Cinnost":  "#f06292",
                    "Nastroj_System":  "#26c6da",
                    "Metrika_Parametr":"#ab47bc",
                    "Subjekt_Role":    "#ff7043",
                    "__Entity__":      "#78909c",
                }

                edge_x, edge_y = [], []
                for e in edges_list:
                    if e["source"] in pos and e["target"] in pos:
                        x0, y0 = pos[e["source"]]
                        x1, y1 = pos[e["target"]]
                        edge_x += [x0, x1, None]
                        edge_y += [y0, y1, None]

                edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines',
                                        line=dict(width=0.6, color='#2a2d36'),
                                        hoverinfo='none')

                node_traces = []
                by_type: dict = {}
                for node in nodes_list:
                    t = node["type"]
                    by_type.setdefault(t, []).append(node)

                for t, grp in by_type.items():
                    xs = [pos[n["id"]][0] for n in grp if n["id"] in pos]
                    ys = [pos[n["id"]][1] for n in grp if n["id"] in pos]
                    lbls = [n["label"][:40] for n in grp if n["id"] in pos]
                    color = TYPE_COLORS_PLOTLY.get(t, "#78909c")
                    node_traces.append(go.Scatter(
                        x=xs, y=ys,
                        mode='markers+text',
                        text=lbls,
                        textposition="top center",
                        textfont=dict(size=7, color="#8b9ab0", family="IBM Plex Mono"),
                        marker=dict(size=8, color=color, line=dict(width=0.5, color="#0d0f14")),
                        name=t,
                        hovertext=lbls,
                        hoverinfo='text',
                    ))

                fig = go.Figure(
                    data=[edge_trace] + node_traces,
                    layout=go.Layout(
                        paper_bgcolor="#0d0f14",
                        plot_bgcolor="#0d0f14",
                        font=dict(color="#8b9ab0", family="IBM Plex Mono"),
                        showlegend=True,
                        legend=dict(bgcolor="#13161d", bordercolor="#252830", borderwidth=1,
                                    font=dict(size=9, color="#8b9ab0")),
                        hovermode='closest',
                        margin=dict(b=10, l=5, r=5, t=10),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        height=650,
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

            # ── Data table ───────────────────────────────────────────────────
            with st.expander(f"Tabulka uzlů ({len(nodes_list)})"):
                import pandas as pd
                df_nodes = pd.DataFrame([{"ID": n["id"], "Label": n["label"], "Typ": n["type"]} for n in nodes_list])
                st.dataframe(df_nodes, use_container_width=True, height=300)

        except Exception as e:
            logger_v.log(f"❌ Chyba vizualizace: {e}")
            st.error(traceback.format_exc())