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
