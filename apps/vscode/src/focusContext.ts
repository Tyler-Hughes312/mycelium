import * as path from "path";
import * as vscode from "vscode";
import type { CoreClient, Workspace } from "./coreClient";

export type EditorFocus = {
  workspaceId: string;
  workspacePath: string;
  relPath: string;
  symbol?: string;
  line: number;
  absPath: string;
};

/** Match open folder to a registered Mycelium workspace by absolute path. */
export async function resolveMyceliumWorkspace(
  client: CoreClient,
  folder: vscode.WorkspaceFolder,
): Promise<Workspace | undefined> {
  const workspaces = await client.listWorkspaces();
  const folderPath = path.resolve(folder.uri.fsPath);
  return workspaces.find((w) => {
    const wp = path.resolve(w.path);
    return folderPath === wp || folderPath.startsWith(wp + path.sep);
  });
}

export async function getEditorFocus(
  client: CoreClient,
  editor: vscode.TextEditor | undefined,
): Promise<EditorFocus | { error: string }> {
  if (!editor) {
    return { error: "No active editor" };
  }
  const folder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
  if (!folder) {
    return { error: "File is outside a VS Code workspace folder" };
  }
  let ws: Workspace | undefined;
  try {
    ws = await resolveMyceliumWorkspace(client, folder);
  } catch (err) {
    return {
      error: err instanceof Error ? err.message : "Failed to list workspaces",
    };
  }
  if (!ws) {
    return {
      error: `Folder not registered in Mycelium. Add it in Desktop Library: ${folder.uri.fsPath}`,
    };
  }

  const absPath = editor.document.uri.fsPath;
  const relPath = path.relative(ws.path, absPath).split(path.sep).join("/");
  const line = editor.selection.active.line + 1;
  const symbol = await enclosingSymbolName(editor, line);

  return {
    workspaceId: ws.id,
    workspacePath: ws.path,
    relPath,
    symbol,
    line,
    absPath,
  };
}

async function enclosingSymbolName(
  editor: vscode.TextEditor,
  line: number,
): Promise<string | undefined> {
  try {
    const symbols = await vscode.commands.executeCommand<
      vscode.DocumentSymbol[] | undefined
    >("vscode.executeDocumentSymbolProvider", editor.document.uri);
    if (symbols?.length) {
      const hit = findEnclosing(symbols, line - 1);
      if (hit) return hit.name;
    }
  } catch {
    // fall through
  }
  const word = editor.document.getWordRangeAtPosition(editor.selection.active);
  if (word) {
    return editor.document.getText(word);
  }
  return undefined;
}

function findEnclosing(
  symbols: vscode.DocumentSymbol[],
  zeroLine: number,
): vscode.DocumentSymbol | undefined {
  let best: vscode.DocumentSymbol | undefined;
  const walk = (list: vscode.DocumentSymbol[]) => {
    for (const s of list) {
      if (s.range.start.line <= zeroLine && s.range.end.line >= zeroLine) {
        best = s;
        if (s.children?.length) walk(s.children);
      }
    }
  };
  walk(symbols);
  return best;
}
