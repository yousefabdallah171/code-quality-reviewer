#!/bin/bash
# Codeguard installer — installs all 3 skills in one command
# Run: curl -fsSL https://raw.githubusercontent.com/yousefabdallah171/code-quality-reviewer/main/install.sh | bash

set -e

SKILLS_DIR="$HOME/.claude/skills"
REPO_URL="https://github.com/yousefabdallah171/code-quality-reviewer.git"
TEMP_DIR=$(mktemp -d)

echo "Installing codeguard skill..."

# Clone repo to temp
git clone --depth 1 "$REPO_URL" "$TEMP_DIR" 2>/dev/null

# Create skills dir if needed
mkdir -p "$SKILLS_DIR"

# Install main codeguard skill
rm -rf "$SKILLS_DIR/codeguard"
cp -r "$TEMP_DIR" "$SKILLS_DIR/codeguard"
rm -rf "$SKILLS_DIR/codeguard/.git"

# Install feature-build as separate skill
rm -rf "$SKILLS_DIR/feature-build"
cp -r "$TEMP_DIR/feature-build" "$SKILLS_DIR/feature-build"

# Install feature-review as separate skill
rm -rf "$SKILLS_DIR/feature-review"
cp -r "$TEMP_DIR/feature-review" "$SKILLS_DIR/feature-review"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "Installed:"
echo "  $SKILLS_DIR/codeguard"
echo "  $SKILLS_DIR/feature-build"
echo "  $SKILLS_DIR/feature-review"
echo ""
echo "Restart Claude Code to use /feature-build and /feature-review"
