"""Interactive Chat & Agentic Assistant for TinCan CLI."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

SYSTEM_PROMPT = """You are TinCan Agent, an autonomous assistant embedded inside the TinCan 2 / IoT Federated Mesh CLI.
You have access to the mesh network, peer addresses, encrypted communication, and OpenRouter multi-lab models.
Keep your answers sharp, technical, and concise. Help the user interact with peer agents, check inbox messages, craft secure envelopes, and route intelligence across nodes."""


class TinCanAgentChat:
    """Agentic REPL loop supporting natural queries, commands, and live model completions."""

    def __init__(
        self,
        relay_url: str,
        model_alias: str = "gemini-brain",
        thread_id: Optional[str] = None,
        peer_id: Optional[str] = None,
    ):
        self.relay_url = relay_url.rstrip("/")
        self.model_alias = model_alias
        self.thread_id = thread_id
        self.peer_id = peer_id
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def ask(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
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
        print("  Connected to:", self.relay_url)
        print("  Model Target:", self.model_alias)
        print("  Type '/model <alias>' to switch, '/help' for tools, 'exit' to quit")
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
                        print(f"[+] Switched model target to: {self.model_alias}")
                    else:
                        print(f"Current model: {self.model_alias}")
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
                    print("  /model <alias>   Switch active model (e.g. claude-brain, grok-brain, gemini-brain, openai-brain)")
                    print("  /rodin <prompt>  Generate 3D mesh via Hyper3D Rodin and save to space (alias /ronin)")
                    print("  /space <cmd>     Manage .space VFS (ls, read, write, run, agent)")
                    print("  /clear           Reset conversation memory")
                    print("  /help            Show this help text")
                    print("  exit / quit      Exit the agent REPL")
                    continue
                else:
                    print(f"[-] Unknown command: {cmd}")
                    continue

            print("\033[2mthinking...\033[0m", end="\r")
            reply = self.ask(prompt)
            print(" " * 20, end="\r")  # clear 'thinking...'
            print(f"\033[1;34m[TinCan]\033[0m {reply}\n")
