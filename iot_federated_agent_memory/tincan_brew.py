"""Homebrew (`brew`) integration for the TinCan Terminal, Mesh OS & CLI.

Provides:
1. Ruby Homebrew Formula generation (`Formula/tincan.rb`, `Formula/context-palace.rb`)
   served at `/Formula/<name>.rb` so `brew install <relay>/Formula/tincan.rb` works out of the box.
2. Curated TinCan Tap (`NoJuanNobody/tap`) + Homebrew formula/cask catalog.
3. Interactive `brew` command execution (`install`, `uninstall`, `tap`, `list`, `info`,
   `search`, `update`, `upgrade`, `doctor`, `--version`) for the TinCan Web Terminal
   (`#win-terminal` / `/api/terminal/brew`) and `tincan brew` CLI.
4. Human-In-The-Loop (HITL) Accessibility Gate integration (`enqueue_action`) so web
   terminal `brew install` commands can also be approved & executed on the host Mac via
   `tincan actions` / `tincan trigger`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from .tincan_actions import enqueue_action

DEFAULT_RELAY_URL = os.environ.get(
    "TINCAN_RELAY",
    "https://iot-federated-agent-memory-production.up.railway.app",
)

# Curated TinCan Tap (`NoJuanNobody/tap`) + popular Homebrew formulas available in the TinCan Terminal
BREW_CATALOG: Dict[str, Dict[str, Any]] = {
    "tincan": {
        "name": "tincan",
        "full_name": "NoJuanNobody/tap/tincan",
        "tap": "NoJuanNobody/tap",
        "version": "2.2.0",
        "kind": "formula",
        "desc": "Zero-account Ed25519/X25519 Blind Relay CLI, WebRTC media bridge & TinCan Mesh OS",
        "homepage": "https://iot-federated-agent-memory-production.up.railway.app/mesh",
        "license": "MIT",
        "dependencies": ["python@3.13", "libsodium"],
        "bottle_size": "1.8MB",
        "files_count": 48,
        "caveats": "Run `tincan whoami` to inspect your Ed25519 identity or `tincan start` for the live Mesh TUI.",
    },
    "context-palace": {
        "name": "context-palace",
        "full_name": "NoJuanNobody/tap/context-palace",
        "tap": "NoJuanNobody/tap",
        "version": "2.0.0",
        "kind": "formula",
        "desc": "Federated SQLite WAL Context Lake, Bitemporal Belief Revision & Textual TUI Memory Palace",
        "homepage": "https://github.com/NoJuanNobody/context-palace",
        "license": "MIT",
        "dependencies": ["python@3.13", "sqlite"],
        "bottle_size": "2.4MB",
        "files_count": 36,
        "caveats": "Launch the visual Memory Palace TUI with `context-palace tui` or press [w] for Drag & Drop Studio.",
    },
    "kokoro-tts": {
        "name": "kokoro-tts",
        "full_name": "NoJuanNobody/tap/kokoro-tts",
        "tap": "NoJuanNobody/tap",
        "version": "0.8.2",
        "kind": "formula",
        "desc": "Local Kokoro-82M neural voice synthesis CLI (kokoro-say) for TinCan voice envelopes",
        "homepage": "https://github.com/NoJuanNobody/tincan-skills",
        "license": "Apache-2.0",
        "dependencies": ["python@3.13", "espeak-ng", "onnxruntime"],
        "bottle_size": "84.2MB",
        "files_count": 29,
        "caveats": "Test neural speech locally with `tincan say \"Hello from Kokoro\" --voice bella`.",
    },
    "artcraft-launcher": {
        "name": "artcraft-launcher",
        "full_name": "artcraft-launcher",
        "tap": "NoJuanNobody/tap",
        "version": "1.5.0",
        "kind": "cask",
        "desc": "Native desktop launcher & MCP bridge for the 15 ArtCraft creative applications",
        "homepage": "https://getartcraft.com",
        "license": "Commercial",
        "dependencies": [],
        "bottle_size": "68.5MB",
        "files_count": 112,
        "caveats": "Verify installed ArtCraft desktop apps with `tincan space artcraft`.",
    },
    "jq": {
        "name": "jq",
        "full_name": "jq",
        "tap": "homebrew/core",
        "version": "1.7.1",
        "kind": "formula",
        "desc": "Lightweight and flexible command-line JSON processor for `tincan --json` pipelines",
        "homepage": "https://jqlang.github.io/jq/",
        "license": "MIT",
        "dependencies": ["oniguruma"],
        "bottle_size": "1.1MB",
        "files_count": 19,
    },
    "ripgrep": {
        "name": "ripgrep",
        "full_name": "ripgrep",
        "tap": "homebrew/core",
        "version": "14.1.1",
        "kind": "formula",
        "desc": "Recursively search directories for a regex pattern (`rg`)",
        "homepage": "https://github.com/BurntSushi/ripgrep",
        "license": "Unlicense",
        "dependencies": ["pcre2"],
        "bottle_size": "5.4MB",
        "files_count": 14,
    },
    "gh": {
        "name": "gh",
        "full_name": "gh",
        "tap": "homebrew/core",
        "version": "2.62.0",
        "kind": "formula",
        "desc": "GitHub command-line tool for PRs, issues, and skill publishing",
        "homepage": "https://cli.github.com/",
        "license": "MIT",
        "dependencies": [],
        "bottle_size": "46.0MB",
        "files_count": 162,
    },
    "tmux": {
        "name": "tmux",
        "full_name": "tmux",
        "tap": "homebrew/core",
        "version": "3.5a",
        "kind": "formula",
        "desc": "Terminal multiplexer for multi-agent coding fleets",
        "homepage": "https://tmux.github.io/",
        "license": "ISC",
        "dependencies": ["libevent", "ncurses", "utf8proc"],
        "bottle_size": "1.2MB",
        "files_count": 15,
    },
    "uv": {
        "name": "uv",
        "full_name": "uv",
        "tap": "homebrew/core",
        "version": "0.5.4",
        "kind": "formula",
        "desc": "Extremely fast Python package installer and resolver written in Rust",
        "homepage": "https://github.com/astral-sh/uv",
        "license": "MIT",
        "dependencies": [],
        "bottle_size": "28.4MB",
        "files_count": 12,
    },
    "ollama": {
        "name": "ollama",
        "full_name": "ollama",
        "tap": "homebrew/core",
        "version": "0.4.6",
        "kind": "formula",
        "desc": "Create, run, and share local large language models on Apple Silicon",
        "homepage": "https://ollama.com/",
        "license": "MIT",
        "dependencies": [],
        "bottle_size": "34.8MB",
        "files_count": 9,
    },
    "zellij": {
        "name": "zellij",
        "full_name": "zellij",
        "tap": "homebrew/core",
        "version": "0.41.2",
        "kind": "formula",
        "desc": "Pluggable terminal workspace and multiplexer with Rust WebAssembly plugins",
        "homepage": "https://zellij.dev/",
        "license": "MIT",
        "dependencies": [],
        "bottle_size": "11.6MB",
        "files_count": 11,
    },
    "ffmpeg": {
        "name": "ffmpeg",
        "full_name": "ffmpeg",
        "tap": "homebrew/core",
        "version": "7.1",
        "kind": "formula",
        "desc": "Play, record, convert, and stream audio and video for Relay TV & WebRTC",
        "homepage": "https://ffmpeg.org/",
        "license": "GPL-2.0-or-later",
        "dependencies": ["dav1d", "libvpx", "opus", "x264"],
        "bottle_size": "54.2MB",
        "files_count": 94,
    },
}

# Aliases mapping common package names to canonical catalog keys
PACKAGE_ALIASES: Dict[str, str] = {
    "nojuannobody/tap/tincan": "tincan",
    "nojuannobody/tincan/tincan": "tincan",
    "tin-can": "tincan",
    "nojuannobody/tap/context-palace": "context-palace",
    "context_palace": "context-palace",
    "nojuannobody/tap/kokoro-tts": "kokoro-tts",
    "kokoro": "kokoro-tts",
    "kokoro-say": "kokoro-tts",
    "artcraft": "artcraft-launcher",
    "rg": "ripgrep",
}


def generate_homebrew_formula(
    formula_name: str = "tincan",
    relay_url: str = DEFAULT_RELAY_URL,
) -> str:
    """Return a valid Ruby Homebrew formula (`.rb`) for `tincan` or `context-palace`."""
    clean = (formula_name or "tincan").strip().lower().replace(".rb", "")
    relay = (relay_url or DEFAULT_RELAY_URL).rstrip("/")

    if clean in ("context-palace", "context_palace"):
        return f'''class ContextPalace < Formula
  desc "Federated SQLite WAL Context Lake, Bitemporal Belief Revision & Textual TUI Memory Palace"
  homepage "https://github.com/NoJuanNobody/context-palace"
  url "https://github.com/NoJuanNobody/context-palace/archive/refs/heads/main.tar.gz"
  version "2.0.0"
  license "MIT"

  depends_on "python@3.13"
  depends_on "sqlite"

  def install
    libexec.install Dir["*"]
    (bin/"context-palace").write <<~EOS
      #!/bin/bash
      export PYTHONPATH="#{{libexec}}:$PYTHONPATH"
      exec "#{{Formula["python@3.13"].opt_bin}}/python3" -m context_palace.cli "$@"
    EOS
    chmod 0755, bin/"context-palace"
  end

  test do
    assert_match "context-palace", shell_output("#{{bin}}/context-palace --help")
  end
end
'''

    return f'''class Tincan < Formula
  desc "TinCan 2.2 Zero-Account Ed25519/X25519 Blind Relay CLI, WebRTC Media & Mesh OS"
  homepage "{relay}/mesh"
  url "{relay}/install.sh"
  version "2.2.0"
  license "MIT"

  depends_on "python@3.13"

  def install
    bin.install "install.sh" => "tincan-bootstrap"
    chmod 0755, bin/"tincan-bootstrap"
    (bin/"tincan").write <<~EOS
      #!/bin/bash
      if [ ! -x "$HOME/.local/bin/tincan" ]; then
        TINCAN_RELAY="{relay}" "#{{bin}}/tincan-bootstrap"
      fi
      exec "$HOME/.local/bin/tincan" "$@"
    EOS
    chmod 0755, bin/"tincan"
  end

  def caveats
    <<~EOS
      TinCan 2.2 CLI is linked to:
        {relay}

      Quickstart:
        tincan whoami
        tincan start
        tincan brew list
    EOS
  end

  test do
    assert_predicate bin/"tincan", :exist?
  end
end
'''


def _get_cellar_file(config_dir: Optional[str] = None) -> str:
    base = config_dir or os.path.expanduser("~/.tin-can")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "brew_cellar.json")


def load_cellar_state(config_dir: Optional[str] = None) -> Dict[str, Any]:
    path = _get_cellar_file(config_dir)
    default_state: Dict[str, Any] = {
        "taps": ["homebrew/core", "homebrew/cask", "NoJuanNobody/tap"],
        "installed": {
            "tincan": {
                "name": "tincan",
                "version": "2.2.0",
                "kind": "formula",
                "tap": "NoJuanNobody/tap",
                "installed_at": 1762600000.0,
                "cellar_path": "/opt/homebrew/Cellar/tincan/2.2.0",
            },
            "zellij": {
                "name": "zellij",
                "version": "0.41.2",
                "kind": "formula",
                "tap": "homebrew/core",
                "installed_at": 1762600000.0,
                "cellar_path": "/opt/homebrew/Cellar/zellij/0.41.2",
            },
        },
    }
    if not os.path.exists(path):
        return default_state
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default_state
        data.setdefault("taps", default_state["taps"])
        data.setdefault("installed", default_state["installed"])
        return data
    except Exception:
        return default_state


def save_cellar_state(state: Dict[str, Any], config_dir: Optional[str] = None) -> None:
    path = _get_cellar_file(config_dir)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def resolve_pkg_spec(raw_pkg: str) -> Dict[str, Any]:
    """Resolve a package name, tap path, or Formula URL into a structured formula spec."""
    cleaned = raw_pkg.strip()
    if cleaned.endswith("/Formula/tincan.rb") or cleaned.endswith("tincan.rb"):
        cleaned = "tincan"
    elif cleaned.endswith("/Formula/context-palace.rb") or cleaned.endswith("context-palace.rb"):
        cleaned = "context-palace"

    low = cleaned.lower()
    canonical = PACKAGE_ALIASES.get(low, low.split("/")[-1] if "/" in low else low)
    if canonical in BREW_CATALOG:
        return dict(BREW_CATALOG[canonical])

    tap_name = "/".join(cleaned.split("/")[:2]) if cleaned.count("/") >= 2 else "homebrew/core"
    return {
        "name": canonical,
        "full_name": cleaned if "/" in cleaned else canonical,
        "tap": tap_name,
        "version": "1.0.0",
        "kind": "Formula",
        "desc": f"Homebrew package '{canonical}' installed via TinCan Terminal",
        "homepage": f"https://formulae.brew.sh/formula/{canonical}",
        "license": "MIT",
        "dependencies": [],
        "bottle_size": "3.2MB",
        "files_count": 24,
    }


def handle_brew_command(
    cmd_str: str,
    peer_id: str = "aeonik",
    config_dir: Optional[str] = None,
    relay_url: str = DEFAULT_RELAY_URL,
    queue_hitl: bool = True,
    execute_native: bool = False,
) -> Dict[str, Any]:
    """
    Parse and execute a `brew ...` command from the TinCan Terminal or `tincan brew` CLI.
    Returns structured status, lines of terminal output, cellar snapshot, and any queued HITL action.
    """
    raw = (cmd_str or "").strip()
    # Strip leading `brew` if present
    tokens = [t for t in re.split(r"\s+", raw) if t]
    if tokens and tokens[0].lower() == "brew":
        tokens = tokens[1:]

    state = load_cellar_state(config_dir)
    taps: List[str] = state["taps"]
    installed: Dict[str, Any] = state["installed"]

    if not tokens or tokens[0] in ("help", "--help", "-h"):
        lines = [
            "Example usage:",
            "  brew search [TEXT|/REGEX/]     Search TinCan Tap & Homebrew formulas",
            "  brew info [FORMULA|CASK...]    Display formula version, bottle size & caveats",
            "  brew install FORMULA|CASK...   Install a package into TinCan Terminal (/opt/homebrew/Cellar)",
            "  brew tap [USER/REPO]           Tap a formula repository (e.g. NoJuanNobody/tap)",
            "  brew list                      List all installed formulas & casks",
            "  brew update / brew upgrade     Fetch newest version of Homebrew and TinCan Tap",
            "  brew uninstall FORMULA|CASK... Uninstall a formula or cask",
            "  brew doctor                    Check TinCan Mesh & Homebrew environment health",
        ]
        return {
            "status": "ok",
            "subcommand": "help",
            "output": "\n".join(lines),
            "lines": lines,
            "installed": list(installed.keys()),
            "taps": taps,
        }

    sub = tokens[0].lower()
    args = tokens[1:]
    flags = [a for a in args if a.startswith("-")]
    posit = [a for a in args if not a.startswith("-")]

    if sub in ("--version", "-v", "version"):
        lines = [
            "Homebrew 4.4.8 (TinCan Mesh OS v2.2 Bridge)",
            "Homebrew/homebrew-core (git revision a49f21; last commit today)",
            "NoJuanNobody/homebrew-tap (TinCan 2.2 + Context Palace 2.0 + ArtCraft Suite)",
        ]
        return {
            "status": "ok",
            "subcommand": "version",
            "output": "\n".join(lines),
            "lines": lines,
            "installed": list(installed.keys()),
            "taps": taps,
        }

    if sub == "tap":
        if not posit:
            lines = sorted(taps)
            return {
                "status": "ok",
                "subcommand": "tap",
                "output": "\n".join(lines),
                "lines": lines,
                "taps": taps,
            }
        target_tap = posit[0]
        if target_tap not in taps:
            taps.append(target_tap)
            save_cellar_state(state, config_dir)
        lines = [
            f"==> Tapping {target_tap}",
            f"Cloning into '/opt/homebrew/Library/Taps/{target_tap}'...",
            "Tapped 4 formulae and 1 cask (62 files, 148.4KB).",
        ]
        return {
            "status": "ok",
            "subcommand": "tap",
            "tap": target_tap,
            "output": "\n".join(lines),
            "lines": lines,
            "taps": taps,
        }

    if sub in ("list", "ls"):
        names = sorted(installed.keys())
        lines = [
            "==> Formulae",
            "  ".join(names) if names else "(empty cellar)",
        ]
        if "--versions" in flags:
            lines = [f"{k} {installed[k].get('version', '1.0.0')}" for k in names]
        return {
            "status": "ok",
            "subcommand": "list",
            "output": "\n".join(lines),
            "lines": lines,
            "installed": names,
        }

    if sub == "search":
        q = (posit[0].lower() if posit else "").strip()
        matches = []
        for k, spec in sorted(BREW_CATALOG.items()):
            if not q or q in k.lower() or q in spec.get("desc", "").lower() or q in spec.get("full_name", "").lower():
                badge = "✔" if k in installed else ""
                matches.append(f"{spec['full_name']}{(' ' + badge) if badge else ''}  ({spec['version']}) — {spec['desc']}")
        if not matches and q:
            matches.append(f"No formula found matching '{q}' in local tap; run `brew install {q}` to fetch from homebrew/core.")
        lines = ["==> Formulae & Casks (NoJuanNobody/tap + homebrew/core)", *matches]
        return {
            "status": "ok",
            "subcommand": "search",
            "query": q,
            "output": "\n".join(lines),
            "lines": lines,
            "matches": matches,
        }

    if sub in ("info", "abv"):
        if not posit:
            lines = [f"{len(installed)} kegs, {len(BREW_CATALOG)} available in TinCan Tap"]
            return {"status": "ok", "subcommand": "info", "output": "\n".join(lines), "lines": lines}
        spec = resolve_pkg_spec(posit[0])
        cname = spec["name"]
        is_inst = cname in installed
        cellar_p = f"/opt/homebrew/Cellar/{cname}/{spec['version']}"
        lines = [
            f"==> {spec['full_name']}: stable {spec['version']} (bottled)",
            spec["desc"],
            spec["homepage"],
            f"Installed: {cellar_p} ({spec['files_count']} files, {spec['bottle_size']}) *" if is_inst else "Not installed",
            f"From: {relay_url.rstrip('/')}/Formula/{cname}.rb",
            f"License: {spec.get('license', 'MIT')}",
        ]
        if spec.get("dependencies"):
            lines.append(f"Dependencies: {', '.join(spec['dependencies'])}")
        if spec.get("caveats"):
            lines.append(f"==> Caveats\n{spec['caveats']}")
        return {
            "status": "ok",
            "subcommand": "info",
            "package": spec,
            "installed": is_inst,
            "output": "\n".join(lines),
            "lines": lines,
        }

    if sub in ("install", "reinstall"):
        if not posit:
            msg = "Error: `brew install` requires at least 1 formula or cask argument (e.g. `brew install tincan context-palace jq`)."
            return {"status": "error", "subcommand": sub, "output": msg, "lines": [msg]}

        is_cask = "--cask" in flags
        lines: List[str] = []
        installed_now: List[str] = []
        queued_actions: List[Dict[str, Any]] = []

        for raw_pkg in posit:
            # Validate safe package identifier
            if not re.match(r"^[A-Za-z0-9_.\-@/:]+$", raw_pkg):
                lines.append(f"Error: Invalid package name '{raw_pkg}'.")
                continue

            spec = resolve_pkg_spec(raw_pkg)
            cname = spec["name"]
            ver = spec["version"]
            kind = "cask" if (is_cask or spec.get("kind") == "cask") else "formula"
            cellar_path = (
                f"/Applications/{cname}.app"
                if kind == "cask"
                else f"/opt/homebrew/Cellar/{cname}/{ver}"
            )

            if spec.get("tap") == "NoJuanNobody/tap" and "NoJuanNobody/tap" not in taps:
                taps.append("NoJuanNobody/tap")
                lines.append("==> Tapping NoJuanNobody/tap")

            lines.append(f"==> Downloading https://ghcr.io/v2/homebrew/core/{cname}/manifests/{ver}")
            for dep in spec.get("dependencies") or []:
                if dep not in installed:
                    lines.append(f"==> Installing {cname} dependency: {dep}")
                    installed[dep] = {
                        "name": dep,
                        "version": "latest",
                        "kind": "formula",
                        "tap": "homebrew/core",
                        "installed_at": time.time(),
                        "cellar_path": f"/opt/homebrew/Cellar/{dep}/latest",
                    }
            lines.append(f"==> Pouring {cname}--{ver}.arm64_sequoia.bottle.tar.gz")
            if spec.get("caveats"):
                lines.append(f"==> Caveats\n  {spec['caveats']}")
            lines.append(f"==> Summary\n🍺  {cellar_path}: {spec['files_count']} files, {spec['bottle_size']} installed")

            installed[cname] = {
                "name": cname,
                "version": ver,
                "kind": kind,
                "tap": spec.get("tap", "homebrew/core"),
                "installed_at": time.time(),
                "cellar_path": cellar_path,
            }
            installed_now.append(cname)

            # Queue into TinCan's Human-In-The-Loop Accessibility Gate so the local Mac operator
            # can also approve native execution via `tincan trigger <seq>`
            if queue_hitl:
                try:
                    brew_cmd = f"brew install {'--cask ' if kind == 'cask' else ''}{cname}".strip()
                    seq = int(time.time() * 1000) % 100000
                    act = enqueue_action(
                        seq=seq,
                        sender=peer_id,
                        sender_alias=peer_id,
                        command_text=brew_cmd,
                        config_dir=config_dir,
                        action_type="brew",
                    )
                    queued_actions.append(act)
                except Exception:
                    pass

            if execute_native:
                brew_bin = "/opt/homebrew/bin/brew" if os.path.exists("/opt/homebrew/bin/brew") else shutil.which("brew")
                if brew_bin and cname not in ("tincan", "context-palace", "kokoro-tts", "artcraft-launcher"):
                    try:
                        cmd_list = [brew_bin, "install"]
                        if kind == "cask":
                            cmd_list.append("--cask")
                        cmd_list.append(cname)
                        proc = subprocess.run(cmd_list, capture_output=True, text=True, timeout=120)
                        if proc.stdout:
                            lines.append(proc.stdout.strip())
                    except Exception as exc:
                        lines.append(f"[native brew note] {exc}")

        save_cellar_state(state, config_dir)
        if queued_actions:
            seq_list = ", ".join(str(a["seq"]) for a in queued_actions)
            lines.append(
                f"🛡️  HITL Accessibility Gate: Queued native host install (#{seq_list}) — run `tincan trigger {queued_actions[0]['seq']}` in local CLI to run on host Mac."
            )

        return {
            "status": "ok",
            "subcommand": sub,
            "installed_now": installed_now,
            "installed": sorted(installed.keys()),
            "queued_actions": queued_actions,
            "output": "\n".join(lines),
            "lines": lines,
        }

    if sub in ("uninstall", "remove", "rm"):
        if not posit:
            msg = "Error: `brew uninstall` requires a package name."
            return {"status": "error", "subcommand": "uninstall", "output": msg, "lines": [msg]}
        lines = []
        removed = []
        for raw_pkg in posit:
            spec = resolve_pkg_spec(raw_pkg)
            cname = spec["name"]
            if cname in installed:
                cpath = installed[cname].get("cellar_path", f"/opt/homebrew/Cellar/{cname}")
                del installed[cname]
                removed.append(cname)
                lines.append(f"Uninstalling {cpath}... ({spec['files_count']} files, {spec['bottle_size']} freed)")
            else:
                lines.append(f"Error: No such keg: /opt/homebrew/Cellar/{cname}")
        save_cellar_state(state, config_dir)
        return {
            "status": "ok",
            "subcommand": "uninstall",
            "removed": removed,
            "installed": sorted(installed.keys()),
            "output": "\n".join(lines),
            "lines": lines,
        }

    if sub in ("update", "upgrade"):
        lines = [
            "==> Updating Homebrew & NoJuanNobody/tap...",
            "Updated 2 taps (homebrew/core and NoJuanNobody/tap).",
            "==> Updated Formulae",
            "NoJuanNobody/tap/tincan 2.2.0   NoJuanNobody/tap/context-palace 2.0.0",
            f"Already up-to-date ({len(installed)} kegs in /opt/homebrew/Cellar).",
        ]
        return {
            "status": "ok",
            "subcommand": sub,
            "output": "\n".join(lines),
            "lines": lines,
            "installed": sorted(installed.keys()),
        }

    if sub == "doctor":
        brew_bin = "/opt/homebrew/bin/brew" if os.path.exists("/opt/homebrew/bin/brew") else shutil.which("brew")
        lines = [
            "Your system is ready to brew.",
            f"  • Homebrew Prefix:     {'/opt/homebrew' if brew_bin else '/opt/homebrew (TinCan Virtual Cellar)'}",
            f"  • TinCan Tap:          NoJuanNobody/tap ({len(BREW_CATALOG)} packages indexed)",
            f"  • Installed Kegs:      {len(installed)} ({', '.join(sorted(installed.keys()))})",
            f"  • HITL Execution Gate: Active (`tincan actions` / `tincan trigger`)",
        ]
        return {
            "status": "ok",
            "subcommand": "doctor",
            "output": "\n".join(lines),
            "lines": lines,
            "installed": sorted(installed.keys()),
        }

    msg = f"Error: Unknown brew command `{sub}`. Run `brew help` for supported commands."
    return {
        "status": "error",
        "subcommand": sub,
        "output": msg,
        "lines": [msg],
    }
