#!/usr/bin/env bash
# Copy the page into worker/public and deploy it as a Cloudflare Worker at mpts.ie/games/grainy.
# Needs Cloudflare credentials: run `npx wrangler login` once, or set CLOUDFLARE_API_TOKEN.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf public && mkdir public
cp ../index.html ../ref.webp public/
npx --yes wrangler@latest deploy "$@"
