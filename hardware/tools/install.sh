#!/usr/bin/env bash
# Install the pinned open-source toolchain and standard-cell platforms, user-local (no sudo).
#
#   hardware/tools/install.sh            # installs into $HWBENCH_TOOLS (default ~/.local/hwbench)
#
# What it installs (recorded in $HWBENCH_TOOLS/VERSIONS):
#   micromamba      static binary, only used to create the two environments below
#   env "yosys"     Yosys 0.71 (conda-forge, with its ABC as yosys-abc) and Icarus Verilog 12.0
#   env "openroad"  OpenROAD 2.0-12381-g01bba3695 (litex-hub build of 2024-03, includes OpenSTA)
#   platforms/      nangate45 and sky130hd of OpenROAD-flow-scripts at a pinned commit
#                   (Liberty, LEF, tracks, RC settings), the ORFS commit of the OpenROAD build's date
#
# The environments are created from the lock files next to this script (exact package builds,
# with checksums).  HWBENCH_UNLOCKED=1 resolves the version specs below instead.
set -euo pipefail

MICROMAMBA_VERSION=2.9.0-0
YOSYS_SPEC='yosys=0.71'
IVERILOG_SPEC='iverilog=12.0'
OPENROAD_SPEC='openroad=2.0_12381_g01bba3695'
ORFS_COMMIT=90b19ec40311152d38a3295cf21918248e7761ca   # 2024-03-04

HERE=$(cd "$(dirname "$0")" && pwd)
T=${HWBENCH_TOOLS:-$HOME/.local/hwbench}
mkdir -p "$T/bin" "$T/platforms"
export MAMBA_ROOT_PREFIX="$T/mamba"

if [ ! -x "$T/bin/micromamba" ]; then
  curl -fsSL -o "$T/bin/micromamba" \
    "https://github.com/mamba-org/micromamba-releases/releases/download/$MICROMAMBA_VERSION/micromamba-linux-64"
  chmod +x "$T/bin/micromamba"
fi
MM="$T/bin/micromamba"

if [ ! -d "$MAMBA_ROOT_PREFIX/envs/yosys" ]; then
  if [ -z "${HWBENCH_UNLOCKED:-}" ]; then
    "$MM" create -y -n yosys --file "$HERE/yosys.lock.txt"
  else
    "$MM" create -y -n yosys -c conda-forge --override-channels "$YOSYS_SPEC" "$IVERILOG_SPEC" python=3.12
  fi
fi
if [ ! -d "$MAMBA_ROOT_PREFIX/envs/openroad" ]; then
  if [ -z "${HWBENCH_UNLOCKED:-}" ]; then
    "$MM" create -y -n openroad --file "$HERE/openroad.lock.txt"
  else
    # The litex-hub build needs libboost 1.73 (only on Anaconda's main channel) and libfmt.so.8,
    # which its package does not declare.
    "$MM" create -y -n openroad -c litex-hub -c conda-forge -c main --override-channels \
      "$OPENROAD_SPEC" python=3.10 fmt=8.1
  fi
fi

# Platforms: sparse checkout of the two platform folders only.
if [ ! -d "$T/platforms/orfs/flow/platforms/nangate45" ]; then
  rm -rf "$T/platforms/orfs"
  git clone --filter=blob:none --no-checkout \
    https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git "$T/platforms/orfs"
  cd "$T/platforms/orfs"
  # sky130hd/rcx_patterns.rules is a symlink to sky130hs/rcx_patterns.rules
  git sparse-checkout set --no-cone /flow/platforms/nangate45/ /flow/platforms/sky130hd/ \
    /flow/platforms/sky130hs/rcx_patterns.rules
  git -c advice.detachedHead=false checkout "$ORFS_COMMIT"
  cd - >/dev/null
fi

Y="$MAMBA_ROOT_PREFIX/envs/yosys/bin"
O="$MAMBA_ROOT_PREFIX/envs/openroad/bin"
{
  echo "# hwbench toolchain, installed $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "micromamba $("$MM" --version)"
  "$Y/yosys" -V
  "$Y/yosys-abc" -c 'version' 2>/dev/null | grep -m1 'Berkeley' || true
  "$Y/iverilog" -V 2>/dev/null | head -1 || true
  echo "openroad $("$O/openroad" -version 2>/dev/null | tail -1)"
  echo "orfs platforms commit $(git -C "$T/platforms/orfs" rev-parse HEAD)"
} > "$T/VERSIONS"

# bench.py refuses to run if the Liberty files differ from hardware/tools/platforms.sha256.
( cd "$T/platforms/orfs/flow/platforms" && sha256sum -c "$HERE/platforms.sha256" )
echo "installed into $T"
cat "$T/VERSIONS"
