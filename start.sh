#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════"
echo "  ☁️  Cloud Agent - Starting Up"
echo "═══════════════════════════════════════════════════"
echo ""

# Buat data directory untuk SQLite
mkdir -p /app/data

export NANOBOT_PORT=${NANOBOT_PORT:-3000}

echo "📁 Data directory: /app/data"
echo "🔌 Nanobot port: $NANOBOT_PORT"
echo ""
echo "🔑 API Keys loaded:"
echo "   DeepSeek: $(echo $DEEPSEEK_API_KEY_1 | cut -c1-8)... (5 keys)"
echo "   Perplexity: $(echo $PERPLEXITY_API_KEY_1 | cut -c1-8)... (2 keys - native search)"
echo "   Groq: $(echo $GROQ_API_KEY | cut -c1-8)... (fallback)"
echo "   Qwen: $(echo $QWEN_API_KEY | cut -c1-8)... (backup)"
echo "   Telegram: token configured ✓"
echo ""

echo "🤖 Starting Nanobot..."
echo "═══════════════════════════════════════════════════"

export BRIDGE_PORT=3001
export AUTH_DIR=/app/data/whatsapp-auth
export BRIDGE_TOKEN="koyeb-cloud-agent-secure"

echo "📱 Starting WhatsApp Bridge in background..."
(cd /home/nanobot/.nanobot/bridge && npm start) &

# Give the bridge a moment to initialize
sleep 3
echo ""

# Trap untuk cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    exit 0
}
trap cleanup SIGTERM SIGINT

exec nanobot gateway --config "${NANOBOT_CONFIG:-/etc/nanobot/config.json}"
