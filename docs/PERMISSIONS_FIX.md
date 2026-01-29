# Script Permissions Fix - Critical Update

## The Problem You Identified ✅

You were absolutely right! Scripts created via Git or programmatically **don't have execute permissions** by default.

When you run:
```bash
bash scripts/setup_kiosk.sh
```

It works because you're explicitly using `bash` to interpret the file.

But when systemd or autostart tries to run the scripts directly, they fail with:
```
Permission denied
```

## The Solution

### 1. **Immediate Fix Script Created**
`scripts/fix_permissions.sh` - Run this anytime permissions are wrong:

```bash
bash scripts/fix_permissions.sh
```

This sets `chmod +x` on all `.sh` and `.py` files in the scripts directory.

### 2. **Updated setup_kiosk.sh**
Now automatically fixes permissions at the start:
```bash
chmod +x "$PROJECT_DIR/scripts/"*.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR/scripts/"*.py 2>/dev/null || true
```

### 3. **Updated install_dependencies.sh**
Now includes permission fixing as step [7/7]:
```bash
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
```

## Workflow After Git Clone

**Old way (would fail):**
```bash
git clone ...
bash scripts/setup_kiosk.sh  # Might work
sudo reboot                   # Systemd fails: "Permission denied"
```

**New way (always works):**
```bash
git clone ...
bash scripts/fix_permissions.sh  # ← Fix permissions FIRST
bash scripts/setup_kiosk.sh       # Now sets +x on generated scripts
sudo reboot                       # Works!
```

## Why This Happens

Git tracks file permissions, but GitHub doesn't preserve the `+x` (execute) bit when you download files. So every time you clone or pull, scripts lose execute permissions.

**Solutions:**
1. Run `fix_permissions.sh` after every `git pull`
2. The install script now does this automatically
3. The kiosk setup script now does this automatically

## Files Updated

1. ✅ `scripts/fix_permissions.sh` - **NEW** - One-command fix
2. ✅ `scripts/setup_kiosk.sh` - Now sets permissions at start
3. ✅ `scripts/install_dependencies.sh` - Added step [7/7] for permissions
4. ✅ `docs/RASPBERRY_PI_SETUP.md` - **NEW** - Complete setup guide with permission fix
5. ✅ `README.md` - Added quick start with permission fix command

## Testing Your Fix

### Before Fix (Would Fail):
```bash
./scripts/find_arduino.py
# bash: ./scripts/find_arduino.py: Permission denied
```

### After Fix (Works):
```bash
bash scripts/fix_permissions.sh
./scripts/find_arduino.py
# ✅ Scans for Arduino...
```

## Systemd Service Files

The systemd services now point to scripts with correct paths:

**mash-kiosk.service:**
```ini
ExecStart=/usr/bin/startx /home/USER/MASH-IoT/scripts/run_kiosk_x.sh
```

The `run_kiosk_x.sh` script is:
1. Created by `setup_kiosk.sh`
2. Immediately given execute permissions: `chmod +x`
3. So systemd can run it directly

## Summary

**Your diagnosis was 100% correct!** The autostart wasn't working because:
- Scripts didn't have execute (`+x`) permission
- Systemd couldn't run them
- LXDE autostart couldn't run them

**Now fixed by:**
- Creating `fix_permissions.sh` (quick fix tool)
- Updating all setup scripts to set permissions automatically
- Documenting the permission requirement in setup guides

## Quick Reference

```bash
# After git clone (ALWAYS DO THIS FIRST)
bash scripts/fix_permissions.sh

# After git pull (if scripts changed)
bash scripts/fix_permissions.sh

# Check if scripts have execute permission
ls -l scripts/*.sh
# Should see: -rwxr-xr-x (the 'x' means executable)

# Manual permission fix
chmod +x scripts/*.sh scripts/*.py
```

Great catch! This was the missing piece for reliable auto-start on boot. 🎉
