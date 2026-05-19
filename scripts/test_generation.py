#!/usr/bin/env python3
"""VoxMea — Generation Testing (Phase 3)

End-to-end testing script that:
- Connects to configured LLM backend (Ollama / LM Studio / llama.cpp)
- Sends test prompts with style context as system message
- Compares generated text against control text
- Saves timestamped results
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from collections import Counter

try:
    import requests
except ImportError:
    print("requests is required. Install: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
except ImportError:
    import os

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_DIR / "tests" / "results"
CONTROL_TEXT = PROJECT_DIR / "tests" / "control_text.md"
STYLE_CONTEXT = PROJECT_DIR / "dataset" / "style_context.md"
TEST_PROMPTS = PROJECT_DIR / "prompts" / "test_prompts.md"
SYSTEM_PROMPT = PROJECT_DIR / "prompts" / "system_prompt.md"


def get_config():
    """Load configuration from environment variables."""
    return {
        "backend": os.getenv("LLM_BACKEND", "ollama"),
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "lmstudio_host": os.getenv("LMSTUDIO_HOST", "http://localhost:1234/v1"),
        "llamacpp_host": os.getenv("LLAMACPP_HOST", "http://localhost:8080"),
        "model": os.getenv("MODEL_NAME", "llama3.2"),
    }


def load_text(filepath):
    """Load text content from a file."""
    if filepath.exists():
        return filepath.read_text(encoding="utf-8", errors="replace").strip()
    return ""


def load_test_prompts(filepath):
    """Load test prompts from markdown file."""
    if not filepath.exists():
        return [{"title": "Default Prompt", "prompt": "Write a short reflective paragraph about a personal experience."}]

    text = filepath.read_text(encoding="utf-8")
    prompts = []

    # Split by ## headings
    sections = re.split(r'^##\s+', text, flags=re.MULTILINE)
    for section in sections[1:]:
        lines = section.strip().split("\n")
        title = lines[0].strip()
        body = "\n".join(line for line in lines[1:] if not line.startswith(">") and not line.startswith("*"))
        body = body.strip()
        if body:
            prompts.append({"title": title, "prompt": body})

    return prompts


def call_llm(backend, host, model, system_prompt, user_prompt):
    """Call the LLM backend API and return the generated text."""
    if backend == "ollama":
        return call_ollama(host, model, system_prompt, user_prompt)
    elif backend == "lmstudio":
        return call_lmstudio(host, model, system_prompt, user_prompt)
    elif backend == "llamacpp":
        return call_llamacpp(host, system_prompt, user_prompt)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def call_ollama(host, model, system_prompt, user_prompt):
    """Call Ollama /api/generate endpoint."""
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
    }
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json().get("response", "")


def call_lmstudio(host, model, system_prompt, user_prompt):
    """Call LM Studio /v1/chat/completions endpoint."""
    url = f"{host}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def call_llamacpp(host, system_prompt, user_prompt):
    """Call llama.cpp server /completion endpoint."""
    url = f"{host}/completion"
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    payload = {
        "prompt": full_prompt,
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json().get("content", "")


def extract_words(text):
    """Extract lowercase words from text."""
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())


def lexical_similarity(text1, text2):
    """Calculate lexical overlap (shared vocabulary percentage)."""
    words1 = set(extract_words(text1))
    words2 = set(extract_words(text2))

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2
    return round(len(intersection) / len(union) * 100, 1)


def avg_sentence_length(text):
    """Calculate average sentence length in words."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if len(s.split()) > 2]
    if not sentences:
        return 0
    lengths = [len(s.split()) for s in sentences]
    return round(sum(lengths) / len(lengths), 1)


def punctuation_similarity(text1, text2):
    """Compare punctuation pattern similarity."""
    def punct_profile(text):
        marks = {".": 0, "!": 0, "?": 0, ",": 0, ";": 0, ":": 0, "—": 0, "...": 0}
        text_len = len(text) or 1
        for mark in marks:
            if mark == "...":
                marks[mark] = len(re.findall(r'\.\.\.', text))
            elif mark == "—":
                marks[mark] = text.count("\u2014") + text.count("---")
            else:
                marks[mark] = text.count(mark)
        total = sum(marks.values()) or 1
        return {k: v / total for k, v in marks.items()}

    p1 = punct_profile(text1)
    p2 = punct_profile(text2)

    # Cosine similarity
    dot = sum(p1[k] * p2[k] for k in p1)
    norm1 = sum(v ** 2 for v in p1.values()) ** 0.5
    norm2 = sum(v ** 2 for v in p2.values()) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return round(dot / (norm1 * norm2) * 100, 1)


def readability_score(text):
    """Calculate a simple readability score (Flesch-Kincaid approximation)."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    num_sentences = len(sentences) or 1
    words = text.split()
    num_words = len(words) or 1
    syllables = sum(count_syllables(w) for w in words)

    # Flesch-Kincaid Grade Level
    grade = 0.39 * (num_words / num_sentences) + 11.8 * (syllables / num_words) - 15.59
    return round(max(0, min(grade, 20)), 1)


def count_syllables(word):
    """Simple syllable counter (vowel groups)."""
    word = word.lower().strip(".,!?;:")
    if not word:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    return max(count, 1)


def score_generation(control_text, generated_text):
    """Score a generated text against the control text."""
    return {
        "lexical_similarity": lexical_similarity(control_text, generated_text),
        "control_avg_sentence_length": avg_sentence_length(control_text),
        "generated_avg_sentence_length": avg_sentence_length(generated_text),
        "punctuation_similarity": punctuation_similarity(control_text, generated_text),
        "control_readability": readability_score(control_text),
        "generated_readability": readability_score(generated_text),
        "generated_word_count": len(generated_text.split()),
        "generated_char_count": len(generated_text),
    }


def format_report(test_name, scores, generated_text):
    """Format a test result block."""
    lines = []
    lines.append(f"## Test: {test_name}")
    lines.append(f"Timestamp: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("### Metrics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    for key, value in scores.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    lines.append("### Generated Text")
    lines.append("")
    lines.append(generated_text)
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main():
    print("VoxMea — Generation Testing")
    print("=" * 50)

    config = get_config()
    print(f"Backend: {config['backend']}")
    print(f"Model:   {config['model']}")

    # Load control text
    control_text = load_text(CONTROL_TEXT)
    if not control_text:
        print(f"\nNo control text found at {CONTROL_TEXT}")
        print("Create tests/control_text.md with a representative sample of your writing.")
        control_text = input("Enter a sample paragraph as control text (or press Enter to skip): ")
        if not control_text:
            print("Skipping comparison metrics.")
    else:
        print(f"\nLoaded control text ({len(control_text.split())} words)")

    # Load style context
    style_context = load_text(STYLE_CONTEXT)
    if not style_context:
        print(f"No style context found at {STYLE_CONTEXT}")
        print("Run analyze_style.py first, or use the base system prompt.")
        style_context = load_text(SYSTEM_PROMPT)

    # Load system prompt
    base_system = load_text(SYSTEM_PROMPT)
    if base_system and style_context:
        # Combine: replace {{STYLE_PROFILE}} placeholder
        combined = base_system.replace("{{STYLE_PROFILE}}", style_context)
    elif style_context:
        combined = style_context
    else:
        combined = "Write in a natural, personal voice."

    # Load test prompts
    prompts = load_test_prompts(TEST_PROMPTS)
    if not prompts:
        print(f"\nNo test prompts found at {TEST_PROMPTS}")
        sys.exit(1)

    print(f"\nLoaded {len(prompts)} test prompts")

    # Results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = RESULTS_DIR / f"test_results_{timestamp}.md"
    report_parts = []
    report_parts.append(f"# VoxMea — Test Results")
    report_parts.append(f"Run: {datetime.now().isoformat()}")
    report_parts.append(f"Backend: {config['backend']}, Model: {config['model']}")
    report_parts.append("")

    all_metrics = []

    for i, tp in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] {tp['title']}")
        print(f"  Prompt: {tp['prompt'][:80]}...")

        try:
            print(f"  Calling LLM...")
            start = time.time()
            generated = call_llm(
                config["backend"],
                config["ollama_host"] if config["backend"] == "ollama"
                    else config["lmstudio_host"] if config["backend"] == "lmstudio"
                    else config["llamacpp_host"],
                config["model"],
                combined,
                tp["prompt"],
            )
            elapsed = time.time() - start
            print(f"  Generated {len(generated.split())} words in {elapsed:.1f}s")

            if control_text:
                scores = score_generation(control_text, generated)
                all_metrics.append(scores)
                print(f"  Lexical similarity: {scores['lexical_similarity']}%")
            else:
                scores = {"note": "No control text available for comparison"}

            report_parts.append(format_report(tp["title"], scores, generated))

        except requests.exceptions.ConnectionError:
            msg = f"Could not connect to {config['backend']} at the configured host."
            print(f"  ERROR: {msg}")
            report_parts.append(f"## Test: {tp['title']}")
            report_parts.append(f"**ERROR:** {msg}")
            report_parts.append("")
        except Exception as e:
            print(f"  ERROR: {e}")
            report_parts.append(f"## Test: {tp['title']}")
            report_parts.append(f"**ERROR:** {e}")
            report_parts.append("")

    # Summary
    if all_metrics:
        avg_lexical = sum(m["lexical_similarity"] for m in all_metrics) / len(all_metrics)
        avg_punct = sum(m["punctuation_similarity"] for m in all_metrics) / len(all_metrics)

        summary = f"""
## Summary

| Metric | Average |
|--------|---------|
| Lexical Similarity | {avg_lexical:.1f}% |
| Punctuation Similarity | {avg_punct:.1f}% |
| Tests Run | {len(all_metrics)} |
"""
        report_parts.append(summary)

    report = "\n".join(report_parts)
    report_path.write_text(report, encoding="utf-8")
    print(f"\nResults saved to {report_path}")
    print("Done.")


if __name__ == "__main__":
    main()
