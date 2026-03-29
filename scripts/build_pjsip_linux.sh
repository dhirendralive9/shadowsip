#!/bin/bash
# ============================================
# ShadowSIP — Build PJSIP + pjsua2 Python bindings (Ubuntu)
# Run: chmod +x scripts/build_pjsip_linux.sh && ./scripts/build_pjsip_linux.sh
# ============================================

set -e

PJSIP_VERSION="2.14.1"
PJSIP_DIR="pjproject-${PJSIP_VERSION}"
PJSIP_TAR="${PJSIP_DIR}.tar.gz"
PJSIP_URL="https://github.com/pjsip/pjproject/archive/refs/tags/${PJSIP_VERSION}.tar.gz"
BUILD_DIR="$(pwd)/build/pjsip"
PYTHON_BIN=$(which python3)

echo "============================================"
echo " ShadowSIP — PJSIP Build Script (Linux)"
echo " PJSIP Version: ${PJSIP_VERSION}"
echo " Python: ${PYTHON_BIN} ($(${PYTHON_BIN} --version))"
echo "============================================"
echo ""

# Step 1: Install dependencies
echo "[1/6] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    build-essential python3-dev swig \
    libasound2-dev libpulse-dev \
    libssl-dev libsrtp2-dev \
    libv4l-dev libavcodec-dev libavformat-dev libswscale-dev \
    libopus-dev libvpx-dev \
    uuid-dev

# Step 2: Download PJSIP source
echo ""
echo "[2/6] Downloading PJSIP ${PJSIP_VERSION}..."
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

if [ ! -f "${PJSIP_TAR}" ]; then
    wget -q "${PJSIP_URL}" -O "${PJSIP_TAR}"
fi

if [ ! -d "${PJSIP_DIR}" ]; then
    tar xzf "${PJSIP_TAR}"
fi
cd "${PJSIP_DIR}"

# Step 3: Configure with site-specific settings
echo ""
echo "[3/6] Configuring PJSIP..."

cat > pjlib/include/pj/config_site.h << 'EOF'
/*
 * ShadowSIP — PJSIP build configuration
 */
#define PJMEDIA_AUDIO_DEV_HAS_ALSA      1
#define PJMEDIA_AUDIO_DEV_HAS_PULSE      1
#define PJMEDIA_HAS_VIDEO               1
#define PJMEDIA_VIDEO_DEV_HAS_V4L2      1
#define PJMEDIA_HAS_SRTP                1
#define PJ_HAS_SSL_SOCK                 1

/* Opus codec support */
#define PJMEDIA_HAS_OPUS_CODEC          1

/* Increase max accounts and calls for multi-account support */
#define PJSUA_MAX_ACC                   8
#define PJSUA_MAX_CALLS                 16
#define PJSUA_MAX_PLAYERS               16

/* Enable ICE */
#define PJ_ICE_MAX_CAND                 32
#define PJ_ICE_MAX_CHECKS               100

/* Thread count — set to 0 for Python (we handle threading ourselves) */
/* This is set at runtime via EpConfig, not here */
EOF

export CFLAGS="${CFLAGS} -fPIC"
./configure \
    --enable-shared \
    --with-external-srtp \
    --with-external-opus \
    2>&1 | tail -20

# Step 4: Build PJSIP
echo ""
echo "[4/6] Building PJSIP (this takes a few minutes)..."
make dep -j$(nproc) 2>&1 | tail -5
make -j$(nproc) 2>&1 | tail -5

# Step 5: Install PJSIP system-wide
echo ""
echo "[5/6] Installing PJSIP..."
sudo make install
sudo ldconfig

# Step 6: Build Python SWIG bindings (pjsua2)
echo ""
echo "[6/6] Building pjsua2 Python bindings..."
cd pjsip-apps/src/swig

# Generate SWIG wrapper
make -j$(nproc) 2>&1 | tail -10

# Install Python module
cd python
${PYTHON_BIN} setup.py build
sudo ${PYTHON_BIN} setup.py install

echo ""
echo "============================================"
echo " BUILD COMPLETE"
echo "============================================"
echo ""
echo "Verify installation:"
echo "  python3 -c \"import pjsua2; print('pjsua2 OK')\""
echo ""

# Quick test
${PYTHON_BIN} -c "import pjsua2; print('pjsua2 version check: OK')" 2>/dev/null && \
    echo "pjsua2 module installed successfully!" || \
    echo "WARNING: pjsua2 import failed. Check build output above."
