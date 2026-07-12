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
# 1. Start Deployment
# ---------------------------------------------------------------------------
echo "--- Starting backend deployment ---"

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

echo "=== Deploy complete at $(date) ==="
