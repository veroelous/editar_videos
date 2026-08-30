#!/bin/bash
set -euo pipefail

# Only needed for Claude Code on the web — each session starts from a fresh
# container, so the video-use skill's deps must be reinstalled every time.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

SKILL_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/skills/video-use"

if ! command -v ffmpeg >/dev/null 2>&1; then
  apt-get update -qq && apt-get install -y -qq ffmpeg
fi

if [ -d "$SKILL_DIR" ]; then
  cd "$SKILL_DIR"
  if command -v uv >/dev/null 2>&1; then
    uv sync
  else
    pip install -e . -q
  fi

  if [ ! -f .env ] && [ -z "${ELEVENLABS_API_KEY:-}" ]; then
    echo "NOTE: video-use skill has no ELEVENLABS_API_KEY set (needed for transcription)." >&2
    echo "      Add it to $SKILL_DIR/.env or as an environment variable." >&2
  fi
fi
