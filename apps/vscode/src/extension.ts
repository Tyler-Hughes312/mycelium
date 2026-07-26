import * as path from "path";
import * as vscode from "vscode";
import { CoreClient, type FocusResult } from "./coreClient";
import { getEditorFocus } from "./focusContext";
import { MyceliumViewProvider } from "./MyceliumViewProvider";

let client: CoreClient;
let provider: MyceliumViewProvider;
let statusBar: vscode.StatusBarItem;
let lastResults: FocusResult[] = [];
let pollTimer: ReturnType<typeof setInterval> | undefined;
let refreshTimer: ReturnType<typeof setTimeout> | undefined;

export function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration("mycelium");
  const baseUrl = config.get<string>("coreUrl") ?? "http://127.0.0.1:8787";
  client = new CoreClient(baseUrl);

  statusBar = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    100,
  );
  statusBar.command = "mycelium.retryConnection";
  statusBar.text = "$(sync~spin) Mycelium";
  statusBar.tooltip = "Mycelium Core connection — click to retry";
  statusBar.show();
  context.subscriptions.push(statusBar);

  provider = new MyceliumViewProvider(context.extensionUri, (msg) => {
    void handlePanelMessage(msg);
  });

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      MyceliumViewProvider.viewType,
      provider,
    ),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("mycelium.openPanel", async () => {
      await vscode.commands.executeCommand("mycelium.sidePanel.focus");
    }),
    vscode.commands.registerCommand("mycelium.retryConnection", async () => {
      await checkHealth();
      await refreshFocus();
    }),
    vscode.commands.registerCommand("mycelium.refreshContext", async () => {
      await refreshFocus();
    }),
    vscode.commands.registerCommand("mycelium.newNote", async () => {
      await createNoteFromFocus();
    }),
  );

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor(() => {
      scheduleRefresh();
    }),
    vscode.window.onDidChangeTextEditorSelection(() => {
      scheduleRefresh(600);
    }),
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("mycelium.coreUrl")) {
        const url =
          vscode.workspace.getConfiguration("mycelium").get<string>("coreUrl") ??
          "http://127.0.0.1:8787";
        client.setBaseUrl(url);
        void checkHealth();
      }
    }),
  );

  void checkHealth();
  void refreshFocus();
  pollTimer = setInterval(() => {
    void checkHealth();
  }, 5000);
  context.subscriptions.push({
    dispose: () => {
      if (pollTimer) clearInterval(pollTimer);
      if (refreshTimer) clearTimeout(refreshTimer);
    },
  });
}

export function deactivate() {}

function scheduleRefresh(delayMs = 200) {
  if (refreshTimer) clearTimeout(refreshTimer);
  refreshTimer = setTimeout(() => {
    void refreshFocus();
  }, delayMs);
}

async function checkHealth(): Promise<boolean> {
  try {
    const health = await client.health();
    const ok = health.status === "ok";
    const label = ok
      ? `Core · Connected${health.version ? ` · v${health.version}` : ""}`
      : "Core · Degraded";
    provider.setConnection(ok, label);
    statusBar.text = ok ? "$(check) Mycelium" : "$(warning) Mycelium";
    statusBar.backgroundColor = ok
      ? undefined
      : new vscode.ThemeColor("statusBarItem.warningBackground");
    return ok;
  } catch {
    provider.setConnection(false, "Core · Offline");
    statusBar.text = "$(error) Mycelium";
    statusBar.backgroundColor = new vscode.ThemeColor(
      "statusBarItem.errorBackground",
    );
    return false;
  }
}

async function refreshFocus() {
  const online = await checkHealth();
  if (!online) {
    provider.setFocusPayload({
      error: "Core is offline. Start Core (./scripts/dev.sh) then Retry.",
    });
    lastResults = [];
    return;
  }

  const focus = await getEditorFocus(client, vscode.window.activeTextEditor);
  if ("error" in focus) {
    provider.setFocusPayload({ error: focus.error });
    lastResults = [];
    return;
  }

  try {
    const packet = await client.focus({
      workspace_id: focus.workspaceId,
      path: focus.relPath,
      symbol: focus.symbol,
      line: focus.line,
      limit: 10,
    });
    lastResults = packet.results ?? [];
    provider.setFocusPayload({
      focus,
      packet,
      error: packet.reason === "empty_index" ? packet.message : undefined,
    });
  } catch (err) {
    lastResults = [];
    provider.setFocusPayload({
      focus,
      error: err instanceof Error ? err.message : "Focus query failed",
    });
  }
}

async function createNoteFromFocus() {
  const online = await checkHealth();
  if (!online) {
    void vscode.window.showErrorMessage("Mycelium Core is offline.");
    return;
  }
  const focus = await getEditorFocus(client, vscode.window.activeTextEditor);
  if ("error" in focus) {
    void vscode.window.showErrorMessage(focus.error);
    return;
  }

  const symbol = focus.symbol ?? focus.relPath;
  const title = focus.symbol
    ? `Note: ${focus.symbol}`
    : `Note: ${focus.relPath}`;
  const linkTarget = focus.symbol
    ? `${focus.relPath}#${focus.symbol}`
    : focus.relPath;

  try {
    const note = await client.createNote({
      title,
      body:
        `Captured from editor.\n\nFile: \`${focus.relPath}\`\nLine: ${focus.line}\n`,
      link_symbol: linkTarget,
    });
    void vscode.window.showInformationMessage(
      `Created vault note: ${note.title}`,
    );
    if (note.abs_path) {
      const doc = await vscode.workspace.openTextDocument(note.abs_path);
      await vscode.window.showTextDocument(doc, { preview: true });
    }
    await refreshFocus();
  } catch (err) {
    void vscode.window.showErrorMessage(
      err instanceof Error ? err.message : "Failed to create note",
    );
  }
}

async function openResult(index: number) {
  const result = lastResults[index];
  if (!result) return;

  const kind = (result.kind || "").toLowerCase();
  if (kind === "note") {
    try {
      const id = result.id || result.path.replace(/\.md$/, "");
      const note = await client.getNote(String(id));
      if (note.abs_path) {
        const doc = await vscode.workspace.openTextDocument(note.abs_path);
        await vscode.window.showTextDocument(doc, { preview: true });
        return;
      }
    } catch (err) {
      void vscode.window.showErrorMessage(
        err instanceof Error ? err.message : "Could not open note",
      );
      return;
    }
  }

  if (kind === "commit") {
    void vscode.window.showInformationMessage(
      result.title || result.snippet || "Commit",
    );
    return;
  }

  // Symbol / File / Function / …
  const folder = vscode.workspace.workspaceFolders?.[0];
  const focus = await getEditorFocus(client, vscode.window.activeTextEditor);
  const root =
    "workspacePath" in focus
      ? focus.workspacePath
      : folder?.uri.fsPath;

  if (!root || !result.path) {
    void vscode.window.showWarningMessage("No path to open for this result.");
    return;
  }

  // path may be "file:line" style from meta — prefer plain path
  let rel = result.path;
  let line = 1;
  const lineMatch = /:(\d+)$/.exec(rel);
  if (lineMatch && !rel.includes("sha:")) {
    line = Number(lineMatch[1]);
    rel = rel.slice(0, -lineMatch[0].length);
  }
  // Also check meta for start_line via path chip text
  for (const m of result.meta ?? []) {
    const mline = /:(\d+)$/.exec(m.text);
    if (mline) {
      line = Number(mline[1]);
      rel = m.text.slice(0, -mline[0].length);
      break;
    }
  }

  if (rel.startsWith("sha:")) {
    void vscode.window.showInformationMessage(result.title);
    return;
  }

  const uri = vscode.Uri.file(
    path.isAbsolute(rel) ? rel : path.join(root, rel),
  );
  try {
    const doc = await vscode.workspace.openTextDocument(uri);
    const editor = await vscode.window.showTextDocument(doc, { preview: true });
    const pos = new vscode.Position(Math.max(0, line - 1), 0);
    editor.selection = new vscode.Selection(pos, pos);
    editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
  } catch (err) {
    void vscode.window.showErrorMessage(
      err instanceof Error ? err.message : `Could not open ${rel}`,
    );
  }
}

async function handlePanelMessage(msg: {
  type: string;
  [k: string]: unknown;
}) {
  switch (msg.type) {
    case "retry":
      await checkHealth();
      await refreshFocus();
      break;
    case "refresh":
      await refreshFocus();
      break;
    case "newNote":
      await createNoteFromFocus();
      break;
    case "openResult":
      await openResult(Number(msg.index));
      break;
    default:
      break;
  }
}
