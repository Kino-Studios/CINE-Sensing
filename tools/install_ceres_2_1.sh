#!/usr/bin/env bash
# Build and install Ceres Solver 2.1.0 from source.
#
# VINS-Fusion uses ceres::LocalParameterization, which Ceres 2.2 (the Ubuntu 24.04
# package) removed, so 2.1 has to be built. Installs to ${CERES_PREFIX:-/usr/local};
# uses sudo for apt and the install step when not run as root.
#
# Usage: tools/install_ceres_2_1.sh
set -euo pipefail

CERES_VERSION="2.1.0"
# Checksum of GitHub's archive of the 2.1.0 tag, which differs from the ceres-solver.org
# tarball's. GitHub is the source because ceres-solver.org went unreachable during CI.
CERES_SHA256="ccbd716a93f65d4cb017e3090ae78809e02f5426dce16d0ee2b4f8a4ba2411a8"
CERES_PREFIX="${CERES_PREFIX:-/usr/local}"
BUILD_JOBS="${BUILD_JOBS:-$(nproc)}"

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

$SUDO apt-get update
$SUDO apt-get install -y --no-install-recommends \
  build-essential cmake wget ca-certificates \
  libgoogle-glog-dev libgflags-dev libatlas-base-dev libsuitesparse-dev libeigen3-dev

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

ARCHIVE="$WORK_DIR/ceres-solver-${CERES_VERSION}.tar.gz"
wget -q "https://github.com/ceres-solver/ceres-solver/archive/refs/tags/${CERES_VERSION}.tar.gz" -O "$ARCHIVE"
echo "${CERES_SHA256}  ${ARCHIVE}" | sha256sum -c -

tar xzf "$ARCHIVE" -C "$WORK_DIR"
# -DCXSPARSE=OFF: Ubuntu 24.04's SuiteSparse no longer provides CXSparse, and Ceres 2.1's
# configure step fails linking CXSparse::CXSparse without it.
cmake -S "$WORK_DIR/ceres-solver-${CERES_VERSION}" -B "$WORK_DIR/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$CERES_PREFIX" \
  -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF -DBUILD_BENCHMARKS=OFF -DCXSPARSE=OFF
cmake --build "$WORK_DIR/build" -j "$BUILD_JOBS"
$SUDO cmake --install "$WORK_DIR/build"

echo "Ceres Solver ${CERES_VERSION} installed to ${CERES_PREFIX}"
