import assert from "node:assert/strict";
import { test } from "node:test";
import { routesRemountKey, shouldMountRoutes } from "./coreGate.ts";

test("Tauri boot: do not mount routes until Core is healthy", () => {
  assert.equal(shouldMountRoutes(true, true, false), false);
});

test("Tauri: mount routes once Core is connected (even if still clearing boot)", () => {
  assert.equal(shouldMountRoutes(true, true, true), true);
  assert.equal(shouldMountRoutes(true, false, true), true);
});

test("Tauri: after boot timeout with Core offline, still mount routes (banner + settings)", () => {
  assert.equal(shouldMountRoutes(true, false, false), true);
});

test("Browser preview: always mount routes", () => {
  assert.equal(shouldMountRoutes(false, false, false), true);
  assert.equal(shouldMountRoutes(false, true, false), true);
});

test("remount key changes when Core comes online so pages refetch", () => {
  assert.notEqual(routesRemountKey(false), routesRemountKey(true));
});
