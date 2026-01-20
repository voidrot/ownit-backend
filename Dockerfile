FROM node:lts-trixie-slim AS build

WORKDIR /app

RUN corepack enable && corepack prepare --activate pnpm

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm build

FROM node:lts-trixie-slim AS final

USER node
WORKDIR /app

COPY --from=build --chown=node:node /app/.output /app/.output

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]