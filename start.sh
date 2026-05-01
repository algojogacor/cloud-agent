#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════"
echo "  ☁️  Cloud Agent - Starting Up"
echo "═══════════════════════════════════════════════════"
echo ""

# Buat data directory untuk SQLite
mkdir -p /app/data
mkdir -p /home/nanobot/.nanobot

export NANOBOT_PORT=${NANOBOT_PORT:-3000}
export NANOBOT_GATEWAY_HOST=${NANOBOT_GATEWAY_HOST:-0.0.0.0}
export NANOBOT_WORKSPACE_PATH=${NANOBOT_WORKSPACE_PATH:-/app/data}
export NANOBOT_RUNTIME_CONFIG=${NANOBOT_RUNTIME_CONFIG:-/home/nanobot/.nanobot/config.json}

echo "📁 Data directory: /app/data"
echo "🔌 Nanobot port: $NANOBOT_PORT"
echo ""
echo "🔑 API Keys loaded:"
echo "   DeepSeek: $(echo $DEEPSEEK_API_KEY_1 | cut -c1-8)... (5 keys)"
echo "   Perplexity: $(echo $PERPLEXITY_API_KEY_1 | cut -c1-8)... (2 keys - native search)"
echo "   Groq: $(echo $GROQ_API_KEY | cut -c1-8)... (fallback)"
echo "   Qwen: $(echo $QWEN_API_KEY | cut -c1-8)... (backup)"
echo "   WhatsApp: public access enabled"
echo ""

echo "🤖 Starting Nanobot..."
echo "═══════════════════════════════════════════════════"

export BRIDGE_PORT=${BRIDGE_PORT:-3001}
export AUTH_DIR=${AUTH_DIR:-/app/data/whatsapp-auth}
export BRIDGE_TOKEN=${BRIDGE_TOKEN:-koyeb-cloud-agent-secure}
export SUPABASE_SYNC_INTERVAL_SECONDS=${SUPABASE_SYNC_INTERVAL_SECONDS:-300}
export SUPABASE_SYNC_ROOT=${SUPABASE_SYNC_ROOT:-/app/data}

python /app/scripts/render_runtime_config.py

mkdir -p "$SUPABASE_SYNC_ROOT"

echo "☁️ Restoring nanobot workspace from Supabase if available..."
python /app/scripts/supabase_auth_sync.py restore || true
mkdir -p "$AUTH_DIR"

if [ -d /app/bridge ] && [ -f /app/bridge/package.json ]; then
    echo "📱 Starting WhatsApp Bridge in background..."
    (
        cd /app/bridge
        npm start
    ) &

    # Give the bridge a moment to initialize
    sleep 3
    echo ""
else
    echo "❌ WhatsApp bridge source is missing at /app/bridge"
    exit 1
fi

sync_workspace_loop() {
    while true; do
        sleep "$SUPABASE_SYNC_INTERVAL_SECONDS"
        python /app/scripts/supabase_auth_sync.py backup || true
    done
}

echo "🔄 Starting periodic Supabase workspace backup..."
sync_workspace_loop &
SYNC_PID=$!

# Trap untuk cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if [ -n "${SYNC_PID:-}" ]; then
        kill "$SYNC_PID" 2>/dev/null || true
    fi
    python /app/scripts/supabase_auth_sync.py backup || true
    exit 0
}
trap cleanup SIGTERM SIGINT

exec nanobot gateway
