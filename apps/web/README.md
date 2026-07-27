# mycelium-web

Marketing site for Mycelium — local-first **indexed codebase retrieval** for AI-heavy developers (token efficiency, not chat-memory vaults). Live at [getmycelium.vercel.app](https://getmycelium.vercel.app). See [docs/POSITIONING.md](../../docs/POSITIONING.md).

## Develop

```bash
npm install
npm run dev
```

## Test

```bash
npm test
```

## Build

```bash
npm run build
```

Outputs to `dist/`. Preview locally with `npm run preview` (Vite default `:4173`).

## Deploy (Vercel)

Deploy this app independently from the monorepo. In the Vercel project:

| Setting | Value |
|---|---|
| **Root Directory** | `apps/web` |
| **Framework Preset** | Vite |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` (default) |
| **Environment Variables** | none (fully static) |

`vercel.json` mirrors build/output/framework for CLI deploys. No SPA rewrites are required for this single-page landing.

Production alias: `https://getmycelium.vercel.app`
