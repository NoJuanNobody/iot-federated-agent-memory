# TinCan Plain-English Testing Guide (Steps 1 to 10)

**What is this?** A simple, step-by-step guide to prove that **TinCan** works in real life—letting computers and AI assistants share memory directly without needing a cloud server, even when Wi-Fi drops or goes completely offline.  
**Companion Files:** `TinCan_Testing_Log.xlsx` (where you type your results) · `TinCan_Testing_Plan_Fillable.pdf` (printable check-off sheet)  
**Where We Are:** 4 of 10 tests **DONE** (`T-01`, `T-02`, `T-03`, `T-05`) · **6 Left To Do** (`T-04`, `T-06`, `T-07`, `T-08`, `T-09`, `T-10`)

---

## Quick Scorecard

| Test | Plain-English Name | What You Need | Status | What "Good" Looks Like |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | Built-In Safety Check | Your Mac | **PASS** | All 26 built-in checks pass with zero errors (uses ~51 MB RAM) |
| **T-02** | Smaller Offline Catch-Up | Your Mac | **PASS** | Sends 88.6% less data after being offline; zero edits lost |
| **T-03** | Message Privacy Lock | Your Mac | **PASS** | Messages are scrambled; wrong or missing password is blocked |
| **T-04** | Live Server Disagreement | Your Mac | **PENDING** | App saves info, spots two clashing answers, lets you pick a winner |
| **T-05** | Two-Agent Practice Run | Your Mac | **PASS** | Two simulated computers sync offline work & match after fixing clash |
| **T-06** | Two Computers, Same Wi-Fi | 2 Macs on Wi-Fi | **PENDING** | Both Macs find each other automatically (no cloud) and match |
| **T-07** | Wi-Fi vs. Phone Hotspot | 2 Macs, 2 networks | **PENDING** | Both Macs connect directly across different networks with no cloud |
| **T-08** | Small / Cheap Computer | Docker or Pi | **PENDING** | Slim version builds cleanly and uses under 128 MB of memory |
| **T-09** | Bad / Shaky Wi-Fi Test | Docker (Linux) | **PENDING** | Still finishes syncing when 10%–30% of data drops; beats cloud |
| **T-10** | Off-Grid Radio *(Optional)* | 2 LoRa Radios | **PENDING** | Syncs over radio waves with zero Wi-Fi or internet |

---

## Before You Start (Do This First)

Open the **Terminal** app on your Mac and paste this line so you are in the right project folder:

```bash
cd /Users/alejandrolondono/dev/50_research-and-fau/iot-federated-agent-memory/.worktrees/os-desktop-parity
```

Make sure Python 3.11+ is installed. If a test ever says a package is missing, run `pip install -e ".[p2p]"`.

---

## Part 1: Tests You Run on Your Own Mac (T-01 to T-05)

### T-01 · Built-In Safety Check *(Already Passed)*
**What this proves:** TinCan's built-in automatic tests all pass—meaning data stays safe, signed by the real sender, and matches up cleanly.

```bash
PYTHONPATH=. pytest tests/test_gap_closures.py tests/test_crdt_mesh.py -v
```

- **How to know it worked:** Every line ends with `PASSED` and there are `0 failed`.

---

### T-02 · Smaller Offline Catch-Up *(Already Passed)*
**What this proves:** If you make lots of edits while offline, TinCan bundles them into one tiny update instead of re-sending every old draft when you reconnect.

```bash
PYTHONPATH=. python3 scripts/eval_mesh_benchmarks.py
```

- **How to know it worked:** Data sent drops by **88.6%** (from ~1.29 MB down to ~147 KB) with **0 lost edits**.

---

### T-03 · Message Privacy Lock *(Already Passed)*
**What this proves:** When you turn on a shared team password, nobody snooping on the Wi-Fi can read your messages, and anyone with the wrong password is automatically blocked.

```bash
PYTHONPATH=. pytest tests/test_gap_closures.py -k "aead_encrypted_broadcast" -v
```

- **How to know it worked:** The test passes—meaning readable text never leaks onto the network, and wrong or missing passwords are rejected.

---

### T-04 · Live Server Save & Disagreement Check *(PENDING — Do This Next)*
**What this proves:** While TinCan is actually running on your Mac, it can save a note, notice when two people/agents pick two different answers at the same time (15 vs. 60), flag the clash instead of silently deleting someone's work, and let you choose the final answer (30).

**Step 1 — Start the TinCan server (leave this Terminal window open):**
```bash
PORT=8765 python3 server.py
```

**Step 2 — Open a second Terminal window, save a file note, and pick `15` as your answer:**
```bash
# Save a note into the live app
curl -s -X POST http://127.0.0.1:8765/api/crdt/kg \
  -H "Content-Type: application/json" \
  -d '{"action":"upsert_entity","entity_id":"file:auth.py","entity_type":"module","fields":{"owner":"mac-a","status":"draft"}}' | python3 -m json.tool

# Record your choice: jwt_ttl = 15
curl -s -X POST http://127.0.0.1:8765/api/crdt/kg \
  -H "Content-Type: application/json" \
  -d '{"action":"propose_decision","topic":"jwt_ttl","choice":15}' | python3 -m json.tool
```

**Step 3 — Pretend a second computer sends a competing answer (`60`) at the same time:**
```bash
PYTHONPATH=. python3 -c '
import json, urllib.request
from iot_federated_agent_memory.agent_kg_crdt import FederatedAgentKnowledgeGraph

remote = FederatedAgentKnowledgeGraph("remote-peer-b")
delta = remote.propose_decision("jwt_ttl", 60)
req = urllib.request.Request(
    "http://127.0.0.1:8765/api/crdt/gossip",
    data=json.dumps({"delta": delta.to_dict()}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print("Disagreements found:", json.dumps(resp["conflicts"], indent=2))
'
```

**Step 4 — Pick the final winning answer (`30`) and confirm the clash is cleared:**
```bash
curl -s -X POST http://127.0.0.1:8765/api/crdt/kg \
  -H "Content-Type: application/json" \
  -d '{"action":"resolve_decision","topic":"jwt_ttl","choice":30}' | python3 -m json.tool
```

- **How to know it worked:**
  1. Step 3 prints a disagreement showing both `15` and `60`.
  2. Step 4 shows `"conflicts": []` (empty) and saves `30` as the final answer.
- **Record your result:** Mark `T-04` as `PASS` in `TinCan_Testing_Log.xlsx`.

---

### T-05 · Two-Agent Practice Run on One Mac *(Already Passed)*
**What this proves:** Two simulated assistants work offline on your Mac, make overlapping edits, reconnect, spot the clash (15 vs. 60), fix it to 30, and end up with identical memory.

```bash
PYTHONPATH=. python3 scripts/demo_pair_programming_mesh.py
```

- **How to know it worked:** Both sides keep their separate edits, flag the clash, and finish with matching digital fingerprints (~25.5 KB sent).

---

## Part 2: Real-World Tests Across Devices & Networks (T-06 to T-10)

### T-06 · Two Real Computers on the Same Wi-Fi *(PENDING)*
**What this proves:** Two real Macs on the same Wi-Fi find each other automatically—no cloud server, no typing IP addresses—and keep their data in sync.

**On Computer 1 (connected to Wi-Fi):**
```bash
PYTHONPATH=. python3 scripts/demo_p2p_two_machines.py --node-id mac-a --port 45454 --no-stun --duration 60
```

**On Computer 2 (connected to the exact same Wi-Fi):**
```bash
PYTHONPATH=. python3 scripts/demo_p2p_two_machines.py --node-id mac-b --port 45454 --no-stun --duration 60
```

- **How to know it worked:**
  1. Both screens say `[discovery] Joined LAN peer ...` all by themselves.
  2. Both screens show incoming updates and end up printing the **exact same `merkle_root` code** (that code is the digital fingerprint proving both computers match 100%).
- **Tip:** If macOS pops up a firewall box asking to allow Python connections, click **Allow**.
- **Record your result:** Write `PASS`, the bytes sent (`tx`/`rx`), and `YES` for "Both Match?" in `TinCan_Testing_Log.xlsx`.

---

### T-07 · Two Computers on Different Networks — Wi-Fi vs. Phone Hotspot *(PENDING)*
**What this proves:** Two computers on completely different internet connections can still talk **directly to each other** without sending your data through a cloud server.

**Step 1 — On Computer 1 (regular home/office Wi-Fi):**
```bash
PYTHONPATH=. python3 scripts/demo_p2p_two_machines.py --node-id mac-a --port 45454 --duration 90
```
Look near the top of the output and copy the `Public UDP:` address (it looks like `123.45.67.89:45454`).

**Step 2 — Connect Computer 2 to your phone's hotspot, then paste Computer 1's address after `--peer`:**
```bash
PYTHONPATH=. python3 scripts/demo_p2p_two_machines.py \
  --node-id mac-b --port 45454 --peer <PASTE_ADDRESS_HERE> --duration 90
```

- **How to know it worked:**
  1. Computer 1 prints a `Public UDP` address.
  2. Both computers receive updates directly from each other and print the **exact same `merkle_root` fingerprint**.
- **Heads-up:** Some strict cell carriers block direct phone-hotspot connections. If it fails on your carrier, write down which carrier you used—that is still useful data for the paper!

---

### T-08 · Small / Cheap Computer Test (Raspberry Pi or Slim Container) *(PENDING)*
**What this proves:** TinCan's lightweight version is tiny enough to run on a cheap $15–$50 Raspberry Pi without eating up memory.

**Step 1 — Build the slim lightweight package (in Docker or on a Raspberry Pi):**
```bash
docker build -f Dockerfile.edge -t tincan-edge:latest .
```

**Step 2 — Run the memory & speed test inside that slim package:**
```bash
docker run --rm --entrypoint python3 \
  -v "$(pwd)/scripts/measure_edge_footprint.py:/app/measure_edge_footprint.py:ro" \
  tincan-edge:latest /app/measure_edge_footprint.py --output /tmp/edge_footprint.json
```

**Step 3 — (Optional) Run it live on a Raspberry Pi on your Wi-Fi:**
```bash
docker run --rm --network host tincan-edge:latest --node-id pi-edge-01 --port 45454
```

- **How to know it worked:**
  1. It builds cleanly with no errors.
  2. Peak memory stays **under 128 MB** (usually around 50–65 MB) and both test nodes match 100%.
- **Record your result:** Log the memory used (MB) and speed (ms) in `TinCan_Testing_Log.xlsx`.

---

### T-09 · Shaky Wi-Fi Test — Dropping 10% to 30% of Data *(PENDING)*
**What this proves:** Even on a terrible connection where up to 30% of network packets vanish, TinCan still finishes syncing reliably—and is faster than bouncing through a cloud server.

**Step 1 — Run the real packet-drop simulator in Docker (tests 10%, 20%, and 30% data loss):**
```bash
docker run --rm -it --cap-add=NET_ADMIN \
  -v "$(pwd):/work" -w /work python:3.11-slim bash -c '
    apt-get update -qq && apt-get install -y -qq iproute2 >/dev/null
    pip install -q PyNaCl
    for LOSS in 10% 20% 30%; do
      echo "=== Testing bad Wi-Fi: $LOSS packet loss ==="
      tc qdisc replace dev lo root netem delay 25ms loss $LOSS
      PYTHONPATH=. python3 scripts/demo_pair_programming_mesh.py
    done
    tc qdisc del dev lo root
  '
```

**Step 2 — Measure how long a single trip to the cloud server takes for comparison:**
```bash
curl -s -o /dev/null -w "Cloud server round-trip: %{time_total}s\n" \
  https://iot-federated-agent-memory-production.up.railway.app/health
```

- **How to know it worked:**
  1. TinCan finishes syncing at 10%, 20%, and 30% data loss with **zero lost edits**.
  2. Direct syncing finishes faster and sends less data than going through the cloud server.

---

### T-10 · Off-Grid Radio Test *(Optional — Only If You Have LoRa Radios)* *(PENDING)*
**What this proves:** TinCan can even sync over long-range walkie-talkie-style radio waves with **zero Wi-Fi and zero internet** (like during a hurricane or power outage).

**What you need:** Two LoRa radio boards (RNode) plugged in via USB + the radio add-on installed:
```bash
pip install -e ".[disaster]"
```

**How to test:**
1. Set up your two radio boards in `~/.reticulum/config` on both computers.
2. Turn **off** Wi-Fi and unplug Ethernet on both computers so there is zero internet.
3. Run TinCan's radio transport (`ReticulumTransportChannel` in `p2p_transport.py`) on both sides and confirm both computers end up with matching data.

---

## Wrapping Up & Sharing Your Results

1. Fill in the **blue boxes** in `TinCan_Testing_Log.xlsx` as you finish each test (the totals at the top update automatically).
2. Check off each box on `TinCan_Testing_Plan_Fillable.pdf` and sign the bottom when done.
3. Share the filled-in log and checklist back so we can include the real-world numbers in the final TinCan paper.
