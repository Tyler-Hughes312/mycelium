/** When the desktop shell may mount routed pages that hit Core on mount. */

export function shouldMountRoutes(
  inTauri: boolean,
  booting: boolean,
  coreConnected: boolean,
): boolean {
  if (!inTauri) return true;
  if (coreConnected) return true;
  if (booting) return false;
  return true;
}

/** Change this when Core comes online so page mount effects re-run. */
export function routesRemountKey(coreConnected: boolean): string {
  return coreConnected ? "core-up" : "core-down";
}
