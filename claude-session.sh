#!/usr/bin/env bash
# Launch or reattach Claude Code in the fixed tmux session:window used by the phone server.
# Session "setup", window "claude" — phone UI reads from setup:claude via SSE.
SESSION="setup"
WINDOW="claude"

if ! command -v claude &>/dev/null; then
    echo "Claude Code not installed. Run: bash setup/claude-code.sh"
    exit 1
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "==> Creating tmux session: $SESSION"
    tmux new-session -d -s "$SESSION" -n "$WINDOW" -x 220 -y 50
    tmux send-keys -t "$SESSION:$WINDOW" "cd ~/PI3 && claude --dangerously-skip-permissions" Enter
    echo "==> Session started."
elif ! tmux list-windows -t "$SESSION" -F '#W' | grep -qx "$WINDOW"; then
    echo "==> Creating window $WINDOW in session $SESSION"
    tmux new-window -t "$SESSION" -n "$WINDOW"
    tmux send-keys -t "$SESSION:$WINDOW" "cd ~/PI3 && claude --dangerously-skip-permissions" Enter
fi

echo "==> Attaching to $SESSION:$WINDOW"
tmux attach-session -t "$SESSION"
