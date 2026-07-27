import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "ImpactPage.tsx"), "utf8");

test("Impact page centers constrained content like other desktop pages", () => {
  assert.match(
    source,
    /max-w-4xl[^\n]*mx-auto|mx-auto[^\n]*max-w-4xl/,
    "Impact content shell should use max-w-4xl mx-auto so it is not left-pinned",
  );
});

test("Impact page defaults to all-time range so $ saved is visible", () => {
  assert.match(
    source,
    /useState<Range>\("all"\)/,
    "Default Impact range should be all (today often looks like $0)",
  );
});
