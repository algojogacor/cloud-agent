# D:\cloud-agent\setup.ps1 — Copy nanobot source + build Docker image

param(
    [string]$NanobotPath = "D:\nanobot"
)

$ErrorActionPreference = "Stop"
Write-Host "🐱 Setting up cloud-agent..." -ForegroundColor Cyan

# 1. Copy nanobot Python package
Write-Host "  → Copying nanobot source from $NanobotPath..."
if (-not (Test-Path "$NanobotPath\nanobot\__init__.py")) {
    Write-Host "ERROR: nanobot source not found at $NanobotPath\nanobot\" -ForegroundColor Red
    Write-Host "If nanobot is installed via pip, you can skip this. The Dockerfile will install from PyPI."
    exit 1
}
Copy-Item -Recurse -Force "$NanobotPath\nanobot" ".\nanobot"
Copy-Item -Force "$NanobotPath\pyproject.toml", "$NanobotPath\README.md", "$NanobotPath\LICENSE" "." -ErrorAction SilentlyContinue
Write-Host "  ✅ Nanobot source copied" -ForegroundColor Green

# 2. Copy .env if not exists
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  ✏️  Created .env — EDIT THIS with your API keys!" -ForegroundColor Yellow
}

# 3. Build Docker image
Write-Host "  🔨 Building Docker image..."
docker build -t cloud-agent:latest .
Write-Host "  ✅ Image built: cloud-agent:latest" -ForegroundColor Green

# 4. Done
Write-Host ""
Write-Host "🚀 Setup complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test locally:"
Write-Host "  docker run --rm -p 18790:18790 --env-file .env cloud-agent:latest"
Write-Host ""
Write-Host "To deploy to Koyeb:"
Write-Host "  1. Tag: docker tag cloud-agent:latest <your-registry>/cloud-agent:latest"
Write-Host "  2. Push: docker push <your-registry>/cloud-agent:latest"
Write-Host "  3. Deploy on Koyeb → Use Docker image"
Write-Host "  4. Set env vars from .env"
