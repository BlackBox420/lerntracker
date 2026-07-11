#!/bin/sh
# Einmalig ausführen (z.B. direkt nach dem Klonen), verknüpft den
# versionierten pre-commit-Hook mit .git/hooks, da .git/hooks selbst nicht
# von git getrackt wird und daher bei einem frischen Klon leer ist.
set -e
cd "$(dirname "$0")/.."
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "pre-commit-Hook installiert (automatische sw.js-Cache-Version)."
