import * as vscode from "vscode";
import { MyceliumViewProvider } from "./MyceliumViewProvider";

export function activate(context: vscode.ExtensionContext) {
  const provider = new MyceliumViewProvider(context.extensionUri);

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
  );
}

export function deactivate() {}
