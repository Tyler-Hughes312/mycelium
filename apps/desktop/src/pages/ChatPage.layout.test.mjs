import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "ChatPage.tsx"), "utf8");

test("Chat page includes honesty empty-state copy about Cursor", () => {
  assert.match(
    source,
    /Long threads stay in Mycelium Chat; Cursor/,
    "Empty state should state Cursor's window is unchanged",
  );
});

test("Chat page exposes Context used panel", () => {
  assert.match(
    source,
    /Context used/,
    "Chat should show collapsible Context used panel",
  );
});

test("Chat page wires thread client APIs", () => {
  assert.match(source, /createThread/);
  assert.match(source, /sendThreadMessage/);
  assert.match(source, /handoffThread/);
});
