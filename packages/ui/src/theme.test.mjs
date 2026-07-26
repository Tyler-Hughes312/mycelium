import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(join(root, "theme.css"), "utf8");

function varValue(name) {
  const re = new RegExp(`${name}:\\s*([^;]+);`);
  const m = css.match(re);
  assert.ok(m, `missing ${name}`);
  return m[1].trim().toLowerCase();
}

test("logo E slate + teal primary", () => {
  assert.equal(varValue("--mycelium-primary"), "#00d1b2");
  assert.equal(varValue("--mycelium-accent-hypha"), "#00d1b2");
  assert.equal(varValue("--mycelium-slate"), "#3a3f44");
});

test("slate surfaces and teal dim accents", () => {
  assert.equal(varValue("--mycelium-accent-muted"), "#1a9a86");
  assert.equal(varValue("--mycelium-accent-dim"), "#0a2e2a");
  assert.equal(varValue("--mycelium-secondary"), "#c5ccd1");
});
