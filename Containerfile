FROM ubuntu:24.04

# Build arguments
ARG PYTHON_VERSION=3.12
ARG USERNAME=dev

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
ENV PATH="/opt/venv/bin:/opt/uv-python/bin:/home/${USERNAME}/.local/bin:${PATH}"
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /bin/

# Prepare Python dependencies (copy only metadata, not the full source)
COPY ./pyproject.toml ./uv.lock /tmp/project/

# Install system dependencies and Python, then install project dependencies
# Using --no-install-project so only the declared dependencies are installed
# (the project source itself is mounted at runtime via the devcontainer volume)
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        pkg-config \
        sudo && \
    uv python install ${PYTHON_VERSION} && \
    uv --project /tmp/project sync --frozen --python ${PYTHON_VERSION} --no-install-project && \
    chmod -R a+rX /opt/uv-python /opt/venv

# Create a non-root user
# TODO: Figure out the GID situation (currently: --gid 1000 fails because the group already exists).
RUN useradd -m -s $(which bash) $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-nopasswd && \
    chmod 0440 /etc/sudoers.d/90-nopasswd && \
    chown -R $USERNAME:$USERNAME /opt/venv /opt/uv-python

# Final setup
USER $USERNAME
WORKDIR /workspaces/epiworldPythonStreamlit
