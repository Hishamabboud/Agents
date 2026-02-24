#!/bin/bash
# Job Hunter Orchestrator — runs the full pipeline sequentially.
#
# Usage:
#   bash scripts/run.sh           # Full pipeline
#   bash scripts/run.sh search    # Search only
#   bash scripts/run.sh score     # Score only
#   bash scripts/run.sh tailor    # Tailor only
#   bash scripts/run.sh apply     # Apply only

set -euo pipefail

cd ~/job-hunter

LOG_FILE="logs/agent.log"
mkdir -p logs

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $*" | tee -a "$LOG_FILE"
}

run_search() {
    log "Starting job search..."
    python3 scripts/search.py >> "$LOG_FILE" 2>&1
    log "Search phase complete."
}

run_score() {
    log "Starting job scoring..."
    python3 scripts/score.py >> "$LOG_FILE" 2>&1
    log "Scoring phase complete."
}

run_tailor() {
    log "Starting resume tailoring..."
    python3 scripts/tailor.py >> "$LOG_FILE" 2>&1
    log "Tailoring phase complete."
}

run_apply() {
    log "Starting application submissions..."
    python3 scripts/apply.py --max-applications 5 >> "$LOG_FILE" 2>&1
    log "Application phase complete."
}

# Determine which phases to run
PHASE="${1:-all}"

log "=== Job Hunt Cycle Started (phase: $PHASE) ==="

case "$PHASE" in
    search)
        run_search
        ;;
    score)
        run_score
        ;;
    tailor)
        run_tailor
        ;;
    apply)
        run_apply
        ;;
    all)
        run_search
        run_score
        run_tailor
        run_apply
        ;;
    *)
        echo "Usage: $0 {search|score|tailor|apply|all}"
        exit 1
        ;;
esac

log "=== Job Hunt Cycle Complete ==="
