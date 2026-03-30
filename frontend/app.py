"""
CampusGenie — Streamlit Frontend
RAG-based campus document assistant.
Pages: Chat | Documents | System Status
"""

import os
import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
API_TIMEOUT = 120

st.set_page_config(
    page_title="CampusGenie",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "CampusGenie — RAG-based AI assistant. ETT Course Project."},
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f5f6fa; }
[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e5ee; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { padding-top: 0; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

.sb-brand { padding: 20px 0 14px; border-bottom: 1px solid #f0f1f5; margin-bottom: 16px; }
.sb-brand-name { font-size: 1.05rem; font-weight: 700; color: #1a1f36; letter-spacing: -0.3px; }
.sb-brand-tag  { font-size: 0.72rem; color: #9aa0b4; margin-top: 2px; }

.page-header {
    background: #ffffff; border: 1px solid #e2e5ee; border-radius: 12px;
    padding: 20px 24px; margin-bottom: 24px;
    display: flex; align-items: center; justify-content: space-between;
}
.page-header-left h2 { font-size: 1.2rem; font-weight: 700; color: #1a1f36; margin: 0; }
.page-header-left p  { font-size: 0.82rem; color: #6b7280; margin: 4px 0 0; }
.page-header-badge {
    background: #eef0fd; color: #4f46e5; border-radius: 6px;
    padding: 5px 14px; font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.4px; text-transform: uppercase;
}

.stat-row { display: flex; gap: 14px; margin-bottom: 22px; }
.stat-card {
    flex: 1; background: #ffffff; border: 1px solid #e2e5ee;
    border-radius: 10px; padding: 16px 18px;
}
.stat-label { font-size: 0.73rem; color: #9aa0b4; font-weight: 500;
              text-transform: uppercase; letter-spacing: 0.4px; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: #1a1f36; margin-top: 4px; line-height: 1; }

.chat-wrap { display: flex; flex-direction: column; gap: 16px; margin-bottom: 16px; }
.msg-row-user { display: flex; justify-content: flex-end; }
.msg-row-bot  { display: flex; justify-content: flex-start; }
.msg-bubble { max-width: 78%; border-radius: 14px; padding: 13px 16px;
              font-size: 0.9rem; line-height: 1.65; }
.msg-bubble-user {
    background: #4f46e5; color: #ffffff; border-bottom-right-radius: 4px;
}
.msg-bubble-bot {
    background: #ffffff; color: #1a1f36; border: 1px solid #e2e5ee;
    border-bottom-left-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.msg-bubble-notfound {
    background: #fff7ed; color: #92400e; border: 1px solid #fed7aa;
    border-bottom-left-radius: 4px;
}
.msg-sender { font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
              letter-spacing: 0.5px; margin-bottom: 5px; opacity: 0.6; }

.cite-wrap { margin-top: 10px; border-top: 1px solid #f0f1f5; padding-top: 10px; }
.cite-item {
    background: #f8f9fc; border: 1px solid #e8eaed; border-left: 3px solid #4f46e5;
    border-radius: 6px; padding: 9px 12px; margin-bottom: 6px;
}
.cite-head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.cite-doc  { font-size: 0.8rem; font-weight: 600; color: #1a1f36; }
.cite-pg   { font-size: 0.72rem; background: #eef0fd; color: #4f46e5;
             border-radius: 4px; padding: 1px 7px; font-weight: 500; }
.cite-snip { font-size: 0.78rem; color: #6b7280; font-style: italic; line-height: 1.5; }

.doc-name { font-size: 0.9rem; font-weight: 600; color: #1a1f36; }
.doc-meta { font-size: 0.76rem; color: #9aa0b4; margin-top: 3px; }
.doc-pill {
    font-size: 0.72rem; font-weight: 500; background: #f5f6fa; color: #4b5563;
    border: 1px solid #e2e5ee; border-radius: 5px; padding: 3px 10px;
    display: inline-block; margin-right: 6px;
}

.svc-row {
    background: #ffffff; border: 1px solid #e2e5ee; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 16px;
}
.svc-name { font-size: 0.88rem; font-weight: 600; color: #1a1f36; flex: 1; }
.svc-desc { font-size: 0.78rem; color: #9aa0b4; flex: 2; }
.badge-up   { background:#ecfdf5; color:#065f46; border:1px solid #bbf7d0;
              border-radius:5px; padding:3px 10px; font-size:0.72rem; font-weight:600; }
.badge-down { background:#fef2f2; color:#991b1b; border:1px solid #fecaca;
              border-radius:5px; padding:3px 10px; font-size:0.72rem; font-weight:600; }
.badge-deg  { background:#fffbeb; color:#92400e; border:1px solid #fde68a;
              border-radius:5px; padding:3px 10px; font-size:0.72rem; font-weight:600; }
.badge-unk  { background:#f5f6fa; color:#6b7280; border:1px solid #e2e5ee;
              border-radius:5px; padding:3px 10px; font-size:0.72rem; font-weight:600; }

.empty-state {
    text-align: center; padding: 56px 24px; background: #ffffff;
    border: 1px dashed #d1d5db; border-radius: 12px; color: #9aa0b4;
}
.empty-state h3 { font-size: 1rem; color: #4b5563; margin: 0 0 8px; }
.empty-state p  { font-size: 0.84rem; line-height: 1.65; margin: 0; }

.section-title {
    font-size: 0.78rem; font-weight: 600; color: #6b7280;
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;
}
.upload-zone {
    background: #ffffff; border: 1px solid #e2e5ee;
    border-radius: 10px; padding: 20px 24px; margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── API helpers ────────────────────────────────────────────────────────────────
def api_get(path):
    try:
        r = httpx.get(f"{BACKEND_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def api_post(path, **kwargs):
    try:
        r = httpx.post(f"{BACKEND_URL}{path}", timeout=API_TIMEOUT, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"Error {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None

def api_delete(path):
    try:
        r = httpx.delete(f"{BACKEND_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def fetch_docs():
    data = api_get("/api/documents/")
    return data.get("documents", []) if data else []

def check_health():
    return api_get("/api/health") or {"status": "unknown", "services": {}}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-brand-name">CampusGenie</div>
        <div class="sb-brand-tag">ETT Course Project &nbsp;&middot;&nbsp; RAG + Docker</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation", ["Chat", "Documents", "System Status"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='margin:16px 0;border-top:1px solid #f0f1f5;'></div>",
                unsafe_allow_html=True)

    selected_docs = []
    docs_sidebar = fetch_docs()

    if page == "Chat":
        st.markdown("<div class='section-title'>Filter Documents</div>", unsafe_allow_html=True)
        if docs_sidebar:
            selected_docs = st.multiselect(
                "Filter", options=[d["filename"] for d in docs_sidebar],
                default=[], placeholder="Search all documents",
                label_visibility="collapsed",
            )
        else:
            st.caption("No documents uploaded yet.")
        st.markdown("<div style='margin:14px 0;border-top:1px solid #f0f1f5;'></div>",
                    unsafe_allow_html=True)

    total_chunks = sum(d.get("chunk_count", 0) for d in docs_sidebar)
    st.markdown(f"""
    <div style='font-size:0.78rem;line-height:2.1;'>
        <span style='color:#9aa0b4;'>Documents</span>
        <strong style='color:#1a1f36;float:right;'>{len(docs_sidebar)}</strong><br>
        <span style='color:#9aa0b4;'>Total chunks</span>
        <strong style='color:#1a1f36;float:right;'>{total_chunks}</strong><br>
        <span style='color:#9aa0b4;'>Messages</span>
        <strong style='color:#1a1f36;float:right;'>{len(st.session_state.messages)}</strong>
    </div>
    """, unsafe_allow_html=True)

# ── Page header ────────────────────────────────────────────────────────────────
PAGE_META = {
    "Chat":          ("Ask CampusGenie",  "Natural language queries over your campus documents"),
    "Documents":     ("Document Manager", "Upload and manage indexed PDF documents"),
    "System Status": ("System Status",    "Service health and RAG pipeline diagnostics"),
}
title, subtitle = PAGE_META[page]
st.markdown(f"""
<div class="page-header">
    <div class="page-header-left">
        <h2>{title}</h2>
        <p>{subtitle}</p>
    </div>
    <span class="page-header-badge">RAG + Docker</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CHAT
# ══════════════════════════════════════════════════════════════════════════════
if page == "Chat":
    docs = fetch_docs()

    if not docs:
        st.markdown("""
        <div class="empty-state">
            <h3>No documents indexed</h3>
            <p>Go to the <strong>Documents</strong> tab and upload a campus PDF.<br>
            Once indexed, you can ask questions and get citation-backed answers.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    col_c1, col_c2 = st.columns([6, 1])
    with col_c2:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <h3>Start a conversation</h3>
            <p>Ask any question about your uploaded documents.<br>
            Every answer includes page-level citations from the source PDF.</p>
            <p style="margin-top:16px;font-size:0.8rem;color:#b0b8c8;">
                Examples &mdash;
                "What are the course outcomes?" &nbsp;|&nbsp;
                "List all Unit 3 topics." &nbsp;|&nbsp;
                "What is the attendance policy?"
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        chat_html = '<div class="chat-wrap">'
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="msg-row-user">
                  <div class="msg-bubble msg-bubble-user">
                    <div class="msg-sender">You</div>
                    {msg["content"]}
                  </div>
                </div>"""
            else:
                found = msg.get("found_in_docs", True)
                if not found:
                    chat_html += """
                    <div class="msg-row-bot">
                      <div class="msg-bubble msg-bubble-notfound">
                        <div class="msg-sender">CampusGenie</div>
                        Not found in uploaded documents.
                        Try uploading a more relevant PDF.
                      </div>
                    </div>"""
                else:
                    citations = msg.get("citations", [])
                    cite_html = ""
                    if citations:
                        cite_html = '<div class="cite-wrap">'
                        for c in citations[:3]:
                            snip = c["snippet"][:160].replace('"', "&quot;")
                            cite_html += f"""
                            <div class="cite-item">
                              <div class="cite-head">
                                <span class="cite-doc">{c["document"]}</span>
                                <span class="cite-pg">Page {c["page"]}</span>
                              </div>
                              <div class="cite-snip">{snip}...</div>
                            </div>"""
                        cite_html += "</div>"
                    chat_html += f"""
                    <div class="msg-row-bot">
                      <div class="msg-bubble msg-bubble-bot">
                        <div class="msg-sender">CampusGenie</div>
                        {msg["content"]}
                        {cite_html}
                      </div>
                    </div>"""
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

    question = st.chat_input("Ask a question about your documents...")
    if question and question.strip():
        st.session_state.messages.append({"role": "user", "content": question})
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[-8:]
            if m["role"] in ("user", "assistant")
        ]
        with st.spinner("Searching documents..."):
            result = api_post("/api/chat/ask", json={
                "question": question,
                "document_filter": selected_docs if selected_docs else None,
                "chat_history": history,
            })
        if result:
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "citations": result.get("citations", []),
                "found_in_docs": result.get("found_in_docs", True),
            })
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Documents":
    docs = fetch_docs()

    if docs:
        total_chunks = sum(d.get("chunk_count", 0) for d in docs)
        avg = round(total_chunks / len(docs)) if docs else 0
        st.markdown(f"""
        <div class="stat-row">
            <div class="stat-card">
                <div class="stat-label">Documents</div>
                <div class="stat-value">{len(docs)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Chunks</div>
                <div class="stat-value">{total_chunks}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Chunks / Doc</div>
                <div class="stat-value">{avg}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Upload Document</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload PDF", type=["pdf"], label_visibility="collapsed",
        help="Maximum file size: 50 MB",
    )
    if uploaded_file:
        size_kb = len(uploaded_file.getvalue()) / 1024
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.markdown(f"**{uploaded_file.name}**")
            st.caption(f"{size_kb:.1f} KB")
        with col3:
            if st.button("Index", type="primary", use_container_width=True):
                with st.spinner(f"Indexing {uploaded_file.name}..."):
                    result = api_post(
                        "/api/documents/upload",
                        files={"file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )},
                    )
                if result:
                    st.success(
                        f"Indexed — {result['page_count']} pages, "
                        f"{result['chunk_count']} chunks."
                    )
                    st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Indexed Documents</div>", unsafe_allow_html=True)

    if not docs:
        st.markdown("""
        <div class="empty-state">
            <h3>No documents indexed</h3>
            <p>Upload a PDF above to get started.<br>
            Documents are chunked, embedded, and stored in ChromaDB.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for doc in docs:
            col1, col2, col3 = st.columns([5, 2, 1])
            with col1:
                st.markdown(f"""
                <div style="padding:4px 0;">
                  <div class="doc-name">{doc["filename"]}</div>
                  <div class="doc-meta">ID: {doc["doc_id"]}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="padding:8px 0;">
                  <span class="doc-pill">{doc.get("page_count","—")} pages</span>
                  <span class="doc-pill">{doc["chunk_count"]} chunks</span>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                if st.button("Delete", key=f"del_{doc['doc_id']}", use_container_width=True):
                    res = api_delete(f"/api/documents/{doc['doc_id']}")
                    if res and res.get("success"):
                        st.success("Deleted.")
                        st.rerun()
            st.markdown("<hr style='margin:4px 0;border-color:#f0f1f5;'>",
                        unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM STATUS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "System Status":
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    health = check_health()
    overall = health.get("status", "unknown")
    services = health.get("services", {})

    if overall == "healthy":
        st.success("All services operational.")
    elif overall == "degraded":
        st.warning("One or more services are degraded.")
    else:
        st.error("Backend unreachable. Ensure Docker containers are running.")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Services</div>", unsafe_allow_html=True)

    SERVICES = {
        "backend":  ("FastAPI Backend",  "REST API — handles upload and chat requests",         "8080"),
        "ollama":   ("Ollama (Llama 3)", "Local LLM — generates answers from context",          "11434"),
        "chromadb": ("ChromaDB",         "Vector database — stores and retrieves embeddings",   "8000"),
    }
    for key, (label, desc, port) in SERVICES.items():
        status = services.get(key, "unknown")
        badge = {
            "up":       '<span class="badge-up">UP</span>',
            "degraded": '<span class="badge-deg">DEGRADED</span>',
            "down":     '<span class="badge-down">DOWN</span>',
        }.get(status, '<span class="badge-unk">UNKNOWN</span>')
        st.markdown(f"""
        <div class="svc-row">
            <div class="svc-name">{label}</div>
            {badge}
            <div class="svc-desc">
                {desc} &nbsp;
                <span style="color:#d1d5db;">:{port}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>RAG Pipeline</div>", unsafe_allow_html=True)
    st.code("""
Indexing  (PDF upload)
  PDF file
    -> PDFProcessor    : extract text per page (PyMuPDF)
    -> TextChunker     : sliding window word chunks (size=500, overlap=50)
    -> EmbeddingEngine : sentence-transformers / all-MiniLM-L6-v2
    -> ChromaDB        : store vectors + metadata

Query  (user question)
  Question
    -> EmbeddingEngine : embed question into query vector
    -> ChromaDB        : retrieve top-5 similar chunks
    -> Ollama Llama3   : answer strictly from context (no hallucination)
    -> Response        : answer text + citations (document, page, snippet)
    """, language="text")

    st.markdown("<div class='section-title'>Runtime Configuration</div>",
                unsafe_allow_html=True)
    st.json({
        "backend_url":     BACKEND_URL,
        "llm_model":       "llama3",
        "embedding_model": "all-MiniLM-L6-v2",
        "vector_db":       "chromadb",
        "chunk_size":      500,
        "chunk_overlap":   50,
        "retrieval_top_k": 5,
        "max_upload_mb":   50,
    })
