import * as vscode from "vscode";

export class MyceliumViewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "mycelium.sidePanel";

  constructor(private readonly extensionUri: vscode.Uri) {}

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, "media")],
    };

    const cssUri = webviewView.webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "panel.css"),
    );

    webviewView.webview.html = this.getHtml(cssUri.toString());
  }

  private getHtml(cssHref: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="${cssHref}" />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0..1,0&display=swap" rel="stylesheet" />
</head>
<body>
  <aside class="panel">
    <div class="header">
      <div class="header-row">
        <h2 class="label-caps">Mycelium Context</h2>
        <div class="status">
          <span class="dot"></span>
          <span class="mono-sm primary">Core · Connected</span>
        </div>
      </div>
      <div class="local-only">
        <span class="material-symbols-outlined icon-sm">lock</span>
        <span class="mono-sm muted">Local only</span>
      </div>
    </div>

    <div class="focus">
      <div class="mono-sm muted uppercase mb">Current Focus</div>
      <div class="body-md">src/auth/session.ts</div>
      <div class="mono secondary mt">authenticate()</div>
    </div>

    <div class="results">
      <div class="rail"></div>

      <article class="card">
        <div class="card-meta">
          <span class="chip">Commit</span>
          <span class="mono-sm muted">2 hours ago</span>
        </div>
        <div class="body-sm mb-1">Fixed edge case where expired tokens returned invalid session type instead of null.</div>
        <div class="mono-sm muted truncate">auth/session.ts</div>
      </article>

      <article class="card">
        <div class="card-meta">
          <span class="chip">Note</span>
          <span class="mono-sm muted">Yesterday</span>
        </div>
        <div class="body-sm mb-1">Architecture Decision: We are moving all session validation to edge workers. Local fallback required.</div>
        <div class="mono-sm muted truncate">docs/arch/auth-flow.md</div>
      </article>

      <article class="card">
        <div class="card-meta">
          <span class="chip">Symbol</span>
        </div>
        <div class="mono mb-1">verifySessionToken()</div>
        <div class="body-sm muted mb-1">Similar validation pattern used in middleware.</div>
        <div class="mono-sm muted truncate">src/middleware/auth.ts</div>
      </article>

      <article class="card">
        <div class="card-meta">
          <span class="chip">File</span>
        </div>
        <div class="body-sm mb-1">Contains the <span class="mono">Session</span> type definition referenced here.</div>
        <div class="mono-sm muted truncate">types/auth.d.ts</div>
      </article>

      <article class="card">
        <div class="card-meta">
          <span class="chip">Commit</span>
          <span class="mono-sm muted">last week</span>
        </div>
        <div class="body-sm mb-1">Initial implementation of local-only auth fallback mechanism.</div>
        <div class="mono-sm muted truncate">src/auth/local.ts</div>
      </article>
    </div>

    <div class="footer">
      <button type="button" class="cta">
        <span class="material-symbols-outlined icon-md">edit_document</span>
        New note
      </button>
    </div>
  </aside>
</body>
</html>`;
  }
}
