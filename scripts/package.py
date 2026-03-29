#!/usr/bin/env python3
"""
ShadowSIP — Build & Package Automation
Usage:
    python scripts/package.py          # Build distributable
    python scripts/package.py --clean  # Clean build artifacts
"""

import os
import sys
import shutil
import subprocess
import argparse


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")


def clean():
    """Remove build artifacts."""
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.isdir(d):
            shutil.rmtree(d)
            print(f"Removed: {d}")

    # Remove __pycache__
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for d in dirs:
            if d == "__pycache__":
                path = os.path.join(root, d)
                shutil.rmtree(path)
                print(f"Removed: {path}")

    print("Clean complete.")


def build():
    """Build distributable using PyInstaller."""
    spec_file = os.path.join(PROJECT_ROOT, "shadowsip.spec")

    if not os.path.exists(spec_file):
        print(f"ERROR: Spec file not found: {spec_file}")
        sys.exit(1)

    # Ensure resource directories exist (even if empty)
    for subdir in ["icons", "ringtones", "translations"]:
        d = os.path.join(PROJECT_ROOT, "resources", subdir)
        os.makedirs(d, exist_ok=True)
        # Create .gitkeep so PyInstaller doesn't complain about empty dirs
        gitkeep = os.path.join(d, ".gitkeep")
        if not os.listdir(d):
            open(gitkeep, "a").close()

    print("=" * 50)
    print(" ShadowSIP — Building Distributable")
    print("=" * 50)
    print()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        spec_file,
        "--noconfirm",
        "--clean",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode == 0:
        output_dir = os.path.join(DIST_DIR, "ShadowSIP")
        print()
        print("=" * 50)
        print(" BUILD SUCCESSFUL")
        print(f" Output: {output_dir}")
        print("=" * 50)

        # Calculate size
        total = 0
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        print(f" Size: {total / (1024*1024):.1f} MB")
    else:
        print()
        print("BUILD FAILED")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="ShadowSIP Build Tool")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    args = parser.parse_args()

    if args.clean:
        clean()
    else:
        build()


if __name__ == "__main__":
    main()
