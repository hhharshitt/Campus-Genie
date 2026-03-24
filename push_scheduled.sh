#!/bin/bash
# =============================================================================
# CampusGenie — Scheduled Commit Pusher
# Pushes one commit every 12 hours to GitHub.
#
# SETUP (run once on your Mac):
#   1. cd ~/Desktop/Campus-Genie
#   2. chmod +x push_scheduled.sh
#   3. Edit REPO_DIR and GITHUB_TOKEN below
#   4. ./push_scheduled.sh
#
# It will run in the background. Each commit goes live every 12 hours.
# Total: 11 commits over ~5.5 days
# =============================================================================

# ── CONFIG — edit these ───────────────────────────────────────────────────────
REPO_DIR="$HOME/Desktop/Campus-Genie"         # path to your cloned repo
GITHUB_TOKEN="YOUR_GITHUB_PAT_HERE"           # your GitHub Personal Access Token
GITHUB_USER="asutoshsabat91"
GITHUB_REPO="Campus-Genie"
INTERVAL_HOURS=12
# ─────────────────────────────────────────────────────────────────────────────

REMOTE_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"
LOG_FILE="$REPO_DIR/push_log.txt"
STATE_FILE="$REPO_DIR/.push_state"

# All 11 commit hashes in order (oldest → newest)
COMMITS=(
  "f2d2019e14fa021948612d07128a5bb275590556"  # 1  chore: initial project scaffold
  "6a0ac818931b39a20770b736a408c60b93350297"  # 2  feat(backend): FastAPI skeleton
  "8372f4837450b70fdf9fb87b55c7bfaebbf0a6f3"  # 3  feat(rag): PDF processor and text chunker
  "a86c0d814f4f79b574fc386b34711b3184e8fc22"  # 4  feat(rag): ChromaDB vector store client
  "6cb2371c2f41b11bc21f5b12fc1bdbabfcf5b95f"  # 5  feat(rag): sentence-transformer embeddings
  "fe1ddbad722268c7c3d469fe9fe7a614e041bda4"  # 6  feat(rag): Ollama LLM client
  "e8ec64ba554f6e10f66b3c812c6d9ef517c61cfd"  # 7  feat(rag): RAG pipeline + document indexer
  "c27cd303121246cb9f45dcf0d9b3317366d64712"  # 8  feat(rag): RAG pipeline orchestrator
  "89f13eaa12f1b514766a32b5f013a87f8d262d46"  # 9  feat(api): wire up /documents and /chat
  "0f3bbee9e3174c8b77d9b6fd8d39b80d5b71c882"  # 10 feat(frontend): Streamlit UI
  "4dcb80265145991354362a0bd2d29c58cb10357e"  # 11 feat(docker): docker-compose
)

COMMIT_LABELS=(
  "chore: initial project scaffold"
  "feat(backend): FastAPI skeleton with project structure"
  "feat(rag): PDF processor and text chunker"
  "feat(rag): ChromaDB vector store client"
  "feat(rag): sentence-transformer embedding engine"
  "feat(rag): Ollama LLM client with anti-hallucination prompt"
  "feat(rag): RAG pipeline + document indexer"
  "feat(rag): RAG pipeline orchestrator"
  "feat(api): wire up /documents and /chat routes to RAG pipeline"
  "feat(frontend): Streamlit UI — upload + chat interface"
  "feat(docker): docker-compose with 4-service orchestration"
)

TOTAL=${#COMMITS[@]}

# ── Helpers ───────────────────────────────────────────────────────────────────

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

get_next_index() {
  if [ -f "$STATE_FILE" ]; then
    cat "$STATE_FILE"
  else
    echo "0"
  fi
}

save_index() {
  echo "$1" > "$STATE_FILE"
}

push_commit() {
  local idx=$1
  local hash=${COMMITS[$idx]}
  local label=${COMMIT_LABELS[$idx]}

  log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "Pushing commit $((idx + 1))/$TOTAL: $label"
  log "Hash: $hash"

  cd "$REPO_DIR" || { log "ERROR: Cannot cd to $REPO_DIR"; exit 1; }

  # Set the remote with token
  git remote set-url origin "$REMOTE_URL"

  # Push exactly this commit (not the whole branch yet)
  git push origin "${hash}:refs/heads/main" 2>>"$LOG_FILE"

  if [ $? -eq 0 ]; then
    log "✅ Successfully pushed: $label"
    save_index $((idx + 1))
  else
    log "❌ Push failed for commit $((idx + 1)). Will retry next run."
  fi
}

# ── Main loop ─────────────────────────────────────────────────────────────────

mkdir -p "$REPO_DIR"
log "🚀 CampusGenie scheduled pusher started"
log "📁 Repo: $REPO_DIR"
log "⏱  Interval: every ${INTERVAL_HOURS} hours"
log "📦 Total commits to push: $TOTAL"

while true; do
  NEXT=$(get_next_index)

  if [ "$NEXT" -ge "$TOTAL" ]; then
    log "🎉 All $TOTAL commits pushed successfully! Script done."
    exit 0
  fi

  push_commit "$NEXT"

  REMAINING=$((TOTAL - NEXT - 1))
  if [ "$REMAINING" -gt 0 ]; then
    log "⏳ Next push in ${INTERVAL_HOURS} hours. ($REMAINING commits remaining)"
    sleep $((INTERVAL_HOURS * 3600))
  fi
done
