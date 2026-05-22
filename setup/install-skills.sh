#!/usr/bin/env bash
# Install Claude Code slash-command skills to ~/.claude/commands/
set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "$0")/../config/claude-skills" && pwd)"
DEST="$HOME/.claude/commands"

mkdir -p "$DEST"

for f in "$SKILLS_DIR"/*.md; do
    name=$(basename "$f")
    cp "$f" "$DEST/$name"
    echo "  installed: $name"
done

echo ""
echo "Skills installed to $DEST"
echo "Use in Claude Code: /caveman  /remember  /pi  /retro"
