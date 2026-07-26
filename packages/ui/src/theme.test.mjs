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

test("Soft Electric primary replaces hypha green", () => {
  assert.equal(varValue("--mycelium-primary"), "#6ec8ff");
  assert.equal(varValue("--mycelium-accent-hypha"), "#6ec8ff");
  assert.notEqual(varValue("--mycelium-primary"), "#9cd2ba");
});

test("muted/dim accents and warn secondary exist", () => {
  assert.equal(varValue("--mycelium-accent-muted"), "#3a7fa8");
  assert.equal(varValue("--mycelium-accent-dim"), "#1a3a4d");
  assert.equal(varValue("--mycelium-secondary"), "#e5c276");
});
