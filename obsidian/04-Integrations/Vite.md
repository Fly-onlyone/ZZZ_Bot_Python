---
tags: [integration]
---

# Vite

> Frontend dev server + production bundler; outputs `frontend/dist/` which Tauri bundles as the WebView source in release builds.

## Used for
- `bun run dev` — dev server on port 3000 with HMR
- `bun run build` — production bundle to `frontend/dist/`
- Env loading: `frontend/.env.development` sets `VITE_BACKEND_URL=http://127.0.0.1:8001` for dev

## Configuration
- Version `vite 7.1.11` (`frontend/package.json`)
- Plugin: `@vitejs/plugin-react ^1.0.7`
- `vite.config.js` defines server port + alias
- `tauri.conf.json` `frontendDist: "../frontend/dist"` and `devUrl: "http://127.0.0.1:3000"`

## Wire-up
- `frontend/vite.config.js` — config
- `frontend/.env.development` — dev backend URL override
- `frontend/src/config/constants.js` — fallback `BACKEND_URL` for production builds

## Auth mode
N/A

## Gotchas
- `.env.development` is only loaded by `bun run dev`, NOT `bun run build` — production falls back to the `BACKEND_URL` constant.

## See also
- [[_index]]
- [[Bun]]
- [[Frontend Constants]]
