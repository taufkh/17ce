# ============================================================
# ICONN MODULE – UPDATE POLICY (PULL-ONLY, NO CUSTOMIZATION)
# ============================================================
# This folder (addons/iconn) is a direct git clone of:
# https://github.com/McCoy-Pte-Ltd/iconnexion-new.git
#
# IMPORTANT RULES:
# 1. DO NOT modify any files inside this folder.
# 2. DO NOT add custom logic here.
# 3. DO NOT copy-paste or overwrite files manually.
# 4. This repo is treated as vendor-controlled source code.
#
# HOW TO UPDATE (STANDARD PROCEDURE):
#
# Step 1: Open terminal in VS Code
# Step 2: Navigate to the repo folder
#   cd addons/iconn
#
# Step 3: Verify working tree is clean
#   git status
#   (Expected: "nothing to commit, working tree clean")
#
# Step 4: Pull latest changes from GitHub
#   git pull
#
# Step 5: Restart Odoo container
#   docker compose down
#   docker compose up -d
#
# Step 6: In Odoo UI
#   - Activate Developer Mode
#   - Go to Apps
#   - Click "Update Apps List"
#   - Upgrade affected Iconn modules if required
#
# NOTE:
# - If git status shows modified files, STOP.
# - Investigate immediately. Local changes are NOT allowed.
#
#   share IP
#   ngrok http http://localhost:8069
#
# ============================================================


update git

# git status

# git add .

# git commit -m "text"

# git push origin main

#aplikasi ini berjalan menggunakan podman compose, logs ada di folder logs, coba cek modul di iconn, folder custom nya dengan nama 'crm_project_classification
