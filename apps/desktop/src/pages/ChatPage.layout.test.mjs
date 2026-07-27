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

test("Chat page offers Load older when transcript is truncated", () => {
  assert.match(source, /Load older/);
  assert.match(source, /older[\s\S]*messages are hidden/);
  assert.match(source, /loadOlderTurns/);
});

test("Chat page links to Settings on LLM config errors", () => {
  assert.match(source, /llm_not_configured/);
  assert.match(source, /remote_llm_disabled/);
  assert.match(source, /to="\/settings"/);
  assert.match(source, /Open Settings/);
});

test("Chat empty state offers Create thread CTA", () => {
  assert.match(source, /Create thread/);
  assert.match(source, /pickDefaultWorkspaceId/);
});

test("Chat empty cards use rem max-width not spacing-scale max-w-xl", () => {
  // Custom --spacing-xl is 24px; max-w-xl collapses to that and stacks glyphs.
  assert.match(source, /max-w-\[36rem\]/);
  assert.doesNotMatch(source, /max-w-xl/);
});
