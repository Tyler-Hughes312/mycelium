export function getPrefersReducedMotion(): boolean {
  const matchMedia: typeof window.matchMedia | undefined =
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia.bind(window)
      : typeof globalThis.matchMedia === "function"
        ? globalThis.matchMedia.bind(globalThis)
        : undefined;

  if (!matchMedia) {
    return false;
  }
  return matchMedia("(prefers-reduced-motion: reduce)").matches;
}
