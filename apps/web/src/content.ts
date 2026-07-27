export const LINKS = {
  /** Release notes / other platforms. */
  releases: "https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.2-desktop",
  /**
   * Same-origin Desktop DMG — fetched into public/downloads at build time
   * so Download CTAs save the file instead of opening GitHub.
   */
  desktopDownload: "/downloads/Mycelium_0.1.2_aarch64.dmg",
  desktopFilename: "Mycelium_0.1.2_aarch64.dmg",
  github: "https://github.com/Tyler-Hughes312/mycelium",
  desktopInstallDoc:
    "https://github.com/Tyler-Hughes312/mycelium/blob/main/docs/DESKTOP-INSTALL.md",
} as const;

export const HERO = {
  brand: "Mycelium",
  headline: "Stop burning tokens re-reading your codebase every session",
  sub: "Mycelium indexes your repos locally and returns a precise context packet — then a one-line receipt so agents cite what they already retrieved instead of dumping the tree again. Not a chat journal: an efficient path into the code you already have.",
  proof: "Tight packets · Context receipts · Grounded Impact · Private on localhost",
  primaryCta: "Download Desktop",
  secondaryCta: "See how it saves tokens",
} as const;

export const OUTCOMES_INTRO = {
  eyebrow: "Why it exists",
  headline: "Proof-carrying retrieval — not another memory diary",
  sub: "Agent “memory vaults” remember conversations. Mycelium indexes your project, serves only the slices that answer the question, and attaches a compact receipt — so agents stay grounded without stuffing more context into the window.",
} as const;

export type Outcome = {
  id: string;
  title: string;
  body: string;
};

export const OUTCOMES: Outcome[] = [
  {
    id: "tokens",
    title: "Spend tokens on the answer, not the haystack",
    body: "Hybrid search + focus packets pull matching symbols, commits, and notes — instead of re-pasting giant files or re-searching the tree every chat.",
  },
  {
    id: "quality",
    title: "Session bootstrap for agents",
    body: "mycelium_session_start auto-registers the repo, optionally indexes, and returns a compact prefs + open-file packet — not a vault dump or chat transcript.",
  },
  {
    id: "reuse",
    title: "Task-shaped context, not raw search lists",
    body: "change_context and debug_context return ranked hits for implement vs fix — so agents pick the right tool instead of grepping forever.",
  },
  {
    id: "scale",
    title: "Cite a receipt — don’t re-dump the repo",
    body: "Every recall ends with a one-line receipt (paths/ids only). verify_receipt checks staleness without pasting bodies. Impact tracks grounded %.",
  },
  {
    id: "local",
    title: "Private by default",
    body: "Indexes, receipts, and an optional Thinking Vault live on your machine. Desktop and MCP start Core locally — nothing leaves localhost unless you opt in.",
  },
];

/** Hardcoded compare strip in Outcomes.tsx — keep copy centralized. */
export const OUTCOMES_COMPARE = {
  withoutTitle: "Without Mycelium",
  withTitle: "With Mycelium",
  without: [
    "Re-paste the same files every session",
    "Burn tokens re-reading half the repo",
    "Agents grep blindly with no shared world model",
    "Generic answers that ignore your conventions",
  ],
  with: [
    "One indexed path to the relevant slice",
    "Tight packets + one-line receipts",
    "Session bootstrap + task-shaped tools",
    "Impact: tokens saved and grounded %",
  ],
} as const;

export type Capability = {
  id: "library" | "index" | "search" | "vault" | "agents";
  title: string;
  body: string;
  wash: "magenta" | "sage" | "violet" | "teal" | "amber";
};

export const CAPABILITIES: Capability[] = [
  {
    id: "library",
    title: "Library",
    body: "Import repos so retrieval can reuse real code across projects — not chat history.",
    wash: "magenta",
  },
  {
    id: "index",
    title: "Index",
    body: "Local embeddings of symbols, files, and commits under ~/.mycelium — built for code, not transcripts.",
    wash: "sage",
  },
  {
    id: "search",
    title: "Search",
    body: "Hybrid recall: a precise packet of symbols, commits, and files — plus a compact receipt to cite.",
    wash: "violet",
  },
  {
    id: "vault",
    title: "Vault",
    body: "Optional markdown notes for decisions and ADRs — secondary to code indexing, not the product.",
    wash: "teal",
  },
  {
    id: "agents",
    title: "Agents",
    body: "MCP: session_start, change/debug context, receipts — agents get relevant packets, not another window dump.",
    wash: "amber",
  },
];

export const SETUP_STEPS = [
  {
    n: 1,
    title: "Install",
    body: "Download Desktop 0.1.2 from Releases, or add the Mycelium MCP server in Cursor / Claude.",
  },
  {
    n: 2,
    title: "Open",
    body: "Launch Desktop or connect MCP — Core starts automatically on localhost.",
  },
  {
    n: 3,
    title: "Use",
    body: "Call session_start on your repo, then change_context or search — cite the receipt instead of re-pasting files. Watch grounded % on Desktop Impact.",
  },
] as const;

export const IMPACT_INTRO = {
  eyebrow: "Impact",
  headline: "Token efficiency you can measure — and prove",
  sub: "Stop burning context on re-reads and greps. Mycelium serves an indexed packet with a receipt. Desktop Impact tracks estimated tokens saved and how often recalls were grounded.",
} as const;

export type ImpactMetric = {
  id: string;
  stat: string;
  title: string;
  body: string;
};

export const IMPACT_METRICS: ImpactMetric[] = [
  {
    id: "tokens",
    stat: "~60–90%",
    title: "Fewer context tokens",
    body: "Illustrative vs dumping whole files: focus/search packets spend the window on the answer, not the haystack.",
  },
  {
    id: "packet",
    stat: "1 receipt",
    title: "Per recall",
    body: "A one-line attestation of which hits were served — cite it instead of pasting bodies again.",
  },
  {
    id: "reuse",
    stat: "Library-wide",
    title: "Skip the re-grep",
    body: "Find the auth helper, fixture, or ADR you already shipped in another imported repo — without hunting the tree.",
  },
  {
    id: "grounded",
    stat: "Grounded %",
    title: "Receipt-backed recalls",
    body: "Desktop Impact shows how often agents used Mycelium packets with a receipt vs flying blind.",
  },
];

export const IMPACT_DISCLAIMER =
  "The ~60–90% figure is illustrative of typical focus/search vs paste-the-file sessions. Desktop Impact tracks live estimated savings and grounded (receipt) rate locally — not LLM billing accuracy, and not yet a published customer benchmark.";
