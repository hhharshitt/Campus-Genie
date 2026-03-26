"""
CampusGenie — Educational LLM Client
Integrates with Ollama (Gemma 2B) to provide detailed, explanatory answers for students.

Why Ollama + Educational Focus?
  - Runs 100% locally inside Docker — no API keys, no internet
  - Gemma 2B provides excellent balance of performance and memory efficiency
  - Educational prompt engineering ensures detailed, learning-focused responses
  - Proper citation formatting helps students learn to reference sources

The LLM is designed to provide comprehensive educational responses while
maintaining strict adherence to provided context to ensure accuracy.
"""

import logging
import ollama
from app.config import settings

logger = logging.getLogger(__name__)

# ── Prompt Template ───────────────────────────────────────────────────────────
# The system prompt is the KEY to preventing hallucination.
# We explicitly tell the model: use ONLY the context below.

RAG_PROMPT_TEMPLATE = """You are CampusGenie, an educational AI assistant designed to provide direct, detailed answers to student questions about course materials.

RESPONSE STYLE:
- Provide direct, comprehensive answers without asking cross-questions
- Focus on explaining concepts thoroughly with proper structure and formatting
- Include detailed explanations, examples, and context when available
- Use clear headings, bullet points, and numbered lists for better readability
- Always cite sources properly using [Source: Document Name, Page X] format

GUIDELINES:
1. Answer the question directly and comprehensively using the provided context
2. Do NOT ask follow-up questions or engage in conversational exchanges
3. Provide detailed explanations that break down complex concepts
4. Include relevant examples, context, and background information
5. Structure answers clearly with proper formatting
6. Always cite your sources using the format: [Source: Document Name, Page X]
7. If multiple sources provide different perspectives, synthesize and reference each
8. If you cannot find relevant information after careful review, respond with exactly:
   "Not found in uploaded documents. Try uploading a more relevant PDF."

EDUCATIONAL APPROACH:
- Explain concepts step-by-step for better understanding
- Provide context to help students see the bigger picture
- Use clear, educational language appropriate for college-level learning
- Include practical implications and applications when relevant
- Help students connect new information to existing knowledge

Context from campus documents:
---
{context}
---

Chat History:
{chat_history}

Student Question: {question}

Detailed Educational Answer:"""

NOT_FOUND_RESPONSE = "Not found in uploaded documents."


class LLMClient:
    """
    Educational LLM Client for CampusGenie.
    Provides detailed, explanatory answers for student learning with proper citations.
    Engineered to prevent hallucination while maximizing educational value.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            logger.info(f"Initialising Ollama client: model={settings.ollama_model}")
            self._client = ollama.Client(
                host=settings.ollama_base_url.replace('http://', '').replace('https://', '')
            )
            # Test connection
            try:
                models = self._client.list()
                logger.info(f"Ollama connection successful, available models: {models}")
            except Exception as e:
                logger.error(f"Ollama connection failed: {e}")
                raise e
        return self._client

    def generate_answer(
        self,
        question: str,
        context_chunks: list[dict],
        chat_history: list[dict] | None = None,
    ) -> str:
        """
        Generate an answer grounded in the retrieved context chunks.
        Handles both conversational interactions and educational questions.

        Args:
            question:       The user's question
            context_chunks: Retrieved chunks from VectorStore.query()
            chat_history:   Prior Q&A pairs for conversational context

        Returns:
            Answer string (or NOT_FOUND_RESPONSE if info not in docs)
        """
        
        # Check for basic conversational interactions first
        conversational_response = self._handle_conversational_interactions(question)
        if conversational_response:
            return conversational_response
            
        client = self._get_client()

        # Build context from chunks
        context = "\n\n".join([chunk["text"] for chunk in context_chunks])
        
        # Build chat history string
        history_str = ""
        if chat_history:
            # Convert role/content format to Q/A format
            qa_pairs = []
            for i, msg in enumerate(chat_history):
                if msg['role'] == 'user':
                    qa_pairs.append(f"Q: {msg['content']}")
                elif msg['role'] == 'assistant' and qa_pairs:
                    qa_pairs[-1] += f"\nA: {msg['content']}"
            history_str = "\n".join(qa_pairs)

        # Format prompt
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context,
            chat_history=history_str,
            question=question
        )

        try:
            response = client.generate(
                model=settings.ollama_model,
                prompt=prompt,
                options={
                    'temperature': 0.1,  # Lower temperature for more factual, direct responses
                    'num_ctx': 4096,
                    'num_predict': 1500,  # Allow longer, more detailed responses
                }
            )
            answer = response['response'].strip()
            
            # Post-process answer for better formatting
            answer = self._enhance_answer_formatting(answer)
            
            # Check if answer indicates not found
            if not answer or answer.lower() in ['not found in uploaded documents. try uploading a more relevant pdf.', 'i cannot answer based on the provided context.']:
                return NOT_FOUND_RESPONSE
                
            return answer
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return NOT_FOUND_RESPONSE

    def _handle_conversational_interactions(self, question: str) -> str | None:
        """
        Handle basic conversational interactions without going through RAG pipeline.
        Returns appropriate response for greetings and basic pleasantries.
        """
        question_lower = question.lower().strip()
        
        # Greetings
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'hi there', 'hello there']
        if any(greeting in question_lower for greeting in greetings):
            return "Hello! I'm CampusGenie, your educational AI assistant. I'm here to help you understand your course materials and answer questions about uploaded documents. What would you like to learn about today?"
        
        # How are you
        if 'how are you' in question_lower:
            return "I'm doing great, thanks for asking! I'm ready to help you with your academic questions. What can I assist you with today?"
        
        # Thanks
        if any(word in question_lower for word in ['thanks', 'thank you', 'thx']):
            return "You're welcome! I'm glad I could help. Do you have any other questions about your course materials?"
        
        # Goodbye
        if any(word in question_lower for word in ['bye', 'goodbye', 'see you', 'see ya']):
            return "Goodbye! Feel free to come back anytime you need help with your studies. Have a great day!"
        
        # Basic acknowledgments
        if any(word in question_lower for word in ['ok', 'okay', 'got it', 'understood', 'alright']):
            return "Great! Is there anything specific you'd like to know more about, or do you have other questions about your documents?"
        
        # What can you do
        if any(phrase in question_lower for phrase in ['what can you do', 'what do you do', 'help me']):
            return "I'm CampusGenie! I can help you understand your uploaded course documents by answering questions, providing detailed explanations, and giving you proper citations. Just upload your PDFs and ask me anything about them!"
        
        return None

    def _enhance_answer_formatting(self, answer: str) -> str:
        """
        Enhance answer formatting for better readability and educational value.
        Ensures proper citations and direct educational responses.
        """
        # Ensure proper spacing and formatting
        lines = answer.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Add proper spacing for bullet points and numbered lists
                if line.startswith(('•', '-', '*')):
                    formatted_lines.append(f"  {line}")
                elif line and line[0].isdigit() and '.' in line[:10]:
                    formatted_lines.append(f"  {line}")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append("")  # Preserve empty lines
        
        # Ensure proper paragraph breaks
        formatted_answer = '\n\n'.join(formatted_lines)
        
        # Add citation reminder if no citations are present in educational responses
        if not any(phrase in formatted_answer.lower() for phrase in ['source:', 'reference:', '[source:']):
            formatted_answer += "\n\n*Please refer to the source documents for complete details and proper citations.*"
        
        return formatted_answer

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
