#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;

use serde::{Deserialize, Serialize};
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::{AppHandle, Manager, WebviewUrl, WebviewWindowBuilder, WindowEvent};
use url::Url;

const FALLBACK_RELAY_URL: &str = "https://iot-federated-agent-memory-production.up.railway.app";

#[derive(Clone, Copy)]
struct AppToolSpec {
    slug: &'static str,
    title: &'static str,
    route: &'static str,
    width: f64,
    height: f64,
}

const APP_TOOLS: &[AppToolSpec] = &[
    AppToolSpec { slug: "desktop", title: "TinCan Desktop (Zen Shell)", route: "/", width: 1280.0, height: 820.0 },
    AppToolSpec { slug: "tv", title: "Watch Party", route: "/tv", width: 1120.0, height: 760.0 },
    AppToolSpec { slug: "talk", title: "Talk & Comms", route: "/comms", width: 1040.0, height: 740.0 },
    AppToolSpec { slug: "call", title: "Video Call", route: "/call", width: 1080.0, height: 720.0 },
    AppToolSpec { slug: "board", title: "Board", route: "/board", width: 1180.0, height: 780.0 },
    AppToolSpec { slug: "space", title: "Workstation", route: "/workstation", width: 1280.0, height: 820.0 },
    AppToolSpec { slug: "copilot", title: "AI Copilot", route: "/copilot", width: 1060.0, height: 760.0 },
    AppToolSpec { slug: "ai", title: "AI Hub", route: "/ai", width: 1080.0, height: 740.0 },
    AppToolSpec { slug: "3dstudio", title: "3D Studio", route: "/3dstudio", width: 1200.0, height: 780.0 },
    AppToolSpec { slug: "node-studio", title: "Node Studio", route: "/nodes", width: 1320.0, height: 840.0 },
    AppToolSpec { slug: "terminal", title: "Terminal", route: "/terminal", width: 1080.0, height: 720.0 },
    AppToolSpec { slug: "arena", title: "Arena", route: "/arena", width: 1180.0, height: 780.0 },
    AppToolSpec { slug: "network", title: "Network", route: "/network", width: 980.0, height: 700.0 },
    AppToolSpec { slug: "quests", title: "Quests", route: "/quests", width: 960.0, height: 700.0 },
    AppToolSpec { slug: "tokens", title: "Tokens & Ads", route: "/tokens", width: 1020.0, height: 740.0 },
    AppToolSpec { slug: "browser", title: "Browser", route: "/browser", width: 1160.0, height: 780.0 },
    AppToolSpec { slug: "localhost", title: "Localhost", route: "/localhost", width: 1120.0, height: 760.0 },
    AppToolSpec { slug: "moderator", title: "Moderate & Treasury", route: "/moderator", width: 1040.0, height: 720.0 },
];

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SavedWindowGeom {
    width: f64,
    height: f64,
}

struct DesktopState {
    base_url: String,
    window_geoms: Mutex<HashMap<String, SavedWindowGeom>>,
}

fn config_dir() -> PathBuf {
    if let Ok(dir) = env::var("TINCAN_CONFIG_DIR") {
        if !dir.trim().is_empty() {
            return PathBuf::from(dir);
        }
    }
    let home = env::var("HOME").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home).join(".tincan")
}

fn geom_file_path() -> PathBuf {
    config_dir().join("desktop_windows.json")
}

fn load_window_geoms() -> HashMap<String, SavedWindowGeom> {
    let path = geom_file_path();
    fs::read_to_string(path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default()
}

fn save_window_geoms(map: &HashMap<String, SavedWindowGeom>) {
    let dir = config_dir();
    let _ = fs::create_dir_all(&dir);
    if let Ok(json) = serde_json::to_string_pretty(map) {
        let _ = fs::write(geom_file_path(), json);
    }
}

/// Locate the `tincan` executable on PATH (no hardcoded user paths).
fn find_tincan_bin() -> Option<PathBuf> {
    if let Ok(explicit) = env::var("TINCAN_BIN") {
        let p = PathBuf::from(explicit);
        if p.is_file() {
            return Some(p);
        }
    }
    if let Ok(path_var) = env::var("PATH") {
        for dir in env::split_paths(&path_var) {
            let candidate = dir.join("tincan");
            if candidate.is_file() {
                return Some(candidate);
            }
        }
    }
    let home = env::var("HOME").unwrap_or_default();
    let fallbacks = [
        PathBuf::from(&home).join(".local/bin/tincan"),
        PathBuf::from("/opt/homebrew/bin/tincan"),
        PathBuf::from("/usr/local/bin/tincan"),
    ];
    for p in fallbacks {
        if p.is_file() {
            return Some(p);
        }
    }
    None
}

/// Start or attach to the local TinCan OS node (`tincan os --no-open --json`),
/// falling back to `TINCAN_RELAY_URL` / Railway only if the local node is unavailable.
fn resolve_node_base_url() -> String {
    if let Ok(override_url) = env::var("TINCAN_DESKTOP_URL") {
        let trimmed = override_url.trim().trim_end_matches('/');
        if !trimmed.is_empty() {
            return trimmed.to_string();
        }
    }
    if let Some(bin) = find_tincan_bin() {
        if let Ok(output) = Command::new(&bin)
            .args(["os", "--no-open", "--json"])
            .output()
        {
            if output.status.success() {
                if let Ok(val) = serde_json::from_slice::<serde_json::Value>(&output.stdout) {
                    if let Some(url) = val.get("url").and_then(|u| u.as_str()) {
                        return url.trim_end_matches('/').to_string();
                    }
                }
            }
        }
    }
    env::var("TINCAN_RELAY_URL")
        .ok()
        .filter(|s| !s.trim().is_empty())
        .unwrap_or_else(|| FALLBACK_RELAY_URL.to_string())
        .trim_end_matches('/')
        .to_string()
}

fn open_or_focus_tool_window(app: &AppHandle, spec: &AppToolSpec) {
    let label = if spec.slug == "desktop" {
        "main".to_string()
    } else {
        format!("app-{}", spec.slug)
    };

    if let Some(existing) = app.get_webview_window(&label) {
        let _ = existing.show();
        let _ = existing.unminimize();
        let _ = existing.set_focus();
        return;
    }

    let state = app.state::<DesktopState>();
    let target = format!("{}{}", state.base_url, spec.route);
    let Ok(parsed_url) = Url::parse(&target) else {
        return;
    };

    let (w, h) = {
        let map = state.window_geoms.lock().unwrap();
        map.get(&label)
            .map(|g| (g.width.max(640.0), g.height.max(460.0)))
            .unwrap_or((spec.width, spec.height))
    };

    let title = format!("TinCan — {}", spec.title);
    let builder = WebviewWindowBuilder::new(app, &label, WebviewUrl::External(parsed_url))
        .title(&title)
        .inner_size(w, h)
        .min_inner_size(640.0, 460.0)
        .resizable(true)
        .center();

    if let Ok(win) = builder.build() {
        let app_clone = app.clone();
        let label_clone = label.clone();
        win.on_window_event(move |event| {
            if let WindowEvent::Resized(size) = event {
                let st = app_clone.state::<DesktopState>();
                if let Ok(mut map) = st.window_geoms.lock() {
                    map.insert(
                        label_clone.clone(),
                        SavedWindowGeom {
                            width: f64::from(size.width),
                            height: f64::from(size.height),
                        },
                    );
                    save_window_geoms(&map);
                };
            }
        });
    }
}

fn trigger_cmd_k(app: &AppHandle) {
    if let Some(main_win) = app.get_webview_window("main") {
        let _ = main_win.show();
        let _ = main_win.unminimize();
        let _ = main_win.set_focus();
        let _ = main_win.eval("if (window.TinCanZen) { window.TinCanZen.openLauncher(); }");
    }
}

fn set_theme_all_windows(app: &AppHandle, mode: &str) {
    let js = format!("if (window.TinCanTheme) {{ window.TinCanTheme.set('{}'); }}", mode);
    for (_label, win) in app.webview_windows() {
        let _ = win.eval(&js);
    }
}

fn build_native_menu(app: &AppHandle) -> tauri::Result<Menu<tauri::Wry>> {
    let file_menu = Submenu::with_items(
        app,
        "File",
        true,
        &[
            &MenuItem::with_id(app, "cmd-k", "Universal Command Bar…", true, Some("CmdOrCtrl+K"))?,
            &MenuItem::with_id(app, "app-desktop", "Focus TinCan Desktop", true, Some("CmdOrCtrl+0"))?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::close_window(app, None)?,
            &PredefinedMenuItem::quit(app, None)?,
        ],
    )?;

    let edit_menu = Submenu::with_items(
        app,
        "Edit",
        true,
        &[
            &PredefinedMenuItem::undo(app, None)?,
            &PredefinedMenuItem::redo(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::cut(app, None)?,
            &PredefinedMenuItem::copy(app, None)?,
            &PredefinedMenuItem::paste(app, None)?,
            &PredefinedMenuItem::select_all(app, None)?,
        ],
    )?;

    let mut app_items: Vec<MenuItem<tauri::Wry>> = Vec::with_capacity(APP_TOOLS.len());
    for spec in APP_TOOLS {
        let id = format!("app-{}", spec.slug);
        app_items.push(MenuItem::with_id(app, id, spec.title, true, None::<&str>)?);
    }
    let app_refs: Vec<&dyn tauri::menu::IsMenuItem<tauri::Wry>> = app_items
        .iter()
        .map(|m| m as &dyn tauri::menu::IsMenuItem<tauri::Wry>)
        .collect();
    let apps_menu = Submenu::with_items(app, "Apps", true, &app_refs)?;

    let view_menu = Submenu::with_items(
        app,
        "View",
        true,
        &[
            &MenuItem::with_id(app, "cmd-k-view", "Command Bar (⌘K)", true, Some("CmdOrCtrl+K"))?,
            &PredefinedMenuItem::separator(app)?,
            &MenuItem::with_id(app, "theme-system", "Theme: Follow System", true, None::<&str>)?,
            &MenuItem::with_id(app, "theme-light", "Theme: Light (Celadon)", true, None::<&str>)?,
            &MenuItem::with_id(app, "theme-dark", "Theme: Dark (Ink & Paper)", true, None::<&str>)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::fullscreen(app, None)?,
        ],
    )?;

    let window_menu = Submenu::with_items(
        app,
        "Window",
        true,
        &[
            &PredefinedMenuItem::minimize(app, None)?,
            &PredefinedMenuItem::maximize(app, None)?,
            &PredefinedMenuItem::close_window(app, None)?,
        ],
    )?;

    Menu::with_items(app, &[&file_menu, &edit_menu, &apps_menu, &view_menu, &window_menu])
}

fn main() {
    let base_url = resolve_node_base_url();
    let initial_geoms = load_window_geoms();

    tauri::Builder::default()
        .manage(DesktopState {
            base_url: base_url.clone(),
            window_geoms: Mutex::new(initial_geoms),
        })
        .setup(move |app| {
            let menu = build_native_menu(app.handle())?;
            app.set_menu(menu)?;

            if let Some(main_win) = app.get_webview_window("main") {
                if let Ok(url) = Url::parse(&base_url) {
                    let _ = main_win.navigate(url);
                }
            }
            Ok(())
        })
        .on_menu_event(|app, event| {
            let id = event.id().as_ref();
            if id == "cmd-k" || id == "cmd-k-view" {
                trigger_cmd_k(app);
                return;
            }
            if id == "theme-system" {
                set_theme_all_windows(app, "system");
                return;
            }
            if id == "theme-light" {
                set_theme_all_windows(app, "light");
                return;
            }
            if id == "theme-dark" {
                set_theme_all_windows(app, "dark");
                return;
            }
            if let Some(slug) = id.strip_prefix("app-") {
                if let Some(spec) = APP_TOOLS.iter().find(|t| t.slug == slug) {
                    open_or_focus_tool_window(app, spec);
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running TinCan Mesh OS desktop");
}
