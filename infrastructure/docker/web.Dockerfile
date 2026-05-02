FROM node:20-alpine AS base
RUN corepack enable && corepack prepare pnpm@9.12.0 --activate
WORKDIR /app

# Development stage
FROM base AS dev
COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/
COPY packages/types/package.json ./packages/types/
RUN pnpm install --frozen-lockfile
COPY apps/web/ ./apps/web/
COPY packages/types/ ./packages/types/
WORKDIR /app/apps/web
EXPOSE 3000
CMD ["pnpm", "dev"]

# Build stage
FROM base AS builder
COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/
COPY packages/types/package.json ./packages/types/
RUN pnpm install --frozen-lockfile
COPY apps/web/ ./apps/web/
COPY packages/types/ ./packages/types/
WORKDIR /app/apps/web
RUN pnpm build

# Production stage
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./.next/static
COPY --from=builder /app/apps/web/public ./public
EXPOSE 3000
ENV NODE_ENV=production
CMD ["node", "server.js"]
