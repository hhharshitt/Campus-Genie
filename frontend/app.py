"""
CampusGenie — Streamlit Frontend
Two-page app: 📂 Documents (upload/manage) + 💬 Chat (Q&A with RAG)
"""

import os
import httpx
import streamlit as st
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
API_TIMEOUT = 120  # seconds — LLM generation can be slow

st.set_page_config(
    page_title="CampusGenie",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { font-size: 2.4rem; margin: 0; }
    .main-header p  { font-size: 1.1rem; margin: 0.4rem 0 0; opacity: 0.85; }

    /* Chat bubbles */
    .chat-user {
        background: #e3f2fd;
        border-radius: 12px 12px 4px 12px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
        border-left: 4px solid #1976d2;
    }
    .chat-bot {
        background: #f3e5f5;
        border-radius: 12px 12px 12px 4px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
        border-left: 4px solid #7b1fa2;
    }

    /* Citation card */
    .citation-card {
        background: #fff8e1;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        margin: 0.3rem 0;
        font-size: 0.85rem;
    }

    /* Not-found banner */
    .not-found {
        background: #fce4ec;
        border: 1px solid #e91e63;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        color: #880e4f;
    }

    /* Status pill */
    .pill-green { background:#e8f5e9; color:#2e7d32; border-radius:20px;
                  padding:2px 10px; font-size:0.8rem; font-weight:600; }
    .pill-red   { background:#ffebee; color:#c62828; border-radius:20px;
                  padding:2px 10px; font-size:0.8rem; font-weight:600; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def api_get(path: str) -> dict | None:
    try:
        r = httpx.get(f"{BACKEND_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path: str, **kwargs) -> dict | None:
    try:
        r = httpx.post(f"{BACKEND_URL}{path}", timeout=API_TIMEOUT, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def api_delete(path: str) -> dict | None:
    try:
        r = httpx.delete(f"{BACKEND_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def check_health() -> dict:
    data = api_get("/api/health")
    return data or {"status": "unknown", "services": {}}


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 CampusGenie")
    st.markdown("*Chat with your campus PDFs*")
    st.divider()

    page = st.radio(
        "Navigate",
        ["💬 Chat", "📂 Documents", "🔍 System Status"],
        label_visibility="collapsed",
    )

    st.divider()

    # Document filter
    st.markdown("**🗂️ Document Filter**")
    docs_data = api_get("/api/documents/")
    doc_options = []
    if docs_data and docs_data.get("documents"):
        doc_options = [d["doc_id"] for d in docs_data["documents"]]
        st.caption(f"{len(doc_options)} document(s) indexed")
    else:
        st.caption("No documents uploaded yet")

    selected_docs = st.multiselect(
        "Query specific docs (leave empty for all)",
        options=doc_options,
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("ETT Course Project")
    st.caption("Docker + RAG")


# ── Page: Header ──────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="main-header">
        <h1>🎓 CampusGenie</h1>
        <p>AI assistant powered by RAG — answers only from your campus documents</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CHAT
# ═══════════════════════════════════════════════════════════════════════════════

if page == "💬 Chat":
    # Init chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("💬 Ask CampusGenie")
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Render chat history
    if not st.session_state.messages:
        st.info(
            "👋 Upload your campus PDFs in the **Documents** tab, then ask anything!\n\n"
            "**Example questions:**\n"
            "- What are the COs for CS3232?\n"
            "- What is the attendance policy?\n"
            "- List all Unit-3 topics.\n"
            "- What is the marking scheme?"
        )
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-user">🧑‍🎓 <strong>You:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                answer = msg["content"]
                citations = msg.get("citations", [])
                found = msg.get("found_in_docs", True)

                if found:
                    st.markdown(
                        f'<div class="chat-bot">🤖 <strong>CampusGenie:</strong><br>{answer}</div>',
                        unsafe_allow_html=True,
                    )
                    if citations:
                        with st.expander(f"📌 {len(citations)} Citation(s)", expanded=False):
                            for c in citations:
                                st.markdown(
                                    f'<div class="citation-card">'
                                    f'📄 <strong>{c["document"]}</strong> — Page {c["page"]}<br>'
                                    f'<em>{c["snippet"]}</em>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                else:
                    st.markdown(
                        '<div class="not-found">❌ <strong>Not found in uploaded documents.</strong></div>',
                        unsafe_allow_html=True,
                    )

    st.divider()

    # Input box
    with st.form("chat_form", clear_on_submit=True):
        question = st.text_input(
            "Ask a question...",
            placeholder="e.g. What are the COs for CS3232?",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("🔍 Ask", use_container_width=True)

    if submitted and question.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": question})

        # Build history for API (last 6 turns)
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[-6:]
            if m["role"] in ("user", "assistant")
        ]

        with st.spinner("🧠 Thinking..."):
            payload = {
                "question": question,
                "document_filter": selected_docs or None,
                "chat_history": history,
            }
            result = api_post("/api/chat/query", json=payload)

        if result:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "citations": result.get("citations", []),
                    "found_in_docs": result.get("found_in_docs", True),
                }
            )
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "📂 Documents":
    st.subheader("📂 Manage Documents")

    # Upload section
    with st.container(border=True):
        st.markdown("### ⬆️ Upload PDF")
        st.caption("Upload campus PDFs: syllabus, notes, lab manuals, rules, timetables...")

        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            label_visibility="collapsed",
        )

        if uploaded_file:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info(f"📄 **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
            with col2:
                if st.button("📥 Upload & Index", use_container_width=True):
                    with st.spinner(f"Indexing {uploaded_file.name}... this may take a moment"):
                        result = api_post(
                            "/api/documents/upload",
                            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                        )
                    if result:
                        st.success(
                            f"✅ **{result['filename']}** indexed!\n\n"
                            f"📄 {result['page_count']} pages | "
                            f"🧩 {result['chunk_count']} chunks"
                        )
                        st.rerun()

    st.divider()

    # Document list
    st.markdown("### 📋 Indexed Documents")

    docs_data = api_get("/api/documents/")

    if not docs_data or not docs_data.get("documents"):
        st.warning("No documents uploaded yet. Upload a PDF above to get started.")
    else:
        docs = docs_data["documents"]
        st.caption(f"Total: **{len(docs)}** document(s)")

        for doc in docs:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                with col1:
                    st.markdown(f"**📄 {doc['filename']}**")
                    st.caption(f"ID: `{doc['doc_id']}`")
                with col2:
                    st.metric("Pages", doc.get("page_count", "—"))
                with col3:
                    st.metric("Chunks", doc["chunk_count"])
                with col4:
                    if st.button("🗑️ Delete", key=f"del_{doc['doc_id']}"):
                        result = api_delete(f"/api/documents/{doc['doc_id']}")
                        if result and result.get("success"):
                            st.success("Deleted!")
                            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SYSTEM STATUS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🔍 System Status":
    st.subheader("🔍 System Status")

    if st.button("🔄 Refresh Status"):
        st.rerun()

    health = check_health()

    overall = health.get("status", "unknown")
    if overall == "healthy":
        st.success("✅ All systems operational")
    elif overall == "degraded":
        st.warning("⚠️ Some services are degraded")
    else:
        st.error("❌ System status unknown")

    st.divider()
    services = health.get("services", {})

    service_info = {
        "backend":  ("⚙️ FastAPI Backend",    "Core API server"),
        "ollama":   ("🤖 Ollama LLM",          "Llama 3 model server"),
        "chromadb": ("🗄️ ChromaDB",            "Vector database"),
    }

    for key, (label, desc) in service_info.items():
        status_val = services.get(key, "unknown")
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            pill = "pill-green" if status_val == "up" else "pill-red"
            emoji = "🟢" if status_val == "up" else "🔴"
            st.markdown(
                f'<span class="{pill}">{emoji} {status_val.upper()}</span>',
                unsafe_allow_html=True,
            )
        with col3:
            st.caption(desc)

    st.divider()
    st.markdown("**Architecture Overview**")
    st.code(
        """
User Question
    │
    ▼
[Streamlit UI] ──HTTP──▶ [FastAPI Backend]
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              [sentence-transformers]  [ChromaDB]
               embed question          retrieve top-k chunks
                    │                     │
                    └──────────┬──────────┘
                               ▼
                         [Ollama LLM]
                          Llama 3
                               │
                               ▼
                    Answer + Citations
        """,
        language="text",
    )
