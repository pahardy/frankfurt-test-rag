"""
app.py — Conversational web interface for the Frankfurt School RAG.
Usage: uv run streamlit run app.py
"""

import config
import os

import anthropic
import chromadb
import streamlit as st
from openai import OpenAI

from query import embed_question, retrieve, synthesise

CHROMA_DIR = "chroma_db"

FONTS_URL = "https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400;1,500&display=swap"

# (url, side, top_pct, delay_s) — images that drift in/out in the viewport margins
MARGIN_IMAGES = [
    ("https://upload.wikimedia.org/wikipedia/commons/8/87/Flammarion.jpg",                                                                       "left",  6,  0.0),
    ("https://upload.wikimedia.org/wikipedia/commons/c/cc/Walter_Benjamin_vers_1928.jpg",                                                        "left",  30, 7.5),
    ("https://upload.wikimedia.org/wikipedia/commons/7/76/Azoth-Sixth_woodcut.jpg",                                                              "left",  55, 15.0),
    ("https://upload.wikimedia.org/wikipedia/commons/6/6d/Atalanta_Fugiens_14_Ouroboros.jpg",                                                    "left",  74, 22.5),
    ("https://upload.wikimedia.org/wikipedia/commons/0/08/Hegel_portrait_by_Schlesinger_1831.jpg",                                               "right", 10, 3.75),
    ("https://upload.wikimedia.org/wikipedia/commons/2/2f/Fotothek_df_tg_0008255_Theosophie_%5E_Alchemie_%5E_Hermetik_%28cropped%29.jpg",        "right", 34, 11.25),
    ("https://upload.wikimedia.org/wikipedia/commons/4/48/Theodor_Ludwig_Wiesengrund_Adorno.jpg",                                                "right", 57, 18.75),
    ("https://upload.wikimedia.org/wikipedia/commons/a/ad/Michael_Maier_Atalanta_Fugiens_Emblem_21.jpeg",                                        "right", 77, 26.25),
]

st.set_page_config(
    page_title="Western Esotericism & Critical Theory",
    page_icon="⚗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS injected into the parent document via JS ───────────────────────
# String concatenation (not f-string) — avoids Python escaping CSS/keyframe braces.
GLOBAL_CSS = """
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background-color: #181820 !important;
    font-family: 'EB Garamond', Georgia, serif !important;
}
#MainMenu, footer,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    display: none !important;
}
.block-container {
    max-width: 760px !important;
    padding: 0 2rem 5rem !important;
}
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.4rem 0 !important;
}
[data-testid="stChatMessageContent"] {
    background: #1e1e2a !important;
    border-radius: 2px !important;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMarkdownContainer"] p {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 1.1rem !important;
    line-height: 1.8 !important;
    color: #ccc5b4 !important;
}
[data-testid="stBottom"] {
    background-color: #181820 !important;
    border-top: 1px solid #25253a !important;
}
[data-testid="stChatInput"] {
    background-color: #1e1e2a !important;
    border: 1px solid #2a2a3c !important;
    border-radius: 2px !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: rgba(181, 146, 42, 0.5) !important;
    box-shadow: none !important;
}
[data-testid="stChatInputTextArea"] {
    background-color: transparent !important;
    color: #ccc5b4 !important;
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 1.05rem !important;
    caret-color: #b5922a !important;
}
.stSpinner > div {
    border-top-color: #b5922a !important;
}
#rag-margins {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 1000;
    overflow: hidden;
}
.rag-img {
    position: absolute;
    width: 115px;
    opacity: 0;
    animation: rag-drift 30s ease-in-out infinite;
}
.rag-img.side-left  { left:  max(8px, calc(50vw - 500px)); }
.rag-img.side-right { right: max(8px, calc(50vw - 500px)); }
.rag-img img {
    width: 100%;
    display: block;
    filter: grayscale(90%) sepia(20%) brightness(0.3) contrast(1.2);
}
@keyframes rag-drift {
    0%   { opacity: 0; transform: translateY(16px); }
    18%  { opacity: 1; transform: translateY(0);    }
    82%  { opacity: 1; transform: translateY(0);    }
    100% { opacity: 0; transform: translateY(-16px); }
}
"""

# ── CSS scoped to the header iframe ──────────────────────────────────────────
HEADER_CSS = """
* { box-sizing: border-box; }
body {
    margin: 0; padding: 0;
    background: #181820;
    font-family: 'EB Garamond', Georgia, serif;
    overflow: hidden;
}
.site-header {
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid rgba(181, 146, 42, 0.28);
}
.site-title {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 2rem;
    font-weight: 400;
    font-style: italic;
    color: #ccc5b4;
    line-height: 1.2;
    margin: 0 0 0.5rem;
    letter-spacing: 0.01em;
}
.site-subtitle {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 0.88rem;
    color: #4a4a5a;
    letter-spacing: 0.06em;
    line-height: 1.5;
    margin: 0;
}
"""

margin_html = "".join(
    '<div class="rag-img side-' + side + '" style="top:' + str(top) + '%;animation-delay:' + str(delay) + 's">'
    '<img src="' + url + '" alt="" loading="lazy">'
    '</div>'
    for url, side, top, delay in MARGIN_IMAGES
)

# Build the full header HTML via concatenation — never embed CSS in an f-string.
HEADER_HTML = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link href="' + FONTS_URL + '" rel="stylesheet">\n'
    '<script>\n'
    'try {\n'
    '  var lnk = document.createElement("link");\n'
    '  lnk.href = "' + FONTS_URL + '";\n'
    '  lnk.rel = "stylesheet";\n'
    '  window.parent.document.head.appendChild(lnk);\n'
    '  if (!window.parent.document.getElementById("rag-css")) {\n'
    '    var sty = document.createElement("style");\n'
    '    sty.id = "rag-css";\n'
    '    sty.textContent = `\n'
    + GLOBAL_CSS +
    '`;\n'
    '    window.parent.document.head.appendChild(sty);\n'
    '  }\n'
    '  if (!window.parent.document.getElementById("rag-margins")) {\n'
    '    var mg = document.createElement("div");\n'
    '    mg.id = "rag-margins";\n'
    '    mg.innerHTML = `\n'
    + margin_html +
    '\n`;\n'
    '    window.parent.document.body.appendChild(mg);\n'
    '  }\n'
    '} catch(e) {}\n'
    '</script>\n'
    '<style>\n'
    + HEADER_CSS +
    '</style>\n'
    '<div class="site-header">\n'
    '  <h1 class="site-title">Western Esotericism &amp; Critical Theory</h1>\n'
    '  <p class="site-subtitle">'
    'The Hermetic tradition &middot; German Idealism &middot; Marxism &middot; Frankfurt School'
    '</p>\n'
    '</div>\n'
)

# ── Render header (iframe injects CSS + margin imagery into parent) ───────────
st.iframe(HEADER_HTML, height=130)

# ── State & clients ───────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []


@st.cache_resource
def load_clients():
    """Create API clients and open the database once; reuse across requests."""
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    collection = chromadb.PersistentClient(path=CHROMA_DIR).get_collection("frankfurt")
    return openai_client, anthropic_client, collection


# ── Conversation ──────────────────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("Ask something..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    openai_client, anthropic_client, collection = load_clients()
    with st.chat_message("assistant"):
        with st.spinner(""):
            question_vector = embed_question(question, openai_client)
            chunks = retrieve(question_vector, collection)
            answer = synthesise(question, chunks, st.session_state.messages[:-1], anthropic_client)
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
