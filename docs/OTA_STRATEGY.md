# M.A.S.H. IoT - Over-the-Air (OTA) Update Strategy

This document outlines a proposed strategy for implementing secure, reliable, and automated Over-the-Air (OTA) updates for the M.A.S.H. IoT Raspberry Pi gateway. This is intended as a roadmap for moving beyond the development-phase `git pull` method to a production-grade update system.

## 1. Core Requirements for a Production OTA System

The current development workflow (`git pull` via a Personal Access Token) is convenient but has significant limitations:

*   **Security Risk:** Storing a GitHub Personal Access Token (PAT) on the device is a major security vulnerability. If a device is compromised, the token could be extracted and used to access all repositories it has permission for.
*   **No Rollback:** If a pulled update contains a bug that crashes the application, the device may be left in a broken state, requiring physical intervention.
*   **Incomplete Updates:** The `git pull` method only updates the application code. It does not handle updates to system dependencies, OS-level security patches, or changes in the Python environment.
*   **Scalability:** Manually updating a fleet of devices is not feasible.

A production system must address these issues by providing **security**, **atomic updates**, and **automatic rollback**.

## 2. Proposed Solution: A/B Redundant System with Mender

The industry-standard solution for this problem is to use an **A/B redundant partition scheme**. This is a powerful concept that provides a near-bulletproof update process.

### How A/B Redundancy Works

1.  **Two Identical System Partitions:** The Raspberry Pi's SD card is partitioned with two identical root filesystems (`A` and `B`).
2.  **Active vs. Inactive:** At any time, the device is running from one partition (the "active" one, e.g., `A`). The other partition (`B`) is inactive and can be safely modified.
3.  **Update Process:**
    *   An OTA update is downloaded and written to the **inactive** partition (`B`).
    *   The bootloader is then instructed to boot from partition `B` on the next reboot.
    *   The device reboots into the new, updated system.
4.  **Health Check & Rollback:**
    *   After rebooting, the system performs a health check (e.g., "Is the MASH application running?").
    *   **If the check passes**, the update is "committed," and partition `B` is now the permanent active partition.
    *   **If the check fails** (e.g., the app crashes), the system automatically reboots again, but this time back into the **old, working partition `A`**. The device is never left in a broken state.

### Recommended Framework: Mender.io

Implementing an A/B system from scratch is complex. We recommend using **Mender.io**, a mature, open-source, end-to-end OTA update manager designed specifically for embedded Linux devices like the Raspberry Pi.

Mender provides all the necessary components:
*   **Mender Client:** A service that runs on the Raspberry Pi to manage the update process.
*   **Mender Server:** A central dashboard (which you can self-host or use their cloud service) to manage devices and deploy updates.
*   **`mender-convert` Tool:** A utility to take a standard Raspberry Pi OS image and automatically create the required A/B partition layout.

## 3. The Future Update Workflow with Mender

1.  **Initial Device Setup:**
    *   Using `mender-convert`, you create a custom M.A.S.H. OS image for the Raspberry Pi. This is a one-time process.
    *   Every new Raspberry Pi is flashed with this special Mender-enabled image.

2.  **Creating an Update:**
    *   When you have a new version of the `rpi_gateway` application ready, you don't just push the code. Instead, you build a complete **Mender Artifact** (`.mender` file).
    *   This artifact is a compressed image of the entire system partition, including your new code, updated dependencies, and any other system changes.

3.  **Deploying an Update:**
    *   You upload the new `.mender` artifact to the Mender Server's web interface.
    *   From the dashboard, you select which devices should receive the update and create a new deployment.

4.  **The Device Handles the Rest:**
    *   The Mender client on the Raspberry Pi periodically checks in with the server.
    *   When it sees a new deployment, it securely downloads the artifact.
    *   It installs the artifact to the inactive partition.
    *   It reboots, performs the health check, and either commits the update or automatically rolls back.

## 4. Security Advantages over the Current Method

This approach directly solves your security concerns:

*   **No GitHub Credentials on Device:** The device no longer needs any knowledge of Git or any Personal Access Tokens. Its only secret is a unique device token used to authenticate with the Mender server.
*   **Cryptographically Signed Updates:** Mender artifacts can be signed with a private key. The Mender client on the device will have a public key and will refuse to install any update that doesn't have a valid signature, preventing unauthorized software from being installed.
*   **Secure Communication Channel:** All communication between the device and the Mender server is encrypted over HTTPS.

This strategy provides a clear and professional path forward for when you are ready to move your project into a production environment.
