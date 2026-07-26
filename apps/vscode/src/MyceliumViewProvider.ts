import * as vscode from "vscode";
import type { FocusPacket } from "./coreClient";
import type { EditorFocus } from "./focusContext";

type PanelState = {
  connected: boolean;
  statusLabel: string;
  focus?: EditorFocus;
  packet?: FocusPacket;
  error?: string;
};

export class MyceliumViewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "mycelium.sidePanel";

  private view?: vscode.WebviewView;
  private state: PanelState = {
    connected: false,
    statusLabel: "Core · Connecting…",
  };

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly onMessage: (msg: { type: string; [k: string]: unknown }) => void,
  ) {}

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    this.view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, "media")],
    };

    const cssUri = webviewView.webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "panel.css"),
    );

    webviewView.webview.html = this.getHtml(cssUri.toString());
    webviewView.webview.onDidReceiveMessage((msg) => {
      if (msg && typeof msg.type === "string") {
        this.onMessage(msg as { type: string; [k: string]: unknown });
      }
    });

    this.pushState();
  }

  setConnection(connected: boolean, label: string) {
    this.state.connected = connected;
    this.state.statusLabel = label;
    this.pushState();
  }

  setFocusPayload(input: {
    focus?: EditorFocus;
    packet?: FocusPacket;
    error?: string;
  }) {
    this.state.focus = input.focus;
    this.state.packet = input.packet;
    this.state.error = input.error;
    this.pushState();
  }

  private pushState() {
    void this.view?.webview.postMessage({ type: "state", state: this.state });
  }

  private getHtml(cssHref: string): string {
    const csp = [
      "default-src 'none'",
      `style-src ${this.view?.webview.cspSource ?? ""} 'unsafe-inline' https://fonts.googleapis.com`,
      "font-src https://fonts.gstatic.com",
      "img-src data:",
      "script-src 'unsafe-inline'",
    ].join("; ");

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="${csp}" />
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
          <span id="dot" class="dot off"></span>
          <span id="statusLabel" class="mono-sm muted">Core · Connecting…</span>
        </div>
      </div>
      <div class="local-only">
        <span class="material-symbols-outlined icon-sm">lock</span>
        <span class="mono-sm muted">Local only</span>
      </div>
      <div class="actions">
        <button type="button" id="retryBtn" class="ghost">Retry</button>
        <button type="button" id="refreshBtn" class="ghost">Refresh</button>
      </div>
    </div>

    <div class="focus">
      <div class="mono-sm muted uppercase mb">Current Focus</div>
      <div id="focusPath" class="body-md">—</div>
      <div id="focusSymbol" class="mono secondary mt"></div>
    </div>

    <div id="error" class="error hidden"></div>

    <div id="results" class="results">
      <div class="rail"></div>
      <div id="cards"></div>
    </div>

    <div class="footer">
      <button type="button" id="newNoteBtn" class="cta">
        <span class="material-symbols-outlined icon-md">edit_document</span>
        New note
      </button>
    </div>
  </aside>
  <script>
    const vscode = acquireVsCodeApi();
    const dot = document.getElementById('dot');
    const statusLabel = document.getElementById('statusLabel');
    const focusPath = document.getElementById('focusPath');
    const focusSymbol = document.getElementById('focusSymbol');
    const errorEl = document.getElementById('error');
    const cards = document.getElementById('cards');

    document.getElementById('retryBtn').addEventListener('click', () => {
      vscode.postMessage({ type: 'retry' });
    });
    document.getElementById('refreshBtn').addEventListener('click', () => {
      vscode.postMessage({ type: 'refresh' });
    });
    document.getElementById('newNoteBtn').addEventListener('click', () => {
      vscode.postMessage({ type: 'newNote' });
    });

    function esc(s) {
      return String(s ?? '').replace(/[&<>"']/g, (c) => ({
        '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
      })[c]);
    }

    function render(state) {
      const connected = !!state.connected;
      dot.className = 'dot' + (connected ? '' : ' off');
      statusLabel.textContent = state.statusLabel || (connected ? 'Core · Connected' : 'Core · Offline');
      statusLabel.className = 'mono-sm ' + (connected ? 'primary' : 'muted');

      if (state.focus) {
        focusPath.textContent = state.focus.relPath || '—';
        focusSymbol.textContent = state.focus.symbol
          ? state.focus.symbol + '()'
          : 'line ' + state.focus.line;
      } else {
        focusPath.textContent = '—';
        focusSymbol.textContent = '';
      }

      if (state.error) {
        errorEl.textContent = state.error;
        errorEl.classList.remove('hidden');
      } else {
        errorEl.classList.add('hidden');
        errorEl.textContent = '';
      }

      const results = (state.packet && state.packet.results) || [];
      if (!results.length) {
        cards.innerHTML = '<p class="empty mono-sm muted">No context yet. Index the workspace in Mycelium Desktop, then refresh.</p>';
        return;
      }
      cards.innerHTML = results.map((r, i) => {
        const kind = esc(r.kind || 'Symbol');
        const title = esc(r.title || '');
        const snippet = esc(r.snippet || '');
        const path = esc(r.path || '');
        return \`<article class="card" data-index="\${i}" role="button" tabindex="0">
          <div class="card-meta">
            <span class="chip">\${kind}</span>
          </div>
          <div class="body-sm mb-1">\${title}</div>
          <div class="body-sm muted mb-1 truncate">\${snippet}</div>
          <div class="mono-sm muted truncate">\${path}</div>
        </article>\`;
      }).join('');

      cards.querySelectorAll('.card').forEach((el) => {
        el.addEventListener('click', () => {
          const idx = Number(el.getAttribute('data-index'));
          vscode.postMessage({ type: 'openResult', index: idx });
        });
      });
    }

    window.addEventListener('message', (event) => {
      const msg = event.data;
      if (msg && msg.type === 'state') render(msg.state);
    });
  </script>
</body>
</html>`;
  }
}

export type { PanelState };
