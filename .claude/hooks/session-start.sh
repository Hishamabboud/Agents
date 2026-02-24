#!/bin/bash
set -euo pipefail

# Only run in remote (web) sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Node.js dependencies (uses cache on subsequent runs)
cd "$CLAUDE_PROJECT_DIR"
npm install

# Install Python dependencies
pip install beautifulsoup4 requests --break-system-packages -q

# Create required output directories
mkdir -p output/tailored-resumes output/cover-letters output/screenshots data logs

# Install Playwright chromium browser (may take a while on first run)
npx playwright install chromium || echo "Warning: Playwright chromium install failed, will retry on next session"
