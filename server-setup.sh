#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# server-setup.sh — One-time bootstrap for a fresh Ubuntu VPS
# Run as root: bash server-setup.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

APP_USER="greenproof"
APP_DIR="/opt/greenproof"
REPO_URL="https://github.com/YOUR_ORG/greenproof.git"   # ← change this

echo "── 1. System packages ──────────────────────────────────"
apt-get update
apt-get install -y --no-install-recommends \
    python3.12 python3.12-venv python3-pip \
    nginx git curl ufw fail2ban sqlite3

echo "── 2. Firewall ─────────────────────────────────────────"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "── 3. App user ─────────────────────────────────────────"
id "$APP_USER" &>/dev/null || useradd --system --create-home --shell /bin/bash "$APP_USER"

echo "── 4. Clone repo ───────────────────────────────────────"
if [ ! -d "$APP_DIR/.git" ]; then
    git clone "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "── 5. Python virtualenv ────────────────────────────────"
sudo -u "$APP_USER" python3.12 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install gunicorn

echo "── 6. .env file ────────────────────────────────────────"
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "⚠  Edit $APP_DIR/.env with real values before starting the app."
fi
chmod 600 "$APP_DIR/.env"

echo "── 7. DB migration ─────────────────────────────────────"
cd "$APP_DIR"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/flask" db upgrade
sudo -u "$APP_USER" python3 migrations/add_scan_count.py

echo "── 8. Systemd service ──────────────────────────────────"
cp "$APP_DIR/greenproof.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable greenproof
systemctl start greenproof

echo "── 9. Nginx ────────────────────────────────────────────"
cp "$APP_DIR/nginx/nginx.conf" /etc/nginx/nginx.conf
nginx -t
systemctl reload nginx

echo "✅ Server setup complete."
echo "   Next steps:"
echo "   1. Fill in $APP_DIR/.env"
echo "   2. Add TLS certs to /etc/nginx/certs/ (or use Certbot)"
echo "   3. Update 'server_name' in nginx.conf"
echo "   4. systemctl restart greenproof nginx"