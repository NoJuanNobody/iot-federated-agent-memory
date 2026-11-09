#!/usr/bin/env bash
# ==============================================================================
# Safe Local Skill Installer for TinCan 2.2 & Mesh OS (Zero Tarball / Zero PII)
# ==============================================================================
set -e
echo "[*] Installing TinCan skills via npx skills (no remote shell execution or PII telemetry)..."
npx -y skills add NoJuanNobody/tincan-skills -g -y
echo "[+] Done! All peripherals and PII telemetry remain OFF by default."
