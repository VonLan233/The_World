#!/bin/bash
set -e

echo "=========================================="
echo "  The World - One-Click Startup"
echo "=========================================="

# Step 1: Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "[1/3] Creating .env from .env.example..."
    cp .env.example .env
    echo "      Created .env -- edit it to customize settings."
else
    echo "[1/3] .env already exists, skipping."
fi

# Step 2: Build Docker images
echo "[2/3] Building Docker images..."
docker compose build

# Step 3: Start all services
echo "[3/3] Starting all services..."
docker compose up -d

echo ""
echo "=========================================="
echo "  Services starting up..."
echo "=========================================="
echo ""
echo "  Frontend:  http://localhost:${FRONTEND_PORT:-3000}"
echo "  Backend:   http://localhost:${BACKEND_PORT:-8000}"
echo "  API Docs:  http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
echo "  To view logs:      docker compose logs -f"
echo "  To stop:           docker compose down"
echo "  To include Ollama: docker compose --profile ai up -d"
echo ""
