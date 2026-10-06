#!/usr/bin/env sh
# Ping health endpoint so Neon / free hosts stay warm. Schedule every 10-14 minutes (cron or platform scheduler).
# Example cron: */12 * * * * /path/to/ops/health_ping.sh
BASE_URL="${HEALTHCHECK_URL:-http://127.0.0.1:8000/api/health}"
curl -fsS -m 15 "$BASE_URL" >/dev/null || exit 1
