#!/bin/bash
# M.A.S.H. IoT - Fix Script Permissions
# Run this if scripts won't execute due to permission errors

echo "========================================="
echo " M.A.S.H. IoT - Fixing Script Permissions"
echo "========================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Setting execute permissions on all scripts..."
echo ""

# Make all shell scripts executable
chmod +x "$PROJECT_DIR/scripts/"*.sh 2>/dev/null
echo "✓ Shell scripts (.sh)"

# Make all Python scripts executable
chmod +x "$PROJECT_DIR/scripts/"*.py 2>/dev/null
echo "✓ Python scripts (.py)"

# Specifically ensure critical scripts are executable
chmod +x "$PROJECT_DIR/scripts/setup_kiosk.sh" 2>/dev/null
chmod +x "$PROJECT_DIR/scripts/launch_kiosk.sh" 2>/dev/null
chmod +x "$PROJECT_DIR/scripts/run_kiosk.sh" 2>/dev/null
chmod +x "$PROJECT_DIR/scripts/run_kiosk_x.sh" 2>/dev/null
chmod +x "$PROJECT_DIR/scripts/find_arduino.py" 2>/dev/null
chmod +x "$PROJECT_DIR/scripts/test_arduino.py" 2>/dev/null

echo ""
echo "========================================="
echo " Permissions Fixed!"
echo "========================================="
echo ""
echo "You can now run:"
echo "  bash scripts/setup_kiosk.sh"
echo "  bash scripts/launch_kiosk.sh"
echo "  python3 scripts/find_arduino.py"
echo "  python3 scripts/test_arduino.py"
echo ""
echo "Or directly:"
echo "  ./scripts/setup_kiosk.sh"
echo "  ./scripts/find_arduino.py"
echo ""
