FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# ── Minimal system deps ──────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install nanobot from PyPI ────────────────────────────
RUN uv pip install --system --no-cache nanobot-ai

# ── MCP server deps ─────────────────────────────────────
COPY mcp-servers/brave-search/requirements.txt /tmp/brave-req.txt
COPY mcp-servers/google-workspace/requirements.txt /tmp/google-req.txt
RUN uv pip install --system --no-cache -r /tmp/brave-req.txt \
    && uv pip install --system --no-cache -r /tmp/google-req.txt \
    && rm /tmp/brave-req.txt /tmp/google-req.txt

# ── MCP server code ─────────────────────────────────────
COPY mcp-servers/ mcp-servers/

# ── Config & entrypoint ─────────────────────────────────
COPY config.json /etc/nanobot/config.json
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# ── User setup ──────────────────────────────────────────
RUN useradd -m -u 1000 -s /bin/bash nanobot && \
    mkdir -p /home/nanobot/.nanobot && \
    chown -R nanobot:nanobot /home/nanobot /app /etc/nanobot

USER nanobot
ENV HOME=/home/nanobot
ENV NANOBOT_CONFIG=/etc/nanobot/config.json

# ── Prebuild WhatsApp Bridge ────────────────────────────
RUN python -c "from nanobot.channels.whatsapp import _ensure_bridge_setup; _ensure_bridge_setup()"

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/start.sh"]
