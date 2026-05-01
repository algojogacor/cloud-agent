#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def main() -> int:
    target = Path(env("NANOBOT_RUNTIME_CONFIG", "/home/nanobot/.nanobot/config.json"))
    target.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "agents": {
            "defaults": {
                "model": env("NANOBOT_MODEL", "deepseek-chat"),
                "provider": env("NANOBOT_PROVIDER", "deepseek"),
                "workspace": env("NANOBOT_WORKSPACE_PATH", "/app/data"),
            }
        },
        "providers": {
            "deepseek": {
                "api_key": env("DEEPSEEK_API_KEY_1", ""),
            },
            "perplexity": {
                "api_key": env("PERPLEXITY_API_KEY_1", ""),
            },
            "groq": {
                "api_key": env("GROQ_API_KEY", ""),
            },
            "qwen": {
                "api_key": env("QWEN_API_KEY", ""),
            },
        },
        "channels": {
            "whatsapp": {
                "enabled": True,
                "bridgeUrl": env("WHATSAPP_BRIDGE_URL", "ws://127.0.0.1:3001"),
                "bridgeToken": env("BRIDGE_TOKEN", "koyeb-cloud-agent-secure"),
                "allowFrom": [
                    "*",
                    "628999021644",
                    "6289509542780",
                    "6281774156939",
                ],
                "groupPolicy": "open",
            },
            "telegram": {
                "enabled": False,
            },
        },
        "gateway": {
            "host": env("NANOBOT_GATEWAY_HOST", "0.0.0.0"),
            "port": int(env("NANOBOT_PORT", "3000")),
        },
    }

    target.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[render-config] wrote runtime config to {target}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
