//! Mycelium Desktop — Tauri shell with bundled Core sidecar lifecycle.

use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use tauri::{AppHandle, Manager, RunEvent, State};

struct CoreProcess {
  child: Mutex<Option<Child>>,
  /// True when this app spawned Core (so we should stop it on exit).
  owned: Mutex<bool>,
}

fn core_binary(app: &AppHandle) -> Result<PathBuf, String> {
  let resource_dir = app
    .path()
    .resource_dir()
    .map_err(|e| format!("resource_dir: {e}"))?;
  let candidates = [
    // Packaged: tauri copies bundle.resources under Contents/Resources/
    resource_dir.join("resources/mycelium-core/mycelium-core"),
    resource_dir.join("resources/mycelium-core/mycelium-core.exe"),
    resource_dir.join("mycelium-core/mycelium-core"),
    resource_dir.join("mycelium-core/mycelium-core.exe"),
    // Dev: resources may live next to the crate when running `tauri dev`
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
      .join("resources/mycelium-core/mycelium-core"),
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
      .join("resources/mycelium-core/mycelium-core.exe"),
  ];
  for path in &candidates {
    if path.is_file() {
      return Ok(path.clone());
    }
  }
  Err(format!(
    "mycelium-core binary not found under {} (tried resources/mycelium-core/…)",
    resource_dir.display()
  ))
}

fn core_healthy() -> bool {
  match ureq::get("http://127.0.0.1:8787/health")
    .timeout(Duration::from_millis(800))
    .call()
  {
    Ok(resp) => (200..300).contains(&resp.status()),
    Err(_) => false,
  }
}

fn wait_until_healthy(timeout: Duration) -> bool {
  let start = std::time::Instant::now();
  while start.elapsed() < timeout {
    if core_healthy() {
      return true;
    }
    thread::sleep(Duration::from_millis(250));
  }
  core_healthy()
}

fn spawn_core(app: &AppHandle, state: &CoreProcess) -> Result<(), String> {
  if core_healthy() {
    *state.owned.lock().map_err(|e| e.to_string())? = false;
    return Ok(());
  }

  let bin = core_binary(app)?;
  let workdir = bin
    .parent()
    .ok_or_else(|| "core binary has no parent dir".to_string())?
    .to_path_buf();

  let mut cmd = Command::new(&bin);
  cmd.current_dir(&workdir)
    .args(["--host", "127.0.0.1", "--port", "8787"])
    .stdin(Stdio::null())
    .stdout(Stdio::null())
    .stderr(Stdio::null());

  let child = cmd
    .spawn()
    .map_err(|e| format!("failed to spawn {}: {e}", bin.display()))?;

  *state.child.lock().map_err(|e| e.to_string())? = Some(child);
  *state.owned.lock().map_err(|e| e.to_string())? = true;

  if !wait_until_healthy(Duration::from_secs(45)) {
    return Err(
      "Core sidecar started but /health did not become ready in time. See ~/.mycelium/logs/"
        .into(),
    );
  }
  Ok(())
}

fn stop_owned_core(state: &CoreProcess) {
  let owned = state.owned.lock().map(|g| *g).unwrap_or(false);
  if !owned {
    return;
  }
  if let Ok(mut guard) = state.child.lock() {
    if let Some(mut child) = guard.take() {
      let _ = child.kill();
      let _ = child.wait();
    }
  }
}

/// Leave Core running after the Desktop quits so MCP / VS Code keep working.
/// Owned children are intentionally not killed on Exit.
#[tauri::command]
fn restart_core(app: AppHandle, state: State<'_, CoreProcess>) -> Result<(), String> {
  // Only kill if we own a live child; otherwise just ensure something is healthy.
  let should_kill = {
    let owned = *state.owned.lock().map_err(|e| e.to_string())?;
    let has_child = state
      .child
      .lock()
      .map_err(|e| e.to_string())?
      .as_mut()
      .map(|c| c.try_wait().ok().flatten().is_none())
      .unwrap_or(false);
    owned && has_child
  };
  if should_kill {
    stop_owned_core(&state);
    thread::sleep(Duration::from_millis(400));
  }
  spawn_core(&app, &state)
}

#[tauri::command]
fn core_status() -> bool {
  core_healthy()
}

/// Open a local file in Cursor / VS Code at an optional line, else system default.
#[tauri::command]
fn open_path_at_line(path: String, line: Option<u32>) -> Result<(), String> {
  let path_buf = PathBuf::from(&path);
  if !path_buf.exists() {
    return Err(format!("Path not found: {path}"));
  }
  let line_n = line.unwrap_or(1).max(1);
  let goto = format!("{}:{line_n}", path_buf.display());

  let try_spawn = |program: &str, args: &[&str]| -> bool {
    Command::new(program)
      .args(args)
      .stdout(Stdio::null())
      .stderr(Stdio::null())
      .spawn()
      .is_ok()
  };

  if try_spawn("cursor", &["--goto", &goto]) {
    return Ok(());
  }
  if try_spawn("code", &["--goto", &goto]) {
    return Ok(());
  }

  #[cfg(target_os = "macos")]
  {
    let cursor_uri = format!("cursor://file/{}:{}", path_buf.display(), line_n);
    if try_spawn("open", &[&cursor_uri]) {
      return Ok(());
    }
    let vscode_uri = format!("vscode://file/{}:{}", path_buf.display(), line_n);
    if try_spawn("open", &[&vscode_uri]) {
      return Ok(());
    }
    if try_spawn("open", &[path_buf.to_str().unwrap_or(path.as_str())]) {
      return Ok(());
    }
  }

  #[cfg(target_os = "windows")]
  {
    if try_spawn("cmd", &["/C", "start", "", path_buf.to_str().unwrap_or(path.as_str())]) {
      return Ok(());
    }
  }

  #[cfg(all(unix, not(target_os = "macos")))]
  {
    if try_spawn("xdg-open", &[path_buf.to_str().unwrap_or(path.as_str())]) {
      return Ok(());
    }
  }

  Err(format!("Could not open {path}"))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_dialog::init())
    .manage(CoreProcess {
      child: Mutex::new(None),
      owned: Mutex::new(false),
    })
    .invoke_handler(tauri::generate_handler![
      restart_core,
      core_status,
      open_path_at_line
    ])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      let handle = app.handle().clone();
      let state = app.state::<CoreProcess>();
      // Spawn Core before the window is useful; errors surface via UI Retry.
      if let Err(err) = spawn_core(&handle, &state) {
        log::error!("Core sidecar: {err}");
      }
      Ok(())
    })
    .build(tauri::generate_context!())
    .expect("error while building Mycelium")
    .run(|_app_handle, event| {
      if let RunEvent::Exit = event {
        // Do not kill Core — MCP and other local clients keep using :8787.
        log::info!("Desktop exiting; leaving Core on 127.0.0.1:8787 if running");
      }
    });
}
