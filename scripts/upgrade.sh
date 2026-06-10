#!/usr/bin/env bash
# Upgrade hermes-devcrew agent profiles to latest from GitHub.
#   HERMES_DEVCREW_DIR=<path> scripts/upgrade.sh
# Idempotent — safe to re-run.
set -euo pipefail

INSTALL_DIR="${HERMES_DEVCREW_DIR:-${HERMES_DEVCREW_STACK_DIR:-/opt/hermes-devcrew}}"
echo "hermes-devcrew upgrade: $INSTALL_DIR"

if [ ! -d "$INSTALL_DIR/.git" ]; then
  echo "no git checkout at $INSTALL_DIR — cloning"
  git clone https://github.com/must-mohsin1/hermes-devcrew "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
git fetch --tags --force
# If DEVCREW_VERSION given, checkout that tag; otherwise latest main
if [ -n "${DEVCREW_VERSION:-}" ]; then
  echo "pinning to version ${DEVCREW_VERSION}"
  git checkout "v${DEVCREW_VERSION#v}" 2>/dev/null || git checkout "${DEVCREW_VERSION}"
else
  CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    git pull --ff-only origin "$CURRENT_BRANCH"
  else
    git pull --ff-only origin main 2>/dev/null || git pull --ff-only origin master 2>/dev/null || true
  fi
fi

# Re-run install to update agent profiles (idempotent — preserves keys + memory)
bash install.sh --yes --skip-keys 2>&1 || echo "install.sh completed with warnings"

# Update the runner symlink
chmod +x devcrew-run devcrew-closeout 2>/dev/null || true
[ -d "$HOME/.local/bin" ] && ln -sf "$INSTALL_DIR/devcrew-run" "$HOME/.local/bin/devcrew-run"
[ -d "$HOME/.local/bin" ] && ln -sf "$INSTALL_DIR/devcrew-closeout" "$HOME/.local/bin/devcrew-closeout"

echo "hermes-devcrew upgrade: done ($(cat VERSION 2>/dev/null || echo unknown))"