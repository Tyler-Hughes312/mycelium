export const LINKS = {
  /** Latest Desktop release page (0.1.1). */
  releases: "https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.1-desktop",
  /** Direct macOS Apple Silicon DMG for Download CTAs. */
  desktopDownload:
    "https://github.com/Tyler-Hughes312/mycelium/releases/download/v0.1.1-desktop/Mycelium_0.1.1_aarch64.dmg",
  github: "https://github.com/Tyler-Hughes312/mycelium",
  desktopInstallDoc:
    "https://github.com/Tyler-Hughes312/mycelium/blob/main/docs/DESKTOP-INSTALL.md",
} as const;

export const HERO = {
  brand: "Mycelium",
  headline: "Stop re-explaining your codebase in every chat",
  sub: "Index your repos and notes once on your machine. When Cursor or Claude asks, Mycelium returns the symbols, commits, and decisions that matter — so you spend fewer tokens and get answers that match how you already ship.",
  proof: "Fewer tokens · Better reuse · Private on localhost",
  primaryCta: "Download Desktop",
  secondaryCta: "See what it does",
} as const;

export const OUTCOMES_INTRO = {
  eyebrow: "Why it exists",
  headline: "Stop pasting half the repo into every chat",
  sub: "Mycelium indexes your code and decisions locally, then feeds agents only the slices that matter — so you burn fewer tokens, get sharper answers, and reuse work you already shipped.",
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
    body: "Hybrid search + focus packets pull symbols, commits, and notes that match the question — instead of dumping giant files and hoping the model finds the needle.",
  },
  {
    id: "quality",
    title: "Outputs grounded in your real codebase",
    body: "Agents cite patterns you already use: naming, error handling, rate-limit fixes, vault decisions. Less generic advice, more “how we do it here.”",
  },
  {
    id: "reuse",
    title: "Reuse code across projects",
    body: "Import multiple repos into Library. When you start something new, Search still finds the auth helper, fixture, or ADR you wrote last quarter.",
  },
  {
    id: "scale",
    title: "Stay oriented in large codebases",
    body: "Index once, recall by meaning and structure. Navigate monorepos and long histories without re-explaining the architecture in every thread.",
  },
  {
    id: "local",
    title: "Private by default",
    body: "Indexes and Thinking Vault live on your machine. Desktop and MCP start Core locally — nothing leaves localhost unless you opt in.",
  },
];

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
    body: "Import repos so Search can reuse old code across projects.",
    wash: "magenta",
  },
  {
    id: "index",
    title: "Index",
    body: "Local embeddings and indexes under ~/.mycelium.",
    wash: "sage",
  },
  {
    id: "search",
    title: "Search",
    body: "Hybrid recall over symbols, commits, files, and vault notes.",
    wash: "violet",
  },
  {
    id: "vault",
    title: "Vault",
    body: "Markdown second brain with buckets and wikilinks.",
    wash: "teal",
  },
  {
    id: "agents",
    title: "Agents",
    body: "MCP tools for Cursor / Claude — Core starts with your IDE on demand.",
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
    body: "Add a repo in Library, Index it, then Search — agents call Mycelium through MCP on demand.",
  },
] as const;

export const IMPACT_INTRO = {
  eyebrow: "Impact",
  headline: "Fewer tokens. Sharper code. Same machine.",
  sub: "Mycelium retrieves the slices that matter — so agents spend context on answers, not haystacks, and your conventions travel with every recall.",
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
    body: "Focus and search packets beat dumping whole files — spend the window on the answer, not the haystack.",
  },
  {
    id: "packet",
    stat: "1 packet",
    title: "Per question",
    body: "Symbols, commits, and notes that match the ask — not half the repo pasted into every chat.",
  },
  {
    id: "reuse",
    stat: "Library-wide",
    title: "Reuse without re-paste",
    body: "Find the auth helper, fixture, or ADR you already shipped in another imported repo.",
  },
  {
    id: "grounded",
    stat: "Your patterns",
    title: "Grounded outputs",
    body: "Answers match naming, error handling, and decisions you already use — less generic advice.",
  },
];

export const IMPACT_DISCLAIMER =
  "Illustrative of typical sessions — your Desktop app will track live savings once telemetry ships.";
