#!/usr/bin/env bash
# Launch or reattach Claude Code in a named tmux session
# Usage: ./claude-session.sh [session-name]
SESSION="${1:-creative}"

if ! command -v claude &>/dev/null; then
    echo "Claude Code not installed. Run: bash setup/claude-code.sh"
    exit 1
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "==> Starting new tmux session: $SESSION"
    tmux new-session -d -s "$SESSION" -x 220 -y 50
    tmux send-keys -t "$SESSION" "cd ~/PI3 && claude --dangerously-skip-permissions" Enter
    echo "==> Session started. Attaching..."
fi

tmux attach-session -t "$SESSION"
