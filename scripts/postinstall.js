#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const home = process.env.HOME || process.env.USERPROFILE;
const skillsDir = path.join(home, ".claude", "skills");
const selfDir = path.resolve(__dirname, "..");

const wrappers = ["feature-build", "feature-review"];

for (const name of wrappers) {
  const src = path.join(selfDir, name);
  const dest = path.join(skillsDir, name);

  if (!fs.existsSync(src)) continue;

  if (fs.existsSync(dest)) fs.rmSync(dest, { recursive: true, force: true });

  copyDir(src, dest);
  console.log(`Installed ${name} → ${dest}`);
}

console.log(
  "\nRestart Claude Code to use /feature-build and /feature-review"
);

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}
