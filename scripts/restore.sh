#!/bin/bash

# Database restore script for PostgreSQL
# Usage: ./restore.sh <backup_file>

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-data_storage}"
DB_USER="${DB_USER:-postgres}"

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/backup_20240101_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found"
    exit 1
fi

echo "Starting database restore..."
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Backup file: $BACKUP_FILE"

# Confirm restore operation
read -p "This will replace all data in the database. Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Create temporary database for restore
TEMP_DB="temp_restore_$(date +%s)"
echo "Creating temporary database: $TEMP_DB"

createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TEMP_DB"

# Restore to temporary database
echo "Restoring to temporary database..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TEMP_DB"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TEMP_DB" -f "$BACKUP_FILE"
fi

# Verify restore
echo "Verifying restore..."
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TEMP_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo "Tables restored: $TABLE_COUNT"

# Final confirmation
read -p "Restore verification complete. Replace production database? (yes/no): " final_confirm
if [ "$final_confirm" != "yes" ]; then
    echo "Restore cancelled. Cleaning up temporary database..."
    dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TEMP_DB"
    exit 0
fi

# Drop and recreate production database
echo "Replacing production database..."
dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" || true
createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

# Restore to production database
echo "Restoring to production database..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE"
fi

# Clean up temporary database
dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TEMP_DB"

echo "Database restore completed successfully!"
echo "Please restart your application to ensure all connections are refreshed."
