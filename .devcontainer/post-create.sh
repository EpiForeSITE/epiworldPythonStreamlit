# Install development dependencies. As far as I know, there's no container native
# way to do this that also allows us to specify it through the devcontainer infra.
uv sync --frozen --group dev --no-install-project

# Install some tools that are useful to have in the container, but aren't necessarily needed for the project itself.
sudo apt-get update && sudo apt-get install -y \
    git \
    vim \
    nano \
    curl \
    wget \
