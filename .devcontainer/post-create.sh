echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
echo 'export LANG=C.UTF-8' >> "$HOME/.bashrc"
echo 'export LC_ALL=C.UTF-8' >> "$HOME/.bashrc"

export PATH="$HOME/.local/bin:$PATH"
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# Install project dependencies
if [ -f requirements.txt ]; then
    uv pip install -r requirements.txt
fi
