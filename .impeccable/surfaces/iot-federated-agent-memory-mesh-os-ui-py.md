---
version: 1
slug: "iot-federated-agent-memory-mesh-os-ui-py"
primary_target: "iot_federated_agent_memory/mesh_os_ui.py"
related_targets: ["iot_federated_agent_memory/zen_shell.py"]
---

# Surface: Mesh OS startup shell (`/`)

Mode: Experience on first viewport (the feed leads, interface recedes); Operate once a tool is open.
Audience: ad viewers first, returning peers second. Job: watch, then optionally join; peers reach any tool in one gesture.
Constraints: windows, popouts and single-window routes keep working; registration still gates every tool; shell injected from `zen_shell.py` so concurrent edits to `mesh_os_ui.py` stay conflict-light. Owner pinned the aesthetic (zen, dirty gradients, video background), so no direction roll ran.

## Direction contract
THESIS: The feed is the room and the OS is a whisper. Refuses the default of a colored pill dock plus every window tiled open on load.
OWN-WORLD: Sumi ink ground, washi-white type, one persimmon accent reserved for the mark and the active clip. Muddy rust / moss / indigo washes drifting over the video with fine grain; 1px washi hairlines; Shippori Mincho for names, Zen Kaku Gothic New for small UI. No pills, no glow, no emoji.
STORY: A visitor sees a clip playing, scrolls to the next, taps for sound, and finds one quiet "join" when ready. A peer taps the mark (or ⌘K) and opens any tool from a hushed full-screen list.
FIRST VIEWPORT: Blurred cover of the current clip fills the screen; the 9:16 clip sits centered at ~92vh (full-bleed on phones). Mark top-left, title and creator bottom-left, sound and join bottom-right, hairline position ticks on the right edge.
FORM: Vertical feed with ink-wash launcher (owner-pinned, position 1 of 1). Signature interaction: the clip change is a vertical drift with a backdrop crossfade; opening the launcher deepens the wash and blur over the still-playing video. seed: none (brief-pinned)
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
