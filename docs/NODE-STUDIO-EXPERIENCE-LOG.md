# Node Studio — Living Product Experience Log

A running, chronological record of hands-on user testing feedback, root causes diagnosed, and fixes shipped in TinCan Node Studio (`/nodes` & `#win-nodes`).

---

## Entry #1 — 2026-11-19

### User Experience Notes (Verbatim Summary)
1. **Regressions after adding multi-modality**: Originally Node Studio worked cleanly for generating images; after expanding it to generate anything, the interface became buggy and confusing.
2. **Hard to discover non-image / non-splat generation**: You can tell how to generate images and splats, and you can select models from the picker, but generating other modalities (especially **Text**) felt weird and unclear ("I was able to generate a text object, but I don't understand how it works").
3. **Bug — Merging 2 images with Nano Banana 2 still creates a 3D Splat**:
   - Steps: Select 2 images on the canvas -> confirm the selected model is **Nano Banana 2** -> enter prompt `"Put this dog in space"` -> click Generate.
   - Expected: A merged 2D image created by Nano Banana 2.
   - Actual: Created a World Labs 3D Splat even though Nano Banana 2 was selected and no 3D Splat option was chosen.
4. **Atlas v2 Pipeline Bar**: The permanently-mounted `● ATLAS v2 PIPELINE` workflow bar inside the Prompt Island didn't make sense and cluttered the workspace — requested to rip it out.
5. **Core UX Goal**: Make it straightforward and user-friendly to use ALL models (Image, Text, Video, Audio, 3D Mesh, 3D Splat) and switch cleanly between them.

### Root Causes Found
- **Stale `/atlas splat` default hijack**: `state.activeSlashCommand` initialized to `"/atlas splat"` with `#nsActiveSlashPill` visible by default. `selectModel("gemini-3.1-flash-image")` never cleared `state.activeSlashCommand` or hid `#nsActiveSlashPill`, and `generate()` had a catch-all `(slashPillActive && hasPhotos)` branch that hijacked any multi-image generation into `runTerminalCommand("/atlas splat ...")`.
- **No Text models in the Model Picker + broken `/text` route**: `AVAILABLE_MODELS` completely omitted Text models (`gemini-3.1-pro`, `nanogpt/TEE/deepseek-v4.1-flash`, `nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic`), `/text` pointed at `gemini-nano-banana-2.1`, and `buildOmniNodeFromParsed` fell through to an Atlas card for `/text` and an Omni-World Splat card for `/video` and `/3d`.
- **Broken Audio / Video / 3D rendering**: Selecting Audio/Video/3D from the model dropdown bypassed `/api/omni/route` or rendered a fake `"Gemini"` text box / Atlas Splat card instead of modality-native cards (`<audio controls>`, `<video controls>`, `.GLB` card).
- **Sticky drag-drop references & cluttered initial stage**: Dropping images onto the canvas added sticky `source: "upload"` duplicates; `#nsAtlasWorkflowBar`, `#nsFloatingTerminal`, and 4 ghost Torii Gate Atlas showcase cards cluttered every fresh session.

### Fixes Shipped
- **Ripped out `#nsAtlasWorkflowBar` (`ATLAS v2 PIPELINE`)**, removed the Atlas HUD credit pill and ghost showcase cards, and collapsed the Dark Terminal by default (`Terminal [Show]` / `` ` `` shortcut).
- **Fixed Image Merge routing**: Default `activeSlashCommand` is `""` (hidden pill), `selectModel()` and `selectModality()` always clear stale slash routes and reset provider cleanly, `applyGraphState()` sanitizes old saved graphs, and `generate()` NEVER hijacks non-Atlas models into 3D Splats.
- **Added 1-click Modality Switcher (`Image | Text | Video | Audio | 3D Mesh | 3D Splat`) + Grouped Model Picker** with all 14 models (including first-class Text models), remembered last-used model per modality, plain-English placeholders, dynamic Generate button labels, and context-aware settings controls (hiding irrelevant `ASPECT`/`RES` for Text/Audio/3D, showing `FPS` for Video, `TYPE` for Audio, `TIER` for 3D Mesh, `STEP`/`QUALITY` for 3D Splat).
- **Upgraded Text, Audio, Video, and 3D Mesh Node Cards**:
  - **Text nodes**: Readable selectable text card with model badge, prompt subtitle, `Copy`, `→ To Image`, `Reply`, and `+ Ref` chaining (Text → Image, Image → Text, Text → Text).
  - **Audio nodes**: Real HTML5 `<audio controls>` player + `.WAV` download via `/api/omni/route`.
  - **Video nodes**: Dedicated `<video controls>` card + FPS/model metadata + `.MP4` download.
  - **3D Mesh nodes**: Dedicated PBR `.GLB` card + `.GLB` download + 1-click `Auto-Rig Walk`.
- **Engine fixes (`node_studio_engine.py`)**: Auto-extract `base64`/`mimeType` from `data:` URLs in `_normalize_references`, pass selected Text & Image references cleanly to Gemini and NanoGPT, and prevent single-parent `conversationHistory` leakage during multi-image `MERGE` mode.

---

## Entry #2 — 2026-11-19 (Argon Orchestrator Swarm · Full-Parity Upgrade)

### Follow-Up Goal
Resolve every remaining Node Studio limitation via parallel worktree swarm (`swarm/ns-backend-async` + `swarm/ns-ui-async-media` -> `feat/node-studio-full-parity` -> `main`) and deploy to Railway production.

### Shipped Enhancements
1. **Async Video Polling + Durable `.space` Streaming**:
   - `_generate_with_nanogpt()` now handles NanoGPT asynchronous `runId` / `requestId` video jobs cleanly instead of fabricating `media.local` URLs, and `poll_nanogpt_video_status()` polls `GET https://api.nano-gpt.com/api/video/status`.
   - Added `GET /api/nodes/video/status` (and synchronous video mirroring) in `server.py`, persisting finished `.mp4` bytes to `.space/videos/` and serving them via `/api/space/file?raw=1...` with full **HTTP `Range` (`206 Partial Content`, `Accept-Ranges: bytes`, `Content-Range`, `416`)** support for Chrome and Safari/WebKit.
   - Added live 4s `pollVideoJobForNode()` in `node_studio_ui.py` with elapsed timers, error boxes, graph reload auto-resume, and live hot-swap into `<video controls playsinline loop>`.
2. **Inline Interactive 3D `.GLB` Preview + Async Rodin Polling**:
   - Added `GET /api/nodes/mesh/status` + async `/api/omni/route` `/3d` handling in `server.py` with `.space/models3d/` persistence and `glb_raw_url`.
   - Added lazy `@google/model-viewer@3.5.0` loading with automatic offline Canvas 2D rotating wireframe fallback directly inside 3D Mesh cards (`.ns-mesh-stage`), cached Blob URL lifecycle cleanup, live 4s `pollMeshJobForNode()`, and a Fullscreen 3D Mesh Inspector modal (`#nsMeshViewerModal`) with orbit, auto-rotate, animation play/pause, `.GLB` download, and `Esc` close.
3. **Synced `Chat` & `Library` Top Views**:
   - Upgraded `#nsConversationView` (`Chat`) into a live canvas-lineage conversation feed (`renderConversationView`) with rich multi-modal previews, `Focus on Canvas`, and direct inline reply composer (`sendChatPrompt`).
   - Upgraded `#nsLibraryView` (`Library`) with modality filter pills (`All | Image | Text | Video | Audio | 3D Mesh | 3D Splat`), live search, and 1-click `Focus`, `+ Ref`, `Download`, and `Delete` actions.

---

## Entry #3 — 2026-11-20 (Live Production QA · Audio Pipeline Repair)

### User Experience Notes (Verbatim)
- `"audio files are not working"` during live production QA on `/nodes`.

### Root Causes Found
1. **Fake 120ms beep instead of real NanoGPT audio**: `DynamicAIGatewayRouter.generate_omni_audio()` in `ai_gateway.py` never called NanoGPT even when `NANOGPT_API_KEY` was configured in production — it unconditionally emitted a 3.8 KB, 0.12-second synthetic sine-wave `.wav`.
2. **Hardcoded `.wav`, missing durable streaming URL, and missing async `runId` polling**: `_audio_generate_and_save()` in `server.py` forced `.wav` extensions regardless of real MP3/OGG/WAV magic bytes, omitted `/api/space/file?raw=1...` `Range` `206` streaming URLs (forcing huge inline `data:` URLs that stall Safari/Chrome playback), and had no `/api/nodes/audio/status` polling endpoint for NanoGPT HTTP `202` pending `runId` jobs.
3. **Clipped `<audio controls>`, canvas click-stealing, and rejected local audio uploads**:
   - Audio cards (`310x218px`, `overflow: hidden`) + `.ns-audio-player` (`32px`) clipped native browser `<audio controls>`.
   - Clicking an unselected Audio card's native Play button triggered `renderNodes()` synchronously on `mousedown` (destroying the `<audio>` DOM node mid-click) and initiated card dragging on scrub/volume gestures.
   - `#nsFileInput` omitted `audio/*` and `addImageFilesToCanvas` / `addFilesToRefs` silently dropped local `.mp3`/`.wav`/`.ogg`/`.flac`/`.m4a` files.

### Fixes Shipped
- **Real NanoGPT Audio Synthesis (`ai_gateway.py`)**: Wired `generate_omni_audio()` to live NanoGPT `POST /api/tts` (with `/api/v1/audio/speech` fallback), real magic-byte format detection (`.mp3`/`.wav`/`.ogg`/`.flac`/`.m4a`), valid model/voice mapping (`google/lyria-3.5`, `elevenlabs/eleven-v4` -> `Aria`, `elevenlabs/sound-effects/v3`, `Kokoro-82m` -> `af_bella`), async HTTP `202` `runId` support + `poll_nanogpt_audio_status()` (`GET /api/tts/status`), and honest upstream error propagation (keeping deterministic WAV fallback only when offline without a key).
- **Durable Streaming & Async Polling (`server.py`)**: Persisted completed audio into `.space/audio/` with real detected MIME/extension, returned durable `/api/space/file?raw=1...` `audio_raw_url` (served with HTTP `Range` `206 Partial Content`), omitted >2MB inline base64 payloads, and added `GET /api/nodes/audio/status` in both `BaseHTTPRequestHandler` and FastAPI.
- **Playable Audio Cards + Local Audio Upload (`node_studio_ui.py`)**: Expanded audio cards to `320x256px` and `.ns-audio-player` to `42px`, preferred streaming `/api/space/file?raw=1...` URLs with `preload="metadata"` and dynamic `.MP3`/`.WAV`/`.OGG` download buttons, added live 3.5s `pollAudioJobForNode()` + reload auto-resume, fixed canvas `mousedown` so `<audio>`/`<video>`/`<model-viewer>` controls never rebuild or drag mid-click, and added `audio/*` support to `#nsFileInput`, attach, and drag-and-drop onto the canvas.

---

## Entry #4 — 2026-11-20 (Live Production QA · Smooth Scroll Zoom Damping)

### User Experience Notes (Verbatim)
- `"can we fix the scroll zoom thing its like way too sensitive"`

### Root Cause
- All three `wheel` handlers (`#nsDotCanvas`, `.ns-splat-canvas`, `#nsSplatModalCanvas`) ignored `ev.deltaY` magnitude and applied a fixed `1.08x`/`0.92x` (or `1.1x`/`0.9x`) multiplier per wheel event, causing MacBook trackpads (60–120 tiny pixel events/sec) to explode zoom by `~500–700%` on a gentle scroll.
- `zoomBy` rounded to `toFixed(2)` and zoomed around `(0, 0)` rather than the cursor position, and scrolling inside overflowing Text cards / popovers zoomed the canvas instead of scrolling the element.

### Fixes Shipped
- Added `_wheelZoomFactor(ev, baseScale, pinchScale)` using `deltaMode` normalization, `[-80, 80]` per-event clamping, and smooth exponential damping (`0.0012` scroll / `0.004` trackpad pinch) across `#nsDotCanvas` and both 3D Splat viewports.
- Upgraded `zoomBy(factor, clientX, clientY)` to keep 4-decimal precision (`[0.15, 3.0]`) and anchor zoom cleanly around the mouse cursor.
- Preserved native vertical scrolling inside overflowing Text cards / popovers / menus and converted two-finger horizontal trackpad swipes into smooth horizontal panning instead of accidental zoom jitter.

---

## Entry #5 — 2026-11-20 (Live Production QA · Smart Generating Placement, Dynamic Auto-Layout & Real Text LLM Execution)

### User Experience Notes (Verbatim)
- `"we have an auto layout bug where the generating node just shows up anywhere, and we need to put that in a more appropriate placement."`
- `"Also, I would like the text prompts in Node Studio to actually run on something, and then we need the output based on the input. That's generally what it should be doing."`

### Root Causes Found
1. **Hardcoded random node placement + fixed-height Auto-Layout**:
   - `generate()` placed new/generating nodes at hardcoded `x: 420 + (nodeSeq % 3) * 40, y: 120 + (parentIds.length ? 280 : 0)`, and `buildOmniNodeFromParsed()` placed Audio/3D/Atlas nodes at `x: 240 + ..., y: 110 + ...` — completely ignoring parent positions, existing sibling cards, and viewport pan/zoom.
   - `autoLayout()` used a fixed `310px` vertical step, causing taller cards (`326px` 3D Mesh, `348–368px` Atlas Splat) to overlap the row underneath.
2. **Default Text model rejected on NanoGPT + silent local echo fallback**:
   - `MODEL_SPECS["gemini-3.1-pro"]["nanogptModel"]` in `node_studio_engine.py` was `"gemini-3.1-pro"` instead of NanoGPT's live catalog slug `"google/gemini-3.1-pro-preview"`, causing every default Text prompt on Railway production to fail with HTTP 400 (`Model gemini-3.1-pro is not supported on /v1/chat/completions.`).
   - On any API error, `generate()`'s `catch` block silently set `content = { text: prompt + " (staged locally)" }`, echoing the user's own prompt back instead of running a real LLM or showing an error.

### Fixes Shipped
- **Real Text LLM Execution Grounded in Inputs (`node_studio_engine.py`)**: Mapped `gemini-3.1-pro` to NanoGPT's live `"google/gemini-3.1-pro-preview"` with automatic fallback (`TEE/deepseek-v4.1-flash` / `gemini-2.5-pro`), added a system grounding prompt when input nodes are selected, passed HTTPS image URLs plus non-image/non-text parent node metadata (Audio/Video/3D/Splat) as input context, and extracted `content` / list parts / `reasoning_content` cleanly.
- **Honest Error Reporting (`node_studio_ui.py`)**: Replaced silent `"(staged locally)"` echoing on server errors with a visible `✕ ERROR` badge and `.ns-omni-error-box` inside Text cards, and enabled scrolling/selection inside `.ns-msg-body`.
- **Smart Collision-Free Placement & Dynamic Auto-Layout (`node_studio_ui.py`)**: Added `_computeSmartNodePosition`, `_findNonOverlappingSlot`, and `_ensureNodeVisible` so generating spinners reserve their full final footprint directly beneath selected parent(s) (or centered in the visible viewport / neatly beside root nodes), expand smoothly in place with zero jumping or sibling overlap, and gently pan into view. Upgraded `autoLayout()` with longest-path layering, parent-barycenter ordering, and dynamic per-row heights (`maxRowH + 64`).

---

## Entry #6 — 2026-11-20 (Live Production QA · Resizable Text Notes + Nano Banana Image Collections & Lightbox)

### User Experience Notes (Verbatim)
- `"We need a way to resize notes so we can view the content, specifically the text notes."`
- `"we need a way for nano banana to generate a collection of images and we need the ui to handle showing a collection of images with a lightbox to view them"`

### Shipped Enhancements
1. **Resizable Nodes + 1-Click Expand for Text Notes (`node_studio_ui.py`)**:
   - Added a tactile bottom-right corner drag-to-resize handle (`.ns-resize-handle`) to every non-generating canvas card with zoom-aware 60fps resizing (`220–1100px` × `140–1000px`), live edge updates, and `.nodes.json` persistence.
   - Added a 1-click **`⤢ Expand` / `↙ Compact`** button in Text note headers (and double-click on any resize grip) that automatically sizes the note to fit long LLM outputs cleanly with scrollable, selectable `.ns-msg-body` prose.
2. **Nano Banana Multi-Image Collections (`node_studio_engine.py`, `node_studio_ui.py`)**:
   - Added a `COUNT` selector (`1x`, `2x`, `3x`, `4x`) beside `ASPECT`/`RES` in the Prompt Island (visible in Image mode) and updated the Generate button label dynamically (`Generate 4 Images →`).
   - Upgraded `_generate_with_nanogpt`, `_generate_with_gemini`, and `_generate_offline_synthetic` to request `n=count` and automatically top up remaining frames in parallel (`ThreadPoolExecutor`) when an upstream Nano Banana endpoint caps single calls to 1 image — returning `content.images[]`, `collectionCount`, and `type: "COLLECTION"`.
   - Built a 2×2 bento contact-sheet Collection card (`.ns-collection-card` / `.ns-collection-grid`) with numbered tiles, **`⤢ Lightbox`**, **`Split Nodes`** (expands all collection frames into individual connected canvas nodes), and **`↓ All`**.
3. **Fullscreen Image Lightbox (`#nsImageLightboxModal`)**:
   - Accessible from any collection tile, any single image card (`⤢` button or double-click), Chat view, and Asset Library.
   - Includes `←`/`→` keyboard & button navigation, bottom filmstrip thumbnails, click-to-zoom `2×`, **`+ Use as Ref`** (attaches the exact chosen frame), **`↗ Pop Out Node`** (spawns that frame onto the canvas), **`↓ Download`**, and `Esc`/backdrop close.

---

## Entry #7 — 2026-11-20 (Zero-Reset Persistent Deploy Architecture)

### User Experience Notes (Verbatim)
- `"we need the ability to deploy without reseting everyones space files"`

### Root Causes Found
1. **Node Studio opened empty `user:default` instead of the user's real `.space` after refresh/deploy**: `_resolveSpaceTarget()` ignored `localStorage.getItem("tincan_peer_id")` when `window.currentSpaceOwner` was `""` during initial page boot (or on standalone `/nodes`), and `init()` only tried `/nodes/workspace.nodes.json` instead of the user's last active graph (e.g. `test.nodes.json`), making real persisted files on `/data/spaces/users/peer-jewkdo.space` look reset.
2. **Unsafe SQLite + S3 sync & missing graceful `SIGTERM` flush**: `SingleFileSpaceVFS` lacked WAL mode / `busy_timeout` / `sqlite3.backup()` online snapshots, fired unbounded overlapping raw-file S3 upload threads (risking torn uploads or OOM on 385 MB spaces), downloaded S3 restores non-atomically without integrity checks, and `server.py` had no `SIGTERM` handler to checkpoint WALs before container swap (plus `TinCanBlindRelay` used `:memory:`).
3. **No automatic S3 hydration or pre/post-deploy space audit**: `AgentSpaceManager` only read local disk at boot without hydrating missing spaces from S3, and there was no persistence audit or on-demand backup endpoint.

### Fixes Shipped
- **Atomic Integrity-Verified S3 Storage (`s3_storage.py`, `agent_space.py`)**: Enabled SQLite WAL + `busy_timeout=10000`, consistent `sqlite3.backup()` online snapshots for S3 uploads, debounced single-worker coalesced S3 sync, atomic `.tmp` + `PRAGMA quick_check` S3 downloads (never clobbering healthy local `/data` files), startup `hydrate_from_s3()`, `backup_all_spaces()`, `flush_all_spaces()`, and `get_persistence_status()`.
- **Graceful Deploy Shutdown & Persistence API (`server.py`)**: Added `SIGTERM`/`SIGINT`/`atexit` WAL checkpointing + dirty-space flush, persisted `TinCanBlindRelay` to `/data/tincan_relay.db`, and added `GET /api/spaces/persistence`, `POST /api/spaces/backup`, and `POST /api/spaces/hydrate`.
- **Identity & Last-Graph Auto-Restore (`node_studio_ui.py`, `mesh_os_ui.py`)**: Initialized `window.currentSpaceOwner` from `myPeerId`/`tincan_peer_id` immediately, updated `_resolveSpaceTarget()` to honor `tincan_peer_id`, remembered the active graph per `(scope, owner_id)`, and auto-restored the user's last graph (or newest saved graph in their `.space`) on reload/deploy.
- **Zero-Reset Deploy Wrapper (`scripts/safe_deploy.sh`)**: Audits space & VFS file counts before deploy, triggers consistent S3 backup, pushes & waits for Railway `SUCCESS`, and asserts zero spaces or files were lost post-deploy.

