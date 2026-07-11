#!/bin/bash
# =============================================================================
# Mosaic — EC2 userdata bootstrap script
# Runs once on first boot as root.
# =============================================================================
set -euo pipefail
exec > /var/log/mosaic-setup.log 2>&1

echo "=== Mosaic bootstrap started at $(date) ==="

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
apt-get update -y
apt-get install -y \
    nginx git curl \
    python3.11 python3.11-venv python3-pip \
    nodejs npm

echo "=== System packages installed ==="

# ---------------------------------------------------------------------------
# 2. Create app user
# ---------------------------------------------------------------------------
useradd -m -s /bin/bash mosaic || true

# ---------------------------------------------------------------------------
# 3. Clone repo
# ---------------------------------------------------------------------------
git clone https://github.com/AdityaWagh19/Mosaic.git /home/mosaic/app
chown -R mosaic:mosaic /home/mosaic/app
chmod 755 /home/mosaic

echo "=== Repo cloned ==="

# ---------------------------------------------------------------------------
# 4. Python virtualenv + dependencies (CPU-only torch to save memory)
# ---------------------------------------------------------------------------
sudo -u mosaic python3.11 -m venv /home/mosaic/app/.venv
sudo -u mosaic /home/mosaic/app/.venv/bin/pip install --upgrade pip --quiet
sudo -u mosaic /home/mosaic/app/.venv/bin/pip install \
    torch==2.4.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu --quiet
sudo -u mosaic /home/mosaic/app/.venv/bin/pip install \
    -r /home/mosaic/app/requirements.txt --quiet

echo "=== Python dependencies installed ==="

# ---------------------------------------------------------------------------
# 5. Frontend build
# ---------------------------------------------------------------------------
cd /home/mosaic/app/frontend
npm install --silent
VITE_API_BASE_URL=/api npm run build
cd /

echo "=== Frontend built ==="

# ---------------------------------------------------------------------------
# 6. nginx config
# ---------------------------------------------------------------------------
cp /home/mosaic/app/deploy/nginx.conf /etc/nginx/sites-available/mosaic
ln -sf /etc/nginx/sites-available/mosaic /etc/nginx/sites-enabled/mosaic
rm -f /etc/nginx/sites-enabled/default

# ---------------------------------------------------------------------------
# 7. systemd service
# ---------------------------------------------------------------------------
cp /home/mosaic/app/deploy/mosaic-api.service /etc/systemd/system/mosaic-api.service

# ---------------------------------------------------------------------------
# 8. sudoers — allow mosaic user to restart its own service
# ---------------------------------------------------------------------------
echo "mosaic ALL=(ALL) NOPASSWD: /bin/systemctl restart mosaic-api, /bin/systemctl status mosaic-api" \
    > /etc/sudoers.d/mosaic
chmod 440 /etc/sudoers.d/mosaic

# ---------------------------------------------------------------------------
# 9. Enable and start services
# ---------------------------------------------------------------------------
systemctl daemon-reload
systemctl enable mosaic-api
systemctl start mosaic-api
systemctl enable nginx
systemctl restart nginx

echo "=== Mosaic bootstrap complete at $(date) ==="
echo "=== Services started. Check: systemctl status mosaic-api nginx ==="
