#!/usr/bin/env python3
"""
WardogKit — Lightweight open-source CLI companion for Wardogs Optimizer.
Safe, transparent, reversible system tuning for Windows.
MIT License.
"""
import argparse, ctypes, os, platform, shutil, subprocess, sys
from pathlib import Path

VERSION = "0.3.0"
BANNER = r"""
  ██╗    ██╗ █████╗ ██████╗ ██████╗  ██████╗  ██████╗
  ██║    ██║██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝
  ██║ █╗ ██║███████║██████╔╝██║  ██║██║   ██║██║  ███╗
  ██║███╗██║██╔══██║██╔══██╗██║  ██║██║   ██║██║   ██║
  ╚███╔███╔╝██║  ██║██║  ██║██████╔╝╚██████╔╝╚██████╔╝
   ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚═════╝
        KIT v{VERSION} — open-source tuning companion
"""

# ───────────────────────── helpers ─────────────────────────

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def ok(msg):  print(f"  [\033[92m+\033[0m] {msg}")
def warn(msg): print(f"  [\033[93m!\033[0m] {msg}")
def err(msg):  print(f"  [\033[91m-\033[0m] {msg}")


def run(cmd: list[str], check=False):
    try:
        return subprocess.run(cmd, shell=False, capture_output=True,
                              text=True, check=check)
    except Exception as e:
        err(f"{' '.join(cmd)} → {e}")
        return None

# ───────────────────────── commands ─────────────────────────

def cmd_info(_):
    """Print system information."""
    print(f"  OS       : {platform.system()} {platform.release()} ({platform.version()})")
    print(f"  Machine  : {platform.machine()}")
    print(f"  Python   : {platform.python_version()}")
    print(f"  Admin    : {'yes' if is_admin() else 'no'}")
    if os.name == "nt":
        for var in ("PROCESSOR_IDENTIFIER", "NUMBER_OF_PROCESSORS"):
            print(f"  {var:<9}: {os.environ.get(var, 'n/a')}")


def cmd_clean(_):
    """Remove temp files from %TEMP% and Windows Temp."""
    targets = [Path(os.environ.get("TEMP", "")), Path("C:/Windows/Temp")]
    freed = 0
    for folder in targets:
        if not folder.exists():
            continue
        for item in folder.glob("*"):
            try:
                size = item.stat().st_size if item.is_file() else 0
                shutil.rmtree(item) if item.is_dir() else item.unlink()
                freed += size
            except Exception:
                pass
    ok(f"Temp cleanup done — freed ≈ {freed / 1_048_576:.1f} MB")


def cmd_tune(args):
    """Apply a safe, reversible tuning preset."""
    preset = args.preset
    print(f"  → Applying preset: \033[96m{preset}\033[0m")

    if os.name != "nt":
        warn("Tuning presets are Windows-only. Skipping.")
        return

    tweaks = {
        "balanced": [
            ("powercfg", "/setactive", "SCHEME_BALANCED"),
        ],
        "gaming": [
            ("powercfg", "/setactive", "SCHEME_MIN"),
            ("ipconfig", "/flushdns"),
        ],
        "extreme": [
            ("powercfg", "/setactive", "SCHEME_MIN"),
            ("ipconfig", "/flushdns"),
            ("netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"),
        ],
    }

    for cmd in tweaks.get(preset, []):
        r = run(list(cmd))
        (ok if r and r.returncode == 0 else warn)(f"{' '.join(cmd)}")

    warn("Reboot recommended for full effect.")


def cmd_restore(_):
    """Restore Windows defaults."""
    if os.name != "nt":
        warn("Restore is Windows-only. Skipping.")
        return
    run(["powercfg", "/setactive", "SCHEME_BALANCED"])
    run(["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"])
    ok("Defaults restored.")


def cmd_about(_):
    print("  WardogKit — open-source CLI companion.")
    print("  Repo   : github.com/DirectorRelease/wardog-kit")
    print("  Author : DirectorRelease")
    print("  License: MIT")
    print("  Full GUI optimizer (closed-source): github.com/DirectorRelease/wardogs-optimizer/releases")

# ───────────────────────── entry point ─────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="wardog", description="WardogKit — lightweight tuning companion."
    )
    parser.add_argument("-v", "--version", action="version",
                        version=f"WardogKit {VERSION}")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("info",    help="show system info").set_defaults(fn=cmd_info)
    sub.add_parser("clean",   help="clean temp files").set_defaults(fn=cmd_clean)
    sub.add_parser("restore", help="restore defaults").set_defaults(fn=cmd_restore)
    sub.add_parser("about",   help="about this project").set_defaults(fn=cmd_about)

    p = sub.add_parser("tune", help="apply tuning preset")
    p.add_argument("preset", choices=["balanced", "gaming", "extreme"])
    p.set_defaults(fn=cmd_tune)

    args = parser.parse_args()
    print(BANNER.format(VERSION=VERSION))

    if not args.cmd:
        parser.print_help()
        sys.exit(0)

    if args.cmd in ("tune", "clean", "restore") and not is_admin():
        warn("Not running as Administrator — some operations may fail.")

    args.fn(args)


if __name__ == "__main__":
    main()
