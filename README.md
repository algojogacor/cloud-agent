# ☁️ Cloud Agent - Always-On AI Assistant

Bot WhatsApp 24/7 di Koyeb (free tier) — riset internet (Perplexity native search), DeepSeek key rotation (5 keys auto-fallback).

## 🚀 Features

- **Always-On**: Jalan 24/7 di Koyeb free tier (512MB)
- **Multi-Provider**: DeepSeek (5 keys) → Perplexity (native search) → Groq → Qwen
- **Search**: Perplexity sonar/sonar-pro built-in web search (no MCP needed)
- **WhatsApp Bot**: Chat interface
- **Persistence**: Supabase Storage backup for the whole nanobot workspace
- **Zero Cost**: Semua free tier

## 📁 Structure

```
cloud-agent/
├── Dockerfile              # Build container
├── nanobot.toml           # Multi-provider config
├── .env.example           # Template env vars
├── start.sh               # Entrypoint
├── docker-compose.yml     # Local testing
└── mcp-servers/           # Optional MCP (Brave Search + Google Workspace)
```

## ⚡ Quick Start

### 1. Prerequisites

- Docker Desktop
- API keys (DeepSeek, Groq, Qwen, Perplexity)

### 2. Setup

```powershell
copy .env.example .env
# Edit .env with your API keys
notepad .env
```

### 3. Build & Test

```powershell
docker-compose up --build
```

### 4. Test Bot

- Jalankan container
- Scan QR WhatsApp dari log bridge
- Chat nomor yang terhubung

## 🐳 Deploy ke Koyeb

### Prerequisites

- GitHub repo connected
- Koyeb account (free tier)

### Deploy Steps

1. Push code to GitHub
2. Create Koyeb Service: GitHub → repo → branch `cloud-agent`
3. Builder: **Dockerfile**
4. Instance: **Free** (0.1 vCPU, 512MB RAM)
5. Port: **3000**
6. Env vars — copy from `.env`:

```
DEEPSEEK_API_KEY_1=sk-xxx
DEEPSEEK_API_KEY_2=sk-xxx
DEEPSEEK_API_KEY_3=sk-xxx
DEEPSEEK_API_KEY_4=sk-xxx
DEEPSEEK_API_KEY_5=sk-xxx
GROQ_API_KEY=gsk_xxx
QWEN_API_KEY=sk-xxx
PERPLEXITY_API_KEY_1=pplx-xxx
PERPLEXITY_API_KEY_2=pplx-xxx
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=nanobot-private
SUPABASE_WORKSPACE_OBJECT=nanobot/workspace.zip
```

### Supabase Notes

- Supabase Storage is used to restore and back up the whole `/app/data` workspace automatically.
- This includes WhatsApp auth, nanobot memory, sessions, and generated workspace files.
- On first boot, scan the QR code once. After that, the restored workspace should keep the session and memory across restarts.
- `SUPABASE_DB_URL` is optional right now. This repo still persists state as files, but those files are synced to Supabase.

## 🆓 Cost

| Service | Cost |
|---------|------|
| Koyeb Nano | **$0** |
| DeepSeek | **$0** (free x5) |
| Perplexity | **$0** (free tier) |
| Groq | **$0** |
| **Total** | **$0/month** |

## 🧠 How It Works

Model routing priority:
1. Perplexity `sonar` — native web search
2. Perplexity `sonar-pro` — better search
3. DeepSeek (5 keys) — reasoning
4. Groq — fast fallback
5. Qwen — last backup
