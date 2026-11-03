#!/usr/bin/env bash
# Installe le studio du skill « What If » (MIT, github.com/kelano86/what-if-animation) avec des polices locales,
# pour faire le rendu dans un environnement où le navigateur ne peut pas charger Google Fonts.
#   bash setup_studio.sh <dossier_du_studio>
# Ensuite :  cd <dossier_du_studio> && npx remotion render src/index.ts CopyPaste out/copypaste.mp4 \
#              --browser-executable=<chrome-headless-shell> --concurrency=4
set -euo pipefail
STUDIO="${1:?usage: setup_studio.sh <dossier_du_studio>}"
SKILL="${SKILL_DIR:-$HOME/.claude/skills/what-if-animation}"
[ -d "$SKILL" ] || git clone --depth 1 https://github.com/kelano86/what-if-animation "$SKILL"
cp -r "$SKILL/studio" "$STUDIO"
cd "$STUDIO"
npm install --no-audit --no-fund
mkdir -p public/fonts
python3 "$(dirname "$0")/local_fonts.py" public/fonts src/engine/fonts.ts
echo "Studio prêt : $STUDIO"
