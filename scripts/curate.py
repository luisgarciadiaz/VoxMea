#!/usr/bin/env python3
"""VoxMea — Text Curation Pipeline (Phase 1)

Scans sources/ and produces clean, classified files in curated/.
Supports .md, .txt, .eml, .html, .docx, and .pdf.
Strips YAML frontmatter, code blocks, and redacts sensitive data.
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import docx
except ImportError:
    docx = None

try:
    import fitz
except ImportError:
    fitz = None

import email
from email import policy

SOURCE_DIR = Path("sources")
CURATED_DIR = Path("curated")
REDACTION_CONFIG = Path("redaction_patterns.yaml")

DEFAULT_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b',
    "ssn": r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
    "credit_card": r'\b(?:\d{4}[- ]?){3}\d{4}\b',
    "url": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
    "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
}

CLASSIFICATION_KEYWORDS = {
    "narrative": [
        "i remember", "i felt", "i thought", "i realized", "it was",
        "i recall", "back then", "i used to", "i wonder", "i miss",
        "reflecting", "looking back", "that morning", "i'll never forget",
    ],
    "argumentative": [
        "i believe", "in my opinion", "i think", "the problem", "we should",
        "it is clear", "the truth is", "the issue", "we need",
        "however", "therefore", "because", "this is why",
    ],
    "informal": [
        "lol", "btw", "tbh", "hey", "anyway", "so yeah",
        "actually", "literally", "honestly", "you know",
        "kinda", "stuff", "things", "whatever", "awesome",
    ],
    "technical": [
        "function", "class", "import", "def ", "return",
        "server", "database", "api", "endpoint", "config",
        "build", "framework", "library", "module", "interface",
    ],
}

CLASSIFICATION_THRESHOLD = 3

VALID_EXTENSIONS = {".md", ".txt", ".eml", ".html", ".htm", ".docx", ".pdf"}

stats = {"processed": 0, "skipped": 0, "total_words": 0, "redactions": 0, "by_type": {}}


def load_redaction_patterns(config_path):
    """Load redaction patterns from YAML config with defaults fallback."""
    patterns = dict(DEFAULT_PATTERNS)

    if config_path.exists() and yaml:
        with open(config_path, "r", encoding="utf-8") as f:
            custom = yaml.safe_load(f)
        if custom:
            user_patterns = custom.get("patterns", {})
            for name, pattern in user_patterns.items():
                if pattern is None or pattern == "":
                    patterns.pop(name, None)
                else:
                    patterns[name] = pattern
            for name, pattern in custom.get("custom_patterns", {}).items():
                patterns[f"custom_{name}"] = pattern

    return patterns


def strip_yaml_frontmatter(text):
    """Remove Obsidian-style YAML frontmatter (--- ... ---)."""
    return re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, count=1, flags=re.DOTALL)


def strip_code_blocks(text):
    """Remove fenced code blocks and inline code."""
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`\n]+`', '', text)
    return text


def redact_sensitive_data(text, patterns):
    """Apply redaction patterns to mask sensitive information."""
    count = 0
    for name, pattern in patterns.items():
        replacement = f"[REDACTED:{name}]"
        text, n = re.subn(pattern, replacement, text, flags=re.IGNORECASE)
        count += n
    return text, count


def extract_html(filepath):
    """Extract readable text from HTML files."""
    if BeautifulSoup is None:
        return filepath.read_text(encoding="utf-8", errors="replace")
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def extract_docx(filepath):
    """Extract text from .docx files."""
    if docx is None:
        raise ImportError("python-docx is required for .docx files. Install: pip install python-docx")
    document = docx.Document(str(filepath))
    return "\n".join(p.text for p in document.paragraphs)


def extract_pdf(filepath):
    """Extract text from PDF files."""
    if fitz is None:
        raise ImportError("pymupdf is required for .pdf files. Install: pip install pymupdf")
    document = fitz.open(str(filepath))
    text = "\n".join(page.get_text() for page in document)
    document.close()
    return text


def extract_eml(filepath):
    """Extract plain text content from .eml files."""
    with open(filepath, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    parts = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    payload = part.get_content()
                    if payload:
                        parts.append(payload)
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_content()
            if payload:
                parts.append(payload)
        except Exception:
            pass

    return "\n".join(parts)


def read_file(filepath):
    """Read and extract text from a file based on its extension."""
    suffix = filepath.suffix.lower()

    readers = {
        ".md": lambda p: p.read_text(encoding="utf-8", errors="replace"),
        ".txt": lambda p: p.read_text(encoding="utf-8", errors="replace"),
        ".html": extract_html,
        ".htm": extract_html,
        ".eml": extract_eml,
        ".docx": extract_docx,
        ".pdf": extract_pdf,
    }

    reader = readers.get(suffix)
    if not reader:
        raise ValueError(f"Unsupported file format: {suffix}")

    return reader(filepath)


def classify_text(text, filepath):
    """Classify text into narrative, argumentative, informal, or technical."""
    lower_text = text.lower()

    path_str = str(filepath).lower()
    for category in CLASSIFICATION_KEYWORDS:
        if category in path_str:
            return category

    scores = {}
    for category, keywords in CLASSIFICATION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower_text)
        if score >= CLASSIFICATION_THRESHOLD:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)

    return "narrative"


def process_file(filepath, patterns, verbose):
    """Process a single source file."""
    rel_path = filepath.relative_to(SOURCE_DIR)

    try:
        raw_text = read_file(filepath)
    except (ImportError, ValueError, Exception) as e:
        print(f"  SKIPPED {rel_path}: {e}")
        stats["skipped"] += 1
        return

    text = strip_yaml_frontmatter(raw_text)
    text = strip_code_blocks(text)
    text, redacted = redact_sensitive_data(text, patterns)

    word_count = len(text.split())
    if word_count < 10:
        if verbose:
            print(f"  SKIPPED {rel_path}: too short ({word_count} words)")
        stats["skipped"] += 1
        return

    stats["processed"] += 1
    stats["total_words"] += word_count
    stats["redactions"] += redacted

    classification = classify_text(text, filepath)
    stats["by_type"][classification] = stats["by_type"].get(classification, 0) + 1

    out_dir = CURATED_DIR / classification
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{filepath.stem}.md"
    out_path.write_text(text, encoding="utf-8")

    if verbose:
        print(f"  {rel_path} -> {out_dir.name}/ ({word_count} words, {redacted} redactions)")


def print_stats():
    """Print summary statistics."""
    print("\n" + "=" * 50)
    print("CURATION STATISTICS")
    print("=" * 50)
    print(f"  Files processed:    {stats['processed']}")
    print(f"  Files skipped:      {stats['skipped']}")
    print(f"  Total words:        {stats['total_words']:,}")
    print(f"  Redactions applied: {stats['redactions']}")
    print(f"\n  Classification:")
    for cat in ["narrative", "argumentative", "informal", "technical"]:
        count = stats["by_type"].get(cat, 0)
        if count:
            print(f"    {cat}: {count}")
    print()


def main():
    parser = argparse.ArgumentParser(description="VoxMea - Text Curation Pipeline")
    parser.add_argument("-s", "--source", default="sources", help="Source directory (default: sources/)")
    parser.add_argument("-o", "--output", default="curated", help="Output directory (default: curated/)")
    parser.add_argument("-c", "--config", default="redaction_patterns.yaml", help="Redaction config path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    global SOURCE_DIR, CURATED_DIR
    SOURCE_DIR = Path(args.source)
    CURATED_DIR = Path(args.output)

    if not SOURCE_DIR.exists():
        print(f"Source directory not found: {SOURCE_DIR}")
        print("Create it and add your text files (.md, .txt, .eml, .html, .docx, .pdf)")
        sys.exit(1)

    CURATED_DIR.mkdir(parents=True, exist_ok=True)

    patterns = load_redaction_patterns(Path(args.config))
    print(f"Loaded {len(patterns)} redaction patterns")

    files = []
    for ext in VALID_EXTENSIONS:
        files.extend(SOURCE_DIR.rglob(f"*{ext}"))
    files = [f for f in files if not any(
        part.startswith(".") for part in f.relative_to(SOURCE_DIR).parts
    )]

    if not files:
        print(f"No supported files found in {SOURCE_DIR}/")
        print(f"  Supported: {', '.join(VALID_EXTENSIONS)}")
        sys.exit(0)

    print(f"Found {len(files)} files to process\n")

    for filepath in sorted(files):
        process_file(filepath, patterns, args.verbose)

    print_stats()


if __name__ == "__main__":
    main()
