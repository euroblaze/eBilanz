#!/usr/bin/env bash
#
# run-ebilanz.sh — pm2 control wrapper RESTRICTED to the eBilanz namespace.
#
# It only ever touches pm2 processes in the "ebilanz" namespace; any process in
# another namespace is invisible to it and cannot be started, stopped, restarted,
# or deleted through this tool.
#
# Within eBilanz, processes are grouped into two tiers by name:
#   frontend = name contains "frontend"
#   backend  = name contains "backend"
# restart/reload/stop default to BOTH tiers; use --frontend or --backend to
# target one. (delete always needs an explicit target — no implicit "both".)
#
# Usage:
#   scripts/run-ebilanz.sh <action> [options] [-- <app args...>]
#
# Actions:
#   start      Start an eBilanz app (forced into the "ebilanz" namespace)
#   restart    Restart eBilanz apps (default: frontend + backend)
#   reload     Zero-downtime reload (default: frontend + backend)
#   stop       Stop eBilanz apps without removing them (default: both tiers)
#   delete     Stop and remove an eBilanz app (explicit target required)
#   status     Show the eBilanz process list (or details for one app)
#   logs       Tail logs for an eBilanz app (or a snapshot of all)
#
# Options:
#   -n, --name <name>        Target a single app by pm2 name
#       --frontend           Target the frontend tier only
#       --backend            Target the backend tier only
#   -a, --all                Target ALL eBilanz apps (every tier + untiered)
#   -s, --script <file>      Entry file/command to run        (start only)
#   -i, --instances <n>      Number of cluster instances, or "max" (start)
#   -e, --env <name>         Environment to use (e.g. production)
#   -w, --watch              Restart on file changes          (start only)
#       --cwd <dir>          Working directory for the app    (start only)
#       --interpreter <bin>  Interpreter (node, python3, bash...) (start)
#   -f, --file <ecosystem>   Use a pm2 ecosystem config file  (start only)
#       --lines <n>          Number of log lines to show      (logs only)
#   -d, --dry-run            Print the pm2 command, don't run it
#   -h, --help               Show this help
#
# Anything after `--` is passed straight through to the app being started.
#
# Examples:
#   scripts/run-ebilanz.sh start -n ebilanz-frontend -s dist/web.js -i max -e production
#   scripts/run-ebilanz.sh start -n ebilanz-backend  -s dist/api.js -i max -e production
#   scripts/run-ebilanz.sh restart                 # both frontend + backend
#   scripts/run-ebilanz.sh restart --frontend      # frontend only
#   scripts/run-ebilanz.sh restart --backend       # backend only
#   scripts/run-ebilanz.sh stop                    # stop both tiers
#   scripts/run-ebilanz.sh delete -n ebilanz-backend
#   scripts/run-ebilanz.sh status
#   scripts/run-ebilanz.sh logs -n ebilanz-frontend --lines 100

set -euo pipefail

NS="ebilanz"   # the only pm2 namespace this tool will ever operate on

die() { echo "Error: $*" >&2; exit 1; }

usage() {
  sed -n '3,/^set -euo/p' "$0" | sed '$d' | sed 's/^#\{0,1\} \{0,1\}//'
  exit "${1:-0}"
}

command -v pm2  >/dev/null 2>&1 || die "pm2 is not installed or not on PATH."
command -v node >/dev/null 2>&1 || die "node is required (to read pm2 state) and not on PATH."

# Robust read of pm2's process list as JSON on stdout.
#
# `pm2 jlist` can exit non-zero (e.g. while it cold-spawns its daemon) and can
# even print a "[PM2] Spawning ..." banner to stdout. Neither must be allowed to
# abort this script (we run under `set -euo pipefail`): the trailing `|| true`
# swallows the exit code, and the JSON consumers below tolerate banner noise by
# slicing out the outermost [...] before parsing. Worst case we treat the list
# as empty rather than crashing.
_pm2_jlist() { pm2 jlist 2>/dev/null || true; }

# Parse the (possibly banner-prefixed) jlist JSON on stdin into a JS array `a`.
# Shared by the readers below; defaults to [] on any garbage.
_JLIST_PARSE='
  const fs=require("fs"); const s=fs.readFileSync(0,"utf8");
  const i=s.indexOf("["), j=s.lastIndexOf("]"); let a=[];
  if(i>=0 && j>i){ try{ a=JSON.parse(s.slice(i,j+1)); }catch(e){ a=[]; } }
'

# Names of all pm2 processes currently in the eBilanz namespace.
_ebilanz_names() {
  _pm2_jlist | node -e "$_JLIST_PARSE"'
    const ns=process.argv[1];
    for (const p of a)
      if (((p.pm2_env&&p.pm2_env.namespace)||"default")===ns) console.log(p.name);
  ' "$NS"
}

# eBilanz process names filtered by tier: frontend | backend | both.
_ebilanz_tier() {
  local tier=$1 n
  while IFS= read -r n; do
    case "$tier" in
      frontend) [[ "$n" == *frontend* ]] && echo "$n" ;;
      backend)  [[ "$n" == *backend*  ]] && echo "$n" ;;
      both)     [[ "$n" == *frontend* || "$n" == *backend* ]] && echo "$n" ;;
    esac
  done < <(_ebilanz_names)
}

# Compact status table for eBilanz processes only.
_ebilanz_status() {
  _pm2_jlist | node -e "$_JLIST_PARSE"'
    const ns=process.argv[1];
    const rows=a.filter(p=>((p.pm2_env&&p.pm2_env.namespace)||"default")===ns);
    if(!rows.length){
      console.log("No eBilanz processes (pm2 namespace \x27"+ns+"\x27).");
    } else {
      console.log(["id","name","status","restarts","cpu","mem"].join("\t"));
      for(const p of rows){
        const e=p.pm2_env||{}, m=p.monit||{};
        console.log([p.pm_id, p.name, e.status||"?", e.restart_time||0,
          (m.cpu||0)+"%", Math.round((m.memory||0)/1048576)+"mb"].join("\t"));
      }
    }
  ' "$NS"
}

require_ebilanz() {
  local target=$1 n
  while IFS= read -r n; do
    [[ "$n" == "$target" ]] && return 0
  done < <(_ebilanz_names)
  die "Refusing: '$target' is not an eBilanz process (pm2 namespace '$NS')."
}

[[ $# -ge 1 ]] || usage 1
action=$1; shift

# Defaults
name="" script="" instances="" env_name="" watch="" cwd="" interpreter=""
eco_file="" all="" fe="" be="" lines="" dry_run="" app_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--name)        name=${2:?missing value for $1}; shift 2 ;;
    --frontend)       fe=1; shift ;;
    --backend)        be=1; shift ;;
    -a|--all)         all=1; shift ;;
    -s|--script)      script=${2:?missing value for $1}; shift 2 ;;
    -i|--instances)   instances=${2:?missing value for $1}; shift 2 ;;
    -e|--env)         env_name=${2:?missing value for $1}; shift 2 ;;
    -w|--watch)       watch=1; shift ;;
    --cwd)            cwd=${2:?missing value for $1}; shift 2 ;;
    --interpreter)    interpreter=${2:?missing value for $1}; shift 2 ;;
    -f|--file)        eco_file=${2:?missing value for $1}; shift 2 ;;
    --lines)          lines=${2:?missing value for $1}; shift 2 ;;
    -d|--dry-run)     dry_run=1; shift ;;
    -h|--help)        usage 0 ;;
    --)               shift; app_args=("$@"); break ;;
    -*)               die "Unknown option: $1 (try --help)" ;;
    *)                die "Unexpected argument: $1 (try --help)" ;;
  esac
done

run() {
  if [[ -n "$dry_run" ]]; then
    printf 'DRY-RUN: '; printf '%q ' pm2 "$@"; echo
  else
    pm2 "$@"
  fi
}

# Resolve the tier implied by --frontend/--backend (empty if none given).
selected_tier() {
  if   [[ -n "$fe" && -z "$be" ]]; then echo frontend
  elif [[ -n "$be" && -z "$fe" ]]; then echo backend
  elif [[ -n "$fe" && -n "$be" ]]; then echo both
  else echo ""
  fi
}

case "$action" in
  start)
    cmd=(start)
    if [[ -n "$eco_file" ]]; then
      cmd+=("$eco_file")
    else
      [[ -n "$script" ]] || die "start needs --script <file> (or --file <ecosystem>)"
      cmd+=("$script")
      [[ -n "$name" ]] && cmd+=(--name "$name")
    fi
    cmd+=(--namespace "$NS")          # force every start into the eBilanz namespace
    [[ -n "$instances" ]]   && cmd+=(-i "$instances")
    [[ -n "$env_name" ]]    && cmd+=(--env "$env_name")
    [[ -n "$watch" ]]       && cmd+=(--watch)
    [[ -n "$cwd" ]]         && cmd+=(--cwd "$cwd")
    [[ -n "$interpreter" ]] && cmd+=(--interpreter "$interpreter")
    [[ ${#app_args[@]} -gt 0 ]] && cmd+=(-- "${app_args[@]}")
    run "${cmd[@]}"
    ;;

  restart|reload|stop|delete)
    [[ -n "$eco_file" ]] && die "$action: --file is only for 'start'"
    cmd=("$action")
    if [[ -n "$name" ]]; then
      require_ebilanz "$name"
      cmd+=("$name")
    elif [[ -n "$all" ]]; then
      mapfile -t apps < <(_ebilanz_names)
      [[ ${#apps[@]} -gt 0 ]] || die "No eBilanz processes found (pm2 namespace '$NS')."
      cmd+=("${apps[@]}")
    else
      tier=$(selected_tier)
      if [[ -z "$tier" ]]; then
        # No explicit target. restart/reload/stop default to BOTH; delete must be explicit.
        [[ "$action" == delete ]] && \
          die "delete needs an explicit target: --name, --frontend, --backend, or --all"
        tier=both
      fi
      mapfile -t apps < <(_ebilanz_tier "$tier")
      if [[ ${#apps[@]} -eq 0 ]]; then
        avail=$(_ebilanz_names | paste -sd', ' -)
        die "No eBilanz '$tier' process found. Known eBilanz processes: ${avail:-<none>}"
      fi
      cmd+=("${apps[@]}")
    fi
    [[ -n "$env_name" ]] && cmd+=(--env "$env_name")
    run "${cmd[@]}"
    ;;

  status|list|ls)
    if [[ -n "$name" ]]; then
      require_ebilanz "$name"
      run describe "$name"
    else
      _ebilanz_status
    fi
    ;;

  logs)
    if [[ -n "$name" ]]; then
      require_ebilanz "$name"
      cmd=(logs "$name"); [[ -n "$lines" ]] && cmd+=(--lines "$lines")
      run "${cmd[@]}"
    elif [[ -n "$all" ]]; then
      mapfile -t apps < <(_ebilanz_names)
      [[ ${#apps[@]} -gt 0 ]] || die "No eBilanz processes found (pm2 namespace '$NS')."
      for a in "${apps[@]}"; do
        echo "===== logs: $a ====="
        run logs "$a" --nostream --lines "${lines:-20}"
      done
    else
      die "logs needs --name <app> or --all"
    fi
    ;;

  -h|--help|help)
    usage 0
    ;;

  *)
    die "Unknown action: $action (try --help)"
    ;;
esac
