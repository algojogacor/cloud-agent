FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install Node.js 20 and runtime deps for the WhatsApp bridge.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg git bubblewrap openssh-client && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get purge -y gnupg && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install nanobot runtime and Supabase client.
RUN uv pip install --system --no-cache nanobot-ai supabase

# MCP server deps.
COPY mcp-servers/brave-search/requirements.txt /tmp/brave-req.txt
COPY mcp-servers/google-workspace/requirements.txt /tmp/google-req.txt
RUN uv pip install --system --no-cache -r /tmp/brave-req.txt \
    && uv pip install --system --no-cache -r /tmp/google-req.txt \
    && rm /tmp/brave-req.txt /tmp/google-req.txt

# MCP server code and bundled WhatsApp bridge.
COPY mcp-servers/ mcp-servers/
COPY bridge/ bridge/
COPY scripts/ scripts/

# Config and entrypoint.
COPY config.json /etc/nanobot/config.json
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Build the WhatsApp bridge once at image build time.
WORKDIR /app/bridge
RUN npm install && npm run build
WORKDIR /app

# Create non-root user and writable app directories.
RUN useradd -m -u 1000 -s /bin/bash nanobot && \
    mkdir -p /home/nanobot/.nanobot /app/data /etc/nanobot && \
    chown -R nanobot:nanobot /home/nanobot /app /etc/nanobot

USER nanobot
ENV HOME=/home/nanobot
ENV NANOBOT_CONFIG=/etc/nanobot/config.json

EXPOSE 18790

ENTRYPOINT ["/usr/local/bin/start.sh"]
