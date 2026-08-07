#!/bin/bash
# TalentUP Fichaje — Deploy landing to GitHub Pages
# Usage: bash deploy_landing.sh
#
# Copies landing.html to the root that GitHub Pages serves,
# then pushes to trigger auto-deploy.

set -e

REPO_DIR="/c/Users/jordi/talentup-fichaje"
LANDING_SOURCE="$REPO_DIR/frontend/landing.html"
LANDING_DEST="$REPO_DIR/landing.html"

echo "=== TalentUP Fichaje — Deploy landing to GitHub Pages ==="

# Check landing exists
if [ ! -f "$LANDING_SOURCE" ]; then
    echo "[FAIL] landing.html not found at $LANDING_SOURCE"
    exit 1
fi

# Copy landing to repo root for GitHub Pages
cp "$LANDING_SOURCE" "$LANDING_DEST"
echo "[OK] Copied landing.html to repo root"

# Also copy index.html for the dashboard
cp "$REPO_DIR/frontend/index.html" "$REPO_DIR/index.html"
cp "$REPO_DIR/frontend/i18n.js" "$REPO_DIR/i18n.js"
echo "[OK] Copied index.html and i18n.js to repo root"

# Commit
cd "$REPO_DIR"
git add landing.html index.html i18n.js
git commit -m "deploy: landing + dashboard to GitHub Pages" || echo "[INFO] Nothing to commit"
git push origin master
echo "[OK] Pushed to GitHub — Pages will auto-deploy in ~1 min"
echo ""
echo "Landing will be available at: https://jordialbarracin.github.io/talentup-fichaje/landing.html"
echo "Dashboard will be available at: https://jordialbarracin.github.io/talentup-fichaje/"