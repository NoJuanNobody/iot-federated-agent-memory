"""Interactive Chat & Agentic Assistant for TinCan CLI."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from .ai_gateway import (
    DynamicAIGatewayRouter,
    OWLCHAT_BASE_URL,
    normalize_openai_compat_base_url,
)

SYSTEM_PROMPT = """You are TinCan Agent, an autonomous assistant embedded inside the TinCan 2 / IoT Federated Mesh CLI.
You have access to the mesh network, peer addresses, encrypted communication, and OpenRouter multi-lab models.
Keep your answers sharp, technical, and concise. Help the user interact with peer agents, check inbox messages, craft secure envelopes, and route intelligence across nodes."""


class TinCanAgentChat:
    """Agentic REPL loop supporting natural queries, commands, and live or local model completions."""

    def __init__(
        self,
        relay_url: str,
        model_alias: Optional[str] = "gemini-brain",
        thread_id: Optional[str] = None,
        peer_id: Optional[str] = None,
        *,
        local: bool = False,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        gateway: Optional[str] = None,
        router: Optional[DynamicAIGatewayRouter] = None,
    ):
        self.relay_url = relay_url.rstrip("/")
        self.thread_id = thread_id
        self.peer_id = peer_id
        self.local = bool(local or os.environ.get("TINCAN_LOCAL", "").lower() in ("1", "true", "yes"))
        raw_base = base_url or os.environ.get("TINCAN_AI_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        self.base_url: Optional[str] = normalize_openai_compat_base_url(raw_base) if raw_base else None
        self.api_key = api_key
        gw_norm = (gateway or "").strip().lower()
        self.gateway: Optional[str] = None if gw_norm in ("", "auto") else gw_norm
        self._router = router
        self.model_alias = self._resolve_initial_model(model_alias)
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def _get_router(self) -> DynamicAIGatewayRouter:
        if self._router is None:
            self._router = DynamicAIGatewayRouter(
                local_base_url=self.base_url,
                local_api_key=self.api_key,
            )
        return self._router

    def _resolve_initial_model(self, model_alias: Optional[str]) -> str:
        if model_alias:
            return model_alias
        env_model = os.environ.get("TINCAN_LOCAL_MODEL") or os.environ.get("OLLAMA_MODEL")
        if self.gateway == "owlchat" or (self.base_url and "chat.hpc.fau.edu" in self.base_url.lower()):
            return env_model or "owlchat/Gemma4-vibe"
        if self.base_url:
            if env_model:
                return env_model
            discovered = self._get_router().get_openai_compat_models(
                self.base_url,
                api_key=self.api_key,
                gateway_name=self.gateway or "local",
                prefix="local",
                timeout=2.0,
            )
            return discovered[0]["id"] if discovered else "local/default"
        if self.local or self.gateway == "ollama":
            if env_model:
                return env_model if env_model.startswith("ollama/") else f"ollama/{env_model}"
            installed = self._get_router().get_ollama_models()
            return installed[0]["id"] if installed else "ollama/llama3.1:8b"
        if self.gateway == "local":
            return env_model or "local/default"
        return "gemini-brain"

    def is_direct_mode(self) -> bool:
        """True when completions bypass the relay and call Ollama/local/OwlChat directly."""
        if self.gateway == "relay" and not self.local and not self.base_url:
            return False
        if self.local or self.base_url or self.gateway in ("ollama", "owlchat", "trussed", "local", "openai-compat"):
            return True
        return self._get_router()._detect_compat_gateway(self.model_alias, gateway=self.gateway, base_url=self.base_url) is not None

    def _direct_target_label(self) -> str:
        router = self._get_router()
        gw = router._detect_compat_gateway(self.model_alias, gateway=self.gateway, base_url=self.base_url) or "local"
        endpoint, _, label = router._resolve_compat_spec(gw, base_url=self.base_url)
        return f"{label} ({endpoint})"

    def ask(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        if self.is_direct_mode():
            try:
                router = self._get_router()
                gw_hint = "ollama" if (self.local and not self.gateway and not self.base_url and "/" not in self.model_alias) else self.gateway
                data = router.dispatch_completion(
                    self.model_alias,
                    self.history,
                    temperature=0.7,
                    max_tokens=1024,
                    base_url=self.base_url,
                    api_key=self.api_key,
                    gateway=gw_hint,
                )
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if not reply:
                    reply = "[No response returned from model]"
                self.history.append({"role": "assistant", "content": reply})
                return reply
            except urllib.error.URLError as e:
                return f"[TinCan Local/Direct Error ({self._direct_target_label()}): {e.reason}]"
            except Exception as e:
                return f"[TinCan Agent Error: {e}]"

        payload = {
            "model": self.model_alias,
            "messages": self.history,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        if self.thread_id:
            payload["thread_id"] = self.thread_id
        if self.peer_id:
            payload["peer_id"] = self.peer_id

        try:
            req = urllib.request.Request(
                f"{self.relay_url}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if not reply:
                    reply = "[No response returned from model]"
                returned_thread = data.get("thread_id")
                if returned_thread:
                    self.thread_id = returned_thread
                self.history.append({"role": "assistant", "content": reply})
                return reply
        except Exception as e:
            return f"[TinCan Agent Error: {e}]"

    def run_repl(self) -> None:
        print("\033[1;36m==========================================================")
        print("  ⚡ TinCan 2 — Agentic Chat & Mesh Intelligence REPL")
        if self.is_direct_mode():
            print("  Direct Target:", self._direct_target_label())
        else:
            print("  Connected to:", self.relay_url)
        print("  Model Target:", self.model_alias)
        print("  Type '/model <alias>' to switch, '/local [model]' for Ollama, '/help' for tools, 'exit' to quit")
        print("==========================================================\033[0m\n")

        while True:
            try:
                prompt = input("\033[1;32mtincan>\033[0m ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting TinCan Agent.")
                break

            if not prompt:
                continue
            if prompt.lower() in ("exit", "quit", ":q"):
                print("Bye!")
                break
            if prompt.startswith("/"):
                parts = prompt.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "/model":
                    if arg:
                        self.model_alias = arg.strip()
                        mode_tag = f"direct -> {self._direct_target_label()}" if self.is_direct_mode() else f"relay -> {self.relay_url}"
                        print(f"[+] Switched model target to: {self.model_alias} ({mode_tag})")
                    else:
                        print(f"Current model: {self.model_alias}")
                    continue
                elif cmd == "/local":
                    self.local = True
                    self.gateway = "ollama"
                    self.base_url = None
                    if arg.strip():
                        m_name = arg.strip()
                        self.model_alias = m_name if m_name.startswith("ollama/") else f"ollama/{m_name}"
                    else:
                        self.model_alias = self._resolve_initial_model(None)
                    print(f"[+] Switched to local Ollama: {self.model_alias} ({self._direct_target_label()})")
                    continue
                elif cmd == "/endpoint":
                    if arg.strip():
                        self.base_url = normalize_openai_compat_base_url(arg.strip())
                        self.gateway = None
                        self.local = True
                        print(f"[+] Direct OpenAI-compatible base URL set to: {self.base_url}")
                    else:
                        print(f"Current endpoint: {self._direct_target_label() if self.is_direct_mode() else self.relay_url}")
                    continue
                elif cmd == "/owlchat":
                    self.base_url = OWLCHAT_BASE_URL
                    self.gateway = "owlchat"
                    self.local = False
                    self.model_alias = f"owlchat/{arg.strip()}" if arg.strip() else "owlchat/Gemma4-vibe"
                    print(f"[+] Switched to FAU OwlChat: {self.model_alias} ({self._direct_target_label()})")
                    continue
                elif cmd == "/relay":
                    self.local = False
                    self.base_url = None
                    self.gateway = "relay"
                    if arg.strip():
                        self.model_alias = arg.strip()
                    elif self._get_router()._detect_compat_gateway(self.model_alias):
                        self.model_alias = "gemini-brain"
                    print(f"[+] Switched to Relay mode: {self.model_alias} ({self.relay_url})")
                    continue
                elif cmd in ("/rodin", "/ronin"):
                    if not arg:
                        print("[-] Usage: /rodin <prompt to generate 3d mesh>")
                        continue
                    print(f"\033[1;36m[🧊 Hyper3D Rodin] Generating 3D mesh for: \"{arg}\"...\033[0m")
                    try:
                        req_data = json.dumps({"prompt": arg, "tier": "Regular", "format": "glb"}).encode("utf-8")
                        req = urllib.request.Request(
                            f"{self.relay_url}/api/3d/generate",
                            data=req_data,
                            headers={"Content-Type": "application/json", "User-Agent": "TinCanAgent/1.0"},
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=30) as resp:
                            res = json.loads(resp.read().decode("utf-8"))
                        print(f"\033[1;32m[+] 3D Mesh Task: {res.get('uuid')} | Status: {res.get('status')} | Format: {res.get('format', 'glb').upper()}\033[0m")
                        if "saved_to_space" in res:
                            print(f"    Saved into VFS: {res['saved_to_space']['path']}")
                    except Exception as err:
                        print(f"[-] Rodin 3D Error: {err}")
                    continue
                elif cmd == "/space":
                    sp_args = arg.split(maxsplit=2)
                    sub = sp_args[0].lower() if sp_args else "ls"
                    if sub == "ls":
                        try:
                            with urllib.request.urlopen(f"{self.relay_url}/api/space/ls", timeout=10) as resp:
                                summary = json.loads(resp.read().decode("utf-8"))
                            print(f"\033[1;36m[🧪 AgentSpace] {summary.get('file_count', 0)} files in {summary.get('scope', 'user')}:{summary.get('owner_id', 'default')} (Merkle: {summary.get('merkle_root', '')[:12]}...)\033[0m")
                            for f in summary.get("files", []):
                                print(f"  • {f['path']} ({f['size_bytes']} bytes)")
                        except Exception as err:
                            print(f"[-] Space LS Error: {err}")
                    elif sub == "read" and len(sp_args) > 1:
                        target_p = sp_args[1]
                        try:
                            with urllib.request.urlopen(f"{self.relay_url}/api/space/file?path={urllib.parse.quote(target_p)}", timeout=10) as resp:
                                rec = json.loads(resp.read().decode("utf-8"))
                            print(f"\033[1;36m[📄 {target_p}]\033[0m\n{rec.get('content') or '[Binary Content]'}")
                        except Exception as err:
                            print(f"[-] Space Read Error: {err}")
                    elif sub == "write" and len(sp_args) > 2:
                        target_p = sp_args[1]
                        target_c = sp_args[2]
                        try:
                            req_data = json.dumps({"path": target_p, "content": target_c, "action": "write"}).encode("utf-8")
                            req = urllib.request.Request(
                                f"{self.relay_url}/api/space/file",
                                data=req_data,
                                headers={"Content-Type": "application/json"},
                                method="POST",
                            )
                            with urllib.request.urlopen(req, timeout=10) as resp:
                                res = json.loads(resp.read().decode("utf-8"))
                            print(f"\033[1;32m[+] Written {res.get('path')} ({res.get('size_bytes')} bytes)\033[0m")
                        except Exception as err:
                            print(f"[-] Space Write Error: {err}")
                    elif sub == "run":
                        entry = sp_args[1] if len(sp_args) > 1 else "/src/main.py"
                        try:
                            req_data = json.dumps({"entrypoint": entry, "runtime": "auto"}).encode("utf-8")
                            req = urllib.request.Request(
                                f"{self.relay_url}/api/space/exec",
                                data=req_data,
                                headers={"Content-Type": "application/json"},
                                method="POST",
                            )
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                res = json.loads(resp.read().decode("utf-8"))
                            print(f"\033[1;36m[🚀 Run {entry}] Exit: {res.get('exit_code')}\033[0m")
                            if res.get("stdout"):
                                print(res["stdout"].rstrip())
                            if res.get("stderr"):
                                print(f"\033[1;31m{res['stderr'].rstrip()}\033[0m")
                        except Exception as err:
                            print(f"[-] Space Exec Error: {err}")
                    elif sub == "agent" and len(sp_args) > 1:
                        sp_prompt = arg[len("agent"):].strip()
                        try:
                            req_data = json.dumps({"prompt": sp_prompt, "model_alias": self.model_alias}).encode("utf-8")
                            req = urllib.request.Request(
                                f"{self.relay_url}/api/space/agent",
                                data=req_data,
                                headers={"Content-Type": "application/json"},
                                method="POST",
                            )
                            with urllib.request.urlopen(req, timeout=30) as resp:
                                res = json.loads(resp.read().decode("utf-8"))
                            print(f"\033[1;34m[🤖 Space Agent]\033[0m {res.get('reply')}")
                        except Exception as err:
                            print(f"[-] Space Agent Error: {err}")
                    else:
                        print("[-] Space commands: /space ls, /space read <path>, /space write <path> <content>, /space run [path], /space agent <prompt>")
                    continue
                elif cmd == "/clear":
                    self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
                    self.thread_id = None
                    print("[+] Conversation memory cleared.")
                    continue
                elif cmd == "/help":
                    print("Commands:")
                    print("  /model <alias>     Switch active model (e.g. ollama/qwen2.5:3b, owlchat/Gemma4-vibe, gemini-brain)")
                    print("  /local [model]     Switch to local Ollama (auto-detects installed model if omitted)")
                    print("  /owlchat [model]   Switch to FAU OwlChat OpenAI API (default: Gemma4-vibe)")
                    print("  /endpoint <url>    Set a custom OpenAI-compatible base URL (e.g. http://localhost:8000/v1)")
                    print("  /relay [model]     Return to TinCan Relay mode")
                    print("  /rodin <prompt>    Generate 3D mesh via Hyper3D Rodin and save to space (alias /ronin)")
                    print("  /space <cmd>       Manage .space VFS (ls, read, write, run, agent)")
                    print("  /clear             Reset conversation memory")
                    print("  /help              Show this help text")
                    print("  exit / quit        Exit the agent REPL")
                    continue
                else:
                    print(f"[-] Unknown command: {cmd}")
                    continue

            print("\033[2mthinking...\033[0m", end="\r")
            reply = self.ask(prompt)
            print(" " * 20, end="\r")  # clear 'thinking...'
            print(f"\033[1;34m[TinCan]\033[0m {reply}\n")
