export const LINKS = {
  releases: "https://github.com/Tyler-Hughes312/mycelium/releases",
  github: "https://github.com/Tyler-Hughes312/mycelium",
  desktopInstallDoc:
    "https://github.com/Tyler-Hughes312/mycelium/blob/main/docs/DESKTOP-INSTALL.md",
} as const;

export const HERO = {
  brand: "Mycelium",
  headline: "Local-first context layer for AI-heavy developers",
  sub: "Code + Thinking Vault stay on 127.0.0.1. No cloud account required.",
} as const;

export type Capability = {
  id: "library" | "index" | "search" | "vault" | "agents";
  title: string;
  body: string;
  wash: "magenta" | "sage" | "violet" | "teal" | "slate";
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
    body: "MCP tools for Cursor / Claude against Core on :8787.",
    wash: "slate",
  },
];

export const SETUP_STEPS = [
  {
    n: 1,
    title: "Install",
    body: "Clone the repo and run ./scripts/install.sh",
  },
  {
    n: 2,
    title: "Run",
    body: "./scripts/dev.sh — Core :8787 + Desktop — or open packaged Desktop from Releases",
  },
  {
    n: 3,
    title: "Use",
    body: "Library → Index → Search. Try the dogfood fixture from the README.",
  },
] as const;
