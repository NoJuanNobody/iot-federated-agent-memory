"""
TinCan Client & Relay CLI Interface.

Supports:
  whoami                    Inspect local cryptographic identity and address
  send <recipient> <msg>    Encrypt, sign, and post sealed ciphertext to relay
  read [--since <seq>]      Fetch inbox, decrypt using private key, verify signatures
  contacts                  List pinned contacts (TOFU)
  add-contact <alias> <tc>  Pin a trusted contact address
  mcp                       Run standard MCP stdio server
  serve [--port 8080]       Run standalone TinCan Blind Relay server
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from .tincan_mcp import TinCanMCPClient, run_stdio_server
from .tincan_relay import TinCanBlindRelay


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="tincan",
        description="TinCan Agent-to-Agent Encrypted Messaging & Blind Relay CLI",
    )
    parser.add_argument("--dir", default=None, help="Directory for identities & contacts (~/.tin-can)")
    parser.add_argument(
        "--relay",
        default=os.environ.get("TINCAN_RELAY", "https://iot-federated-agent-memory-production.up.railway.app"),
        help="Relay server URL (default: live Railway production relay)",
    )
    parser.add_argument("--as", dest="alias", default="default", help="Identity alias to use (default: 'default')")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    subparsers = parser.add_subparsers(dest="command", help="TinCan commands")

    # whoami
    who_p = subparsers.add_parser("whoami", help="Display current local identity and TinCan address")
    who_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # send
    send_parser = subparsers.add_parser("send", help="Send sealed message to a recipient address or contact alias")
    send_parser.add_argument("recipient", help="Recipient TinCan address (tc:...) or contact alias")
    send_parser.add_argument("message", help="Message text to send")
    send_parser.add_argument("--speak", action="store_true", help="Request vocalization via TTS")
    send_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # read
    read_parser = subparsers.add_parser("read", help="Fetch and decrypt inbox messages")
    read_parser.add_argument("--since", type=int, default=0, help="Fetch messages after this sequence number")
    read_parser.add_argument("--timeout", type=float, default=0.0, help="Long-poll timeout in seconds")
    read_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # contacts
    contacts_p = subparsers.add_parser("contacts", help="List pinned contacts")
    contacts_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # add-contact
    add_parser = subparsers.add_parser("add-contact", help="Pin a contact's public key (TOFU)")
    add_parser.add_argument("alias", help="Human-readable alias name")
    add_parser.add_argument("address", help="TinCan address (tc:<52 base32 chars>)")
    add_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # mcp
    subparsers.add_parser("mcp", help="Start MCP server over stdio")

    # screensaver / start
    start_p = subparsers.add_parser("start", help="Launch the full terminal screensaver and live mesh dashboard")
    start_p.add_argument("--duration", type=float, default=None, help="Exit after N seconds")

    ss_p = subparsers.add_parser("screensaver", help="Alias for 'start'")
    ss_p.add_argument("--duration", type=float, default=None, help="Exit after N seconds")

    # chat / agent
    chat_p = subparsers.add_parser("chat", help="Start interactive agentic chat REPL with the live OpenRouter models")
    chat_p.add_argument("prompt", nargs="?", default=None, help="Single-shot prompt to send to the agent")
    chat_p.add_argument("--model", default="gemini-brain", help="Model alias to use (default: gemini-brain)")

    agent_p = subparsers.add_parser("ask", help="Single-shot query to the TinCan Agent")
    agent_p.add_argument("prompt", help="Prompt question for the agent")
    agent_p.add_argument("--model", default="gemini-brain", help="Model alias to use")

    # actions / accessibility queue
    act_p = subparsers.add_parser("actions", help="List and review incoming actions queued for approval (Accessibility Gate)")
    act_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    run_act_p = subparsers.add_parser("trigger", help="Approve and trigger an incoming queued action (e.g. 'tincan trigger 1')")
    run_act_p.add_argument("action", help="Sequence number or action ID to execute")
    run_act_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    dismiss_act_p = subparsers.add_parser("dismiss", help="Dismiss a queued action without executing")
    dismiss_act_p.add_argument("action", help="Sequence number or action ID to dismiss")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Run local standalone TinCan Blind Relay")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    serve_parser.add_argument("--db", default=":memory:", help="SQLite database path (default: :memory:)")

    # upgrade
    subparsers.add_parser("upgrade", help="Upgrade TinCan CLI and mesh bundles to the latest production release")

    args = parser.parse_args(argv)

    # Check for silent auto-upgrade in background if needed (non-blocking)
    if args.command != "upgrade":
        try:
            from .auto_upgrade import check_and_auto_upgrade
            check_and_auto_upgrade(args.relay, config_dir=args.dir, force=False)
        except Exception:
            pass

    if not args.command:
        # Default bare command: launch the interactive screensaver / live mesh TUI
        from .tui import main as tui_main
        return tui_main(["--screensaver", "--relay", args.relay])

    if args.command == "upgrade":
        import subprocess
        print(f"[*] Upgrading TinCan from {args.relay}...")
        cmd = f"curl -sSL {args.relay}/install.sh | bash"
        res = subprocess.run(cmd, shell=True)
        return res.returncode

    if args.command == "mcp":
        client = TinCanMCPClient(relay_url=args.relay, config_dir=args.dir, alias=args.alias)
        run_stdio_server(client)
        return 0

    if args.command == "serve":
        from http.server import ThreadingHTTPServer
        from .tincan_relay import TinCanBlindRelay

        relay_instance = TinCanBlindRelay(db_path=args.db)
        from ..server import MeshGatewayHandler
        print(f"[*] Starting TinCan Blind Relay on port {args.port} (db: {args.db})...")
        server = ThreadingHTTPServer(("0.0.0.0", args.port), MeshGatewayHandler)
        server.serve_forever()
        return 0

    client = TinCanMCPClient(relay_url=args.relay, config_dir=args.dir, alias=args.alias)

    if args.command == "whoami":
        info = client.tincan_whoami()
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print(f"TinCan Identity: {info['alias']}")
            print(f"Address:         {info['address']}")
            print(f"Public Key (hex): {info['public_key']}")
            print(f"Relay:           {info['relay_url']}")
            print(f"Pinned Contacts: {info['contacts_count']}")
        return 0

    if args.command == "send":
        try:
            res = client.tincan_send(recipient_address=args.recipient, message=args.message, speak=args.speak)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"[+] Message sent! Seq: {res.get('seq')}, Envelope ID: {res.get('envelope_id')}")
            return 0
        except Exception as exc:
            if args.json:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                print(f"[-] Send failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "read":
        try:
            from .tincan_actions import enqueue_action
            msgs = client.tincan_read(since_seq=args.since, timeout=args.timeout)
            if args.json:
                print(json.dumps(msgs, indent=2))
            else:
                if not msgs:
                    print("Inbox empty (no new messages).")
                for m in msgs:
                    sender_label = m.get("sender_alias") or m.get("sender")
                    ver_badge = "✓ verified" if m.get("verified") else "✗ unverified"
                    speak_badge = " [TTS requested]" if m.get("speak") else ""
                    print(f"[{m.get('seq')}] From: {sender_label} ({ver_badge}){speak_badge}")
                    print(f"    {m.get('message')}")

                    # Automatically enqueue actionable requests into the Accessibility Gate
                    msg_txt = m.get("message", "")
                    if any(keyword in msg_txt.lower() for keyword in ["open", "run", "launch", "execute", "start"]):
                        act = enqueue_action(
                            seq=m.get("seq", 0),
                            sender=m.get("sender", ""),
                            sender_alias=m.get("sender_alias"),
                            command_text=msg_txt,
                            config_dir=args.dir,
                        )
                        print(f"    \033[33m⚡ Queued in Accessibility Gate [seq {m.get('seq')}]. Run 'tincan trigger {m.get('seq')}' to execute.\033[0m")
            return 0
        except Exception as exc:
            if args.json:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                print(f"[-] Read failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "actions":
        from .tincan_actions import load_pending_actions
        actions = load_pending_actions(args.dir)
        if args.json:
            print(json.dumps(actions, indent=2))
        else:
            pending = [a for a in actions if a.get("status") == "pending_approval"]
            if not pending:
                print("No pending actions awaiting approval.")
            else:
                print("\033[1;36m=== Pending Inbound Actions (Accessibility Gate) ===\033[0m")
                for a in pending:
                    print(f"[{a['seq']}] From {a['sender_alias']}: \"{a['command']}\"")
                    print(f"    -> Run: \033[1;32mtincan trigger {a['seq']}\033[0m to approve & execute")
        return 0

    if args.command == "trigger":
        from .tincan_actions import execute_action
        try:
            res = execute_action(args.action, args.dir)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"\033[1;32m✓ Action triggered:\033[0m {res['command']}")
                print(f"  Result: {res.get('result')}")
            return 0
        except Exception as exc:
            print(f"[-] Trigger error: {exc}", file=sys.stderr)
            return 1

    if args.command == "dismiss":
        from .tincan_actions import dismiss_action
        try:
            res = dismiss_action(args.action, args.dir)
            print(f"[+] Dismissed action {res['seq']}")
            return 0
        except Exception as exc:
            print(f"[-] Error: {exc}", file=sys.stderr)
            return 1

    if args.command in ("start", "screensaver"):
        from .tui import main as tui_main
        tui_args = ["--screensaver", "--relay", args.relay]
        if args.duration is not None:
            tui_args.extend(["--duration", str(args.duration)])
        return tui_main(tui_args)

    if args.command in ("chat", "ask"):
        from .tincan_agent import TinCanAgentChat
        agent = TinCanAgentChat(relay_url=args.relay, model_alias=args.model)
        if hasattr(args, "prompt") and args.prompt:
            reply = agent.ask(args.prompt)
            print(reply)
            return 0
        agent.run_repl()
        return 0

    if args.command == "contacts":
        contacts = client.tincan_list_contacts()
        if args.json:
            print(json.dumps(contacts, indent=2))
        else:
            if not contacts:
                print("No pinned contacts.")
            for c in contacts:
                print(f"- {c['alias']}: {c['address']}")
        return 0

    if args.command == "add-contact":
        try:
            res = client.tincan_add_contact(args.alias, args.address)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"[+] Pinned contact '{res['alias']}' -> {res['address']}")
            return 0
        except Exception as exc:
            if args.json:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                print(f"[-] Failed to pin contact: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
