#!/usr/bin/env bash
# Install Claude Code CLI on Raspberry Pi 3 (arm64 / armv7l)
set -euo pipefail

ARCH=$(uname -m)
echo "==> Detected arch: $ARCH"

# --- Node.js (LTS via NodeSource) ---
echo "==> Installing Node.js LTS"
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

node --version
npm --version

# --- Claude Code ---
echo "==> Installing Claude Code"
sudo npm install -g @anthropic-ai/claude-code

# --- API key ---
PROFILE="$HOME/.bashrc"
if ! grep -q "ANTHROPIC_API_KEY" "$PROFILE"; then
    echo "" >> "$PROFILE"
    echo "# Claude Code" >> "$PROFILE"
    echo "export ANTHROPIC_API_KEY=\"\"  # <-- paste your key here" >> "$PROFILE"
    echo "==> Added ANTHROPIC_API_KEY placeholder to $PROFILE"
    echo "    Edit it: nano $PROFILE"
fi

# --- tmux for persistent sessions ---
sudo apt-get install -y tmux

cat > "$HOME/.tmux.conf" << 'EOF'
set -g default-terminal "screen-256color"
set -g mouse on
set -g history-limit 10000
set -g status-right "#H | %H:%M"
bind r source-file ~/.tmux.conf \; display "Config reloaded"
# Vi keys in copy mode
setw -g mode-keys vi
EOF

echo ""
echo "==> Claude Code installed. Next steps:"
echo "    1. Set API key:  nano ~/.bashrc  (find ANTHROPIC_API_KEY line)"
echo "    2. Reload shell: source ~/.bashrc"
echo "    3. Run in tmux:  tmux new -s claude  then  claude"
echo "    4. Detach:       Ctrl+B then D"
echo "    5. Reattach:     tmux attach -t claude"
