#!/usr/bin/env python3
"""VoxMea — Dataset Builder (Phase 2)

Consolidates curated texts into LLM-ready formats:
- unified_corpus.txt with document separators
- dataset.jsonl with prompt/completion pairs (optional)
- Smart chunking with configurable size and overlap
"""

import json
import re
import sys
from pathlib import Path

CURATED_DIR = Path("curated")
DATASET_DIR = Path("dataset")
STYLE_CONTEXT = DATASET_DIR / "style_context.md"
UNIFIED_CORPUS = DATASET_DIR / "unified_corpus.txt"
DATASET_JSONL = DATASET_DIR / "dataset.jsonl"

try:
    import tiktoken
    TOKENIZER = tiktoken.get_encoding("cl100k_base")
except ImportError:
    TOKENIZER = None


def count_tokens(text):
    """Count tokens using tiktoken if available, else character-based estimate."""
    if TOKENIZER:
        return len(TOKENIZER.encode(text))
    return len(text) // 4


def load_style_context():
    """Load the style context / system prompt."""
    if STYLE_CONTEXT.exists():
        return STYLE_CONTEXT.read_text(encoding="utf-8")
    return ""


def collect_texts(base_dir):
    """Collect all .md files with their metadata."""
    texts = []
    for filepath in sorted(base_dir.rglob("*.md")):
        if filepath.name == "style_context.md":
            continue

        relative = filepath.relative_to(base_dir)
        category = relative.parts[0] if len(relative.parts) > 1 else "unknown"

        try:
            content = filepath.read_text(encoding="utf-8", errors="replace").strip()
        except Exception as e:
            print(f"  Warning: could not read {filepath}: {e}")
            continue

        if len(content) < 50:
            continue

        tokens = count_tokens(content)

        texts.append({
            "path": str(relative),
            "category": category,
            "content": content,
            "tokens": tokens,
        })

    return texts


def build_unified_corpus(texts):
    """Concatenate all texts with document separators and metadata headers."""
    parts = []
    for t in texts:
        header = (
            f"{'=' * 60}\n"
            f"DOCUMENT: {t['path']}\n"
            f"CATEGORY: {t['category']}\n"
            f"TOKENS: {t['tokens']}\n"
            f"{'=' * 60}\n"
        )
        parts.append(header + t["content"])

    return "\n\n".join(parts)


def smart_chunks(text, chunk_size=2000, overlap=200):
    """Split text into chunks respecting paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if current_tokens + para_tokens > chunk_size and current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(chunk_text)

            # Overlap: keep last paragraphs up to overlap tokens
            overlap_texts = []
            overlap_tokens = 0
            for prev_para in reversed(current_chunk):
                pt = count_tokens(prev_para)
                if overlap_tokens + pt > overlap:
                    break
                overlap_texts.insert(0, prev_para)
                overlap_tokens += pt

            current_chunk = overlap_texts
            current_tokens = overlap_tokens

        current_chunk.append(para)
        current_tokens += para_tokens

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def build_jsonl(texts, style_context, chunk_size=2000):
    """Generate JSONL with prompt/completion pairs for fine-tuning."""
    records = []
    system_content = style_context if style_context else "Write in the author's natural style."

    for t in texts:
        content = t["content"]
        tokens = count_tokens(content)

        if tokens > chunk_size:
            chunks = smart_chunks(content, chunk_size // 2, 100)
            for i, chunk in enumerate(chunks):
                user_prompt = f"Write a {t['category']} text in your voice about the following topic:\n\n{chunk[:200]}..."
                record = {
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_prompt[:500]},
                        {"role": "assistant", "content": chunk},
                    ]
                }
                records.append(record)
        else:
            # Use the full text as assistant response
            user_prompt = f"Write a {t['category']} text in your voice."
            record = {
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": content},
                ]
            }
            records.append(record)

    return records


def main():
    print("VoxMea — Dataset Builder")
    print("=" * 50)

    if not CURATED_DIR.exists():
        print(f"Curated directory not found: {CURATED_DIR}")
        print("Run curate.py first")
        sys.exit(1)

    print(f"Collecting texts from {CURATED_DIR}/...")
    texts = collect_texts(CURATED_DIR)

    if not texts:
        print("No texts found. Run curate.py first.")
        sys.exit(1)

    total_tokens = sum(t["tokens"] for t in texts)
    print(f"  Found {len(texts)} texts, {total_tokens:,} total tokens")

    if TOKENIZER:
        print("  Token counting: tiktoken (cl100k_base)")
    else:
        print("  Token counting: character-based estimate (install tiktoken for accuracy)")

    # Create output directory
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Build unified corpus
    print("\nBuilding unified corpus...")
    corpus = build_unified_corpus(texts)
    UNIFIED_CORPUS.write_text(corpus, encoding="utf-8")
    corpus_tokens = count_tokens(corpus)
    print(f"  Written to {UNIFIED_CORPUS}")
    print(f"  {corpus_tokens:,} tokens")

    # 2. Smart chunking
    print("\nGenerating smart chunks...")
    chunks = smart_chunks(corpus)
    print(f"  Created {len(chunks)} chunks (target {2000} tokens each, {200} overlap)")

    # Save chunks for reference
    chunks_dir = DATASET_DIR / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    for i, chunk in enumerate(chunks, 1):
        chunk_file = chunks_dir / f"chunk_{i:04d}.txt"
        chunk_file.write_text(chunk, encoding="utf-8")
    print(f"  Chunks saved to {chunks_dir}/")

    # 3. Generate JSONL (optional)
    print("\nGenerating JSONL dataset...")
    style_context = load_style_context()
    records = build_jsonl(texts, style_context)

    with open(DATASET_JSONL, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"  Written to {DATASET_JSONL}")
    print(f"  {len(records)} prompt/completion pairs")

    # Summary
    print("\n" + "=" * 50)
    print("DATASET SUMMARY")
    print("=" * 50)
    print(f"  Source texts:     {len(texts)}")
    print(f"  Total tokens:     {total_tokens:,}")
    print(f"  Unified corpus:   {corpus_tokens:,} tokens")
    print(f"  Chunks:           {len(chunks)}")
    print(f"  JSONL records:    {len(records)}")
    print()


if __name__ == "__main__":
    main()
