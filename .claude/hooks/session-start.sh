#!/bin/bash
set -euo pipefail
# Only needed in Claude Code on the web containers.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
"$CLAUDE_PROJECT_DIR/reel/scripts/setup.sh"
