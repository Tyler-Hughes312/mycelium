import assert from "node:assert/strict";
import { test } from "node:test";

test("CTA Download is same-origin DMG (not GitHub navigation)", async () => {
  const { LINKS } = await import("./content.ts");
  assert.equal(LINKS.desktopDownload, "/downloads/Mycelium_0.1.1_aarch64.dmg");
  assert.equal(LINKS.desktopFilename, "Mycelium_0.1.1_aarch64.dmg");
  assert.equal(
    LINKS.releases,
    "https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.1-desktop",
  );
  assert.equal(LINKS.github, "https://github.com/Tyler-Hughes312/mycelium");
  assert.equal(LINKS.desktopInstallDoc, "https://github.com/Tyler-Hughes312/mycelium/blob/main/docs/DESKTOP-INSTALL.md");
});

test("capabilities cover five surfaces in order", async () => {
  const { CAPABILITIES } = await import("./content.ts");
  assert.deepEqual(
    CAPABILITIES.map((c) => c.id),
    ["library", "index", "search", "vault", "agents"],
  );
});

test("outcomes cover token savings reuse and scale", async () => {
  const { OUTCOMES } = await import("./content.ts");
  assert.deepEqual(
    OUTCOMES.map((o) => o.id),
    ["tokens", "quality", "reuse", "scale", "local"],
  );
  const blob = OUTCOMES.map((o) => `${o.title} ${o.body}`).join(" ").toLowerCase();
  assert.match(blob, /token/);
  assert.match(blob, /reuse/);
  assert.match(blob, /large|monorepo/);
});

test("setup never tells users to run shell installers", async () => {
  const { SETUP_STEPS, CAPABILITIES } = await import("./content.ts");
  const blob = [...SETUP_STEPS, ...CAPABILITIES]
    .map((s) => ("body" in s ? `${"title" in s ? s.title : ""} ${s.body}` : ""))
    .join("\n")
    .toLowerCase();
  assert.equal(blob.includes("install.sh"), false);
  assert.equal(blob.includes("dev.sh"), false);
  assert.equal(blob.includes("./scripts"), false);
});

test("impact metrics cover tokens packet reuse grounded with illustrative disclaimer", async () => {
  const { IMPACT_INTRO, IMPACT_METRICS, IMPACT_DISCLAIMER } = await import(
    "./content.ts"
  );
  assert.equal(IMPACT_INTRO.eyebrow, "Impact");
  assert.match(IMPACT_INTRO.headline.toLowerCase(), /token|fewer|sharper/);
  assert.deepEqual(
    IMPACT_METRICS.map((m) => m.id),
    ["tokens", "packet", "reuse", "grounded"],
  );
  for (const m of IMPACT_METRICS) {
    assert.ok(m.stat.length > 0, `${m.id} needs a display stat`);
    assert.ok(m.title.length > 0, `${m.id} needs a title`);
    assert.ok(m.body.length > 0, `${m.id} needs a body`);
  }
  const blob = IMPACT_METRICS.map((m) => `${m.stat} ${m.title} ${m.body}`)
    .join(" ")
    .toLowerCase();
  assert.match(blob, /token/);
  assert.match(IMPACT_DISCLAIMER.toLowerCase(), /illustrative/);
});
