import assert from "node:assert/strict";
import { test } from "node:test";

test("getPrefersReducedMotion reads matchMedia when available", async () => {
  const { getPrefersReducedMotion } = await import("./prefersReducedMotion.ts");
  globalThis.matchMedia = (query) => ({
    matches: query.includes("prefers-reduced-motion"),
    media: query,
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() {
      return false;
    },
    onchange: null,
    addListener() {},
    removeListener() {},
  });
  assert.equal(getPrefersReducedMotion(), true);
});

test("getPrefersReducedMotion returns false when matchMedia is unavailable", async () => {
  const { getPrefersReducedMotion } = await import("./prefersReducedMotion.ts");
  const original = globalThis.matchMedia;
  // @ts-expect-error intentionally removing for test
  delete globalThis.matchMedia;
  assert.equal(getPrefersReducedMotion(), false);
  globalThis.matchMedia = original;
});
