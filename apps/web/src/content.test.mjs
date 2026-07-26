import assert from "node:assert/strict";
import { test } from "node:test";

test("CTA URLs point at official Mycelium repo", async () => {
  const { LINKS } = await import("./content.ts");
  assert.equal(LINKS.releases, "https://github.com/Tyler-Hughes312/mycelium/releases");
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
