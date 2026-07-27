import assert from "node:assert/strict";
import { test } from "node:test";

test("CTA Download is same-origin DMG (not GitHub navigation)", async () => {
  const { LINKS } = await import("./content.ts");
  assert.equal(LINKS.desktopDownload, "/downloads/Mycelium_0.1.3_aarch64.dmg");
  assert.equal(LINKS.desktopFilename, "Mycelium_0.1.3_aarch64.dmg");
  assert.equal(
    LINKS.releases,
    "https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.3-desktop",
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
  const { OUTCOMES, OUTCOMES_INTRO, OUTCOMES_COMPARE } = await import(
    "./content.ts"
  );
  assert.deepEqual(
    OUTCOMES.map((o) => o.id),
    ["tokens", "quality", "reuse", "scale", "local"],
  );
  const blob = [
    OUTCOMES_INTRO.headline,
    OUTCOMES_INTRO.sub,
    ...OUTCOMES.map((o) => `${o.title} ${o.body}`),
    ...OUTCOMES_COMPARE.without,
    ...OUTCOMES_COMPARE.with,
  ]
    .join(" ")
    .toLowerCase();
  assert.match(blob, /token/);
  assert.match(blob, /reuse|index|receipt|bootstrap|open/);
  assert.match(blob, /receipt|grounded|session|reuse/);
  assert.match(blob, /memory|journal|diary|chat/);
  assert.match(blob, /codebase|code|repo|symbol/);
  assert.match(blob, /reuse_check|reuse check|prior art|adapt/);
});

test("hero pitches token efficiency over chat memory", async () => {
  const { HERO } = await import("./content.ts");
  const blob = `${HERO.headline} ${HERO.sub} ${HERO.proof}`.toLowerCase();
  assert.match(blob, /token/);
  assert.match(blob, /index/);
  assert.match(blob, /not a chat journal|journal/);
  assert.match(blob, /reuse|open/);
});

test("vault capability is secondary to code indexing", async () => {
  const { CAPABILITIES } = await import("./content.ts");
  const vault = CAPABILITIES.find((c) => c.id === "vault");
  assert.ok(vault);
  assert.match(vault.body.toLowerCase(), /optional|secondary/);
  const agents = CAPABILITIES.find((c) => c.id === "agents");
  assert.ok(agents);
  assert.match(agents.body.toLowerCase(), /reuse_check|reuse/);
});

test("setup mentions auto-index and reuse without shell scripts", async () => {
  const { SETUP_STEPS, CAPABILITIES } = await import("./content.ts");
  const blob = [...SETUP_STEPS, ...CAPABILITIES]
    .map((s) => ("body" in s ? `${"title" in s ? s.title : ""} ${s.body}` : ""))
    .join("\n")
    .toLowerCase();
  assert.match(blob, /index/);
  assert.match(blob, /reuse_check|reuse/);
  assert.equal(blob.includes("install.sh"), false);
  assert.equal(blob.includes("dev.sh"), false);
  assert.equal(blob.includes("./scripts"), false);
});

test("impact metrics cover tokens packet reuse grounded with illustrative disclaimer", async () => {
  const { IMPACT_INTRO, IMPACT_METRICS, IMPACT_DISCLAIMER } = await import(
    "./content.ts"
  );
  assert.equal(IMPACT_INTRO.eyebrow, "Impact");
  assert.match(IMPACT_INTRO.headline.toLowerCase(), /token|fewer|measure/);
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
  assert.match(blob, /reuse/);
  assert.match(IMPACT_DISCLAIMER.toLowerCase(), /illustrative/);
  assert.match(IMPACT_DISCLAIMER.toLowerCase(), /benchmark|desktop impact/);
});
