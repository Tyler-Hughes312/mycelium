/** Native folder picker (Tauri) with graceful web fallback. */

export function isTauriShell(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

/** Open a directory chooser. Returns an absolute path, or null if cancelled / unavailable. */
export async function pickDirectory(title = "Choose a git repository"): Promise<string | null> {
  if (!isTauriShell()) return null;
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({
      directory: true,
      multiple: false,
      title,
    });
    if (typeof selected === "string" && selected.trim()) return selected;
    return null;
  } catch {
    return null;
  }
}

/**
 * Open a local file at an optional line (Cursor → VS Code → system default).
 * Resolves relative paths against workspaceRoot when provided.
 */
export async function openLocalFile(
  path: string,
  opts?: { line?: number | null; workspaceRoot?: string | null },
): Promise<boolean> {
  const raw = path.trim();
  if (!raw || raw.startsWith("sha:")) return false;

  let abs = raw;
  if (!raw.startsWith("/") && !/^[A-Za-z]:[\\/]/.test(raw)) {
    const root = (opts?.workspaceRoot || "").replace(/\/$/, "");
    if (root) abs = `${root}/${raw.replace(/^\.\//, "")}`;
  }

  const line =
    typeof opts?.line === "number" && Number.isFinite(opts.line) && opts.line > 0
      ? Math.floor(opts.line)
      : undefined;

  if (isTauriShell()) {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("open_path_at_line", { path: abs, line: line ?? null });
      return true;
    } catch {
      return false;
    }
  }

  // Browser / vite-only: best-effort Cursor/VS Code URI (may be blocked)
  try {
    const uri = line
      ? `cursor://file/${abs}:${line}`
      : `cursor://file/${abs}`;
    window.open(uri, "_blank", "noopener,noreferrer");
    return true;
  } catch {
    return false;
  }
}
