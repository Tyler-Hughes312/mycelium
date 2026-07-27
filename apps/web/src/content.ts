export const LINKS = {
  /** Release notes / other platforms. */
  releases: "https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.3-desktop",
  /**
   * Same-origin Desktop DMG — fetched into public/downloads at build time
   * so Download CTAs save the file instead of opening GitHub.
   */
  desktopDownload: "/downloads/Mycelium_0.1.3_aarch64.dmg",
  desktopFilename: "Mycelium_0.1.3_aarch64.dmg",
  github: "https://github.com/Tyler-Hughes312/mycelium",
  desktopInstallDoc:
    "https://github.com/Tyler-Hughes312/mycelium/blob/main/docs/DESKTOP-INSTALL.md",
} as const;

export const HERO = {
  brand: "Mycelium",
  headline: "Stop burning tokens re-reading your codebase every session",
  sub: "Mycelium indexes your repos locally and returns a precise context packet — then a one-line receipt so agents cite what they already retrieved instead of dumping the tree again. Open a project and it starts indexing; before you build, it checks other repos for prior art. Not a chat journal: an efficient path into the code you already have.",
  proof: "Open → index · Reuse check · Context receipts · Grounded Impact · Private on localhost",
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
    title: "Open a repo — indexing starts",
    body: "With Desktop (or Core) running, Cursor’s workspaceOpen hook registers the git repo and starts a full index. session_start still returns the compact prefs + open-file packet when agents begin work.",
  },
  {
    id: "reuse",
    title: "Reuse check before you build",
    body: "mycelium_reuse_check searches all indexed repos for similar prior art. If something matches, agents ask: adapt that code, or build new — so you reuse what you already shipped.",
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
    "Rebuild features you already shipped elsewhere",
    "Generic answers that ignore your conventions",
  ],
  with: [
    "Open folder → register + index automatically",
    "Tight packets + one-line receipts",
    "reuse_check asks adapt vs greenfield",
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
    body: "Local embeddings of symbols, files, and commits under ~/.mycelium — built for code, not transcripts. Open a Cursor workspace and indexing can start automatically.",
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
    body: "MCP: session_start, reuse_check, change/debug context, receipts — agents get relevant packets and ask before rebuilding prior art.",
    wash: "amber",
  },
];

export const SETUP_STEPS = [
  {
    n: 1,
    title: "Install",
    body: "Download Desktop 0.1.3 from Releases, or add the Mycelium MCP server in Cursor / Claude.",
  },
  {
    n: 2,
    title: "Open",
    body: "Launch Desktop so Core is on localhost. Open any git repo in Cursor — it can auto-register and start indexing.",
  },
  {
    n: 3,
    title: "Use",
    body: "Agents call session_start, then reuse_check before plan/build, then change_context or search — cite the receipt instead of re-pasting files. Watch grounded % on Desktop Impact.",
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
    title: "Skip the rebuild",
    body: "reuse_check finds the auth helper, fixture, or flow you already shipped in another indexed repo — then asks adapt vs greenfield.",
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
