#!/usr/bin/env bash
set -uo pipefail

APP_ROOT="${FINANU_APP_ROOT:-/opt/finanU}"
BACKEND_DIR="${FINANU_BACKEND_DIR:-$APP_ROOT/backend}"
PYTHON_BIN="${FINANU_PYTHON_BIN:-$BACKEND_DIR/.venv/bin/python}"
LOG_DIR="${FINANU_LOG_DIR:-/var/log/finanu}"

MARKET_LOG="$LOG_DIR/marketdata_refresh.log"
RSS_LOG="$LOG_DIR/rss_news_import.log"

timestamp() {
  date --iso-8601=seconds
}

cd "$BACKEND_DIR"

status=0

{
  echo "[$(timestamp)] Starting market data refresh"
  if "$PYTHON_BIN" manage.py refresh_market_data_llm; then
    echo "[$(timestamp)] Finished market data refresh"
  else
    market_status=$?
    status=$market_status
    echo "[$(timestamp)] Market data refresh failed with exit code $market_status"
  fi
} >> "$MARKET_LOG" 2>&1

{
  echo "[$(timestamp)] Starting RSS news import"
  if "$PYTHON_BIN" scripts/import_rss_news.py --llm; then
    echo "[$(timestamp)] Finished RSS news import"
  else
    rss_status=$?
    status=$rss_status
    echo "[$(timestamp)] RSS news import failed with exit code $rss_status"
  fi
} >> "$RSS_LOG" 2>&1

exit "$status"
