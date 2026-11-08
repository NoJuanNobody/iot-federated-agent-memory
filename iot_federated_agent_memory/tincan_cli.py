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
    read_parser.add_argument("--speak", action="store_true", help="Speak all unread messages aloud via TTS")
    read_parser.add_argument("--no-speak", action="store_true", help="Disable automatic TTS vocalization")
    read_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # say (local + remote voice TTS)
    say_p = subparsers.add_parser("say", help="Speak text aloud via Kokoro TTS and optionally send spoken message to a peer")
    say_p.add_argument("text", help="Text to vocalize")
    say_p.add_argument("--voice", default=None, help="Optional voice name (e.g. bella, michael)")
    say_p.add_argument("--to", default=None, help="Optional recipient alias or tc: address to also send spoken message")
    say_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # call / video (live WebRTC video, voice & screenshare room)
    for call_cmd in ("call", "video"):
        call_p = subparsers.add_parser(call_cmd, help="Launch live WebRTC Video, Voice & Screenshare call room")
        call_p.add_argument("recipient", nargs="?", default=None, help="Optional contact alias or tc: address to invite")
        call_p.add_argument("--room", default="main", help="WebRTC room name (default: main)")
        call_p.add_argument("--voice-only", action="store_true", help="Start in voice-only microphone mode")
        call_p.add_argument("--screen", action="store_true", help="Start with desktop screenshare enabled")
        call_p.add_argument("--no-browser", action="store_true", help="Do not automatically open local browser")
        call_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

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

    # playlist
    pl_parser = subparsers.add_parser("playlist", help="Manage the Relay Video Channel & Collection Playlist")
    pl_parser.add_argument("action", nargs="?", default="list", choices=["list", "add", "remove"], help="Action (list, add, remove)")
    pl_parser.add_argument("target", nargs="?", default=None, help="TikTok URL, video ID, embed snippet, or item ID")
    pl_parser.add_argument("--title", default=None, help="Optional title for the video")
    pl_parser.add_argument("--category", default="spotlight", help="Category tag (instruction, ad, spotlight)")
    pl_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

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
            from .tincan_voice import speak_text
            msgs = client.tincan_read(since_seq=args.since, timeout=args.timeout)
            if args.json:
                print(json.dumps(msgs, indent=2))
            else:
                if not msgs:
                    print("Inbox empty (no new messages).")
                for m in msgs:
                    sender_label = m.get("sender_alias") or m.get("sender")
                    ver_badge = "✓ verified" if m.get("verified") else "✗ unverified"
                    should_speak = (bool(m.get("speak")) or bool(args.speak)) and not bool(args.no_speak)
                    speak_badge = " [🔊 TTS spoken]" if should_speak else (" [TTS requested]" if m.get("speak") else "")
                    print(f"[{m.get('seq')}] From: {sender_label} ({ver_badge}){speak_badge}")
                    print(f"    {m.get('message')}")

                    msg_txt = m.get("message", "")
                    if should_speak and msg_txt:
                        speak_text(f"Message from {sender_label}: {msg_txt}", background=True)

                    # Automatically enqueue actionable requests into the Accessibility Gate
                    if any(keyword in msg_txt.lower() for keyword in ["open", "run", "launch", "execute", "start", "call", "join"]):
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

    if args.command == "say":
        from .tincan_voice import speak_text
        tts_res = speak_text(args.text, voice=args.voice, background=True)
        send_res = None
        if args.to:
            try:
                send_res = client.tincan_send(recipient_address=args.to, message=args.text, speak=True)
            except Exception as exc:
                send_res = {"error": str(exc)}
        out = {"tts": tts_res, "sent": send_res}
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(f"\033[1;32m🔊 Spoken via {tts_res.get('engine')}:\033[0m \"{args.text}\"")
            if send_res:
                if "error" in send_res:
                    print(f"[-] Remote send failed: {send_res['error']}", file=sys.stderr)
                else:
                    print(f"[+] Sent vocalized envelope to {args.to} (seq {send_res.get('seq')})")
        return 0

    if args.command in ("call", "video"):
        import subprocess
        import urllib.parse
        import urllib.request

        room = args.room or "main"
        mode = "screen" if args.screen else ("voice" if args.voice_only else "video")
        peer_id = f"{args.alias}-{os.uname().nodename.split('.')[0]}"
        relay_base = args.relay.rstrip("/")
        call_url = f"{relay_base}/?room={urllib.parse.quote(room)}&peer={urllib.parse.quote(peer_id)}&mode={mode}#call"

        # Register peer session on relay WebRTC room
        reg_payload = {
            "peer_id": peer_id,
            "display_name": f"{args.alias} ({os.uname().nodename.split('.')[0]})",
            "room": room,
            "has_video": not args.voice_only,
            "has_audio": True,
            "has_screen": bool(args.screen),
        }
        try:
            req = urllib.request.Request(
                f"{relay_base}/api/webrtc/register",
                data=json.dumps(reg_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass

        invite_res = None
        if args.recipient:
            try:
                invite_msg = f"Incoming TinCan {mode.upper()} Call in room '{room}'! Open {call_url} to join."
                invite_res = client.tincan_send(
                    recipient_address=args.recipient,
                    message=invite_msg,
                    speak=True,
                )
            except Exception as exc:
                invite_res = {"error": str(exc)}

        if not args.no_browser and sys.platform == "darwin":
            try:
                subprocess.run(["open", call_url], check=False)
            except Exception:
                pass

        result_info = {
            "status": "call_ready",
            "room": room,
            "mode": mode,
            "peer_id": peer_id,
            "call_url": call_url,
            "invite": invite_res,
        }
        if args.json:
            print(json.dumps(result_info, indent=2))
        else:
            print(f"\033[1;36m📹 TinCan Live WebRTC {mode.upper()} Room Ready:\033[0m")
            print(f"  Room:     {room}")
            print(f"  Join URL: {call_url}")
            if invite_res:
                if "error" in invite_res:
                    print(f"  Invite:   [-] Failed to notify {args.recipient}: {invite_res['error']}")
                else:
                    print(f"  Invite:   ✓ Sent encrypted + spoken call invite to {args.recipient} (seq {invite_res.get('seq')})")
        return 0

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

    if args.command == "playlist":
        import urllib.request
        relay_base = args.relay.rstrip("/")
        try:
            if args.action == "list":
                req = urllib.request.Request(f"{relay_base}/api/playlist", method="GET")
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    print(f"\033[1;35m📺 Relay Video Collection ({data.get('total', 0)} videos):\033[0m")
                    for idx, v in enumerate(data.get("videos", []), 1):
                        print(f"  {idx}. [{v.get('category', '').upper()}] {v.get('title')} ({v.get('creator')}) -> {v.get('cite_url')}")
                return 0
            elif args.action == "add":
                if not args.target:
                    print("[-] Please provide a TikTok URL, video ID, or embed snippet.", file=sys.stderr)
                    return 1
                payload = {"input": args.target, "title": args.title, "category": args.category}
                req = urllib.request.Request(
                    f"{relay_base}/api/playlist/add",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    it = data.get("item", {})
                    print(f"\033[1;32m[+] Added to Relay Collection:\033[0m {it.get('title')} ({it.get('cite_url')})")
                    print(f"    Total videos in rotation: {data.get('playlist', {}).get('total')}")
                return 0
            elif args.action == "remove":
                if not args.target:
                    print("[-] Please provide a video_id to remove.", file=sys.stderr)
                    return 1
                payload = {"video_id": args.target}
                req = urllib.request.Request(
                    f"{relay_base}/api/playlist/remove",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    print(f"[+] Status: {data.get('status')} (Remaining: {data.get('playlist', {}).get('total')})")
                return 0
        except Exception as exc:
            print(f"[-] Playlist error: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
