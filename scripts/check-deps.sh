#!/usr/bin/env bash
# Checks that your operating system is supported and that every tool this
# repository needs is installed - see REQUIREMENTS.md, especially section 1
# (supported operating systems) and section 3 (required software), which
# this script's checks and version numbers are kept in sync with.
#
# Run it with `make check` (see the Makefile) or directly:
#   bash scripts/check-deps.sh
#
# Written for bash 3.2 (macOS's default /bin/bash) as well as newer bash -
# no associative arrays, no `${var,,}`, no `sort -V` (a GNU-only flag the
# default BSD `sort` on macOS does not have) - see ver_ge() below instead.

set -u

FAIL_COUNT=0
WARN_COUNT=0

# --- output helpers ----------------------------------------------------

if [ -t 1 ]; then
  C_OK="\033[32m"
  C_WARN="\033[33m"
  C_FAIL="\033[31m"
  C_RESET="\033[0m"
else
  C_OK=""
  C_WARN=""
  C_FAIL=""
  C_RESET=""
fi

section() {
  echo ""
  echo "== $1 =="
}

ok() {
  printf "  ${C_OK}[ OK ]${C_RESET} %s\n" "$1"
}

warn() {
  printf "  ${C_WARN}[WARN]${C_RESET} %s\n" "$1"
  WARN_COUNT=$((WARN_COUNT + 1))
}

fail() {
  printf "  ${C_FAIL}[FAIL]${C_RESET} %s\n" "$1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

# ver_ge HAVE WANT - true (exit 0) if version HAVE >= WANT, comparing
# dot-separated numeric fields (so "3.9" < "3.10", unlike a plain string
# compare). Implemented in plain awk instead of `sort -V` because macOS's
# default BSD `sort` doesn't support `-V` (a GNU coreutils extension) - see
# the file header.
ver_ge() {
  awk -v have="$1" -v want="$2" '
    BEGIN {
      n1 = split(have, h, ".")
      n2 = split(want, w, ".")
      max = (n1 > n2 ? n1 : n2)
      for (i = 1; i <= max; i++) {
        hv = (i <= n1) ? h[i] + 0 : 0
        wv = (i <= n2) ? w[i] + 0 : 0
        if (hv > wv) { exit 0 }
        if (hv < wv) { exit 1 }
      }
      exit 0
    }'
}

# first_version TEXT - extracts the first "N.N" or "N.N.N" substring found
# in TEXT (most --version outputs have exactly one, but some, like
# `aws --version`, have several - this picks the first, which is always the
# tool's own version in every command this script checks).
first_version() {
  echo "$1" | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n 1
}

REQUIREMENTS_HINT="See REQUIREMENTS.md, section 3 (Required software), for what this is for and the exact install command for your OS."

# --- operating system ----------------------------------------------------

check_os() {
  section "Operating system (REQUIREMENTS.md section 1)"

  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os" in
    Linux)
      distro="unknown"
      distro_ver="unknown"
      if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091  # a real, standard system file - not part of this repo
        distro="$(. /etc/os-release && echo "$ID")"
        # shellcheck disable=SC1091
        distro_ver="$(. /etc/os-release && echo "$VERSION_ID")"
      fi
      if [ "$distro" != "ubuntu" ]; then
        warn "Detected Linux distro '$distro' ($arch) - this repository is tested on Ubuntu 22.04/24.04/26.04 (amd64). Other distros may still work; see REQUIREMENTS.md section 1."
      elif [ "$arch" != "x86_64" ]; then
        warn "Detected Ubuntu $distro_ver on '$arch' - this repository is tested on amd64 (x86_64); see REQUIREMENTS.md section 1."
      else
        case "$distro_ver" in
          22.04 | 24.04 | 26.04)
            ok "Ubuntu $distro_ver ($arch) - supported"
            ;;
          *)
            warn "Ubuntu $distro_ver ($arch) detected - this repository is tested on 22.04/24.04/26.04; $distro_ver is likely fine too, but see REQUIREMENTS.md section 1."
            ;;
        esac
      fi
      ;;
    Darwin)
      macos_ver="$(sw_vers -productVersion 2>/dev/null || echo "")"
      if [ "$arch" != "arm64" ] && [ "$arch" != "x86_64" ]; then
        warn "macOS on unexpected architecture '$arch' - see REQUIREMENTS.md section 1."
      elif [ -z "$macos_ver" ]; then
        warn "macOS ($arch) detected, but the version could not be determined."
      elif ver_ge "$macos_ver" "13.0"; then
        ok "macOS $macos_ver ($arch) - supported"
      else
        warn "macOS $macos_ver ($arch) detected - this repository targets macOS 13+; see REQUIREMENTS.md section 1."
      fi
      ;;
    *)
      fail "Operating system '$os' is not directly supported. Windows users: install WSL2 with an Ubuntu distro and re-run this check inside it - see REQUIREMENTS.md section 1."
      ;;
  esac
}

# --- required software ----------------------------------------------------

check_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found. $REQUIREMENTS_HINT"
    return
  fi
  have="$(first_version "$(python3 --version 2>&1)")"
  if [ -z "$have" ]; then
    warn "python3 found, but its version could not be parsed."
  elif ver_ge "$have" "3.10"; then
    ok "Python $have (>= 3.10 required)"
  else
    fail "Python $have found, but aws-cdk-lib requires >= 3.10. $REQUIREMENTS_HINT"
  fi
}

check_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    fail "uv not found. $REQUIREMENTS_HINT"
    return
  fi
  have="$(first_version "$(uv --version 2>&1)")"
  ok "uv${have:+ $have} found"
}

check_mise() {
  if ! command -v mise >/dev/null 2>&1; then
    warn "mise not found (recommended, not required - installs the pinned Python and AWS CLI; uv can manage Python on its own). See REQUIREMENTS.md section 3.3."
    return
  fi
  ok "mise found"
}

check_node() {
  if ! command -v node >/dev/null 2>&1; then
    fail "Node.js not found (needed for the AWS CDK Toolkit). $REQUIREMENTS_HINT"
    return
  fi
  have="$(first_version "$(node --version 2>&1)")"
  if [ -z "$have" ]; then
    warn "Node.js found, but its version could not be parsed."
  elif ver_ge "$have" "20.0"; then
    ok "Node.js $have (>= 20 LTS required)"
  else
    warn "Node.js $have found, but >= 20 LTS is recommended. $REQUIREMENTS_HINT"
  fi
}

check_cdk() {
  if command -v cdk >/dev/null 2>&1; then
    have="$(first_version "$(cdk --version 2>&1)")"
    ok "AWS CDK Toolkit${have:+ $have} found (cdk)"
    return
  fi
  if command -v npx >/dev/null 2>&1; then
    ok "AWS CDK Toolkit not installed globally, but npx is available - 'npx aws-cdk@2 ...' works on demand (see REQUIREMENTS.md section 3)."
    return
  fi
  fail "Neither 'cdk' nor 'npx' was found (both come from Node.js/npm). $REQUIREMENTS_HINT"
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "docker not found (Docker Desktop, Docker Engine, or Colima - see REQUIREMENTS.md section 3.2). $REQUIREMENTS_HINT"
    return
  fi
  have="$(first_version "$(docker --version 2>&1)")"
  if ! docker info >/dev/null 2>&1; then
    fail "docker was found${have:+ (version $have)}, but its daemon isn't reachable. Start Docker Desktop, or if you use Colima, run 'colima start' - see REQUIREMENTS.md section 3.2."
    return
  fi
  if [ -n "$have" ] && ver_ge "$have" "24.0"; then
    ok "Docker $have (daemon reachable)"
  else
    ok "Docker${have:+ $have} found (daemon reachable)"
  fi
}

check_docker_compose() {
  if ! command -v docker >/dev/null 2>&1; then
    return # already reported by check_docker
  fi
  if ! compose_output="$(docker compose version 2>&1)"; then
    fail "'docker compose' (v2, a space, not the standalone 'docker-compose' script) is not available. $REQUIREMENTS_HINT"
    return
  fi
  have="$(first_version "$compose_output")"
  if [ -n "$have" ] && ver_ge "$have" "2.20"; then
    ok "Docker Compose $have (>= 2.20 required)"
  else
    ok "Docker Compose${have:+ $have} found"
  fi
}

check_git() {
  if ! command -v git >/dev/null 2>&1; then
    fail "git not found. $REQUIREMENTS_HINT"
    return
  fi
  have="$(first_version "$(git --version 2>&1)")"
  ok "git${have:+ $have} found"
}

check_aws_cli() {
  if ! command -v aws >/dev/null 2>&1; then
    warn "AWS CLI not found (recommended, used in every module's 'Verify' section) - run 'mise install' from this repository's root (see REQUIREMENTS.md section 3.3)"
    return
  fi
  have="$(first_version "$(aws --version 2>&1)")"
  ok "AWS CLI${have:+ $have} found"
}

check_floci_cli() {
  if ! command -v floci >/dev/null 2>&1; then
    warn "floci CLI not found (optional - docker compose is the default way to run floci; see REQUIREMENTS.md section 5.2)."
    return
  fi
  ok "floci CLI found"
}

# --- main ----------------------------------------------------

check_os

section "Required software (REQUIREMENTS.md section 3)"
check_python
check_uv
check_node
check_cdk
check_docker
check_docker_compose
check_git

section "Recommended software"
check_aws_cli
check_mise

section "Optional software"
check_floci_cli

echo ""
echo "======================================================================"
if [ "$FAIL_COUNT" -gt 0 ]; then
  printf "${C_FAIL}%s missing/unsupported required item(s), %s warning(s).${C_RESET}\n" "$FAIL_COUNT" "$WARN_COUNT"
  echo ""
  echo "See REQUIREMENTS.md for what each [FAIL] item is for and the exact"
  echo "install command for your operating system:"
  echo "  - Ubuntu: REQUIREMENTS.md section 3.1"
  echo "  - macOS:  REQUIREMENTS.md section 3.2"
  echo "======================================================================"
  exit 1
else
  printf "${C_OK}All required software found and your operating system is supported${C_RESET} (%s warning(s) - see REQUIREMENTS.md for anything marked [WARN] above).\n" "$WARN_COUNT"
  echo "======================================================================"
  exit 0
fi
