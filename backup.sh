#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# backup.sh — Daily SQLite backup with 30-day retention
# Add to crontab: 0 2 * * * /opt/greenproof/scripts/backup.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

DB_PATH="/opt/greenproof/instance/greenproof.db"
BACKUP_DIR="/opt/greenproof/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEST="$BACKUP_DIR/greenproof_$TIMESTAMP.db"
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

# SQLite online backup (safe while the app is running)
sqlite3 "$DB_PATH" ".backup '$DEST'"
gzip "$DEST"

echo "✅ Backup saved: ${DEST}.gz"

# Prune old backups
find "$BACKUP_DIR" -name "*.db.gz" -mtime +$KEEP_DAYS -delete
echo "🗑  Pruned backups older than $KEEP_DAYS days"