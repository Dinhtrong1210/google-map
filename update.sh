#!/bin/bash
# ============================================
# Cap nhat Review Bot tren VPS (Docker)
# ============================================

set -e

APP_DIR="/opt/reviewbot"

echo "========================================="
echo "  Review Bot - Update Script"
echo "========================================="

cd $APP_DIR

echo "[1/3] Pulling latest code..."
git pull origin main || git pull origin master

echo "[2/3] Rebuilding Docker image..."
docker compose build

echo "[3/3] Restarting service..."
docker compose up -d

echo ""
echo "========================================="
echo "  UPDATE THANH CONG!"
echo "========================================="
docker compose ps
