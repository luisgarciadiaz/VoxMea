#!/usr/bin/env python3

import importlib
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
PIPELINE = BASE / "pipeline"
SCRIPTS = PIPELINE / "scripts"
CURATED = PIPELINE / "curated"
SOURCE_DIRS = [BASE / "sources", PIPELINE / "workingfiles" / "sources"]


def find_sources():
    for d in SOURCE_DIRS:
        if d.exists():
            exts = ["*.md", "*.txt", "*.eml", "*.html", "*.htm", "*.docx", "*.pdf"]
            count = sum(len(list(d.rglob(e))) for e in exts)
            if count:
                return d, count
    return None, 0


def count_curated():
    if not CURATED.exists():
        return 0
    return len([f for f in CURATED.rglob("*.md") if f.name != "style_context.md"])


def run(script):
    sp = SCRIPTS / script
    if not sp.exists():
        print(f"[FAIL] Script not found: {script}")
        return 1
    return subprocess.run([sys.executable, str(sp)], cwd=BASE).returncode


def main():
    args = [a.replace(",", "") for a in sys.argv[1:]]
    quick_topic = None
    quick_chars = None
    quick_action = None

    if len(args) >= 1:
        quick_action = args[0]
    if len(args) >= 2:
        quick_topic = args[1]
    if len(args) >= 3:
        try:
            quick_chars = int(args[2])
        except ValueError:
            quick_chars = None

    print()
    print("  +------------------------------------------+")
    print("  |         VoxMea - Voice Cloner            |")
    print("  +------------------------------------------+")

    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 11):
        print(f"[FAIL] Python 3.11+ required (you have {v.major}.{v.minor}.{v.micro})")
        sys.exit(1)

    for pkg, name in [("yaml", "pyyaml"), ("requests", "requests"), ("dotenv", "python-dotenv")]:
        try:
            importlib.import_module(pkg)
        except ImportError:
            print(f"[FAIL] Package {name} not installed. Run: pip install {name}")
            sys.exit(1)

    for pkg, (name, desc) in {"bs4": ("beautifulsoup4", "HTML support"), "docx": ("python-docx", ".docx support"), "fitz": ("pymupdf", ".pdf support"), "tiktoken": ("tiktoken", "accurate token counting")}.items():
        try:
            importlib.import_module(pkg)
        except ImportError:
            print(f"[WARN] Optional {name} not installed ({desc}). Run: pip install {name}")

    env_path = BASE / ".env"
    if not env_path.exists() or "LLM_BACKEND=" not in env_path.read_text(encoding="utf-8"):
        print("[FAIL] .env not configured. Edit .env with your LLM settings.")
        sys.exit(1)

    src_dir, src_count = find_sources()
    if not src_dir or src_count == 0:
        print(f"[FAIL] No source files found. Put your texts in sources/")
        sys.exit(1)

    if count_curated() == 0:
        print("\n  First run: rebuilding voice from source texts...\n")
        for s in ["curate.py", "analyze_style.py", "build_dataset.py"]:
            if run(s) != 0:
                sys.exit(1)
        print()

    # No args: show menu
    if not quick_action:
        print()
        print("  What you want to do today?")
        print()
        print("    [1] Create new text   - Write something in your voice")
        print("    [2] Rebuild voice     - Re-process sources and remake style profile")
        print("    [q] Quit")
        print()
        choice = input("  Choose [1], [2] or [q]: ").strip().lower()
        if choice == "q":
            sys.exit(0)
        if choice == "2":
            for s in ["curate.py", "analyze_style.py", "build_dataset.py"]:
                if run(s) != 0:
                    sys.exit(1)
        sys.exit(run("voice_mode.py"))

    # Args: direct mode
    if quick_action == "2":
        for s in ["curate.py", "analyze_style.py", "build_dataset.py"]:
            if run(s) != 0:
                sys.exit(1)

    voice_args = []
    if quick_topic:
        voice_args.extend(["--topic", quick_topic])
    if quick_chars:
        voice_args.extend(["--chars", str(quick_chars)])

    if voice_args:
        sys.exit(subprocess.run([sys.executable, str(SCRIPTS / "voice_mode.py")] + voice_args, cwd=BASE).returncode)

    sys.exit(run("voice_mode.py"))


if __name__ == "__main__":
    main()
