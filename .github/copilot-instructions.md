# Copilot instructions for Homebase backend

Purpose: give AI coding agents the minimal, high-value context to be productive in this repository.

- Architecture (quick):
  - Nuxt 4 fullstack app. Frontend lives in `app/` and uses `app.vue`, `app.config.ts`, and `app/tailwind.css`.
  - Server bundle and server-only code live under `server/` (Nitro server routes are in `server/api`).
  - Database layer uses Drizzle ORM with Postgres. Connection is in `server/db/conn.ts` and exported from `server/db/index.ts`.
  - Auth is implemented with Better Auth. Main config: `server/lib/auth.ts`. Auth API entrypoint: `server/api/auth/[...all].ts`.

- Important files to open first:
  - `nuxt.config.ts` — shows path aliases and Nitro alias `#server`.
  - `server/lib/auth.ts` — central Better Auth configuration and plugins.
  - `server/db/conn.ts` and `drizzle.config.ts` — DB connection and migration settings.
  - `package.json` — primary scripts you should call (dev, build, db:* and `auth:generate`).

- Developer workflows (commands):
  - Start dev server: `pnpm dev` (runs `nuxt dev`).
  - Build for production: `pnpm build` then `pnpm preview` to run the built server.
  - Drizzle migrations and tools: `pnpm db:migrate`, `pnpm db:push`, `pnpm db:generate`, `pnpm db:studio`.
  - Regenerate Better Auth schema: `pnpm auth:generate` (reads `server/lib/auth.ts` and writes schema into `server/db/schema/auth.ts`).

- Project-specific conventions and patterns:
  - Server-only imports and utilities use the `#server` alias (configured in `nuxt.config.ts`). Prefer `#server/*` for server imports.
  - Database uses a single `pg` Pool in `server/db/conn.ts` and exports `db` (the Drizzle instance). Modifications should reuse this instance.
  - Authentication configuration in `server/lib/auth.ts` is authoritative — changing auth features (providers, plugins) usually requires re-running `pnpm auth:generate` and updating DB schema/migrations.
  - API routes are standard Nitro server routes under `server/api`. Use `defineEventHandler` and `toWebRequest(event)` when wiring 3rd-party handlers (see `server/api/auth/[...all].ts`).

- Integration points and external deps to be aware of:
  - Better Auth (+passkey, +expo plugin) — configured in `server/lib/auth.ts` and wired into `server/api/auth/[...all].ts`.
  - Drizzle ORM + `drizzle-kit` for migrations defined in `drizzle.config.ts` (DB URL read from `DATABASE_URL`).
  - `pg` + `Pool` is used for Postgres connections.
  - Tailwind + daisyUI are used for styling (`app/tailwind.css`).

- Editing guidance for common tasks (concise):
  - Add a server API route: create `server/api/<name>.ts`, use `defineEventHandler` and import server helpers via `#server`.
  - Add DB models / schema: put schema files in `server/db/schema/` and update migrations via `pnpm db:generate` or `pnpm db:migrate` depending on the change.
  - Change auth behavior: edit `server/lib/auth.ts`, then run `pnpm auth:generate` and add/inspect resulting files in `server/db/schema` and migrations.

- Testing / debugging notes:
  - Dev server includes Nitro; use the browser for frontend debugging and check server logs for API errors.
  - The repo includes `@nuxt/test-utils` for unit/integration tests – explore `test` scripts if/when added.

- Safety & security reminders for the agent:
  - Do NOT commit secrets. `DATABASE_URL` and other secrets must come from env vars. The repo expects `process.env.DATABASE_URL`.
  - When modifying SQL/ORM code use parameterized Drizzle APIs — do not inline user input into SQL strings.

- Where to ask a human / open questions to clarify:
  - Which Postgres URL is expected for local development (connection string / docker compose). If absent, ask for local DB instructions.
  - Whether `server/lib/auth.ts` changes should be accompanied by a migration policy (auto vs reviewed).

If anything here is unclear or you want more examples (API route template, migration example, or auth plugin change), ask and I'll expand the file with concrete code snippets.
