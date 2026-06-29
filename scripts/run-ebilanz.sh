#!/usr/bin/env bash
#
# run-ebilanz.sh — start/stop the eBilanz app components DIRECTLY (no pm2).
#
# Each component is launched as a detached background process; its PID is written
# to run/<name>.pid and its merged stdout+stderr to logs/<name>.log. stop/restart/
# status/logs all work off those files — a self-contained replacement for pm2.
#
# Components (see COMPONENTS below):
#   backend   FastAPI/uvicorn  (backend/.venv/bin/uvicorn app.main:app)  -> :$PORT
#   frontend  Vue 3 / Vite dev (npm run dev)                             -> :5173
#
# HOST/PORT for the backend are read from the repo-root .env (defaults 0.0.0.0:8000).
# SQLite auto-initialises on backend startup; Odoo is a remote data source (no local
# process). An ERiC sidecar slots in later as one more COMPONENTS entry.
#
# Usage:
#   scripts/run-ebilanz.sh <action> [target] [options]
#
# Actions:
#   start      Launch component(s) in the background (skips any already running)
#   stop       Stop component(s): SIGTERM, then SIGKILL after a grace period
#   restart    stop + start
#   status     Show each component: running/stopped/stale + whether its port listens
#   logs       Tail a component log (default last 40 lines; -f to follow)
#
# Targets (default for start/stop/restart/status = both):
#       --frontend           Frontend only
#       --backend            Backend only
#   -a, --all                All components
#
# Options:
#       --lines <n>          Number of log lines to show        (logs only)
#   -f, --follow             Follow the log (tail -f)           (logs only)
#   -d, --dry-run            Print what would run, change nothing
#   -h, --help               Show this help
#
# Examples:
#   scripts/run-ebilanz.sh start                  # backend + frontend
#   scripts/run-ebilanz.sh start --backend        # backend only
#   scripts/run-ebilanz.sh status
#   scripts/run-ebilanz.sh logs --backend --lines 100
#   scripts/run-ebilanz.sh logs --frontend -f
#   scripts/run-ebilanz.sh restart --frontend
#   scripts/run-ebilanz.sh stop

set -euo pipefail

# --- Resolve repo root from this script's location (works from any CWD) ---------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_DIR="$ROOT_DIR/run"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$RUN_DIR" "$LOG_DIR"

die() { echo "Error: $*" >&2; exit 1; }

usage() {
  sed -n '3,/^set -euo/p' "$0" | sed '$d' | sed 's/^#\{0,1\} \{0,1\}//'
  exit "${1:-0}"
}

# --- Read HOST/PORT from .env (fallback to backend/app/config.py defaults) -------
read_env() {  # read_env KEY DEFAULT
  local v=""
  [[ -f "$ROOT_DIR/.env" ]] && v=$(grep -E "^$1=" "$ROOT_DIR/.env" | tail -n1 | cut -d= -f2- | tr -d '"' | tr -d "'" | xargs 2>/dev/null || true)
  echo "${v:-$2}"
}
HOST="$(read_env HOST 0.0.0.0)"
PORT="$(read_env PORT 8000)"
FE_PORT=5173   # vite dev server (web-UI/vite.config.ts)

# --- Component registry ----------------------------------------------------------
# Parallel arrays keyed by component name. To add the ERiC sidecar later, append a
# name plus its CWD / command / port entry.
COMPONENTS=(backend frontend)

comp_cwd() {  case "$1" in
  backend)  echo "$ROOT_DIR/backend" ;;
  frontend) echo "$ROOT_DIR/web-UI" ;;
esac; }

comp_cmd() {  case "$1" in
  backend)  echo ".venv/bin/uvicorn app.main:app --host $HOST --port $PORT" ;;
  frontend) echo "npm run dev" ;;
esac; }

comp_port() { case "$1" in
  backend)  echo "$PORT" ;;
  frontend) echo "$FE_PORT" ;;
esac; }

pidfile() { echo "$RUN_DIR/$1.pid"; }
logfile() { echo "$LOG_DIR/$1.log"; }

# --- Process-state helpers -------------------------------------------------------

# is_running NAME -> 0 if a live process is tracked, else 1. Echoes the PID on success.
is_running() {
  local pf; pf=$(pidfile "$1"); [[ -f "$pf" ]] || return 1
  local pid; pid=$(cat "$pf" 2>/dev/null || true)
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && { echo "$pid"; return 0; }
  return 1
}

# port_listening PORT -> 0 if something is bound to it.
port_listening() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -q ":$1[[:space:]]"
  else
    (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && { exec 3>&- 3<&-; return 0; } || return 1
  fi
}

# Pre-flight per component; dies with an actionable hint.
preflight() {
  case "$1" in
    backend)
      [[ -x "$ROOT_DIR/backend/.venv/bin/uvicorn" ]] || \
        die "backend venv missing. Create it: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
      ;;
    frontend)
      command -v npm >/dev/null 2>&1 || die "npm not on PATH (needed for the frontend)."
      command -v node >/dev/null 2>&1 || die "node not on PATH (needed for the frontend)."
      if [[ ! -d "$ROOT_DIR/web-UI/node_modules" ]]; then
        if [[ -n "$DRY_RUN" ]]; then
          echo "DRY-RUN: (cd web-UI && npm install)"
        else
          echo "frontend: node_modules missing -> running npm install ..."
          ( cd "$ROOT_DIR/web-UI" && npm install )
        fi
      fi
      ;;
  esac
}

# --- Actions per component -------------------------------------------------------

start_one() {
  local name=$1 cwd cmd pf log pid
  cwd=$(comp_cwd "$name"); cmd=$(comp_cmd "$name"); pf=$(pidfile "$name"); log=$(logfile "$name")
  if pid=$(is_running "$name"); then
    echo "$name: already running (pid $pid) — skipping."
    return 0
  fi
  preflight "$name"
  if [[ -n "$DRY_RUN" ]]; then
    echo "DRY-RUN: (cd $cwd && setsid $cmd >$log 2>&1 </dev/null &)  # pid -> $pf"
    return 0
  fi
  # setsid puts the command in its own session/process group so stop_one can kill
  # the whole group (e.g. npm AND its child vite). setsid may fork, so $! would be
  # the transient wrapper, not the daemon — instead the session leader records its
  # OWN $$ (which exec preserves) into the pidfile; that pid == the process-group id.
  rm -f "$pf"
  ( cd "$cwd" && setsid bash -c "echo \$\$ > '$pf'; exec $cmd" >"$log" 2>&1 </dev/null & )
  for _ in $(seq 1 20); do [[ -s "$pf" ]] && break; sleep 0.1; done
  if pid=$(is_running "$name"); then
    echo "$name: started (pid $pid) -> http://${HOST/0.0.0.0/10.0.99.1}:$(comp_port "$name")  | log: $log"
  else
    echo "$name: FAILED to start — see $log" >&2
    tail -n 15 "$log" >&2 2>/dev/null || true
    return 1
  fi
}

stop_one() {
  local name=$1 pf pid i
  pf=$(pidfile "$name")
  if ! pid=$(is_running "$name"); then
    [[ -f "$pf" ]] && { rm -f "$pf"; echo "$name: not running (cleared stale pidfile)."; } \
                   || echo "$name: not running."
    return 0
  fi
  if [[ -n "$DRY_RUN" ]]; then
    echo "DRY-RUN: kill -TERM -$pid  # whole process group of $name"
    return 0
  fi
  # Negative PID -> signal the entire process group (leader + children like vite).
  kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  for i in $(seq 1 20); do            # up to ~10s grace
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.5
  done
  if kill -0 "$pid" 2>/dev/null; then
    echo "$name: did not exit — sending SIGKILL."
    kill -KILL -"$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$pf"
  echo "$name: stopped (was pid $pid)."
}

status_one() {
  local name=$1 pid state port pstate
  port=$(comp_port "$name")
  if pid=$(is_running "$name"); then
    state="running (pid $pid)"
  elif [[ -f "$(pidfile "$name")" ]]; then
    state="STOPPED (stale pidfile)"
  else
    state="stopped"
  fi
  port_listening "$port" && pstate="listening" || pstate="-"
  printf '%-10s %-26s port %-6s %s\n' "$name" "$state" "$port" "$pstate"
}

tail_one() {
  local name=$1 log; log=$(logfile "$name")
  [[ -f "$log" ]] || die "no log for '$name' yet ($log)."
  if [[ -n "$FOLLOW" ]]; then
    echo "===== following $log (Ctrl-C to stop) ====="
    tail -n "${LINES:-40}" -f "$log"
  else
    echo "===== $log (last ${LINES:-40}) ====="
    tail -n "${LINES:-40}" "$log"
  fi
}

# --- Arg parsing -----------------------------------------------------------------
[[ $# -ge 1 ]] || usage 1
action=$1; shift

FE="" BE="" ALL="" LINES="" FOLLOW="" DRY_RUN=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --frontend)   FE=1; shift ;;
    --backend)    BE=1; shift ;;
    -a|--all)     ALL=1; shift ;;
    --lines)      LINES=${2:?missing value for $1}; shift 2 ;;
    -f|--follow)  FOLLOW=1; shift ;;
    -d|--dry-run) DRY_RUN=1; shift ;;
    -h|--help)    usage 0 ;;
    -*)           die "Unknown option: $1 (try --help)" ;;
    *)            die "Unexpected argument: $1 (try --help)" ;;
  esac
done

# Resolve the target component list (default: all).
targets=()
if   [[ -n "$ALL" ]]; then targets=("${COMPONENTS[@]}")
elif [[ -n "$FE" && -n "$BE" ]]; then targets=(backend frontend)
elif [[ -n "$FE" ]]; then targets=(frontend)
elif [[ -n "$BE" ]]; then targets=(backend)
else targets=("${COMPONENTS[@]}")
fi

case "$action" in
  start)
    for c in "${targets[@]}"; do start_one "$c"; done
    ;;
  stop)
    for c in "${targets[@]}"; do stop_one "$c"; done
    ;;
  restart)
    for c in "${targets[@]}"; do stop_one "$c"; done
    for c in "${targets[@]}"; do start_one "$c"; done
    ;;
  status|list|ls)
    for c in "${targets[@]}"; do status_one "$c"; done
    ;;
  logs)
    # logs targets a single component; default backend if none given.
    if [[ ${#targets[@]} -ne 1 ]]; then
      [[ -n "$FE" || -n "$BE" ]] || targets=(backend)
      [[ ${#targets[@]} -eq 1 ]] || die "logs needs exactly one target: --frontend or --backend"
    fi
    tail_one "${targets[0]}"
    ;;
  -h|--help|help)
    usage 0
    ;;
  *)
    die "Unknown action: $action (try --help)"
    ;;
esac
