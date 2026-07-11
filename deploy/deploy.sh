#!/bin/bash
# =============================================================================
# Mosaic — deploy script
# Runs on the EC2 instance via GitHub Actions SSH on every push to main.
# =============================================================================
set -euo pipefail

APP=/home/mosaic/app
VENV=$APP/.venv

echo "=== Deploy started at $(date) ==="

cd "$APP"

# ---------------------------------------------------------------------------
# 1. Pull latest code
# ---------------------------------------------------------------------------
echo "--- Pulling latest code ---"
git fetch origin main
git reset --hard origin/main
echo "Now at: $(git log -1 --oneline)"

# ---------------------------------------------------------------------------
# 2. Python deps — only reinstalls if requirements.txt changed
# ---------------------------------------------------------------------------
echo "--- Updating Python dependencies ---"
$VENV/bin/pip install \
    torch==2.4.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu \
    --no-cache-dir --quiet --exists-action i
$VENV/bin/pip install -r requirements.txt --no-cache-dir --quiet --exists-action i

# ---------------------------------------------------------------------------
# 4. Restart API service (passwordless via sudoers)
# ---------------------------------------------------------------------------
echo "--- Restarting API service ---"
sudo /bin/systemctl restart mosaic-api
sleep 3
sudo /bin/systemctl status mosaic-api --no-pager --lines 5

echo "=== Deploy complete at $(date) ==="
