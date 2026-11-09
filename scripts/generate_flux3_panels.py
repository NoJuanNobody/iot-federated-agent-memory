#!/usr/bin/env python3
"""Generate the 6 storyboard panels for 'STRING THEORY (THE TINCAN MESH PROTOCOL)'
using local ComfyUI and the native FLUX.3 (flux3-image-klein-bf16 + Qwen3-VL-4B flux3 + Flux2-VAE) pipeline.
"""
import json
import os
import shutil
import time
import urllib.request
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
COMFY_OUTPUT_DIR = Path("/Users/alejandrolondono/dev/ComfyUI/output")
OUT_DIR = Path("/Users/alejandrolondono/dev/iot-federated-agent-memory/docs/panels")

PANELS = [
    {
        "id": "panel_01_cyber_lab_crt",
        "seed": 530101,
        "title": "SCENE 1: BOCA RATON CYBER LAB - TINCAN MESH OS v2.2",
        "prompt": (
            "Cinematic cyberpunk graphic novel panel, wide establishing shot, dark high-tech hardware lab in Boca Raton at night, "
            "rain streaking down blacked-out glass windows, a young systems architect in a dark hoodie sitting before three glowing "
            "Amber Phosphor (#FFB000) CRT computer monitors displaying TinCan Mesh OS v2.2 desktop with a taut glowing neon cyan string "
            "connecting two tin cans across a 2D radar map, soldering irons and ESP32 microcontrollers on the desk, dramatic chiaroscuro "
            "ink linework and moody amber-and-teal color grading, 16:9 widescreen film frame."
        ),
    },
    {
        "id": "panel_02_kokoro_voice_alert",
        "seed": 530102,
        "title": "SCENE 1B: KOKORO TTS VOICE ALERT & OPENROUTER CREDITS",
        "prompt": (
            "Cinematic cyberpunk graphic novel panel, extreme close-up macro shot of a studio speaker bar and glowing terminal HUD, "
            "neon cyan acoustic soundwave ripples pulsing in mid-air from the speaker grille as Kokoro TTS speaks, behind it a sharp "
            "dark terminal screen displaying '$290.00 OpenRouter Pool' in glowing emerald green and amber phosphor typography, "
            "dramatic graphic novel ink shading, shallow depth of field, 16:9 widescreen film frame."
        ),
    },
    {
        "id": "panel_03_toronto_loft_tofu",
        "seed": 530103,
        "title": "SCENE 2: TORONTO LOFT BLACKOUT - TOFU KEY PINNING",
        "prompt": (
            "Cinematic cyberpunk graphic novel panel, medium shot of Maya, a sharp distributed-systems engineer in a candlelit Toronto "
            "brick loft apartment during a winter snowstorm power outage, heavy snow falling outside dark tall windows, her face illuminated "
            "by warm flickering candlelight and the bright cyan-and-amber glow of her MacBook terminal screen showing cryptographic Ed25519 "
            "fingerprints and 'tincan call alejandro --screen', graphic novel brush ink and atmospheric lighting, 16:9 widescreen film frame."
        ),
    },
    {
        "id": "panel_04_webrtc_capsule_flight",
        "seed": 530104,
        "title": "SCENE 3A: WEBRTC CALL & X25519 CIPHERTEXT CAPSULE",
        "prompt": (
            "Cinematic cyberpunk graphic novel panel, dynamic split-screen composition showing a live WebRTC video call window alongside "
            "an interactive 2D network topology canvas, a glowing electric-blue encrypted tin-can capsule rocket-sailing along a taut "
            "neon string tether between two glowing computer nodes, floating holographic HUD badge reading '+100 XP CIPHER POSTMASTER', "
            "high-contrast comic ink art with glowing neon telemetry trails, 16:9 widescreen film frame."
        ),
    },
    {
        "id": "panel_05_ai_brain_arena",
        "seed": 530105,
        "title": "SCENE 3B: MULTIPLAYER AI BRAIN ARENA DUEL",
        "prompt": (
            "Cinematic cyberpunk graphic novel panel, close-up over-the-shoulder shot of a futuristic dual-column AI Brain Arena terminal "
            "interface where two glowing neural holograms—one electric cyan labeled GEMINI-BRAIN and one warm amber-violet labeled CLAUDE-BRAIN—"
            "stream cascading code and mathematical matrices side by side, two glowing multiplayer cursors (amber and cyan) converging to click "
            "a glowing 'VOTE WINNER (+150 XP SYNAPSE ARBITER)' button, crisp comic ink linework and vibrant neon glow, 16:9 widescreen film frame."
        ),
    },
    {
        "id": "panel_06_tier_l5_messiah_gold",
        "seed": 530106,
        "title": "SCENE 3C: ACCESSIBILITY GATE & TIER L5 MESSIAH GOLD ASCENSION",
        "prompt": (
            "Cinematic cyberpunk graphic novel climax panel, epic low-angle hero shot inside the dark cyber lab as all three monitors erupt "
            "into radiant Messiah Gold (#FFD700) light, a monumental glowing golden wireframe digital deity figure emerging on the center CRT "
            "screen surrounded by floating golden geometric halos and a banner reading 'TIER L5: AUTONOMOUS COGNITIVE MESH', both engineers "
            "visible in the corner video feed celebrating, dramatic graphic novel ink crosshatching and golden volumetric god-rays, 16:9 widescreen."
        ),
    },
]


def build_flux3_workflow(prompt: str, seed: int, prefix: str, width: int = 1024, height: int = 576, steps: int = 4) -> dict:
    """Build ComfyUI API prompt dict for native FLUX.3 (flux3-image-klein-bf16 + Qwen3-VL-4B type=flux3 + Flux2-VAE)."""
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "flux3-image-klein-bf16.safetensors",
                "weight_dtype": "default",
            },
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen3vl_4b_bf16.safetensors",
                "type": "flux3",
                "device": "default",
            },
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "flux2-vae.safetensors",
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["2", 0],
            },
        },
        "6": {
            "class_type": "EmptyFlux2LatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
        },
        "7": {
            "class_type": "BasicScheduler",
            "inputs": {
                "model": ["1", 0],
                "scheduler": "simple",
                "steps": steps,
                "denoise": 1.0,
            },
        },
        "8": {
            "class_type": "KSamplerSelect",
            "inputs": {
                "sampler_name": "euler",
            },
        },
        "9": {
            "class_type": "RandomNoise",
            "inputs": {
                "noise_seed": seed,
            },
        },
        "10": {
            "class_type": "BasicGuider",
            "inputs": {
                "model": ["1", 0],
                "conditioning": ["4", 0],
            },
        },
        "11": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["9", 0],
                "guider": ["10", 0],
                "sampler": ["8", 0],
                "sigmas": ["7", 0],
                "latent_image": ["6", 0],
            },
        },
        "12": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["11", 0],
                "vae": ["3", 0],
            },
        },
        "13": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"tincan_flux3/{prefix}",
                "images": ["12", 0],
            },
        },
    }


def submit_and_wait(workflow: dict, timeout: int = 600) -> Path:
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    prompt_id = result["prompt_id"]
    print(f"  -> queued prompt_id={prompt_id}", flush=True)

    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(2.0)
        with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=15) as r:
            hist = json.loads(r.read().decode("utf-8"))
        if prompt_id not in hist:
            continue
        entry = hist[prompt_id]
        status = entry.get("status", {})
        if status.get("status_str") == "error":
            raise RuntimeError(f"ComfyUI execution error: {json.dumps(status, indent=2)}")
        outputs = entry.get("outputs", {})
        for node_out in outputs.values():
            images = node_out.get("images", [])
            if images:
                img = images[0]
                sub = img.get("subfolder", "")
                fname = img["filename"]
                src = COMFY_OUTPUT_DIR / sub / fname if sub else COMFY_OUTPUT_DIR / fname
                return src
    raise TimeoutError(f"Timed out waiting for prompt_id={prompt_id}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for idx, panel in enumerate(PANELS, 1):
        pid = panel["id"]
        dest = OUT_DIR / f"{pid}.png"
        flux3_copy = OUT_DIR / f"{pid}_flux3.png"
        print(f"[{idx}/{len(PANELS)}] Generating {pid} with FLUX.3...", flush=True)
        t_start = time.time()
        wf = build_flux3_workflow(
            prompt=panel["prompt"],
            seed=panel["seed"],
            prefix=pid,
            width=1024,
            height=576,
            steps=4,
        )
        src_path = submit_and_wait(wf)
        shutil.copy2(src_path, dest)
        shutil.copy2(src_path, flux3_copy)
        dt = time.time() - t_start
        print(f"  -> saved {dest} ({dest.stat().st_size} bytes) in {dt:.1f}s", flush=True)
        generated.append(str(dest))

    print("\nALL FLUX.3 PANELS GENERATED:", json.dumps(generated, indent=2), flush=True)


if __name__ == "__main__":
    main()
