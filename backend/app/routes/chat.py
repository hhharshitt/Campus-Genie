"""
CampusGenie — Chat API Route
Handles student questions via the RAG pipeline.

POST /api/chat/ask — Ask a question, get an answer with citations
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from app.rag.pipeline import get_pipeline, RAGPipeline
from app.models.schemas import ChatRequest, ChatResponse, Citation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """
    Ask a question about uploaded campus documents.

    - Embeds the question and retrieves relevant chunks from ChromaDB
    - Passes context + question to the LLM (Ollama / Llama 3)
    - Returns answer with source citations (document name + page number)

    If the answer is not found in any document, returns:
      "Not found in uploaded documents."
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Build history list for LLM context
    history = [
        {"role": m.role, "content": m.content}
        for m in (request.chat_history or [])
    ]

    try:
        result = pipeline.query(
            question=request.question,
            document_filter=request.document_filter,
            chat_history=history,
        )
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    citations = [
        Citation(
            document=c.document,
            page=c.page,
            snippet=c.snippet,
        )
        for c in result.citations
    ]

    return ChatResponse(
        answer=result.answer,
        citations=citations,
        source_documents=result.source_documents,
        found_in_docs=result.found_in_docs,
    )


@router.get("/status")
async def chat_status(pipeline: RAGPipeline = Depends(get_pipeline)):
    """Check if the LLM is available for answering questions."""
    llm_up = pipeline.llm.is_available()
    docs = pipeline.list_documents()
    return {
        "llm_available": llm_up,
        "indexed_documents": len(docs),
        "ready": llm_up and len(docs) > 0,
        "message": (
            "Ready to answer questions!"
            if (llm_up and docs)
            else "Upload documents and ensure Ollama is running."
        ),
    }
