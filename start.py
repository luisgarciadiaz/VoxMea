#!/usr/bin/env python3
"""VoxMea - Pipeline Launcher

Simple launcher: checks prerequisites, rebuilds voice if needed, then
asks if you want to create new text or rebuild from sources.
"""

import importlib
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
PIPELINE = BASE / "pipeline"
SCRIPTS = PIPELINE / "scripts"
CURATED = PIPELINE / "curated"
DATASET = PIPELINE / "dataset"

SOURCE_DIRS = [BASE / "sources", PIPELINE / "workingfiles" / "sources"]


def find_sources():
    exts = ["*.md", "*.txt", "*.eml", "*.html", "*.htm", "*.docx", "*.pdf"]
    for d in SOURCE_DIRS:
        if d.exists():
            count = sum(len(list(d.rglob(e))) for e in exts)
            if count:
                return d, count
    return None, 0


def count_curated():
    if not CURATED.exists():
        return 0
    return len([f for f in CURATED.rglob("*.md") if f.name != "style_context.md"])


def env_ok():
    p = BASE / ".env"
    if not p.exists():
        return False
    return "LLM_BACKEND=" in p.read_text(encoding="utf-8")


def run(script):
    sp = SCRIPTS / script
    if not sp.exists():
        print(f"[FAIL] Script not found: {script}")
        return 1
    return subprocess.run([sys.executable, str(sp)], cwd=BASE).returncode


def main():
    print()
    print("  " + "+" + "-" * 40 + "+")
    print("  |         VoxMea - Voice Cloner            |")
    print("  " + "+" + "-" * 40 + "+")

    # ---- Prerequisites ----
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 11):
        print(f"[FAIL] Python 3.11+ required (you have {v.major}.{v.minor}.{v.micro})")
        sys.exit(1)
    print(f"[OK]   Python {v.major}.{v.minor}.{v.micro}")

    for pkg, name in [("yaml", "pyyaml"), ("requests", "requests"), ("dotenv", "python-dotenv")]:
        try:
            importlib.import_module(pkg)
            print(f"[OK]   Package {name}")
        except ImportError:
            print(f"[FAIL] Package {name} not installed. Run: pip install {name}")
            sys.exit(1)

    for pkg, (name, desc) in {
        "bs4": ("beautifulsoup4", "HTML support"),
        "docx": ("python-docx", ".docx support"),
        "fitz": ("pymupdf", ".pdf support"),
        "tiktoken": ("tiktoken", "accurate token counting"),
    }.items():
        try:
            importlib.import_module(pkg)
            print(f"[OK]   Optional {name} ({desc})")
        except ImportError:
            print(f"[WARN] Optional {name} not installed ({desc}). Run: pip install {name}")

    if not env_ok():
        print("[FAIL] .env not configured. Copy .env.example to .env and edit it.")
        sys.exit(1)
    print("[OK]   .env configured")

    # ---- Sources ----
    print()
    src_dir, src_count = find_sources()
    if not src_dir or src_count == 0:
        print(f"[FAIL] No source files found.")
        print(f"       Put your texts (.md, .txt, .eml, .html, .docx, .pdf)")
        print(f"       in: {WORK / 'sources'}/")
        sys.exit(1)
    print(f"[OK]   {src_count} source files found in {src_dir.relative_to(BASE)}/")

    # ---- Rebuild if needed, otherwise ask ----
    if count_curated() == 0:
        print("\n  First run: rebuilding voice from source texts...\n")
        for s in ["curate.py", "analyze_style.py", "build_dataset.py"]:
            if run(s) != 0:
                sys.exit(1)
        print("\n[OK]   Voice ready. Starting voice mode...\n")
    else:
        print()
        print("  What now?")
        print()
        print("    [1] Create new text   - Write something in your voice")
        print("    [2] Rebuild voice     - Re-process sources and remake style profile")
        print()
        choice = input("  Choose [1] or [2]: ").strip()

        if choice == "2":
            print("\n  Rebuilding voice...")
            for s in ["curate.py", "analyze_style.py", "build_dataset.py"]:
                if run(s) != 0:
                    sys.exit(1)
            print()

    sys.exit(run("voice_mode.py"))


if __name__ == "__main__":
    main()
