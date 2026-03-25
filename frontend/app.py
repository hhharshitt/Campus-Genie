"""
CampusGenie — Streamlit Frontend
Professional UI for the RAG-based campus document assistant.
Pages: Chat | Documents | System Status
"""

import os
import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
API_TIMEOUT = 120

st.set_page_config(
    page_title="CampusGenie",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "CampusGenie — RAG-based AI assistant. ETT Course Project."},
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f8f9fb; }
[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e8eaed; }

.cg-header {
    background: #1a1f36;
    border-radius: 10px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.cg-header-title { color: #ffffff; font-size: 1.4rem; font-weight: 700; margin: 0; }
.cg-header-sub   { color: #9aa0b4; font-size: 0.82rem; margin: 4px 0 0; }
.cg-badge {
    background: #2d3561; color: #7c8cf8;
    border-radius: 6px; padding: 4px 12px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;
}

.msg-user {
    background: #ffffff; border: 1px solid #e8eaed;
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px; margin: 8px 0;
    max-width: 80%; margin-left: auto;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.msg-bot {
    background: #ffffff; border: 1px solid #e8eaed;
    border-left: 3px solid #7c8cf8;
    border-radius: 4px 12px 12px 12px;
    padding: 12px 16px; margin: 8px 0;
    max-width: 92%;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.msg-notfound {
    background: #fff8f0; border: 1px solid #ffd0a8;
    border-left: 3px solid #f97316;
    border-radius: 4px 12px 12px 12px;
    padding: 12px 16px; margin: 8px 0;
    max-width: 92%; color: #92400e; font-size: 0.92rem;
}
.msg-label {
    font-size: 0.7rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-bottom: 5px;
}
.msg-user .msg-label { color: #9aa0b4; }
.msg-bot  .msg-label { color: #7c8cf8; }
.msg-text { color: #1a1f36; font-size: 0.93rem; line-height: 1.6; }

.citation-block {
    background: #f8f9fb; border: 1px solid #e8eaed;
    border-radius: 8px; padding: 10px 14px; margin: 5px 0;
}
.cite-title   { font-weight: 600; color: #1a1f36; font-size: 0.84rem; }
.cite-page    { color: #7c8cf8; font-size: 0.76rem; font-weight: 500; margin-left: 8px; }
.cite-snippet { color: #6b7280; font-size: 0.82rem; margin-top: 5px;
                font-style: italic; line-height: 1.4;
                border-left: 2px solid #e8eaed; padding-left: 8px; }

.pill { display: inline-block; border-radius: 20px; padding: 3px 11px;
        font-size: 0.73rem; font-weight: 600; }
.pill-up  { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }
.pill-down{ background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
.pill-deg { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }

.empty-state { text-align: center; padding: 48px 20px; color: #9aa0b4; }
.empty-state h3 { color: #6b7280; font-size: 1.05rem; margin-bottom: 8px; }
.empty-state p  { font-size: 0.86rem; line-height: 1.6; }

#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []


# ── API helpers ───────────────────────────────────────────────────────────────

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


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='padding:12px 0 6px;'>
        <div style='font-size:1.15rem;font-weight:700;color:#1a1f36;'>CampusGenie</div>
        <div style='font-size:0.76rem;color:#9aa0b4;margin-top:2px;'>ETT Course Project</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    page = st.radio("Nav", ["Chat", "Documents", "System Status"], label_visibility="collapsed")

    st.divider()

    selected_docs = []
    if page == "Chat":
        st.markdown("<div style='font-size:0.76rem;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;'>Document Filter</div>", unsafe_allow_html=True)
        docs = fetch_docs()
        doc_names = [d["filename"] for d in docs]
        if doc_names:
            selected_docs = st.multiselect(
                "Filter", options=doc_names, default=[],
                placeholder="All documents", label_visibility="collapsed",
            )
            st.caption(f"{len(doc_names)} document(s) indexed")
        else:
            st.caption("No documents uploaded yet")
        st.divider()

    docs_all = fetch_docs()
    total_chunks = sum(d.get("chunk_count", 0) for d in docs_all)
    st.markdown(f"""
    <div style='font-size:0.78rem;color:#9aa0b4;line-height:2;'>
        Documents: <strong style='color:#1a1f36;'>{len(docs_all)}</strong><br>
        Chunks: <strong style='color:#1a1f36;'>{total_chunks}</strong><br>
        Messages: <strong style='color:#1a1f36;'>{len(st.session_state.messages)}</strong>
    </div>
    """, unsafe_allow_html=True)


# ── Page header ───────────────────────────────────────────────────────────────

PAGE_META = {
    "Chat":          ("Ask CampusGenie",   "Query your campus documents using natural language"),
    "Documents":     ("Document Manager",  "Upload, view and manage indexed PDF documents"),
    "System Status": ("System Status",     "Health and diagnostics for all backend services"),
}
title, subtitle = PAGE_META[page]
st.markdown(f"""
<div class="cg-header">
    <div>
        <p class="cg-header-title">{title}</p>
        <p class="cg-header-sub">{subtitle}</p>
    </div>
    <span class="cg-badge">RAG + Docker</span>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CHAT
# ═══════════════════════════════════════════════════════════════════════════════

if page == "Chat":
    docs = fetch_docs()
    if not docs:
        st.markdown("""
        <div class="empty-state">
            <h3>No documents indexed yet</h3>
            <p>Go to the <strong>Documents</strong> tab and upload a campus PDF<br>
            to start asking questions.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <h3>Start a conversation</h3>
            <p>Ask any question about your uploaded documents.<br>
            Answers include page-level citations from source PDFs.</p>
            <p style='margin-top:14px;font-size:0.8rem;color:#b0b8c8;'>
                Try: "What are the course outcomes?" &nbsp;|&nbsp;
                "List Unit 3 topics." &nbsp;|&nbsp;
                "What is the attendance policy?"
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-user">
                    <div class="msg-label">You</div>
                    <div class="msg-text">{msg["content"]}</div>
                </div>""", unsafe_allow_html=True)
            else:
                found = msg.get("found_in_docs", True)
                citations = msg.get("citations", [])
                if not found:
                    st.markdown(f"""
                    <div class="msg-notfound">
                        <strong>Not found in uploaded documents.</strong><br>
                        <span style='font-size:0.85rem;'>
                            This question could not be answered from the indexed documents.
                            Try uploading more relevant PDFs.
                        </span>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="msg-bot">
                        <div class="msg-label">CampusGenie</div>
                        <div class="msg-text">{msg["content"]}</div>
                    </div>""", unsafe_allow_html=True)
                    if citations:
                        with st.expander(f"Sources ({len(citations)})", expanded=False):
                            for c in citations:
                                st.markdown(f"""
                                <div class="citation-block">
                                    <span class="cite-title">{c['document']}</span>
                                    <span class="cite-page">Page {c['page']}</span>
                                    <div class="cite-snippet">{c['snippet']}</div>
                                </div>""", unsafe_allow_html=True)

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


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Documents":
    st.markdown("#### Upload Document")
    st.caption("Supported format: PDF. Maximum file size: 50 MB.")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded_file:
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{uploaded_file.name}**")
            st.caption(f"{file_size_kb:.1f} KB")
        with col3:
            if st.button("Index document", type="primary", use_container_width=True):
                with st.spinner(f"Indexing {uploaded_file.name}..."):
                    result = api_post(
                        "/api/documents/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                    )
                if result:
                    st.success(
                        f"Indexed successfully — "
                        f"{result['page_count']} pages, {result['chunk_count']} chunks."
                    )
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Indexed Documents")

    docs = fetch_docs()
    if not docs:
        st.markdown("""
        <div class="empty-state">
            <h3>No documents indexed</h3>
            <p>Upload a PDF above to get started.<br>
            Documents are chunked, embedded, and stored in ChromaDB.</p>
        </div>""", unsafe_allow_html=True)
    else:
        total_chunks = sum(d.get("chunk_count", 0) for d in docs)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total documents", len(docs))
        col2.metric("Total chunks", total_chunks)
        col3.metric("Avg chunks / doc", round(total_chunks / len(docs)))

        st.markdown("<br>", unsafe_allow_html=True)

        for doc in docs:
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
            with col1:
                st.markdown(f"**{doc['filename']}**")
                st.caption(f"ID: `{doc['doc_id']}`")
            with col2:
                st.markdown(f"<div style='text-align:center;padding-top:8px;'><b>{doc.get('page_count','—')}</b><br><span style='font-size:0.73rem;color:#9aa0b4;'>pages</span></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div style='text-align:center;padding-top:8px;'><b>{doc['chunk_count']}</b><br><span style='font-size:0.73rem;color:#9aa0b4;'>chunks</span></div>", unsafe_allow_html=True)
            with col4:
                if st.button("Delete", key=f"del_{doc['doc_id']}", use_container_width=True):
                    res = api_delete(f"/api/documents/{doc['doc_id']}")
                    if res and res.get("success"):
                        st.success("Deleted.")
                        st.rerun()
            st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM STATUS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "System Status":
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    health = check_health()
    overall = health.get("status", "unknown")
    services = health.get("services", {})

    if overall == "healthy":
        st.success("All services are operational.")
    elif overall == "degraded":
        st.warning("One or more services are degraded.")
    else:
        st.error("Unable to reach backend services.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Service Health")

    service_meta = {
        "backend":  ("FastAPI Backend", "REST API — handles upload and chat requests"),
        "ollama":   ("Ollama LLM",       "Llama 3 model server — generates answers from context"),
        "chromadb": ("ChromaDB",         "Vector database — stores and retrieves embeddings"),
    }

    for key, (label, description) in service_meta.items():
        status = services.get(key, "unknown")
        pill_class = "pill-up" if status == "up" else ("pill-deg" if status == "degraded" else "pill-down")
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            st.markdown(f'<span class="pill {pill_class}">{status.upper()}</span>', unsafe_allow_html=True)
        with col3:
            st.caption(description)
        st.markdown("<hr style='margin:6px 0;border-color:#f0f0f0;'>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### RAG Pipeline")
    st.code("""
Indexing  (on PDF upload)
  PDF file -> PDFProcessor -> TextChunker -> EmbeddingEngine -> ChromaDB

Query  (on user question)
  Question -> EmbeddingEngine -> ChromaDB (top-5) -> Ollama Llama3 -> Answer + Citations
    """, language="text")

    st.markdown("#### Environment")
    st.json({
        "backend_url":    BACKEND_URL,
        "llm_model":      "llama3",
        "embeddings":     "all-MiniLM-L6-v2",
        "vector_db":      "chromadb",
        "chunk_size":     500,
        "chunk_overlap":  50,
        "retrieval_top_k": 5,
    })
