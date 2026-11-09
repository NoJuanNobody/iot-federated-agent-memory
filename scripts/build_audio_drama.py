#!/usr/bin/env python3
"""Synthesize a slow, atmospheric, multi-voice Kokoro-82M Audio Drama for
'STRING THEORY (THE TINCAN MESH PROTOCOL)' with distinct character voices,
natural dramatic pauses, subtle analog synth/CRT room tone, and exact per-panel
timings for FilmCraft timeline assembly.
"""
import json
import subprocess
from pathlib import Path
import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro

MODEL = Path("/Users/alejandrolondono/.local/share/say/models/kokoro-v1.0.onnx")
VOICES = Path("/Users/alejandrolondono/.local/share/say/models/voices-v1.0.bin")
OUT_DIR = Path("/Users/alejandrolondono/dev/iot-federated-agent-memory/docs/panels")
SR = 24000
FPS = 24

# Cast of voices (Kokoro-82M) with slow, deliberate audio-drama pacing
CAST = {
    "NARRATOR":  ("bm_george", "en-gb", 0.84),
    "ALEJANDRO": ("am_fenrir", "en-us", 0.86),
    "MAYA":      ("af_heart",  "en-us", 0.86),
    "SYSTEM":    ("bf_emma",   "en-gb", 0.85),
}

# Six dramatic scenes mapped 1-to-1 to the 6 Flux.2 storyboard panels
SCENES = [
    {
        "id": "panel_01_cyber_lab_crt",
        "lead_in_sec": 0.9,
        "lead_out_sec": 1.0,
        "lines": [
            ("NARRATOR", "String Theory... The TinCan Mesh Protocol.", 1.1),
            ("NARRATOR", "Boca Raton Cyber Lab. Midnight. Rain streaks the dark glass as three Amber Phosphor C R T monitors hum in the shadows.", 0.9),
            ("ALEJANDRO", "Let's see who is actually awake on the mesh.", 0.8),
            ("SYSTEM", "Peer secondary node: Online. OpenRouter federated pool: two hundred ninety dollars across four active labs.", 0.6),
        ],
    },
    {
        "id": "panel_02_kokoro_voice_alert",
        "lead_in_sec": 0.7,
        "lead_out_sec": 1.0,
        "lines": [
            ("NARRATOR", "Suddenly, a cyan acoustic waveform ripples across the studio speaker bar.", 0.85),
            ("MAYA", "Alejandro... Primary cloud ingress just went dark. Corporate S S O is locked out. Tell me the blind relay is still breathing.", 0.95),
            ("ALEJANDRO", "Zero accounts. Zero plaintext on the wire. Pin my key, Maya, and hop into the Comms Studio.", 0.7),
        ],
    },
    {
        "id": "panel_03_toronto_loft_tofu",
        "lead_in_sec": 0.8,
        "lead_out_sec": 1.0,
        "lines": [
            ("NARRATOR", "Toronto Loft. A winter grid brownout. By candlelight, Maya pins Alejandro's Ed25519 identity via Trust-On-First-Use.", 0.95),
            ("MAYA", "Identity pinned. Fingerprint verified. Opening sub-eighty-millisecond U D P screen tunnel... now.", 0.8),
        ],
    },
    {
        "id": "panel_04_webrtc_capsule_flight",
        "lead_in_sec": 0.7,
        "lead_out_sec": 1.0,
        "lines": [
            ("MAYA", "I'm inside your second monitor pop-out. Look at the BroadcastChannel string tether pulsing between our windows.", 0.85),
            ("ALEJANDRO", "Fire the zero-day patch through the Blind Relay. Only my local Curve25519 private key can unseal the envelope.", 0.85),
            ("SYSTEM", "Encrypted X25519 capsule delivered. Plus one hundred X P: Cipher Postmaster.", 0.7),
        ],
    },
    {
        "id": "panel_05_ai_brain_arena",
        "lead_in_sec": 0.7,
        "lead_out_sec": 1.0,
        "lines": [
            ("MAYA", "Before we deploy... which brain audits the assembly diff? Gemini Pro, or Claude Sonnet?", 0.85),
            ("ALEJANDRO", "Why guess? Let's run a live multiplayer Arena duel.", 0.85),
            ("NARRATOR", "Side by side, two neural streams race down the glass. Maya's remote cyan cursor glides across the screen to cast the deciding vote.", 0.8),
            ("SYSTEM", "Plus one hundred fifty X P: Synapse Arbiter.", 0.6),
        ],
    },
    {
        "id": "panel_06_tier_l5_messiah_gold",
        "lead_in_sec": 0.8,
        "lead_out_sec": 1.4,
        "lines": [
            ("SYSTEM", "Accessibility Gate Alert. Action number one from Maya: Execute production hotfix rollout. Awaiting Human-in-the-Loop approval.", 0.9),
            ("ALEJANDRO", "Inbound action verified. Triggering number one... now.", 0.95),
            ("NARRATOR", "The monitors erupt into Messiah Gold as the workstation ascends to Tier L 5: Autonomous Cognitive Mesh.", 0.95),
            ("MAYA", "Patched, verified... and zero keys exposed.", 1.0),
        ],
    },
]


def make_chime(kind: str, duration: float = 0.45) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration), endpoint=False, dtype=np.float32)
    env = np.exp(-t * 6.5) * np.minimum(t * 40.0, 1.0)
    if kind == "SYSTEM":
        sig = 0.08 * (np.sin(2 * np.pi * 528.0 * t) + 0.6 * np.sin(2 * np.pi * 792.0 * t)) * env
    elif kind == "MAYA_VO":
        sig = 0.09 * (np.sin(2 * np.pi * 440.0 * t) + 0.5 * np.sin(2 * np.pi * 660.0 * t)) * env
    elif kind == "GOLD":
        t = np.linspace(0, 1.2, int(SR * 1.2), endpoint=False, dtype=np.float32)
        env = np.exp(-t * 2.2) * np.minimum(t * 15.0, 1.0)
        sig = 0.10 * (
            np.sin(2 * np.pi * 261.63 * t)
            + 0.8 * np.sin(2 * np.pi * 329.63 * t)
            + 0.7 * np.sin(2 * np.pi * 392.00 * t)
            + 0.5 * np.sin(2 * np.pi * 523.25 * t)
        ) * env
    else:
        return np.zeros(0, dtype=np.float32)
    return sig.astype(np.float32)


def add_ambient_bed(mono: np.ndarray, scene_idx: int) -> np.ndarray:
    """Add a subtle warm cyberpunk CRT / analog pad bed underneath the audio drama."""
    n = len(mono)
    t = np.arange(n, dtype=np.float32) / SR
    base_freq = 55.0 if scene_idx < 5 else 65.41  # A1 dark drone -> C2 warm gold resolution
    fifth_freq = base_freq * 1.5
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.18 * t)
    bed = (
        0.018 * np.sin(2 * np.pi * base_freq * t)
        + 0.010 * np.sin(2 * np.pi * (base_freq * 2.0) * t) * lfo
        + 0.007 * np.sin(2 * np.pi * fifth_freq * t) * (1.0 - 0.4 * lfo)
    ).astype(np.float32)
    # Smooth fade-in and fade-out at scene boundaries
    fade_len = min(int(0.35 * SR), n // 4)
    if fade_len > 0:
        ramp = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        bed[:fade_len] *= ramp
        bed[-fade_len:] *= ramp[::-1]
    return np.clip(mono + bed, -0.98, 0.98)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.log_severity_level = 3
    session = ort.InferenceSession(str(MODEL), opts, providers=["CPUExecutionProvider"])
    kokoro = Kokoro.from_session(session, str(VOICES))

    manifest = []
    all_scene_audio = []
    cursor_frames = 0

    for idx, scene in enumerate(SCENES):
        sid = scene["id"]
        parts = [np.zeros(int(scene["lead_in_sec"] * SR), dtype=np.float32)]

        for line_i, (role, text, pause_sec) in enumerate(scene["lines"]):
            voice, lang, speed = CAST[role]
            if role == "SYSTEM":
                parts.append(make_chime("SYSTEM", 0.35))
                parts.append(np.zeros(int(0.15 * SR), dtype=np.float32))
            elif sid == "panel_02_kokoro_voice_alert" and role == "MAYA" and line_i == 1:
                parts.append(make_chime("MAYA_VO", 0.40))
                parts.append(np.zeros(int(0.20 * SR), dtype=np.float32))
            elif sid == "panel_06_tier_l5_messiah_gold" and role == "NARRATOR":
                parts.append(make_chime("GOLD", 0.9))

            samples, _ = kokoro.create(text, voice=voice, speed=speed, lang=lang)
            samples = samples.astype(np.float32)
            # Normalize peak gently per line for balanced broadcast drama dialogue
            peak = float(np.max(np.abs(samples))) if len(samples) else 1.0
            if peak > 0:
                target_peak = 0.78 if role == "SYSTEM" else 0.86
                samples = samples * (target_peak / peak)
            parts.append(samples)
            parts.append(np.zeros(int(pause_sec * SR), dtype=np.float32))

        parts.append(np.zeros(int(scene["lead_out_sec"] * SR), dtype=np.float32))
        raw_scene = np.concatenate(parts)

        # Quantize scene length to an exact integer number of 24fps frames so V1 clips have 0 flash gaps!
        raw_sec = len(raw_scene) / SR
        scene_frames = int(np.ceil(raw_sec * FPS))
        target_samples = int(round((scene_frames / FPS) * SR))
        if len(raw_scene) < target_samples:
            raw_scene = np.pad(raw_scene, (0, target_samples - len(raw_scene)))
        else:
            raw_scene = raw_scene[:target_samples]

        mixed_scene = add_ambient_bed(raw_scene, idx)
        scene_wav_24k = OUT_DIR / f"{sid}_drama_24k.wav"
        scene_wav_48k = OUT_DIR / f"{sid}_drama.wav"
        sf.write(str(scene_wav_24k), mixed_scene, SR)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(scene_wav_24k), "-ar", "48000", "-ac", "2", str(scene_wav_48k)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        scene_wav_24k.unlink(missing_ok=True)

        dur_sec = scene_frames / FPS
        ticks_per_frame = 254016000000 // FPS  # exact integer: 10,584,000,000 ticks/frame
        start_ticks = cursor_frames * ticks_per_frame
        dur_ticks = scene_frames * ticks_per_frame

        manifest.append(
            {
                "id": sid,
                "audio_path": str(scene_wav_48k),
                "start_frame": cursor_frames,
                "frames": scene_frames,
                "start_sec": round(cursor_frames / FPS, 3),
                "duration_sec": round(dur_sec, 3),
                "start_ticks": start_ticks,
                "duration_ticks": dur_ticks,
            }
        )
        print(
            f"[{idx+1}/6] {sid}: {dur_sec:.2f}s ({scene_frames} frames, start={cursor_frames/FPS:.2f}s)",
            flush=True,
        )
        cursor_frames += scene_frames
        all_scene_audio.append(mixed_scene)

    full_audio = np.concatenate(all_scene_audio)
    full_24k = OUT_DIR / "trailer_voiceover_24k.wav"
    full_48k = OUT_DIR / "trailer_voiceover.wav"
    sf.write(str(full_24k), full_audio, SR)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(full_24k), "-ar", "48000", "-ac", "2", str(full_48k)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    full_24k.unlink(missing_ok=True)

    manifest_path = OUT_DIR / "audio_drama_manifest.json"
    manifest_data = {
        "total_frames": cursor_frames,
        "total_seconds": round(cursor_frames / FPS, 3),
        "total_ticks": cursor_frames * (254016000000 // FPS),
        "master_audio": str(full_48k),
        "scenes": manifest,
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2))
    print(f"\nTOTAL AUDIO DRAMA DURATION: {manifest_data['total_seconds']}s ({cursor_frames} frames)")


if __name__ == "__main__":
    main()
