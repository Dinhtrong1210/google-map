#!/bin/bash
# ============================================
# Deploy Review Bot Web tren VPS bang Docker
# Chay script nay tren VPS voi quyen root
# ============================================

set -e

APP_DIR="/opt/reviewbot"
REPO_URL="${1:-}"

echo "========================================="
echo "  Review Bot - Docker Deploy Script"
echo "========================================="

if [ "$EUID" -ne 0 ]; then
    echo "Hay chay script voi quyen root!"
    echo "  sudo bash deploy.sh YOUR_GITHUB_REPO_URL"
    exit 1
fi

# 1. System update
echo "[1/7] System update..."
apt update -y && apt upgrade -y

# 2. Install dependencies
echo "[2/7] Installing dependencies..."
apt install -y git curl

# 3. Check Docker
if ! command -v docker &> /dev/null; then
    echo "  Docker not found! Installing..."
    curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version &> /dev/null; then
    echo "  Docker Compose not found! Installing..."
    apt install -y docker-compose-plugin
fi

# 4. Clone or pull code
echo "[3/7] Getting code..."
if [ -n "$REPO_URL" ]; then
    if [ -d "$APP_DIR/.git" ]; then
        cd $APP_DIR
        git pull origin main || git pull origin master
    else
        rm -rf $APP_DIR
        git clone $REPO_URL $APP_DIR
    fi
else
    if [ -d "$APP_DIR" ]; then
        cd $APP_DIR
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
    else
        echo "  ERROR: Khong co repo URL va $APP_DIR khong ton tai!"
        echo "  Hay clone repo vao $APP_DIR truoc, hoac chay:"
        echo "    sudo bash deploy.sh https://github.com/USER/REPO.git"
        exit 1
    fi
fi

# 5. Create data directory
echo "[4/7] Preparing data directory..."
mkdir -p $APP_DIR/data

# 6. Generate FLASK_SECRET
FLASK_SECRET=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 64)
echo "  FLASK_SECRET: ${FLASK_SECRET:0:8}..."

# 7. Update docker-compose with secret
cd $APP_DIR
sed -i "s/FLASK_SECRET=CHANGE_ME_TO_RANDOM_STRING/FLASK_SECRET=$FLASK_SECRET/" docker-compose.yml

# 8. Build and run
echo "[5/7] Building Docker image..."
docker compose build

echo "[6/7] Starting service..."
docker compose down 2>/dev/null || true
docker compose up -d

# 9. Verify
echo "[7/7] Verifying..."
sleep 5
if docker compose ps | grep -q "running"; then
    STATUS="RUNNING"
else
    STATUS="STOPPED"
fi

VPS_IP=$(curl -s ifconfig.me)

echo ""
echo "========================================="
echo "  DEPLOY THANH CONG!"
echo "========================================="
echo ""
echo "  Status:       $STATUS"
echo "  Web admin:    http://$VPS_IP:5000"
echo "  Tool API:     http://$VPS_IP:5000"
echo "  Admin login:  admin / admin123"
echo ""
echo "  FLASK_SECRET: $FLASK_SECRET"
echo ""
echo "  =========================================="
echo "  CAU HINH SEPAY:"
echo "  =========================================="
echo "  Sua file docker-compose.yml, then:"
echo "    cd $APP_DIR && docker compose up -d"
echo ""
echo "  =========================================="
echo "  QUAN LY:"
echo "  =========================================="
echo "  cd $APP_DIR"
echo "  docker compose logs -f           # Xem log"
echo "  docker compose restart           # Restart"
echo "  docker compose down              # Dung"
echo "  docker compose up -d             # Chay lai"
echo "  docker compose ps                # Kiem tra trang thai"
echo ""
echo "  =========================================="
echo "  UPDATE CODE:"
echo "  =========================================="
echo "  cd $APP_DIR && git pull && docker compose up -d --build"
echo ""
echo "  =========================================="
echo "  CAU HINH TOOL DESKTOP:"
echo "  =========================================="
echo "  Server URL: http://$VPS_IP:5000"
echo ""
