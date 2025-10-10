#!/bin/bash

# Database backup script for PostgreSQL
# Usage: ./backup.sh [backup_name]

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-data_storage}"
DB_USER="${DB_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename
if [ -n "$1" ]; then
    BACKUP_NAME="$1"
else
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
fi

BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.sql"
BACKUP_FILE_COMPRESSED="$BACKUP_FILE.gz"

echo "Starting database backup: $BACKUP_NAME"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Backup file: $BACKUP_FILE"

# Create database backup
echo "Creating database dump..."
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose \
    --no-password \
    --format=plain \
    --file="$BACKUP_FILE"

# Compress the backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"

# Get file size
BACKUP_SIZE=$(du -h "$BACKUP_FILE_COMPRESSED" | cut -f1)
echo "Backup completed: $BACKUP_FILE_COMPRESSED ($BACKUP_SIZE)"

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    echo "Uploading to S3 bucket: $S3_BUCKET"
    aws s3 cp "$BACKUP_FILE_COMPRESSED" "s3://$S3_BUCKET/database-backups/" \
        --region "$AWS_REGION"
    echo "Upload completed"
fi

# Clean up old backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup process completed successfully!"

# Optional: Send notification
if [ -n "$NOTIFICATION_WEBHOOK" ]; then
    curl -X POST "$NOTIFICATION_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"Database backup completed: $BACKUP_NAME ($BACKUP_SIZE)\"}"
fi
