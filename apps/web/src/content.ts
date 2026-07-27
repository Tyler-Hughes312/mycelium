export const LINKS = {
  /** Release notes / other platforms. */
  releases: "https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.1-desktop",
  /**
   * Same-origin Desktop DMG — fetched into public/downloads at build time
   * so Download CTAs save the file instead of opening GitHub.
   */
  desktopDownload: "/downloads/Mycelium_0.1.1_aarch64.dmg",
  desktopFilename: "Mycelium_0.1.1_aarch64.dmg",
  github: "https://github.com/Tyler-Hughes312/mycelium",
  desktopInstallDoc:
    "https://github.com/Tyler-Hughes312/mycelium/blob/main/docs/DESKTOP-INSTALL.md",
} as const;

export const HERO = {
  brand: "Mycelium",
  headline: "Stop burning tokens re-reading your codebase every session",
  sub: "Mycelium indexes your repos locally — symbols, files, commits — and returns a precise context packet when Cursor or Claude asks. Not a chat journal: an efficient path into the code you already have.",
  proof: "Fewer tokens · Faster than re-grep · Private on localhost",
  primaryCta: "Download Desktop",
  secondaryCta: "See how it saves tokens",
} as const;

export const OUTCOMES_INTRO = {
  eyebrow: "Why it exists",
  headline: "Indexed code retrieval — not another memory diary",
  sub: "Agent “memory vaults” remember conversations. Mycelium indexes your project structure and returns the slices that answer the question — so you can show tokens saved, not vague persistence.",
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
    body: "Hybrid search + focus packets pull the matching symbols, commits, and notes — instead of re-pasting giant files or re-searching the tree every chat.",
  },
  {
    id: "quality",
    title: "A precise path into your real codebase",
    body: "Retrieval is optimized for project structure and files: naming, error handling, rate-limit fixes you already shipped — not a transcript of last week’s chat.",
  },
  {
    id: "reuse",
    title: "Reuse code across projects",
    body: "Import multiple repos into Library. When you start something new, Search still finds the auth helper, fixture, or ADR you wrote last quarter — without grepping by hand.",
  },
  {
    id: "scale",
    title: "Stay oriented in large codebases",
    body: "Index once, recall by meaning and structure. Navigate monorepos and long histories without re-explaining the architecture in every thread.",
  },
  {
    id: "local",
    title: "Private by default",
    body: "Indexes (and an optional Thinking Vault for decisions) live on your machine. Desktop and MCP start Core locally — nothing leaves localhost unless you opt in.",
  },
];

/** Hardcoded compare strip in Outcomes.tsx — keep copy centralized. */
export const OUTCOMES_COMPARE = {
  withoutTitle: "Without Mycelium",
  withTitle: "With Mycelium",
  without: [
    "Re-paste the same files every session",
    "Burn tokens re-reading half the repo",
    "Re-grep for last month’s fix in another tree",
    "Generic answers that ignore your conventions",
  ],
  with: [
    "One indexed path to the relevant slice",
    "Tight packets — measure tokens saved",
    "Reuse symbols and commits across Library",
    "Outputs grounded in how you already ship",
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
    body: "Hybrid recall: a precise packet of symbols, commits, and files that match the question.",
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
    body: "MCP tools for Cursor / Claude — agents get indexed context on demand instead of re-scanning the tree.",
    wash: "amber",
  },
];

export const SETUP_STEPS = [
  {
    n: 1,
    title: "Install",
    body: "Download Desktop 0.1.1 from Releases, or add the Mycelium MCP server in Cursor / Claude.",
  },
  {
    n: 2,
    title: "Open",
    body: "Launch Desktop or connect MCP — Core starts automatically on localhost.",
  },
  {
    n: 3,
    title: "Use",
    body: "Add a repo in Library, Index it, then Search — agents pull tight context packets through MCP instead of re-pasting files.",
  },
] as const;

export const IMPACT_INTRO = {
  eyebrow: "Impact",
  headline: "Token efficiency you can measure",
  sub: "The pitch is concrete: stop burning context on re-reads and greps. Mycelium serves an indexed packet — Desktop Impact tracks estimated tokens saved vs dumping matched files.",
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
    stat: "1 packet",
    title: "Per question",
    body: "Symbols, commits, and files that match the ask — a precise path into the repo, not half of it pasted again.",
  },
  {
    id: "reuse",
    stat: "Library-wide",
    title: "Skip the re-grep",
    body: "Find the auth helper, fixture, or ADR you already shipped in another imported repo — without hunting the tree.",
  },
  {
    id: "grounded",
    stat: "Your patterns",
    title: "Codebase-grounded answers",
    body: "Retrieval is about project structure and shipped code — stronger to demo than vague “the agent remembers.”",
  },
];

export const IMPACT_DISCLAIMER =
  "The ~60–90% figure is illustrative of typical focus/search vs paste-the-file sessions. Desktop Impact tracks live estimated savings locally (served packet vs baseline file dump) — not LLM billing accuracy, and not yet a published customer benchmark.";
