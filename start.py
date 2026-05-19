#!/usr/bin/env python3
"""VoxMea — Pipeline Launcher

Orchestrates the full writing style cloning pipeline.
Checks prerequisites and guides you through each step.
"""

import importlib
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
SOURCES_DIR = BASE_DIR / "sources"
CURATED_DIR = BASE_DIR / "curated"
DATASET_DIR = BASE_DIR / "dataset"
PROMPTS_DIR = BASE_DIR / "prompts"
TESTS_DIR = BASE_DIR / "tests"
OUTPUT_DIR = BASE_DIR / "output"

REQUIRED_PACKAGES = {
    "yaml": "pyyaml",
    "requests": "requests",
    "dotenv": "python-dotenv",
}

OPTIONAL_PACKAGES = {
    "bs4": ("beautifulsoup4", "HTML support"),
    "docx": ("python-docx", ".docx support"),
    "fitz": ("pymupdf", ".pdf support"),
    "tiktoken": ("tiktoken", "accurate token counting"),
}

REQUIRED_DIRS = [
    ("sources", SOURCES_DIR, "Place your personal texts here"),
    ("curated", CURATED_DIR, "Populated by curate.py"),
    ("dataset", DATASET_DIR, "Populated by build_dataset.py"),
    ("prompts", PROMPTS_DIR, "System prompt and test prompts"),
    ("tests", TESTS_DIR, "Control text and test results"),
]


def check_python():
    """Check Python version is 3.11+."""
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 11):
        return (False, f"Python 3.11+ required (you have {v.major}.{v.minor}.{v.micro})")
    return (True, f"Python {v.major}.{v.minor}.{v.micro}")


def check_package(pkg_name, install_name):
    """Check if a Python package is installed."""
    try:
        importlib.import_module(pkg_name)
        return (True, "")
    except ImportError:
        return (False, install_name)


def check_optional_package(pkg_name, install_name, description):
    """Check optional package, warn but don't fail."""
    ok, _ = check_package(pkg_name, install_name)
    return (ok, install_name, description)


def check_dir(label, path, hint):
    """Check if a directory exists and has content."""
    if not path.exists():
        return (False, label, f"Not found. {hint}.")
    files = list(path.iterdir())
    has_content = any(
        f.is_file() and f.name != ".gitkeep" for f in files
    )
    if not has_content:
        return (False, label, f"Empty. {hint}.")
    return (True, label, "")


def source_files_count():
    """Count actual source files (excluding .gitkeep)."""
    if not SOURCES_DIR.exists():
        return 0
    count = 0
    for ext in ["*.md", "*.txt", "*.eml", "*.html", "*.htm", "*.docx", "*.pdf"]:
        count += len(list(SOURCES_DIR.rglob(ext)))
    return count


def curated_files_count():
    """Count curated files (excluding .gitkeep)."""
    if not CURATED_DIR.exists():
        return 0
    return len([f for f in CURATED_DIR.rglob("*.md") if f.name != "style_context.md"])


def check_control_text():
    """Check for control text file."""
    path = TESTS_DIR / "control_text.md"
    if path.exists():
        words = len(path.read_text(encoding="utf-8").split())
        return (True, words)
    return (False, 0)


def check_env():
    """Check if .env has been customized (not just defaults)."""
    path = BASE_DIR / ".env"
    if not path.exists():
        return (False, "Missing")
    text = path.read_text(encoding="utf-8")
    # Check if LLM_BACKEND is set to something other than comment
    if "LLM_BACKEND=" in text:
        return (True, "Present")
    return (False, "Missing LLM_BACKEND")


def run_script(name):
    """Run a Python script and return exit code."""
    script_path = SCRIPTS_DIR / name
    if not script_path.exists():
        print(f"  Script not found: {script_path}")
        return 1
    print(f"\n  Running {name}...")
    result = subprocess.run([sys.executable, str(script_path)], cwd=BASE_DIR)
    return result.returncode


def print_header():
    """Print the VoxMea header."""
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║          VoxMea — Pipeline               ║")
    print("  ║     Writing Style Cloning for AI          ║")
    print("  ╚══════════════════════════════════════════╝")
    print()


def phase_status(num, label):
    """Render a phase header."""
    return f"\n  ── Phase {num}: {label} ──"


def status_icon(ok):
    return "✓" if ok else "✗"


def item(label, ok, detail=""):
    icon = status_icon(ok)
    if ok:
        return f"    {icon} {label}"
    else:
        return f"    {icon} {label}  —  {detail}"


def print_checks():
    """Run all checks and return a status dict."""
    print_header()
    print("  Checking environment...\n")

    statuses = {}

    # Python version
    py_ok, py_detail = check_python()
    print(item("Python version", py_ok, py_detail))
    statuses["python"] = py_ok

    # Required packages
    pkgs_ok = True
    for pkg_name, install_name in REQUIRED_PACKAGES.items():
        ok, _ = check_package(pkg_name, install_name)
        if not ok:
            pkgs_ok = False
        print(item(f"Package: {install_name}", ok,
                   f"Run: pip install {install_name}"))
    statuses["packages"] = pkgs_ok

    # Optional packages
    for pkg_name, (install_name, desc) in OPTIONAL_PACKAGES.items():
        ok, _, _ = check_optional_package(pkg_name, install_name, desc)
        if not ok:
            print(item(f"Optional: {install_name} ({desc})", ok,
                       f"Run: pip install {install_name}"))

    # Directories
    print()
    print("  Checking pipeline state...\n")

    all_dirs_ok = True
    for label, path, hint in REQUIRED_DIRS:
        ok, _, detail = check_dir(label, path, hint)
        if not ok:
            all_dirs_ok = False
        print(item(f"Directory: {label}", ok, detail))
    statuses["dirs"] = all_dirs_ok

    # Sources
    src_count = source_files_count()
    src_ok = src_count > 0
    if not src_ok:
        print(item("Source texts", False,
                   "Place .md/.txt/.eml/.html/.docx/.pdf files in sources/"))
    else:
        print(item(f"Source texts ({src_count} files found)", True))
    statuses["sources"] = src_ok

    # Curated
    curated_count = curated_files_count()
    curated_ok = curated_count > 0
    if not curated_ok:
        print(item("Curated texts", False,
                   "Run: python start.py --curate  or  python scripts/curate.py"))
    else:
        print(item(f"Curated texts ({curated_count} files)", True))
    statuses["curated"] = curated_ok

    # Style context
    style_ok = (DATASET_DIR / "style_context.md").exists()
    if not style_ok:
        print(item("Style profile", False,
                   "Run: python start.py --analyze  or  python scripts/analyze_style.py"))
    else:
        print(item("Style profile (dataset/style_context.md)", True))
    statuses["style"] = style_ok

    # Unified corpus
    corpus_ok = (DATASET_DIR / "unified_corpus.txt").exists()
    if not corpus_ok:
        print(item("Unified corpus", False,
                   "Run: python start.py --build  or  python scripts/build_dataset.py"))
    else:
        print(item("Unified corpus (dataset/unified_corpus.txt)", True))
    statuses["corpus"] = corpus_ok

    # Control text
    ctrl_ok, ctrl_words = check_control_text()
    if not ctrl_ok:
        print(item("Control text", False,
                   "Create tests/control_text.md with a sample of your writing"))
    else:
        print(item(f"Control text ({ctrl_words} words)", True))
    statuses["control"] = ctrl_ok

    # .env
    env_ok, env_detail = check_env()
    if not env_ok:
        print(item(".env configuration", False,
                   "Copy .env.example or edit .env with your LLM settings"))
    else:
        print(item(f".env configuration ({env_detail})", True))
    statuses["env"] = env_ok

    return statuses


def show_menu(statuses):
    """Show available actions based on current state."""
    print()
    print("  ── Available Actions ──")
    print()

    options = []

    # Phase 1
    if statuses.get("sources"):
        options.append(("c", "curate", "Run curation (sources -> curated)", statuses.get("curated", False)))
    else:
        options.append(("c", "curate", "Need source files first", True))

    # Phase 2
    if statuses.get("curated"):
        options.append(("a", "analyze", "Run style analysis (curated -> style profile)",
                        statuses.get("style", False)))
        options.append(("b", "build", "Build dataset (curated -> unified corpus + JSONL)",
                        statuses.get("corpus", False)))
    else:
        options.append(("a", "analyze", "Need curated texts first", True))
        options.append(("b", "build", "Need curated texts first", True))

    # Phase 3
    if statuses.get("style") and statuses.get("env") and statuses.get("control"):
        options.append(("t", "test", "Run generation tests (needs LLM running)", False))
    else:
        missing = []
        if not statuses.get("style"): missing.append("style profile")
        if not statuses.get("env"): missing.append(".env config")
        if not statuses.get("control"): missing.append("control text")
        options.append(("t", "test", f"Missing: {', '.join(missing)}", True))

    # Phase 4
    if statuses.get("style") and statuses.get("env"):
        options.append(("v", "voice", "Voice mode: generate text in your style", False))
    else:
        missing = []
        if not statuses.get("style"): missing.append("style profile")
        if not statuses.get("env"): missing.append(".env config")
        options.append(("v", "voice", f"Missing: {', '.join(missing)}", True))

    options.append(("s", "status", "Show this status overview", False))
    options.append(("q", "quit", "Exit", False))

    for key, label, desc, disabled in options:
        status = "  " if disabled else ""
        marker = " " if disabled else ">"
        if disabled and "Need" in desc or "Missing" in desc:
            state = f" [{status_icon(False)}]"
            print(f"    {marker} [{key}] {label}{state}")
            print(f"         {desc}")
        elif disabled:
            state = f" [{status_icon(True)}]"
            print(f"    {marker} [{key}] {label}{state}")
        else:
            print(f"    {marker} [{key}] {label}")
            print(f"         {desc}")
        print()

    return options


def run_interactive():
    """Run the interactive launcher loop."""
    statuses = print_checks()

    while True:
        options = show_menu(statuses)

        choice = input("  Choose an option: ").strip().lower()

        if choice == "q":
            print("\n  Goodbye.\n")
            break

        elif choice == "s":
            statuses = print_checks()
            continue

        elif choice == "c":
            if not statuses.get("sources"):
                print("\n  No source files found. Add files to sources/ first.\n")
                continue
            exit_code = run_script("curate.py")
            if exit_code == 0:
                print("  Curation complete.\n")
                statuses = print_checks()
            else:
                print("  Curation failed. Check the output above.\n")

        elif choice == "a":
            if not statuses.get("curated"):
                print("\n  No curated texts found. Run curation first.\n")
                continue
            exit_code = run_script("analyze_style.py")
            if exit_code == 0:
                print("  Analysis complete.\n")
                statuses = print_checks()
            else:
                print("  Analysis failed. Check the output above.\n")

        elif choice == "b":
            if not statuses.get("curated"):
                print("\n  No curated texts found. Run curation first.\n")
                continue
            exit_code = run_script("build_dataset.py")
            if exit_code == 0:
                print("  Dataset build complete.\n")
                statuses = print_checks()
            else:
                print("  Dataset build failed. Check the output above.\n")

        elif choice == "t":
            if not statuses.get("style"):
                print("\n  Style profile missing. Run analysis first.\n")
                continue
            if not statuses.get("env"):
                print("\n  .env not configured. Edit .env with your LLM settings.\n")
                continue
            if not statuses.get("control"):
                print("\n  Control text missing. Create tests/control_text.md.\n")
                continue
            print("\n  Make sure your LLM backend is running before proceeding.")
            confirm = input("  Continue? (y/n): ").strip().lower()
            if confirm == "y":
                exit_code = run_script("test_generation.py")
                if exit_code == 0:
                    print("  Testing complete.\n")
                else:
                    print("  Testing failed. Check the output above.\n")
            else:
                print()

        elif choice == "v":
            if not statuses.get("style"):
                print("\n  Style profile missing. Run analysis first.\n")
                continue
            if not statuses.get("env"):
                print("\n  .env not configured. Edit .env with your LLM settings.\n")
                continue
            print("\n  Voice mode will prompt you for a topic and character count.")
            print("  Make sure your LLM backend is running.")
            confirm = input("  Continue? (y/n): ").strip().lower()
            if confirm == "y":
                exit_code = run_script("voice_mode.py")
                if exit_code == 0:
                    print("  Generation complete.\n")
                else:
                    print("  Generation failed. Check the output above.\n")
            else:
                print()

        else:
            print(f"\n  Unknown option: '{choice}'\n")


def run_phase(phase):
    """Run a specific phase non-interactively."""
    if phase == "curate":
        return run_script("curate.py")
    elif phase == "analyze":
        return run_script("analyze_style.py")
    elif phase == "build":
        return run_script("build_dataset.py")
    elif phase == "test":
        return run_script("test_generation.py")
    elif phase == "voice":
        return run_script("voice_mode.py")
    else:
        print(f"Unknown phase: {phase}")
        return 1


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="VoxMea — Writing Style Cloning Pipeline",
        epilog="Run without arguments for interactive mode."
    )
    parser.add_argument("--curate", action="store_true", help="Run curation (sources -> curated)")
    parser.add_argument("--analyze", action="store_true", help="Run style analysis")
    parser.add_argument("--build", action="store_true", help="Build dataset (unified corpus + JSONL)")
    parser.add_argument("--test", action="store_true", help="Run generation tests")
    parser.add_argument("--voice", action="store_true", help="Launch voice mode")
    parser.add_argument("--check", action="store_true", help="Check pipeline state and exit")
    parser.add_argument("--all", action="store_true", help="Run full pipeline (curate -> analyze -> build)")

    args = parser.parse_args()

    # No args: interactive mode
    if len(sys.argv) == 1:
        run_interactive()
        return

    # Just check
    if args.check:
        statuses = print_checks()
        all_ok = all(v for k, v in statuses.items())
        print()
        if all_ok:
            print("  All checks passed. Pipeline is ready.\n")
        else:
            print("  Some checks failed. Address the issues above.\n")
        return

    # Run full pipeline
    if args.all:
        print("  Running full pipeline...\n")
        steps = [("curate", "Curation"), ("analyze", "Analysis"), ("build", "Dataset")]
        for step_name, step_label in steps:
            print(f"  Phase: {step_label}")
            code = run_phase(step_name)
            if code != 0:
                print(f"  {step_label} failed. Halting.\n")
                sys.exit(1)
            print()
        print("  Pipeline complete.\n")
        return

    # Run individual phases
    if args.curate:
        sys.exit(run_phase("curate"))
    if args.analyze:
        sys.exit(run_phase("analyze"))
    if args.build:
        sys.exit(run_phase("build"))
    if args.test:
        sys.exit(run_phase("test"))
    if args.voice:
        sys.exit(run_phase("voice"))


if __name__ == "__main__":
    main()
