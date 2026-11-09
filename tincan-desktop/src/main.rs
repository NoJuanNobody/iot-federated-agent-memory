use std::process::Command;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use eframe::egui::{self, Color32, FontFamily, FontId, Pos2, Rect, RichText, Sense, Stroke, Vec2};
use serde::{Deserialize, Serialize};

const LOGO_HEX: &str = include_str!("../assets/ai_messiah_logo.hex");
const RELAY_URL: &str = "https://iot-federated-agent-memory-production.up.railway.app";
const CLI_PATH: &str = "/Users/alejandrolondono/dev/iot-federated-agent-memory/tincan_cli.py";

#[derive(Clone, Copy, PartialEq, Eq)]
enum GlowKind {
    None,
    Halo,
    Eye,
    Brain,
}

struct LogoAsset {
    width: usize,
    height: usize,
    pixels: Vec<[u8; 3]>,
    glow: Vec<GlowKind>,
    phase: Vec<f32>,
}

impl LogoAsset {
    fn load_resampled(target_w: usize, target_h: usize) -> Self {
        let mut lines = LOGO_HEX.lines();
        let header = lines.next().unwrap_or("110 119");
        let mut parts = header.split_whitespace();
        let src_w: usize = parts.next().and_then(|s| s.parse().ok()).unwrap_or(110);
        let src_h: usize = parts.next().and_then(|s| s.parse().ok()).unwrap_or(119);

        let mut src_pixels = Vec::with_capacity(src_w * src_h);
        for _ in 0..src_h {
            if let Some(line) = lines.next() {
                let bytes = line.trim().as_bytes();
                for x in 0..src_w {
                    let idx = x * 6;
                    if idx + 6 <= bytes.len() {
                        let r = u8::from_str_radix(&line[idx..idx + 2], 16).unwrap_or(14);
                        let g = u8::from_str_radix(&line[idx + 2..idx + 4], 16).unwrap_or(6);
                        let b = u8::from_str_radix(&line[idx + 4..idx + 6], 16).unwrap_or(24);
                        src_pixels.push([r, g, b]);
                    } else {
                        src_pixels.push([14, 6, 24]);
                    }
                }
            }
        }

        let tw = target_w.max(1);
        let th = target_h.max(2);
        let mut pixels = Vec::with_capacity(tw * th);
        for ty in 0..th {
            let y0 = ty * src_h / th;
            let y1 = (((ty + 1) * src_h + th - 1) / th).max(y0 + 1).min(src_h);
            for tx in 0..tw {
                let x0 = tx * src_w / tw;
                let x1 = (((tx + 1) * src_w + tw - 1) / tw).max(x0 + 1).min(src_w);
                let (mut r, mut g, mut b, mut n) = (0u32, 0u32, 0u32, 0u32);
                for yy in y0..y1 {
                    for xx in x0..x1 {
                        let p = src_pixels[yy * src_w + xx];
                        r += u32::from(p[0]);
                        g += u32::from(p[1]);
                        b += u32::from(p[2]);
                        n += 1;
                    }
                }
                let n = n.max(1);
                pixels.push([(r / n) as u8, (g / n) as u8, (b / n) as u8]);
            }
        }

        let cx = tw as f32 * 0.5;
        let cy = th as f32 * 0.54;
        let rx = tw as f32 * 0.35;
        let ry = th as f32 * 0.38;
        let bx = tw as f32 * 0.5;
        let by = th as f32 * 0.25;

        let mut glow = Vec::with_capacity(tw * th);
        let mut phase = Vec::with_capacity(tw * th);

        for y in 0..th {
            for x in 0..tw {
                let [r, g, b] = pixels[y * tw + x];
                let dx = (x as f32 - cx) / rx;
                let dy = (y as f32 - cy) / ry;
                let inside_head = dx * dx + dy * dy < 1.0;

                let kind = if g > 140 && g > r.saturating_add(40) && g > b.saturating_add(30) {
                    GlowKind::Eye
                } else if r > 200 && g > 170 && b < 110 && !inside_head {
                    GlowKind::Halo
                } else if inside_head && (y as f32) < (th as f32 * 0.40) && r > 110 && g > 80 && b < 90 && r >= g {
                    GlowKind::Brain
                } else {
                    GlowKind::None
                };
                glow.push(kind);
                let px = (x as f32 - bx) / (tw as f32);
                let py = (y as f32 - by) / (th as f32);
                phase.push((px * px + py * py).sqrt());
            }
        }

        Self { width: tw, height: th, pixels, glow, phase }
    }

    fn color_at(&self, x: usize, y: usize, t: f32) -> Color32 {
        let idx = y * self.width + x;
        let [r, g, b] = self.pixels[idx];
        let f = match self.glow[idx] {
            GlowKind::None => 1.0,
            GlowKind::Eye => 1.0 + 0.32 * (t * 3.4).sin(),
            GlowKind::Halo => 1.0 + 0.24 * (t * 3.0 - self.phase[idx] * 18.0).sin(),
            GlowKind::Brain => {
                let s = (t * 5.0 - self.phase[idx] * 40.0).sin().max(0.0);
                1.0 + 0.48 * s.powi(6)
            }
        };
        Color32::from_rgb(
            ((r as f32 * f).min(255.0)) as u8,
            ((g as f32 * f).min(255.0)) as u8,
            ((b as f32 * f).min(255.0)) as u8,
        )
    }
}

struct RainDrop {
    col: usize,
    y: f32,
    speed: f32,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ContactItem {
    pub alias: String,
    pub address: String,
    #[serde(default)]
    pub public_key: String,
    #[serde(default)]
    pub pinned_at: f64,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct IdentityInfo {
    pub alias: String,
    pub address: String,
    pub public_key: String,
    pub public_key_b32: String,
    pub relay_url: String,
    pub contacts_count: usize,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ActionItem {
    pub id: String,
    pub seq: u64,
    pub sender: String,
    pub sender_alias: String,
    pub command: String,
    pub queued_at: f64,
    pub status: String,
    #[serde(default)]
    pub result: Option<String>,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ChatMessage {
    pub seq: u64,
    pub sender: String,
    pub sender_alias: Option<String>,
    pub message: String,
    #[serde(default)]
    pub verified: bool,
    #[serde(default)]
    pub speak: bool,
    #[serde(default)]
    pub timestamp: f64,
    #[serde(default)]
    pub is_outgoing: bool,
}

#[derive(Clone, Debug, Default)]
pub struct RelaySnapshot {
    pub online: bool,
    pub peers_count: usize,
    pub providers_count: usize,
    pub readiness_tier: String,
    pub composite_score: f32,
    pub peers: Vec<(String, String, String)>,
    pub providers: Vec<(String, f32)>,
    pub openrouter_balance: f64,
}

const TINCAN_COMMANDS: &[(&str, &str)] = &[
    ("whoami", "Display current local identity and TinCan address"),
    ("send", "Send sealed message to a recipient address or contact alias"),
    ("read", "Fetch and decrypt inbox messages"),
    ("say", "Speak text aloud via Kokoro TTS and optionally send spoken message to a peer"),
    ("call", "Launch live WebRTC Video, Voice & Screenshare call room"),
    ("video", "Launch live WebRTC Video, Voice & Screenshare call room"),
    ("contacts", "List pinned contacts"),
    ("add-contact", "Pin a contact's public key (TOFU)"),
    ("mcp", "Start MCP server over stdio"),
    ("start", "Launch the full terminal screensaver and live mesh dashboard"),
    ("screensaver", "Alias for 'start'"),
    ("chat", "Start interactive agentic chat REPL with the live OpenRouter models"),
    ("ask", "Single-shot query to the TinCan Agent"),
    ("actions", "List and review incoming actions queued for approval (Accessibility Gate)"),
    ("trigger", "Approve and trigger an incoming queued action (e.g. 'tincan trigger 1')"),
    ("dismiss", "Dismiss a queued action without executing"),
    ("serve", "Run local standalone TinCan Blind Relay"),
    ("playlist", "Manage the Relay Video Channel & Collection Playlist"),
    ("status", "Check if a peer is online / on their computer and inspect read receipts"),
    ("ping", "Check if a peer is online / on their computer and inspect read receipts"),
    ("credits", "Display live OpenRouter account credits, spend, and per-model cost rates"),
    ("cost", "Display live OpenRouter account credits, spend, and per-model cost rates"),
    ("upgrade", "Upgrade TinCan CLI and mesh bundles to the latest production release"),
];

fn refresh_mesh_data(
    relay_state: &Arc<Mutex<RelaySnapshot>>,
    identity_state: &Arc<Mutex<Option<IdentityInfo>>>,
    contacts_state: &Arc<Mutex<Vec<ContactItem>>>,
    actions_state: &Arc<Mutex<Vec<ActionItem>>>,
    chat_state: &Arc<Mutex<Vec<ChatMessage>>>,
) {
    // 1. Fetch Relay /api/status
    if let Ok(output) = Command::new("curl")
        .args(["-s", "--max-time", "5", &format!("{RELAY_URL}/api/status")])
        .output()
    {
        if output.status.success() {
            if let Ok(val) = serde_json::from_slice::<serde_json::Value>(&output.stdout) {
                if let Ok(mut snap) = relay_state.lock() {
                    snap.online = true;
                    if let Some(tier) = val.get("readiness_tier").and_then(|v| v.as_str()) {
                        snap.readiness_tier = tier.to_string();
                    }
                    if let Some(score) = val.get("composite_score").and_then(|v| v.as_f64()) {
                        snap.composite_score = score as f32;
                    }
                    let mut real_peers = Vec::new();
                    if let Some(arr) = val.get("active_webrtc_streams").and_then(|v| v.as_array()) {
                        for item in arr {
                            let name = item.get("display_name").and_then(|v| v.as_str()).unwrap_or("Peer").to_string();
                            let pid = item.get("peer_id").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            let ip = item.get("udp_address").and_then(|v| v.as_str()).unwrap_or("0.0.0.0");
                            let port = item.get("udp_port").and_then(|v| v.as_u64()).unwrap_or(0);
                            let room = item.get("room").and_then(|v| v.as_str()).unwrap_or("main");
                            let ep = format!("{ip}:{port} (room: {room})");
                            real_peers.push((name, pid, ep));
                        }
                    }
                    snap.peers_count = real_peers.len();
                    snap.peers = real_peers;

                    let mut real_providers = Vec::new();
                    if let Some(obj) = val.get("ai_providers").and_then(|v| v.as_object()) {
                        for (k, v) in obj {
                            let score = v.as_f64().unwrap_or(0.0) as f32;
                            real_providers.push((k.clone(), score));
                        }
                    }
                    snap.providers_count = real_providers.len();
                    snap.providers = real_providers;
                }
            }
        }
    }

    // 2. Fetch Identity (whoami --json)
    if let Ok(output) = Command::new("python3").args([CLI_PATH, "whoami", "--json"]).output() {
        if output.status.success() {
            if let Ok(id_info) = serde_json::from_slice::<IdentityInfo>(&output.stdout) {
                if let Ok(mut id_lock) = identity_state.lock() {
                    *id_lock = Some(id_info);
                }
            }
        }
    }

    // 3. Fetch Contacts (contacts --json)
    if let Ok(output) = Command::new("python3").args([CLI_PATH, "contacts", "--json"]).output() {
        if output.status.success() {
            if let Ok(real_contacts) = serde_json::from_slice::<Vec<ContactItem>>(&output.stdout) {
                if let Ok(mut c_lock) = contacts_state.lock() {
                    *c_lock = real_contacts;
                }
            }
        }
    }

    // 4. Fetch Pending Actions (actions --json)
    if let Ok(output) = Command::new("python3").args([CLI_PATH, "actions", "--json"]).output() {
        if output.status.success() {
            if let Ok(real_actions) = serde_json::from_slice::<Vec<ActionItem>>(&output.stdout) {
                if let Ok(mut a_lock) = actions_state.lock() {
                    *a_lock = real_actions;
                }
            }
        }
    }

    // 5. Fetch Decrypted Inbox (read --no-speak --json)
    if let Ok(output) = Command::new("python3").args([CLI_PATH, "read", "--no-speak", "--json"]).output() {
        if output.status.success() {
            if let Ok(inbox_msgs) = serde_json::from_slice::<Vec<ChatMessage>>(&output.stdout) {
                if let Ok(mut chat_lock) = chat_state.lock() {
                    for m in inbox_msgs {
                        if !chat_lock.iter().any(|c| c.seq == m.seq && c.sender == m.sender) {
                            chat_lock.push(m);
                        }
                    }
                }
            }
        }
    }

    // 6. Fetch OpenRouter credits balance
    if let Ok(output) = Command::new("python3").args([CLI_PATH, "credits", "--json"]).output() {
        if output.status.success() {
            if let Ok(val) = serde_json::from_slice::<serde_json::Value>(&output.stdout) {
                if let Some(bal) = val.get("openrouter").and_then(|v| v.get("account_remaining_balance_usd")).and_then(|v| v.as_f64()) {
                    if let Ok(mut snap) = relay_state.lock() {
                        snap.openrouter_balance = bal;
                    }
                }
            }
        }
    }
}

struct AiMessiahTerminalApp {
    start_instant: Instant,
    logo: LogoAsset,
    rain: Vec<RainDrop>,
    last_rain_tick: f32,
    show_dashboard: bool,
    tincan_gui_mode: bool,
    active_tab: usize,
    selected_contact: String,
    new_contact_alias: String,
    new_contact_addr: String,
    compose_msg: String,
    speak_tts: bool,
    agent_prompt: String,
    selected_model: String,
    is_querying_agent: Arc<Mutex<bool>>,
    webrtc_room: String,
    webrtc_open_browser: bool,
    relay_state: Arc<Mutex<RelaySnapshot>>,
    identity_state: Arc<Mutex<Option<IdentityInfo>>>,
    contacts_state: Arc<Mutex<Vec<ContactItem>>>,
    actions_state: Arc<Mutex<Vec<ActionItem>>>,
    chat_state: Arc<Mutex<Vec<ChatMessage>>>,
    agy_input: String,
    agy_extra_logs: Vec<String>,
    tincan_input: String,
    tincan_output_log: Arc<Mutex<Vec<String>>>,
    git_recent_commits: Vec<(String, String)>,
    git_current_branch: String,
}

impl AiMessiahTerminalApp {
    fn new() -> Self {
        let logo = LogoAsset::load_resampled(38, 42);
        let mut rain = Vec::new();
        for c in 0..68 {
            if c % 2 == 0 || c % 5 == 0 {
                let phase = ((c * 37) % 28) as f32 - 14.0;
                let speed = 6.5 + ((c * 13) % 9) as f32 * 1.1;
                rain.push(RainDrop { col: c, y: phase, speed });
            }
        }

        let relay_state = Arc::new(Mutex::new(RelaySnapshot::default()));
        let identity_state = Arc::new(Mutex::new(None));
        let contacts_state = Arc::new(Mutex::new(Vec::new()));
        let actions_state = Arc::new(Mutex::new(Vec::new()));
        let chat_state = Arc::new(Mutex::new(Vec::new()));
        let tincan_output_log = Arc::new(Mutex::new(Vec::new()));
        let is_querying_agent = Arc::new(Mutex::new(false));

        // Read real git metadata from repository
        let git_current_branch = Command::new("git")
            .args(["-C", "/Users/alejandrolondono/dev/iot-federated-agent-memory", "branch", "--show-current"])
            .output()
            .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
            .unwrap_or_else(|_| "main".to_string());

        let git_recent_commits = Command::new("git")
            .args(["-C", "/Users/alejandrolondono/dev/iot-federated-agent-memory", "log", "-n", "8", "--pretty=format:%h %s"])
            .output()
            .map(|o| {
                String::from_utf8_lossy(&o.stdout)
                    .lines()
                    .filter_map(|l| {
                        let mut parts = l.splitn(2, ' ');
                        let hash = parts.next()?.to_string();
                        let msg = parts.next()?.to_string();
                        Some((hash, msg))
                    })
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();

        // Background worker: initial sync and recurring 5-second polling loop
        let r_clone = Arc::clone(&relay_state);
        let i_clone = Arc::clone(&identity_state);
        let c_clone = Arc::clone(&contacts_state);
        let a_clone = Arc::clone(&actions_state);
        let ch_clone = Arc::clone(&chat_state);

        std::thread::spawn(move || {
            loop {
                refresh_mesh_data(&r_clone, &i_clone, &c_clone, &a_clone, &ch_clone);
                std::thread::sleep(Duration::from_secs(5));
            }
        });

        Self {
            start_instant: Instant::now(),
            logo,
            rain,
            last_rain_tick: 0.0,
            show_dashboard: false,
            tincan_gui_mode: true,
            active_tab: 0,
            selected_contact: "harper".to_string(),
            new_contact_alias: String::new(),
            new_contact_addr: String::new(),
            compose_msg: String::new(),
            speak_tts: true,
            agent_prompt: String::new(),
            selected_model: "gemini-brain".to_string(),
            is_querying_agent,
            webrtc_room: "main".to_string(),
            webrtc_open_browser: true,
            relay_state,
            identity_state,
            contacts_state,
            actions_state,
            chat_state,
            agy_input: String::new(),
            agy_extra_logs: Vec::new(),
            tincan_input: String::new(),
            tincan_output_log,
            git_recent_commits,
            git_current_branch,
        }
    }

    fn run_tincan_subcommand(&self, subcmd: &str) {
        let trimmed = subcmd.trim().to_string();
        if trimmed.is_empty() {
            return;
        }
        let log_clone = Arc::clone(&self.tincan_output_log);
        let relay_state = Arc::clone(&self.relay_state);
        let identity_state = Arc::clone(&self.identity_state);
        let contacts_state = Arc::clone(&self.contacts_state);
        let actions_state = Arc::clone(&self.actions_state);
        let chat_state = Arc::clone(&self.chat_state);

        std::thread::spawn(move || {
            let args: Vec<&str> = trimmed.split_whitespace().collect();
            let output = Command::new("python3")
                .arg(CLI_PATH)
                .args(&args)
                .output();
            match output {
                Ok(out) => {
                    let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
                    let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
                    let combined = if !stdout.is_empty() {
                        stdout
                    } else if !stderr.is_empty() {
                        stderr
                    } else {
                        format!("Completed `tincan {trimmed}` (exit 0)")
                    };
                    if let Ok(mut log) = log_clone.lock() {
                        log.push(format!("$ tincan {trimmed}\n{combined}"));
                    }
                }
                Err(e) => {
                    if let Ok(mut log) = log_clone.lock() {
                        log.push(format!("$ tincan {trimmed}\nError: {e}"));
                    }
                }
            }
            refresh_mesh_data(&relay_state, &identity_state, &contacts_state, &actions_state, &chat_state);
        });
    }

    fn send_sealed_message(&self, recipient: &str, message: &str, speak: bool) {
        let recipient_str = recipient.to_string();
        let message_str = message.to_string();
        let chat_clone = Arc::clone(&self.chat_state);
        let log_clone = Arc::clone(&self.tincan_output_log);
        let relay_state = Arc::clone(&self.relay_state);
        let identity_state = Arc::clone(&self.identity_state);
        let contacts_state = Arc::clone(&self.contacts_state);
        let actions_state = Arc::clone(&self.actions_state);

        std::thread::spawn(move || {
            let mut cmd = Command::new("python3");
            cmd.arg(CLI_PATH)
                .arg("send")
                .arg(&recipient_str)
                .arg(&message_str)
                .arg("--json");
            if speak {
                cmd.arg("--speak");
            }
            if let Ok(output) = cmd.output() {
                if output.status.success() {
                    let seq_num = if let Ok(val) = serde_json::from_slice::<serde_json::Value>(&output.stdout) {
                        val.get("seq").and_then(|v| v.as_u64()).unwrap_or(0)
                    } else {
                        0
                    };
                    if let Ok(mut chat) = chat_clone.lock() {
                        chat.push(ChatMessage {
                            seq: seq_num,
                            sender: "you".to_string(),
                            sender_alias: Some(format!("you → {}", recipient_str)),
                            message: message_str.clone(),
                            verified: true,
                            speak,
                            timestamp: 0.0,
                            is_outgoing: true,
                        });
                    }
                    if let Ok(mut log) = log_clone.lock() {
                        log.push(format!("$ tincan send {} {:?}\n[OK] Sealed envelope seq {} dispatched to relay.", recipient_str, message_str, seq_num));
                    }
                } else {
                    let err = String::from_utf8_lossy(&output.stderr);
                    if let Ok(mut log) = log_clone.lock() {
                        log.push(format!("$ tincan send {} {:?}\nError: {}", recipient_str, message_str, err));
                    }
                }
            }
            refresh_mesh_data(&relay_state, &identity_state, &contacts_state, &actions_state, &chat_clone);
        });
    }

    fn ask_agent_query(&self, prompt: &str) {
        let prompt_str = prompt.to_string();
        let model = self.selected_model.clone();
        let is_querying = Arc::clone(&self.is_querying_agent);
        let log_clone = Arc::clone(&self.tincan_output_log);

        if let Ok(mut q) = is_querying.lock() {
            *q = true;
        }

        std::thread::spawn(move || {
            let output = Command::new("python3")
                .args([CLI_PATH, "ask", &prompt_str, "--model", &model])
                .output();

            if let Ok(mut q) = is_querying.lock() {
                *q = false;
            }

            match output {
                Ok(out) => {
                    let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
                    let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
                    let reply = if !stdout.is_empty() { stdout } else { stderr };
                    if let Ok(mut log) = log_clone.lock() {
                        log.push(format!("$ tincan ask {:?} --model {}\n[TinCan Agent · {}]\n{}", prompt_str, model, model, reply));
                    }
                }
                Err(e) => {
                    if let Ok(mut log) = log_clone.lock() {
                        log.push(format!("$ tincan ask {:?}\nError: {}", prompt_str, e));
                    }
                }
            }
        });
    }

    fn draw_title_bar(&self, ui: &mut egui::Ui) {
        egui::Frame::new()
            .fill(Color32::from_rgb(42, 45, 50))
            .inner_margin(egui::Margin::symmetric(12, 7))
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    let (rect, _) = ui.allocate_exact_size(Vec2::new(56.0, 14.0), Sense::hover());
                    let painter = ui.painter();
                    let cy = rect.center().y;
                    painter.circle_filled(Pos2::new(rect.left() + 6.0, cy), 6.0, Color32::from_rgb(255, 95, 86));
                    painter.circle_filled(Pos2::new(rect.left() + 26.0, cy), 6.0, Color32::from_rgb(255, 189, 46));
                    painter.circle_filled(Pos2::new(rect.left() + 46.0, cy), 6.0, Color32::from_rgb(39, 201, 63));

                    ui.add_space(8.0);
                    ui.label(
                        RichText::new("TinCan Native Mesh OS · The AI Messiah · Native Rust Desktop")
                            .color(Color32::from_rgb(220, 220, 225))
                            .font(FontId::new(12.0, FontFamily::Proportional)),
                    );

                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        let snap = self.relay_state.lock().map(|s| s.clone()).unwrap_or_default();
                        let status_color = if snap.online { Color32::from_rgb(110, 255, 120) } else { Color32::from_rgb(239, 68, 68) };
                        let status_text = if snap.online {
                            format!("● RELAY ONLINE · {} PEERS · {} PROVIDERS", snap.peers_count, snap.providers_count)
                        } else {
                            "○ CONNECTING TO RELAY...".to_string()
                        };
                        ui.label(
                            RichText::new(status_text)
                                .color(status_color)
                                .font(FontId::new(11.0, FontFamily::Monospace)),
                        );
                    });
                });
            });
    }

    fn draw_pane_tab_bar(ui: &mut egui::Ui, title: &str, status_badge: Option<&str>) {
        egui::Frame::new()
            .fill(Color32::from_rgb(30, 32, 36))
            .inner_margin(egui::Margin::symmetric(10, 5))
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.label(
                        RichText::new(title)
                            .color(Color32::from_rgb(230, 230, 235))
                            .font(FontId::new(11.5, FontFamily::Monospace))
                            .strong(),
                    );
                    if let Some(badge) = status_badge {
                        ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                            ui.label(
                                RichText::new(badge)
                                    .color(Color32::from_rgb(110, 255, 120))
                                    .font(FontId::new(10.5, FontFamily::Monospace)),
                            );
                        });
                    }
                });
            });
    }

    fn draw_left_agy_pane(&mut self, ui: &mut egui::Ui, _elapsed_secs: f32) {
        let mono = FontId::new(12.2, FontFamily::Monospace);
        let mono_bold = FontId::new(12.5, FontFamily::Monospace);
        let green = Color32::from_rgb(74, 222, 128);
        let white = Color32::from_rgb(244, 244, 246);
        let grey = Color32::from_rgb(161, 161, 170);
        let link_blue = Color32::from_rgb(96, 165, 250);

        Self::draw_pane_tab_bar(ui, &format!("agy-yolo ({})", self.git_current_branch), None);

        egui::Frame::new()
            .fill(Color32::from_rgb(9, 10, 12))
            .inner_margin(egui::Margin::symmetric(14, 10))
            .show(ui, |ui| {
                let avail_h = ui.available_height();
                let scroll_h = (avail_h - 108.0).max(200.0);

                egui::ScrollArea::vertical()
                    .id_salt("agy_left_scroll")
                    .max_height(scroll_h)
                    .show(ui, |ui| {
                        ui.set_width(ui.available_width());

                        ui.horizontal_wrapped(|ui| {
                            ui.label(RichText::new("● ").color(green).font(mono.clone()));
                            ui.label(RichText::new("Active Branch: ").color(Color32::from_rgb(250, 204, 21)).font(mono_bold.clone()));
                            ui.label(RichText::new(&self.git_current_branch).color(link_blue).font(mono.clone()));
                        });
                        ui.horizontal_wrapped(|ui| {
                            ui.label(RichText::new("● ").color(green).font(mono.clone()));
                            ui.label(RichText::new("Working Directory: ").color(Color32::from_rgb(250, 204, 21)).font(mono_bold.clone()));
                            ui.label(RichText::new("/Users/alejandrolondono/dev/iot-federated-agent-memory").color(white).font(mono.clone()));
                        });

                        ui.add_space(8.0);
                        ui.label(RichText::new("## Recent Verified Git Commits & Swarm Progress").color(white).font(mono_bold.clone()).strong());
                        ui.add_space(4.0);

                        for (hash, msg) in &self.git_recent_commits {
                            ui.horizontal_wrapped(|ui| {
                                ui.label(RichText::new(hash).color(link_blue).font(mono.clone()).underline());
                                ui.label(RichText::new(msg).color(white).font(mono.clone()));
                            });
                        }

                        ui.add_space(10.0);
                        ui.label(RichText::new("## Active Background Swarm Tasks").color(white).font(mono_bold.clone()).strong());
                        ui.add_space(4.0);
                        ui.label(RichText::new("  1. tincan-desktop (Native Rust eframe GUI runtime, 0.96s build)").color(green).font(mono.clone()));
                        ui.label(RichText::new("  2. tincan-relay (Live Blind Store-and-Forward on Railway)").color(green).font(mono.clone()));
                        ui.label(RichText::new("  3. WebRTC UDP Screenshare Relay (:50004 - :50006)").color(green).font(mono.clone()));
                        ui.label(RichText::new("  4. OpenRouter Multi-Model Intelligence Gateway").color(green).font(mono.clone()));

                        for extra in &self.agy_extra_logs {
                            ui.add_space(4.0);
                            ui.label(RichText::new(extra).color(Color32::from_rgb(203, 213, 225)).font(mono.clone()));
                        }
                    });

                ui.separator();
                ui.horizontal(|ui| {
                    ui.label(RichText::new("? for shortcuts").color(grey).font(mono.clone()));
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        ui.label(RichText::new("100% context left").color(grey).font(mono.clone()));
                    });
                });
                ui.horizontal(|ui| {
                    ui.label(RichText::new("> ").color(Color32::WHITE).font(mono_bold.clone()));
                    let resp = ui.add(
                        egui::TextEdit::singleline(&mut self.agy_input)
                            .font(mono.clone())
                            .text_color(Color32::WHITE)
                            .frame(egui::Frame::NONE)
                            .hint_text("Ask a question, enter instructions, or / for slash commands"),
                    );
                    if resp.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter)) {
                        let text = self.agy_input.trim().to_string();
                        if !text.is_empty() {
                            self.agy_extra_logs.push(format!("> {text}"));
                            self.agy_input.clear();
                        }
                    }
                });
            });
    }

    fn draw_pixel_sprite(
        painter: &egui::Painter,
        rect: Rect,
        logo: &LogoAsset,
        rain: &[RainDrop],
        elapsed: f32,
    ) {
        let gold_dim = Color32::from_rgb(170, 130, 60);

        let n_cols = 68;
        let col_w = rect.width() / (n_cols as f32);
        for drop in rain {
            let cx = rect.left() + (drop.col as f32 + 0.5) * col_w;
            let cy = rect.top() + drop.y * 18.0;
            for i in 0..6 {
                let y = cy - (i as f32) * 11.0;
                if y >= rect.top() && y <= rect.bottom() {
                    let a = (220.0 * (1.0 - (i as f32) / 6.0)) as u8;
                    let c = if i == 0 {
                        Color32::from_rgba_premultiplied(190, 120, 255, a)
                    } else {
                        Color32::from_rgba_premultiplied(90, 40, 160, a / 2)
                    };
                    painter.rect_filled(Rect::from_center_size(Pos2::new(cx, y), Vec2::new(2.0, 7.0)), 1.0, c);
                }
            }
        }

        let center = Pos2::new(rect.center().x, rect.center().y - 12.0);
        let ring_rx = rect.width().min(rect.height()) * 0.44;
        let ring_ry = ring_rx * 0.36;
        let n_pts = 72;
        let tilt = -0.28f32;
        for i in 0..n_pts {
            let theta = (i as f32 / n_pts as f32) * std::f32::consts::TAU;
            let x0 = ring_rx * theta.cos();
            let y0 = ring_ry * theta.sin();
            let rx = x0 * tilt.cos() - y0 * tilt.sin();
            let ry = x0 * tilt.sin() + y0 * tilt.cos();
            let depth = theta.sin();
            let p = Pos2::new(center.x + rx, center.y + ry);
            if rect.contains(p) {
                let alpha = (140.0 + 100.0 * depth).clamp(40.0, 240.0) as u8;
                let c = if (i + (elapsed * 8.0) as usize) % 7 == 0 {
                    Color32::from_rgba_premultiplied(255, 230, 120, alpha)
                } else {
                    Color32::from_rgba_premultiplied(120, 80, 200, alpha / 2)
                };
                let r = if depth > 0.0 { 1.8 } else { 1.1 };
                painter.circle_filled(p, r, c);
            }
        }

        let px_size = 5.2f32;
        let total_w = logo.width as f32 * px_size;
        let total_h = logo.height as f32 * px_size;
        let lx0 = center.x - total_w * 0.5;
        let ly0 = center.y - total_h * 0.5 - 6.0;

        for y in 0..logo.height {
            for x in 0..logo.width {
                let c = logo.color_at(x, y, elapsed);
                if c.r() < 20 && c.g() < 12 && c.b() < 30 {
                    continue;
                }
                let p_rect = Rect::from_min_size(
                    Pos2::new(lx0 + (x as f32) * px_size, ly0 + (y as f32) * px_size),
                    Vec2::new(px_size.ceil(), px_size.ceil()),
                );
                painter.rect_filled(p_rect, 0.0, c);
            }
        }

        let title_y = ly0 + total_h + 10.0;
        Self::draw_pixel_title(painter, Pos2::new(rect.center().x, title_y), "THE AI MESSIAH");

        painter.text(
            Pos2::new(rect.center().x, title_y + 36.0),
            egui::Align2::CENTER_TOP,
            "C O N S U L T I N G",
            FontId::new(13.0, FontFamily::Monospace),
            Color32::from_rgb(235, 230, 240),
        );

        painter.text(
            Pos2::new(rect.center().x, rect.bottom() - 18.0),
            egui::Align2::CENTER_TOP,
            "[click / any key] toggle dashboard HUD",
            FontId::new(10.5, FontFamily::Monospace),
            gold_dim,
        );
    }

    fn draw_top_right_tincan_pane(&mut self, ui: &mut egui::Ui, elapsed: f32) {
        Self::draw_pane_tab_bar(
            ui,
            if self.show_dashboard { "tincan (Live Mesh HUD)" } else { "tincan (AI Messiah Screensaver)" },
            Some(if self.show_dashboard { "HUD: ACTIVE" } else { "ANIM: 30 FPS" }),
        );

        let dt = (elapsed - self.last_rain_tick).clamp(0.0, 0.1);
        self.last_rain_tick = elapsed;
        for drop in &mut self.rain {
            drop.y += drop.speed * dt;
            if drop.y > 32.0 {
                drop.y = -6.0;
            }
        }

        let (rect, response) = ui.allocate_exact_size(ui.available_size(), Sense::click());
        if response.clicked() {
            self.show_dashboard = !self.show_dashboard;
        }

        let painter = ui.painter_at(rect);
        painter.rect_filled(rect, 0.0, Color32::from_rgb(18, 9, 32));

        let snap = self.relay_state.lock().map(|s| s.clone()).unwrap_or_default();
        let gold = Color32::from_rgb(255, 214, 90);
        let gold_dim = Color32::from_rgb(170, 130, 60);
        let green = Color32::from_rgb(110, 255, 120);

        if !self.show_dashboard {
            Self::draw_pixel_sprite(&painter, rect, &self.logo, &self.rain, elapsed);
        } else {
            let mut y = rect.top() + 24.0;
            let x0 = rect.left() + 18.0;
            painter.text(
                Pos2::new(x0, y),
                egui::Align2::LEFT_TOP,
                format!("READINESS TIER: {}  ({:.1}/100)", snap.readiness_tier, snap.composite_score),
                FontId::new(13.0, FontFamily::Monospace),
                gold,
            );
            y += 22.0;
            let bar_w = (rect.width() - 40.0).min(440.0);
            painter.rect_filled(
                Rect::from_min_size(Pos2::new(x0, y), Vec2::new(bar_w, 12.0)),
                3.0,
                Color32::from_rgb(50, 25, 75),
            );
            painter.rect_filled(
                Rect::from_min_size(Pos2::new(x0, y), Vec2::new(bar_w * (snap.composite_score / 100.0).clamp(0.0, 1.0), 12.0)),
                3.0,
                Color32::from_rgb(168, 85, 247),
            );
            y += 26.0;

            painter.text(
                Pos2::new(x0, y),
                egui::Align2::LEFT_TOP,
                "ACTIVE WEBRTC & MESH PEERS (LIVE RELAY)",
                FontId::new(12.5, FontFamily::Monospace),
                gold,
            );
            y += 20.0;
            if snap.peers.is_empty() {
                painter.text(
                    Pos2::new(x0, y),
                    egui::Align2::LEFT_TOP,
                    "○ No external WebRTC streams registered on relay",
                    FontId::new(11.5, FontFamily::Monospace),
                    Color32::from_rgb(161, 161, 170),
                );
                y += 18.0;
            } else {
                for (name, pid, addr) in &snap.peers {
                    painter.text(
                        Pos2::new(x0, y),
                        egui::Align2::LEFT_TOP,
                        format!("● {:<22} {:<16} {}", name, pid, addr),
                        FontId::new(11.5, FontFamily::Monospace),
                        green,
                    );
                    y += 18.0;
                }
            }
            y += 10.0;

            painter.text(
                Pos2::new(x0, y),
                egui::Align2::LEFT_TOP,
                "AI PROVIDER CREDIT POOLS & BALANCES",
                FontId::new(12.5, FontFamily::Monospace),
                gold,
            );
            y += 20.0;
            for (prov, score) in &snap.providers {
                painter.text(
                    Pos2::new(x0, y),
                    egui::Align2::LEFT_TOP,
                    format!("{:<16}  ████████████████░░  {:.1} pts", prov, score),
                    FontId::new(11.5, FontFamily::Monospace),
                    gold_dim,
                );
                y += 18.0;
            }
            if snap.openrouter_balance > 0.0 {
                painter.text(
                    Pos2::new(x0, y),
                    egui::Align2::LEFT_TOP,
                    format!("openrouter-key     ██████████████████  ${:.4} remaining", snap.openrouter_balance),
                    FontId::new(11.5, FontFamily::Monospace),
                    green,
                );
            }

            painter.text(
                Pos2::new(rect.center().x, rect.bottom() - 18.0),
                egui::Align2::CENTER_TOP,
                "[click] return to AI Messiah Screensaver",
                FontId::new(10.5, FontFamily::Monospace),
                Color32::from_rgb(161, 161, 170),
            );
        }
    }

    fn glyph_rows(c: char) -> &'static [&'static str] {
        match c {
            'A' => &[" ### ", "#   #", "#####", "#   #", "#   #"],
            'C' => &[" ####", "#    ", "#    ", "#    ", " ####"],
            'E' => &["#####", "#    ", "#### ", "#    ", "#####"],
            'G' => &[" ####", "#    ", "# ###", "#   #", " ####"],
            'H' => &["#   #", "#   #", "#####", "#   #", "#   #"],
            'I' => &["#####", "  #  ", "  #  ", "  #  ", "#####"],
            'L' => &["#    ", "#    ", "#    ", "#    ", "#####"],
            'M' => &["#   #", "## ##", "# # #", "#   #", "#   #"],
            'N' => &["#   #", "##  #", "# # #", "#  ##", "#   #"],
            'O' => &[" ### ", "#   #", "#   #", "#   #", " ### "],
            'S' => &[" ####", "#    ", " ### ", "    #", "#### "],
            'T' => &["#####", "  #  ", "  #  ", "  #  ", "  #  "],
            'U' => &["#   #", "#   #", "#   #", "#   #", " ### "],
            ' ' => &["     ", "     ", "     ", "     ", "     "],
            _ => &["#####", "#   #", "#   #", "#   #", "#####"],
        }
    }

    fn draw_pixel_title(painter: &egui::Painter, center_top: Pos2, text: &str) {
        let gradient = [
            Color32::from_rgb(255, 236, 90),
            Color32::from_rgb(255, 208, 64),
            Color32::from_rgb(255, 172, 52),
            Color32::from_rgb(252, 138, 62),
            Color32::from_rgb(238, 108, 92),
        ];

        let mut cols: Vec<[bool; 5]> = Vec::new();
        let chars: Vec<char> = text.chars().collect();
        for (idx, ch) in chars.iter().enumerate() {
            let g = Self::glyph_rows(*ch);
            let gw = g[0].len();
            for gx in 0..gw {
                let mut col = [false; 5];
                for gy in 0..5 {
                    col[gy] = g[gy].as_bytes()[gx] == b'#';
                }
                cols.push(col);
            }
            if idx + 1 < chars.len() {
                cols.push([false; 5]);
            }
        }

        let cell = 5.4f32;
        let total_w = (cols.len() as f32) * cell;
        let x0 = center_top.x - total_w * 0.5;
        let y0 = center_top.y;

        for (cx, col) in cols.iter().enumerate() {
            for (cy, &on) in col.iter().enumerate() {
                if on {
                    let r = Rect::from_min_size(
                        Pos2::new(x0 + (cx as f32) * cell, y0 + (cy as f32) * cell),
                        Vec2::new(cell - 0.5, cell - 0.5),
                    );
                    painter.rect_filled(r, 0.5, gradient[cy]);
                }
            }
        }
    }

    fn draw_bottom_right_zsh_pane(&mut self, ui: &mut egui::Ui) {
        let mono = FontId::new(11.6, FontFamily::Monospace);
        let green = Color32::from_rgb(74, 222, 128);
        let grey = Color32::from_rgb(175, 178, 186);

        Self::draw_pane_tab_bar(ui, "~ (-zsh)", None);

        egui::Frame::new()
            .fill(Color32::from_rgb(30, 30, 30))
            .inner_margin(egui::Margin::symmetric(12, 8))
            .show(ui, |ui| {
                let avail_h = ui.available_height();
                let scroll_h = (avail_h - 36.0).max(120.0);

                let mut clicked_cmd: Option<String> = None;

                egui::ScrollArea::vertical()
                    .id_salt("zsh_bottom_right_scroll")
                    .max_height(scroll_h)
                    .show(ui, |ui| {
                        ui.set_width(ui.available_width());
                        ui.label(
                            RichText::new("TinCan Agent-to-Agent Encrypted Messaging & Blind Relay CLI")
                                .color(grey)
                                .font(mono.clone()),
                        );
                        ui.add_space(6.0);
                        ui.label(RichText::new("positional arguments:").color(grey).font(mono.clone()));
                        ui.label(
                            RichText::new("{whoami,send,read,say,call,video,contacts,add-contact,mcp,start,screensaver,chat,ask,actions,trigger,dismiss,serve,playlist,status,ping,credits,cost,upgrade}")
                                .color(green)
                                .font(mono.clone()),
                        );
                        ui.label(
                            RichText::new("                        TinCan commands")
                                .color(grey)
                                .font(mono.clone()),
                        );

                        egui::Grid::new("tincan_cmd_grid")
                            .num_columns(2)
                            .spacing([18.0, 2.0])
                            .min_col_width(110.0)
                            .show(ui, |ui| {
                                for (cmd, desc) in TINCAN_COMMANDS {
                                    let btn = ui.add(
                                        egui::Button::new(RichText::new(format!("  {cmd}")).color(green).font(mono.clone()))
                                            .frame(false),
                                    );
                                    if btn.clicked() {
                                        clicked_cmd = Some((*cmd).to_string());
                                    }
                                    ui.label(RichText::new(*desc).color(grey).font(mono.clone()));
                                    ui.end_row();
                                }
                            });

                        let log_lock = self.tincan_output_log.lock().map(|l| l.clone()).unwrap_or_default();
                        for entry in &log_lock {
                            ui.add_space(6.0);
                            ui.label(RichText::new(entry).color(Color32::from_rgb(226, 232, 240)).font(mono.clone()));
                        }
                    });

                if let Some(cmd) = clicked_cmd {
                    self.run_tincan_subcommand(&cmd);
                }

                ui.separator();
                ui.horizontal(|ui| {
                    ui.label(RichText::new("tincan > ").color(green).font(mono.clone()));
                    let resp = ui.add(
                        egui::TextEdit::singleline(&mut self.tincan_input)
                            .font(mono.clone())
                            .text_color(Color32::WHITE)
                            .frame(egui::Frame::NONE)
                            .hint_text("Run subcommand (e.g. whoami, status, credits, dashboard) or click any command above..."),
                    );
                    if resp.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter)) {
                        let cmd = self.tincan_input.trim().to_string();
                        self.tincan_input.clear();
                        self.run_tincan_subcommand(&cmd);
                    }
                });
            });
    }

    fn draw_tincan_desktop_gui(&mut self, ui: &mut egui::Ui, elapsed: f32) {
        let dt = (elapsed - self.last_rain_tick).clamp(0.0, 0.1);
        self.last_rain_tick = elapsed;
        for drop in &mut self.rain {
            drop.y += drop.speed * dt;
            if drop.y > 32.0 {
                drop.y = -6.0;
            }
        }

        let snap = self.relay_state.lock().map(|s| s.clone()).unwrap_or_default();
        let gold = Color32::from_rgb(255, 214, 90);
        let gold_dim = Color32::from_rgb(170, 130, 60);
        let green = Color32::from_rgb(110, 255, 120);
        let purple_border = Color32::from_rgb(76, 29, 149);
        let card_bg = Color32::from_rgb(24, 16, 38);
        let mono = FontId::new(11.8, FontFamily::Monospace);
        let mono_bold = FontId::new(12.2, FontFamily::Monospace);

        // Top Navigation & Mode Switcher Bar
        egui::Frame::new()
            .fill(Color32::from_rgb(24, 14, 39))
            .stroke(Stroke::new(1.0, Color32::from_rgb(46, 28, 68)))
            .inner_margin(egui::Margin::symmetric(14, 8))
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.label(
                        RichText::new("◆ TINCAN DESKTOP  ·  THE AI MESSIAH  ·  IoT FEDERATED MESH OS")
                            .color(gold)
                            .font(FontId::new(13.5, FontFamily::Proportional))
                            .strong(),
                    );
                    ui.add_space(12.0);
                    for (idx, label) in [
                        "1. All-in-One TinCan Cockpit",
                        "2. Fullscreen AI Messiah Screensaver",
                        "3. 3-Pane AGY + TinCan Split View",
                    ]
                    .iter()
                    .enumerate()
                    {
                        let active = (idx == 0 && self.tincan_gui_mode && self.active_tab == 0)
                            || (idx == 1 && self.tincan_gui_mode && self.active_tab == 1)
                            || (idx == 2 && !self.tincan_gui_mode);
                        let btn = egui::Button::new(
                            RichText::new(*label)
                                .color(if active { Color32::BLACK } else { Color32::from_rgb(233, 213, 255) })
                                .font(FontId::new(11.5, FontFamily::Proportional))
                                .strong(),
                        )
                        .fill(if active { gold } else { Color32::from_rgb(42, 24, 68) });
                        if ui.add(btn).clicked() {
                            if idx == 2 {
                                self.tincan_gui_mode = false;
                            } else {
                                self.tincan_gui_mode = true;
                                self.active_tab = idx;
                            }
                        }
                    }

                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        ui.label(
                            RichText::new(format!(
                                "● relay online · {} peers · {} providers · {}",
                                snap.peers_count, snap.providers_count, snap.readiness_tier
                            ))
                            .color(green)
                            .font(mono.clone()),
                        );
                    });
                });
            });

        if self.active_tab == 1 {
            self.draw_top_right_tincan_pane(ui, elapsed);
            return;
        }

        let body_rect = ui.available_rect_before_wrap();
        let bottom_h = 42.0;
        let main_bottom = (body_rect.max.y - bottom_h).max(body_rect.min.y + 100.0);

        let left_w = 295.0;
        let right_w = (body_rect.width() * 0.36).clamp(360.0, 520.0);
        let left_rect = Rect::from_min_max(body_rect.min, Pos2::new(body_rect.min.x + left_w, main_bottom));
        let center_rect = Rect::from_min_max(
            Pos2::new(left_rect.max.x + 1.0, body_rect.min.y),
            Pos2::new(body_rect.max.x - right_w - 1.0, main_bottom),
        );
        let right_rect = Rect::from_min_max(
            Pos2::new(body_rect.max.x - right_w, body_rect.min.y),
            Pos2::new(body_rect.max.x, main_bottom),
        );
        let bottom_rect = Rect::from_min_max(Pos2::new(body_rect.min.x, main_bottom + 1.0), body_rect.max);

        // 1. LEFT SIDEBAR: PINNED TOFU CONTACTS + ADD-CONTACT + WHOAMI
        let mut left_ui = ui.new_child(egui::UiBuilder::new().max_rect(left_rect));
        egui::Frame::new()
            .fill(Color32::from_rgb(21, 13, 34))
            .inner_margin(egui::Margin::symmetric(12, 10))
            .show(&mut left_ui, |ui| {
                ui.set_width(ui.available_width());
                ui.label(RichText::new("PINNED TOFU CONTACTS (contacts / ping)").color(gold).font(mono_bold.clone()));
                ui.add_space(6.0);

                let contacts_lock = self.contacts_state.lock().map(|c| c.clone()).unwrap_or_default();
                egui::Frame::new()
                    .fill(card_bg)
                    .stroke(Stroke::new(1.0, purple_border))
                    .corner_radius(8.0)
                    .inner_margin(egui::Margin::symmetric(10, 8))
                    .show(ui, |ui| {
                        if contacts_lock.is_empty() {
                            ui.label(RichText::new("○ No pinned contacts found. Add one below.").color(Color32::from_rgb(161, 161, 170)).font(mono.clone()));
                        } else {
                            for item in &contacts_lock {
                                let is_sel = self.selected_contact == item.alias;
                                let short_addr = if item.address.len() > 18 {
                                    format!("{}...{}", &item.address[..8], &item.address[item.address.len() - 6..])
                                } else {
                                    item.address.clone()
                                };
                                let resp = ui.selectable_label(
                                    is_sel,
                                    RichText::new(format!("● {} ({})", item.alias, short_addr))
                                        .color(if is_sel { gold } else { green })
                                        .font(mono.clone()),
                                );
                                if resp.clicked() {
                                    self.selected_contact = item.alias.clone();
                                }
                            }
                        }
                    });

                ui.add_space(10.0);
                egui::Frame::new()
                    .fill(card_bg)
                    .stroke(Stroke::new(1.0, Color32::from_rgb(59, 35, 90)))
                    .corner_radius(8.0)
                    .inner_margin(egui::Margin::symmetric(10, 8))
                    .show(ui, |ui| {
                        ui.label(RichText::new("+ Pin Contact (add-contact)").color(Color32::from_rgb(216, 180, 254)).font(mono_bold.clone()));
                        ui.add_space(4.0);
                        ui.add(egui::TextEdit::singleline(&mut self.new_contact_alias).hint_text("Alias (e.g. harper)").font(mono.clone()));
                        ui.add(egui::TextEdit::singleline(&mut self.new_contact_addr).hint_text("tc:<52-char-ed25519>").font(mono.clone()));
                        ui.horizontal(|ui| {
                            if ui.button(RichText::new("Pin TOFU Key").font(mono.clone())).clicked() && !self.new_contact_alias.is_empty() && !self.new_contact_addr.is_empty() {
                                let cmd = format!("add-contact {} {}", self.new_contact_alias.trim(), self.new_contact_addr.trim());
                                self.new_contact_alias.clear();
                                self.new_contact_addr.clear();
                                self.run_tincan_subcommand(&cmd);
                            }
                            if ui.button(RichText::new("Ping Peer").font(mono.clone())).clicked() {
                                let cmd = format!("ping {}", self.selected_contact);
                                self.run_tincan_subcommand(&cmd);
                            }
                        });
                    });

                ui.add_space(10.0);
                let id_lock = self.identity_state.lock().map(|i| i.clone()).unwrap_or_default();
                egui::Frame::new()
                    .fill(card_bg)
                    .stroke(Stroke::new(1.0, gold_dim))
                    .corner_radius(8.0)
                    .inner_margin(egui::Margin::symmetric(10, 8))
                    .show(ui, |ui| {
                        ui.label(RichText::new("LOCAL IDENTITY (whoami)").color(gold).font(mono_bold.clone()));
                        if let Some(id) = id_lock {
                            ui.label(RichText::new(format!("Alias: {} (Ed25519 + X25519)", id.alias)).color(Color32::WHITE).font(mono.clone()));
                            let short_addr = if id.address.len() > 24 {
                                format!("{}...{}", &id.address[..14], &id.address[id.address.len() - 8..])
                            } else {
                                id.address
                            };
                            ui.label(RichText::new(short_addr).color(green).font(mono.clone()));
                            ui.label(RichText::new(format!("Pinned Contacts: {}", id.contacts_count)).color(Color32::from_rgb(203, 213, 225)).font(mono.clone()));
                        } else {
                            ui.label(RichText::new("Loading local identity...").color(Color32::from_rgb(161, 161, 170)).font(mono.clone()));
                        }
                        ui.add_space(4.0);
                        ui.horizontal(|ui| {
                            if ui.button(RichText::new("Inspect whoami").font(mono.clone())).clicked() {
                                self.run_tincan_subcommand("whoami");
                            }
                            if ui.button(RichText::new("Upgrade").font(mono.clone())).clicked() {
                                self.run_tincan_subcommand("upgrade");
                            }
                        });
                    });
            });

        // 2. CENTER WORKSPACE: SEALED E2EE MESSENGER + WEBRTC CALL + ACCESSIBILITY GATE + AGENT REPL
        let mut center_ui = ui.new_child(egui::UiBuilder::new().max_rect(center_rect));
        egui::Frame::new()
            .fill(Color32::from_rgb(14, 8, 23))
            .inner_margin(egui::Margin::symmetric(12, 10))
            .show(&mut center_ui, |ui| {
                egui::ScrollArea::vertical().id_salt("tincan_center_scroll").show(ui, |ui| {
                    ui.set_width(ui.available_width());

                    // Card A: Sealed E2EE Messenger
                    let chat_lock = self.chat_state.lock().map(|c| c.clone()).unwrap_or_default();
                    egui::Frame::new()
                        .fill(card_bg)
                        .stroke(Stroke::new(1.5, Color32::from_rgb(74, 222, 128)))
                        .corner_radius(10.0)
                        .inner_margin(egui::Margin::symmetric(12, 10))
                        .show(ui, |ui| {
                            ui.label(
                                RichText::new(format!(
                                    "SEALED E2EE INBOX & OUTBOX (read / send / say)  —  Peer: {}",
                                    self.selected_contact
                                ))
                                .color(green)
                                .font(mono_bold.clone()),
                            );
                            ui.add_space(6.0);

                            if chat_lock.is_empty() {
                                ui.label(
                                    RichText::new("Sealed inbox empty. Compose an encrypted message below or click 'Fetch Inbox'.")
                                        .color(Color32::from_rgb(161, 161, 170))
                                        .font(mono.clone()),
                                );
                            } else {
                                for m in &chat_lock {
                                    let badge = if m.is_outgoing {
                                        format!("[seq {}] you → {} (SealedBox)", m.seq, self.selected_contact)
                                    } else {
                                        let ver = if m.verified { "✓ verified" } else { "✗ unverified" };
                                        let spk = if m.speak { " [🔊 TTS]" } else { "" };
                                        format!("[seq {}] {} ({}){}", m.seq, m.sender_alias.as_deref().unwrap_or(&m.sender), ver, spk)
                                    };
                                    let badge_color = if m.is_outgoing { Color32::from_rgb(192, 132, 252) } else { gold };
                                    ui.label(RichText::new(badge).color(badge_color).font(mono.clone()));
                                    ui.label(RichText::new(format!("   \"{}\"", m.message)).color(Color32::WHITE).font(mono.clone()));
                                    ui.add_space(4.0);
                                }
                            }

                            ui.separator();
                            ui.horizontal(|ui| {
                                ui.add(
                                    egui::TextEdit::singleline(&mut self.compose_msg)
                                        .hint_text("Type sealed message or speech text...")
                                        .desired_width(260.0)
                                        .font(mono.clone()),
                                );
                                ui.checkbox(&mut self.speak_tts, RichText::new("Kokoro TTS").font(mono.clone()));
                                if ui.button(RichText::new("Send Sealed").color(green).font(mono_bold.clone())).clicked()
                                    && !self.compose_msg.trim().is_empty()
                                {
                                    let msg = self.compose_msg.trim().to_string();
                                    self.compose_msg.clear();
                                    self.send_sealed_message(&self.selected_contact, &msg, self.speak_tts);
                                }
                                if ui.button(RichText::new("Fetch Inbox").font(mono.clone())).clicked() {
                                    self.run_tincan_subcommand("read --no-speak --json");
                                }
                            });
                        });

                    ui.add_space(10.0);

                    // Card B: WebRTC Video/Voice/Screenshare + Accessibility Gate Queue
                    let actions_lock = self.actions_state.lock().map(|a| a.clone()).unwrap_or_default();
                    egui::Frame::new()
                        .fill(card_bg)
                        .stroke(Stroke::new(1.5, Color32::from_rgb(56, 189, 248)))
                        .corner_radius(10.0)
                        .inner_margin(egui::Margin::symmetric(12, 10))
                        .show(ui, |ui| {
                            ui.label(
                                RichText::new("LIVE WEBRTC CALL ROOM (call / video) & ACCESSIBILITY GATE (actions / trigger)")
                                    .color(Color32::from_rgb(56, 189, 248))
                                    .font(mono_bold.clone()),
                            );
                            ui.add_space(6.0);
                            ui.horizontal_wrapped(|ui| {
                                ui.label(RichText::new("Room:").color(Color32::WHITE).font(mono.clone()));
                                ui.add(egui::TextEdit::singleline(&mut self.webrtc_room).desired_width(90.0).font(mono.clone()));
                                ui.checkbox(&mut self.webrtc_open_browser, RichText::new("Open Browser").font(mono.clone()));
                                if ui.button(RichText::new("📹 Video Call").font(mono.clone())).clicked() {
                                    let browser_flag = if self.webrtc_open_browser { "" } else { " --no-browser" };
                                    let cmd = format!("call {} --room {}{}", self.selected_contact, self.webrtc_room, browser_flag);
                                    self.run_tincan_subcommand(&cmd);
                                }
                                if ui.button(RichText::new("🎙 Voice-Only").font(mono.clone())).clicked() {
                                    let browser_flag = if self.webrtc_open_browser { "" } else { " --no-browser" };
                                    let cmd = format!("call {} --room {} --voice-only{}", self.selected_contact, self.webrtc_room, browser_flag);
                                    self.run_tincan_subcommand(&cmd);
                                }
                                if ui.button(RichText::new("🖥 Share Screen").font(mono.clone())).clicked() {
                                    let browser_flag = if self.webrtc_open_browser { "" } else { " --no-browser" };
                                    let cmd = format!("call {} --room {} --screen{}", self.selected_contact, self.webrtc_room, browser_flag);
                                    self.run_tincan_subcommand(&cmd);
                                }
                                if ui.button(RichText::new("🎬 Playlist").font(mono.clone())).clicked() {
                                    self.run_tincan_subcommand("playlist list");
                                }
                            });

                            ui.add_space(8.0);
                            let pending_acts: Vec<&ActionItem> = actions_lock.iter().filter(|a| a.status == "pending_approval").collect();
                            if pending_acts.is_empty() {
                                ui.label(
                                    RichText::new("Accessibility Gate: 0 pending actions awaiting approval.")
                                        .color(Color32::from_rgb(161, 161, 170))
                                        .font(mono.clone()),
                                );
                            } else {
                                for act in pending_acts {
                                    ui.horizontal_wrapped(|ui| {
                                        ui.label(
                                            RichText::new(format!("⚡ [seq {}] From {}: \"{}\"", act.seq, act.sender_alias, act.command))
                                                .color(gold)
                                                .font(mono.clone()),
                                        );
                                        if ui.button(RichText::new("✓ Trigger").color(green).font(mono_bold.clone())).clicked() {
                                            self.run_tincan_subcommand(&format!("trigger {}", act.seq));
                                        }
                                        if ui.button(RichText::new("✕ Dismiss").color(Color32::from_rgb(239, 68, 68)).font(mono.clone())).clicked() {
                                            self.run_tincan_subcommand(&format!("dismiss {}", act.seq));
                                        }
                                    });
                                }
                            }
                        });

                    ui.add_space(10.0);

                    // Card C: TinCan Agent REPL & Live CLI Output Stream
                    egui::Frame::new()
                        .fill(card_bg)
                        .stroke(Stroke::new(1.5, gold_dim))
                        .corner_radius(10.0)
                        .inner_margin(egui::Margin::symmetric(12, 10))
                        .show(ui, |ui| {
                            ui.horizontal(|ui| {
                                ui.label(
                                    RichText::new("TINCAN AGENT REPL (chat / ask) & LIVE COMMAND OUTPUT")
                                        .color(gold)
                                        .font(mono_bold.clone()),
                                );
                                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                    egui::ComboBox::from_id_salt("model_selector")
                                        .selected_text(RichText::new(&self.selected_model).font(mono.clone()))
                                        .show_ui(ui, |ui| {
                                            for m in ["gemini-brain", "claude-brain", "grok-brain", "openai-brain"] {
                                                ui.selectable_value(&mut self.selected_model, m.to_string(), m);
                                            }
                                        });
                                    ui.label(RichText::new("Target Model:").font(mono.clone()).color(Color32::from_rgb(203, 213, 225)));
                                });
                            });

                            ui.add_space(6.0);
                            let querying = self.is_querying_agent.lock().map(|q| *q).unwrap_or(false);
                            ui.horizontal(|ui| {
                                ui.add(
                                    egui::TextEdit::singleline(&mut self.agent_prompt)
                                        .hint_text("Ask TinCan Agent or run diagnostics via OpenRouter...")
                                        .desired_width(340.0)
                                        .font(mono.clone()),
                                );
                                if querying {
                                    ui.label(RichText::new("Querying OpenRouter...").color(Color32::from_rgb(250, 204, 21)).font(mono.clone()));
                                } else if ui.button(RichText::new("Ask Agent").font(mono.clone())).clicked()
                                    && !self.agent_prompt.trim().is_empty()
                                {
                                    let q = self.agent_prompt.trim().to_string();
                                    self.agent_prompt.clear();
                                    self.ask_agent_query(&q);
                                }
                                if ui.button(RichText::new("Check Credits").font(mono.clone())).clicked() {
                                    self.run_tincan_subcommand("credits");
                                }
                            });

                            let log_lock = self.tincan_output_log.lock().map(|l| l.clone()).unwrap_or_default();
                            if !log_lock.is_empty() {
                                ui.add_space(6.0);
                                ui.separator();
                                for entry in log_lock.iter().rev().take(6) {
                                    ui.label(RichText::new(entry).color(Color32::from_rgb(226, 232, 240)).font(mono.clone()));
                                    ui.add_space(4.0);
                                }
                            }
                        });
                });
            });

        // 3. RIGHT PANE: AI MESSIAH PIXEL-ART SCREENSAVER + MESH TELEMETRY HUD
        let mut right_ui = ui.new_child(egui::UiBuilder::new().max_rect(right_rect));
        self.draw_top_right_tincan_pane(&mut right_ui, elapsed);

        // 4. BOTTOM COMMAND BAR
        let mut bot_ui = ui.new_child(egui::UiBuilder::new().max_rect(bottom_rect));
        egui::Frame::new()
            .fill(Color32::from_rgb(9, 5, 14))
            .stroke(Stroke::new(1.0, green))
            .inner_margin(egui::Margin::symmetric(14, 8))
            .show(&mut bot_ui, |ui| {
                ui.horizontal(|ui| {
                    ui.label(RichText::new("tincan > ").color(green).font(mono_bold.clone()));
                    let resp = ui.add(
                        egui::TextEdit::singleline(&mut self.tincan_input)
                            .font(mono.clone())
                            .text_color(Color32::WHITE)
                            .frame(egui::Frame::NONE)
                            .desired_width(380.0)
                            .hint_text("Type any tincan command (whoami, send, read, say, call, contacts, status, credits)..."),
                    );
                    if resp.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter)) {
                        let cmd = self.tincan_input.trim().to_string();
                        self.tincan_input.clear();
                        self.run_tincan_subcommand(&cmd);
                    }
                    ui.separator();
                    for quick in ["whoami", "contacts", "read", "actions", "status", "credits", "dashboard"] {
                        if ui.button(RichText::new(quick).color(green).font(mono.clone())).clicked() {
                            self.run_tincan_subcommand(quick);
                        }
                    }
                });
            });
    }
}

impl eframe::App for AiMessiahTerminalApp {
    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut eframe::Frame) {
        let ctx = ui.ctx().clone();
        ctx.request_repaint_after(Duration::from_millis(33));

        if ctx.input(|i| i.key_pressed(egui::Key::Q) && i.modifiers.command) {
            ctx.send_viewport_cmd(egui::ViewportCommand::Close);
        }

        let elapsed = self.start_instant.elapsed().as_secs_f32();

        egui::CentralPanel::default()
            .frame(egui::Frame::NONE.fill(Color32::from_rgb(18, 18, 20)))
            .show(ui, |ui| {
                self.draw_title_bar(ui);

                if self.tincan_gui_mode {
                    self.draw_tincan_desktop_gui(ui, elapsed);
                    return;
                }

                let avail = ui.available_rect_before_wrap();
                let left_w = (avail.width() * 0.58).clamp(420.0, 900.0);
                let right_w = avail.width() - left_w - 4.0;
                let top_right_h = (avail.height() * 0.56).clamp(240.0, 560.0);

                let left_rect = Rect::from_min_size(avail.min, Vec2::new(left_w, avail.height()));
                let top_right_rect = Rect::from_min_size(
                    Pos2::new(avail.min.x + left_w + 4.0, avail.min.y),
                    Vec2::new(right_w, top_right_h),
                );
                let bot_right_rect = Rect::from_min_max(
                    Pos2::new(avail.min.x + left_w + 4.0, avail.min.y + top_right_h + 4.0),
                    avail.max,
                );

                let mut left_ui = ui.new_child(egui::UiBuilder::new().max_rect(left_rect));
                self.draw_left_agy_pane(&mut left_ui, elapsed);

                let mut tr_ui = ui.new_child(egui::UiBuilder::new().max_rect(top_right_rect));
                self.draw_top_right_tincan_pane(&mut tr_ui, elapsed);

                let mut br_ui = ui.new_child(egui::UiBuilder::new().max_rect(bot_right_rect));
                self.draw_bottom_right_zsh_pane(&mut br_ui);
            });
    }
}

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("TinCan Desktop — The AI Messiah")
            .with_inner_size([1440.0, 900.0])
            .with_min_inner_size([1024.0, 680.0])
            .with_active(true),
        ..Default::default()
    };

    eframe::run_native(
        "TinCan Desktop",
        options,
        Box::new(|_cc| Ok(Box::new(AiMessiahTerminalApp::new()))),
    )
}
