#!/usr/bin/env pwsh
# Codeguard installer — installs all 3 skills in one command
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

$SKILLS_DIR = "$env:USERPROFILE\.claude\skills"
$REPO_URL = "https://github.com/yousefabdallah171/code-quality-reviewer.git"
$TEMP_DIR = "$env:TEMP\codeguard-install"

Write-Host "Installing codeguard skill..." -ForegroundColor Cyan

# Clone repo to temp
if (Test-Path $TEMP_DIR) { Remove-Item -Recurse -Force $TEMP_DIR }
git clone --depth 1 $REPO_URL $TEMP_DIR 2>&1 | Out-Null

if (-not (Test-Path $TEMP_DIR)) {
    Write-Host "Failed to clone repo" -ForegroundColor Red
    exit 1
}

# Create skills dir if needed
if (-not (Test-Path $SKILLS_DIR)) {
    New-Item -ItemType Directory -Force $SKILLS_DIR | Out-Null
}

# Install main codeguard skill
$codeguardDest = "$SKILLS_DIR\codeguard"
if (Test-Path $codeguardDest) { Remove-Item -Recurse -Force $codeguardDest }
Copy-Item -Recurse "$TEMP_DIR" $codeguardDest
Remove-Item -Recurse -Force "$codeguardDest\.git" -ErrorAction SilentlyContinue

# Install feature-build as separate skill
$fbDest = "$SKILLS_DIR\feature-build"
if (Test-Path $fbDest) { Remove-Item -Recurse -Force $fbDest }
Copy-Item -Recurse "$TEMP_DIR\feature-build" $fbDest

# Install feature-review as separate skill
$frDest = "$SKILLS_DIR\feature-review"
if (Test-Path $frDest) { Remove-Item -Recurse -Force $frDest }
Copy-Item -Recurse "$TEMP_DIR\feature-review" $frDest

# Cleanup
Remove-Item -Recurse -Force $TEMP_DIR

Write-Host ""
Write-Host "Installed:" -ForegroundColor Green
Write-Host "  $codeguardDest" -ForegroundColor White
Write-Host "  $fbDest" -ForegroundColor White
Write-Host "  $frDest" -ForegroundColor White
Write-Host ""
Write-Host "Restart Claude Code to use /feature-build and /feature-review" -ForegroundColor Yellow
