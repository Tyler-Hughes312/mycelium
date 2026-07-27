#!/usr/bin/env node
/**
 * Fetch the Desktop DMG into public/downloads so site CTAs are same-origin
 * downloads (no GitHub navigation). Runs during `npm run build`.
 */
import { createWriteStream, existsSync, mkdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { pipeline } from "node:stream/promises";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");

const FILENAME = "Mycelium_0.1.3_aarch64.dmg";
const SOURCE =
  "https://github.com/Tyler-Hughes312/mycelium/releases/download/v0.1.3-desktop/Mycelium_0.1.3_aarch64.dmg";
const DEST_DIR = join(ROOT, "public", "downloads");
const DEST = join(DEST_DIR, FILENAME);

mkdirSync(DEST_DIR, { recursive: true });

if (existsSync(DEST) && statSync(DEST).size > 1_000_000) {
  console.log(`==> Desktop DMG already present (${statSync(DEST).size} bytes)`);
  process.exit(0);
}

console.log(`==> Fetching Desktop DMG → public/downloads/${FILENAME}`);
const res = await fetch(SOURCE, { redirect: "follow" });
if (!res.ok || !res.body) {
  console.error(`Failed to download DMG: ${res.status} ${res.statusText}`);
  process.exit(1);
}

await pipeline(res.body, createWriteStream(DEST));
console.log(`==> Wrote ${statSync(DEST).size} bytes`);
