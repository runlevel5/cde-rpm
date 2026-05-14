#!/bin/bash
# Build an SRPM (and optionally an RPM set) for CDE from this packaging repo.
#
# Layout assumptions:
#   - This repo (cde-rpm) holds cde.spec, the Source* files, and Patch* files.
#   - The CDE source tree (the cdesktopenv-code/cde directory containing
#     configure.ac) lives elsewhere; pass --source-dir or set CDE_SRC_DIR.
#
# Usage:
#   ./build-srpm.sh --source-dir /path/to/cdesktopenv-code/cde
#   ./build-srpm.sh --source-dir ... --rpm
#   ./build-srpm.sh --source-dir ... --rpm --installdeps

set -euo pipefail

PKG_DIR=$(cd "$(dirname "$0")" && pwd)
NAME=cde
SPEC="$PKG_DIR/cde.spec"

if [ ! -f "$SPEC" ]; then
    echo "Error: $SPEC not found." >&2
    exit 1
fi

VERSION=$(awk -F'[][, ]+' '/^Version:/{print $2; exit}' "$SPEC")
TARBALL="${NAME}-${VERSION}.tar.xz"
TOPDIR=$(rpm --eval %_topdir 2>/dev/null || echo "$HOME/rpmbuild")

CDE_SRC_DIR=${CDE_SRC_DIR:-}
DO_RPM=0
DO_DEPS=0

while [ $# -gt 0 ]; do
    case "$1" in
        --source-dir) CDE_SRC_DIR=$2; shift 2 ;;
        --rpm) DO_RPM=1; shift ;;
        --installdeps) DO_DEPS=1; shift ;;
        -h|--help)
            sed -n '2,15p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

if [ -z "$CDE_SRC_DIR" ]; then
    echo "Error: --source-dir <path-to-cde-source> is required" >&2
    exit 2
fi
if [ ! -f "$CDE_SRC_DIR/configure.ac" ]; then
    echo "Error: $CDE_SRC_DIR/configure.ac not found - wrong --source-dir?" >&2
    exit 3
fi

echo "==> Preparing rpmbuild tree at $TOPDIR"
mkdir -p "$TOPDIR"/{SOURCES,SPECS,BUILD,RPMS,SRPMS}

echo "==> Building source tarball ($TARBALL) from $CDE_SRC_DIR"
made_dist=0
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

if [ -f "$CDE_SRC_DIR/Makefile" ] && grep -q '^dist:' "$CDE_SRC_DIR/Makefile" 2>/dev/null; then
    if (cd "$CDE_SRC_DIR" && make dist) >"$WORKDIR/dist.log" 2>&1 \
       && [ -f "$CDE_SRC_DIR/$TARBALL" ]; then
        echo "    used: make dist"
        cp "$CDE_SRC_DIR/$TARBALL" "$TOPDIR/SOURCES/"
        made_dist=1
    else
        echo "    make dist failed; falling back to git archive"
    fi
fi

if [ "$made_dist" -eq 0 ]; then
    if ! (cd "$CDE_SRC_DIR" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
        echo "Error: source tree is not a git checkout; cannot fall back." >&2
        exit 4
    fi
    echo "    used: git archive HEAD"
    (cd "$CDE_SRC_DIR" && git archive --format=tar --prefix="${NAME}-${VERSION}/" HEAD) \
        | xz -c > "$TOPDIR/SOURCES/$TARBALL"
fi

echo "==> Staging spec, sources, and patches"
install -m 0644 "$SPEC" "$TOPDIR/SPECS/cde.spec"
for f in cde.pam dtlogin.service cde.desktop ld.so.conf-cde.conf README.Fedora; do
    install -m 0644 "$PKG_DIR/$f" "$TOPDIR/SOURCES/"
done
for p in "$PKG_DIR"/*.patch; do
    [ -e "$p" ] && install -m 0644 "$p" "$TOPDIR/SOURCES/"
done

if [ "$DO_DEPS" -eq 1 ]; then
    echo "==> Installing build dependencies (sudo dnf builddep)"
    sudo dnf -y builddep "$TOPDIR/SPECS/cde.spec"
fi

if [ "$DO_RPM" -eq 1 ]; then
    echo "==> Building SRPM and binary RPMs"
    rpmbuild -ba "$TOPDIR/SPECS/cde.spec"
else
    echo "==> Building SRPM only"
    rpmbuild -bs "$TOPDIR/SPECS/cde.spec"
fi

echo
echo "Done. Artifacts:"
ls -1 "$TOPDIR/SRPMS/"*.src.rpm 2>/dev/null || true
ls -1 "$TOPDIR/RPMS"/*/*.rpm 2>/dev/null || true
