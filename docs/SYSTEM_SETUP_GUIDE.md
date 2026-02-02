# System Setup Guide - Raspberry Pi

This guide covers essential system configurations for the MASH IoT Gateway running on Raspberry Pi.

## Quick Setup Checklist

After setting up the Raspberry Pi with the Flask application, perform these steps:

### 1. Fix NetworkManager Permissions (Required for WiFi Management)

```bash
# Allow Flask app to control WiFi without sudo
sudo bash MASH-IoT/rpi_gateway/scripts/fix_networkmanager_permissions.sh

# Restart Flask app (if running as service)
sudo systemctl restart mash-iot-gateway

# Or if running manually, just restart the Python script
```

### 2. Disable Onscreen Keyboard (Optional but Recommended)

The system onscreen keyboard may auto-start on boot, which is no longer needed since we removed the keyboard toggle feature.

```bash
# Disable matchbox-keyboard from starting on boot
sudo bash MASH-IoT/rpi_gateway/scripts/disable_onscreen_keyboard.sh

# Reboot to apply changes
sudo reboot
```

### 3. Verify WiFi Management

After reboot, test the WiFi disconnect feature:

1. Open web UI: `http://<rpi-ip>:5000/settings`
2. Click "Disconnect and Enable Provisioning"
3. Confirm in the custom modal
4. Verify:
   - WiFi disconnects successfully
   - Hotspot starts automatically (check for `RPi_IoT_Provisioning` network)
   - No permission errors in logs: `journalctl -f`

---

## UI Updates

### Custom Modal System

All JavaScript `confirm()` and `alert()` dialogs have been replaced with custom styled modals:

**Available Functions:**
- `showConfirm(message, onConfirm, options)` - Confirmation dialog
- `showAlert(message, options)` - Information dialog
- `showError(message, options)` - Error dialog
- `showSuccess(message, options)` - Success dialog

**Example Usage:**
```javascript
showConfirm(
    'Are you sure you want to restart?',
    function() {
        // Execute restart action
    },
    {
        title: 'Restart System',
        icon: 'fa-exclamation-triangle',
        danger: true,
        confirmText: 'Restart'
    }
);
```

### Settings Page Redesign

The Settings page now uses the same card-based design as Dashboard:
- Consistent card styling with hover effects
- Unified color scheme (#4CAF50 primary, #2c2c2c background)
- Full-width WiFi status card at top
- Grid layout for setting cards
- System actions in warning-styled card at bottom

---

## Troubleshooting

### WiFi Disconnect Fails with Permission Error

**Error in logs:**
```
audit: op="connection-deactivate" ... result="fail" reason="Not authorized to deactivate connections"
```

**Solution:**
Run the permission fix script (step 1 above) and restart the Flask app.

### Onscreen Keyboard Appears on Boot

**Solution:**
Run the keyboard disable script (step 2 above) and reboot.

### NetworkManager PolicyKit Not Working

**Check permissions:**
```bash
sudo cat /etc/polkit-1/localauthority/50-local.d/allow-wifi-control.pkla
```

**Should contain:**
```
[Allow WiFi Control]
Identity=unix-user:*
Action=org.freedesktop.NetworkManager.network-control;org.freedesktop.NetworkManager.settings.modify.system
ResultAny=yes
ResultInactive=yes
ResultActive=yes
```

### Custom Modals Not Showing

**Check browser console for errors:**
```javascript
// Test modal manually
showAlert('Test message');
```

**Verify base.html includes modal code:**
- Custom modal HTML should be before closing `</body>` tag
- JavaScript functions should be defined globally

---

## File Changes Summary

### Modified Files:

1. **base.html** - Added custom modal component (HTML, CSS, JavaScript)
2. **settings.html** - Redesigned with card layout, custom modals
3. **wifi_setup.html** - Replaced alerts/confirms with custom modals
4. **routes.py** - WiFi disconnect with proper error handling

### New Files:

1. **scripts/fix_networkmanager_permissions.sh** - PolicyKit configuration
2. **scripts/disable_onscreen_keyboard.sh** - Disable OSK on boot
3. **docs/SYSTEM_SETUP_GUIDE.md** - This file

---

## Testing Checklist

After applying all changes:

- [ ] Flask app runs without errors
- [ ] Settings page loads with new card design
- [ ] WiFi status displays correctly
- [ ] Custom modals appear when clicking buttons
- [ ] WiFi disconnect works (no permission errors in logs)
- [ ] Hotspot starts automatically after disconnect
- [ ] No onscreen keyboard appears after reboot
- [ ] All pages maintain consistent styling

---

## Maintenance

### Re-enabling Onscreen Keyboard

If you need the keyboard again:

```bash
# Re-enable in LXDE autostart
sudo sed -i 's/#@matchbox-keyboard/@matchbox-keyboard/' /etc/xdg/lxsession/LXDE-pi/autostart

# Or start manually
matchbox-keyboard &
```

### Reverting WiFi Permissions

```bash
sudo rm /etc/polkit-1/localauthority/50-local.d/allow-wifi-control.pkla
```

---

## Support

For issues or questions, check:
- Flask app logs: `journalctl -u mash-iot-gateway -f`
- System logs: `journalctl -f`
- NetworkManager logs: `sudo systemctl status NetworkManager`
