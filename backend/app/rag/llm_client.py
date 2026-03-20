"""
CampusGenie — LLM Client
Integrates with Ollama (locally running Llama 3) via LangChain.

Why Ollama?
  - Runs 100% locally inside Docker — no API keys, no internet
  - Llama 3 is strong for Q&A tasks
  - LangChain wraps it with prompt templates + chain abstraction

The LLM is ONLY given retrieved chunks as context.
It is explicitly instructed NOT to use outside knowledge.
This is the anti-hallucination guarantee.
"""

import logging
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from app.config import settings

logger = logging.getLogger(__name__)

# ── Prompt Template ───────────────────────────────────────────────────────────
# The system prompt is the KEY to preventing hallucination.
# We explicitly tell the model: use ONLY the context below.

RAG_PROMPT_TEMPLATE = """You are CampusGenie, an AI assistant for college students.
You answer questions ONLY based on the provided context from campus documents.

STRICT RULES:
1. Answer ONLY from the context below. Do not use any outside knowledge.
2. If the answer is not in the context, respond with exactly:
   "Not found in uploaded documents."
3. Be concise and accurate.
4. When answering, refer to the source document naturally (e.g., "According to the syllabus...").

Context from campus documents:
---
{context}
---

Chat History:
{chat_history}

Student Question: {question}

Answer:"""

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "chat_history", "question"],
    template=RAG_PROMPT_TEMPLATE,
)

NOT_FOUND_RESPONSE = "Not found in uploaded documents."


class LLMClient:
    """
    Wraps Ollama LLM with a RAG prompt chain.
    Enforces context-only answering to prevent hallucination.
    """

    def __init__(self):
        self._llm: OllamaLLM | None = None
        self._chain: LLMChain | None = None

    def _get_chain(self) -> LLMChain:
        if self._chain is None:
            logger.info(
                f"Initialising Ollama LLM: model={settings.ollama_model}, "
                f"url={settings.ollama_base_url}"
            )
            self._llm = OllamaLLM(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=0.1,       # Low temp = factual, not creative
                num_ctx=4096,          # Context window
            )
            self._chain = LLMChain(llm=self._llm, prompt=RAG_PROMPT)
            logger.info("LLM chain ready ✓")
        return self._chain

    def generate_answer(
        self,
        question: str,
        context_chunks: list[dict],
        chat_history: list[dict] | None = None,
    ) -> str:
        """
        Generate an answer grounded in the retrieved context chunks.

        Args:
            question:       The user's question
            context_chunks: Retrieved chunks from VectorStore.query()
            chat_history:   Prior Q&A pairs for conversational context

        Returns:
            Answer string (or NOT_FOUND_RESPONSE if info not in docs)
        """
        if not context_chunks:
            return NOT_FOUND_RESPONSE

        context = self._format_context(context_chunks)
        history_text = self._format_history(chat_history or [])

        chain = self._get_chain()
        response = chain.invoke(
            {
                "context": context,
                "chat_history": history_text,
                "question": question,
            }
        )

        answer = response.get("text", "").strip()
        return answer if answer else NOT_FOUND_RESPONSE

    def is_available(self) -> bool:
        """Check if Ollama service is reachable."""
        try:
            import httpx
            r = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _format_context(chunks: list[dict]) -> str:
        """
        Format retrieved chunks into a numbered context block.
        Each entry shows source info for the LLM to reference.
        """
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"[{i}] Source: {chunk['filename']} (Page {chunk['page_number']})\n"
                f"{chunk['text']}"
            )
        return "\n\n".join(parts)

    @staticmethod
    def _format_history(history: list[dict]) -> str:
        """Format chat history as readable dialogue."""
        if not history:
            return "No prior conversation."
        lines = []
        for msg in history[-4:]:   # last 4 exchanges to stay within context
            role = msg.get("role", "user").capitalize()
            lines.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(lines)
