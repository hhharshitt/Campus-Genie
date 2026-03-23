#!/bin/bash
# CampusGenie — Ollama Model Init Script
# Pulls the Llama 3 model after Ollama server starts.
# Run this once after: docker compose up

set -e

OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
MODEL="${OLLAMA_MODEL:-llama3}"

echo "🦙 Waiting for Ollama to be ready..."
until curl -sf "$OLLAMA_URL/api/tags" > /dev/null; do
  echo "   ...not ready yet, retrying in 3s"
  sleep 3
done

echo "✅ Ollama is up. Pulling model: $MODEL"
curl -X POST "$OLLAMA_URL/api/pull" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$MODEL\"}" \
  --no-buffer

echo ""
echo "🎉 Model '$MODEL' is ready. CampusGenie can now answer questions!"
