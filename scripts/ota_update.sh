#!/bin/bash
# M.A.S.H. IoT - OTA Update Script with A/B Rollback
#
# Usage: bash ota_update.sh <tarball_path> <target_version>
#
# This script:
# 1. Backs up the current rpi_gateway/ to rpi_gateway.old/
# 2. Extracts the new release tarball
# 3. Preserves config, venv, and database
# 4. Installs new dependencies
# 5. Restarts the service
# 6. Runs a health check
# 7. Rolls back automatically if health check fails

set -euo pipefail

TARBALL_PATH="$1"
TARGET_VERSION="$2"

if [ -z "$TARBALL_PATH" ] || [ -z "$TARGET_VERSION" ]; then
    echo "Usage: bash ota_update.sh <tarball_path> <target_version>"
    exit 1
fi

# Navigate to the project root (one level above scripts/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RPI_DIR="$PROJECT_ROOT/rpi_gateway"
BACKUP_DIR="$PROJECT_ROOT/rpi_gateway.old"
FAILED_DIR="$PROJECT_ROOT/rpi_gateway.failed"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

HEALTH_CHECK_URL="http://localhost:5000/api/version"
HEALTH_CHECK_TIMEOUT=30
SERVICE_NAME="mash-iot.service"

echo "========================================="
echo " M.A.S.H. IoT - OTA Update"
echo " Target: v${TARGET_VERSION}"
echo "========================================="
echo ""

# ---------------------------------------------------------------------------
# Step 1: Validate tarball
# ---------------------------------------------------------------------------
echo "[1/7] Validating update package..."
if [ ! -f "$TARBALL_PATH" ]; then
    echo "ERROR: Tarball not found: $TARBALL_PATH"
    exit 1
fi

# Basic validation: check it's a valid gzip
if ! gzip -t "$TARBALL_PATH" 2>/dev/null; then
    echo "ERROR: Invalid tarball (corrupt or not gzip format)"
    exit 1
fi

echo "  Package: $(basename "$TARBALL_PATH")"
echo "  Size: $(du -h "$TARBALL_PATH" | cut -f1)"
echo ""

# ---------------------------------------------------------------------------
# Step 2: Create backup of current installation
# ---------------------------------------------------------------------------
echo "[2/7] Backing up current installation..."

# Remove old backup if it exists
if [ -d "$BACKUP_DIR" ]; then
    echo "  Removing previous backup..."
    rm -rf "$BACKUP_DIR"
fi

# Remove any previous failed update
if [ -d "$FAILED_DIR" ]; then
    rm -rf "$FAILED_DIR"
fi

# Copy current installation to backup
cp -a "$RPI_DIR" "$BACKUP_DIR"
echo "  Backed up to: rpi_gateway.old/"
echo ""

# ---------------------------------------------------------------------------
# Step 3: Extract new release
# ---------------------------------------------------------------------------
echo "[3/7] Extracting update package..."

# Create a temp directory for extraction
TEMP_EXTRACT=$(mktemp -d)

# Extract tarball
tar -xzf "$TARBALL_PATH" -C "$TEMP_EXTRACT"

# Find the rpi_gateway directory in the extracted content
# It might be at root level or nested one level deep
if [ -d "$TEMP_EXTRACT/rpi_gateway" ]; then
    EXTRACT_SOURCE="$TEMP_EXTRACT/rpi_gateway"
elif [ -d "$TEMP_EXTRACT/app" ]; then
    # Direct content without wrapper directory
    EXTRACT_SOURCE="$TEMP_EXTRACT"
else
    # Try to find it one directory deep
    EXTRACT_SOURCE=$(find "$TEMP_EXTRACT" -maxdepth 2 -name "app" -type d -exec dirname {} \; | head -1)
    if [ -z "$EXTRACT_SOURCE" ]; then
        echo "ERROR: Could not find rpi_gateway content in tarball"
        rm -rf "$TEMP_EXTRACT"
        # Restore backup
        rm -rf "$RPI_DIR"
        mv "$BACKUP_DIR" "$RPI_DIR"
        exit 1
    fi
fi

echo "  Found content at: $EXTRACT_SOURCE"
echo ""

# ---------------------------------------------------------------------------
# Step 4: Apply update (preserve config, venv, database)
# ---------------------------------------------------------------------------
echo "[4/7] Applying update (preserving config and data)..."

# Items to preserve from the current installation
PRESERVE_ITEMS=(
    "venv"
    "config"
    "rpi_gateway/data.db"
    "rpi_gateway/data"
)

# Copy the new files over (except preserved items)
# First, remove non-preserved items from current
find "$RPI_DIR" -mindepth 1 -maxdepth 1 \
    ! -name "venv" \
    ! -name "config" \
    ! -name "data.db" \
    ! -name "data" \
    ! -name "__pycache__" \
    -exec rm -rf {} +

# Copy new files from extraction
find "$EXTRACT_SOURCE" -mindepth 1 -maxdepth 1 \
    ! -name "venv" \
    ! -name "config" \
    ! -name "data.db" \
    ! -name "data" \
    -exec cp -a {} "$RPI_DIR/" \;

echo "  Files updated (config, venv, and data preserved)"

# Clean up extraction temp directory
rm -rf "$TEMP_EXTRACT"
echo ""

# ---------------------------------------------------------------------------
# Step 5: Install/update dependencies
# ---------------------------------------------------------------------------
echo "[5/7] Checking for updated dependencies..."

if [ -f "$RPI_DIR/requirements.txt" ] && [ -d "$RPI_DIR/venv" ]; then
    source "$RPI_DIR/venv/bin/activate"
    pip install -r "$RPI_DIR/requirements.txt" --quiet 2>/dev/null || {
        echo "  WARNING: Some dependencies failed to install"
    }
    deactivate
    echo "  Dependencies updated"
else
    echo "  WARNING: Skipping dependency install (venv or requirements.txt not found)"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 6: Restart service
# ---------------------------------------------------------------------------
echo "[6/7] Restarting MASH IoT service..."

sudo systemctl restart "$SERVICE_NAME"

echo "  Service restarted, waiting for startup..."
echo ""

# ---------------------------------------------------------------------------
# Step 7: Health check
# ---------------------------------------------------------------------------
echo "[7/7] Running health check (${HEALTH_CHECK_TIMEOUT}s timeout)..."

HEALTH_OK=false
for i in $(seq 1 $HEALTH_CHECK_TIMEOUT); do
    sleep 1
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        # Verify the version matches
        RESPONSE=$(curl -s "$HEALTH_CHECK_URL" 2>/dev/null)
        REPORTED_VERSION=$(echo "$RESPONSE" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)

        if [ "$REPORTED_VERSION" = "$TARGET_VERSION" ]; then
            HEALTH_OK=true
            echo "  Health check PASSED (v${REPORTED_VERSION} running, ${i}s elapsed)"
            break
        else
            echo "  Version mismatch: expected v${TARGET_VERSION}, got v${REPORTED_VERSION}"
        fi
    fi

    # Show progress every 5 seconds
    if [ $((i % 5)) -eq 0 ]; then
        echo "  Waiting... (${i}/${HEALTH_CHECK_TIMEOUT}s, HTTP: ${HTTP_CODE})"
    fi
done

if [ "$HEALTH_OK" = true ]; then
    # Success -- clean up tarball
    echo ""
    echo "========================================="
    echo " Update to v${TARGET_VERSION} SUCCESSFUL"
    echo "========================================="
    echo ""
    echo "  Backup kept at: rpi_gateway.old/"
    echo "  Remove with: rm -rf rpi_gateway.old/"

    # Clean up the downloaded tarball
    rm -f "$TARBALL_PATH"

    exit 0
else
    # Health check failed -- ROLLBACK
    echo ""
    echo "  Health check FAILED after ${HEALTH_CHECK_TIMEOUT}s"
    echo ""
    echo "========================================="
    echo " ROLLING BACK to previous version"
    echo "========================================="

    # Move failed update out of the way
    mv "$RPI_DIR" "$FAILED_DIR"

    # Restore backup
    mv "$BACKUP_DIR" "$RPI_DIR"

    # Restart service with the restored version
    sudo systemctl restart "$SERVICE_NAME"

    echo ""
    echo "  Rollback complete. Previous version restored."
    echo "  Failed update saved at: rpi_gateway.failed/"
    echo "  Check logs with: journalctl -u $SERVICE_NAME -n 50"
    echo ""

    # Clean up tarball
    rm -f "$TARBALL_PATH"

    exit 1
fi
