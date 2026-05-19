#!/usr/bin/env python3
"""VoxMea — Style Analyzer (Phase 2)

Analyzes curated corpus and generates a detailed linguistic profile
in dataset/style_context.md — usable as a system prompt for an LLM.
"""

import re
import sys
import statistics
from collections import Counter
from pathlib import Path

CURATED_DIR = Path("curated")
DATASET_DIR = Path("dataset")
OUTPUT_FILE = DATASET_DIR / "style_context.md"

FILLER_WORDS = {
    "actually", "basically", "honestly", "literally", "basically",
    "essentially", "frankly", "just", "like", "basically", "seriously",
    "simply", "well", "you know", "i mean", "sort of", "kind of",
    "i guess", "i suppose", "at the end of the day",
}

CONNECTORS = {
    "however", "therefore", "moreover", "furthermore", "nevertheless",
    "meanwhile", "consequently", "additionally", "besides", "hence",
    "thus", "otherwise", "nonetheless", "then", "next", "finally",
    "after all", "in addition", "on the other hand", "in contrast",
    "as a result", "for example", "for instance", "in particular",
    "first", "second", "third", "lastly", "in conclusion",
}

TONE_FORMAL_INDICATORS = {
    "therefore", "thus", "hence", "furthermore", "nevertheless",
    "consequently", "accordingly", "thereby", "heretofore",
}

TONE_INFORMAL_INDICATORS = {
    "gonna", "wanna", "kinda", "sorta", "lol", "btw", "tbh",
    "yeah", "nah", "cool", "awesome", "stuff", "things",
}

TONE_HUMOR_INDICATORS = {
    "ironically", "hilarious", "absurd", "ridiculous",
    "unfortunately", "surprisingly", "sarcasm",
}


def read_all_texts(base_dir):
    """Read all .md files recursively from curated/ subdirectories."""
    texts = {}
    for filepath in sorted(base_dir.rglob("*.md")):
        if filepath.name == "style_context.md":
            continue
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
            texts[filepath] = text
        except Exception as e:
            print(f"  Warning: could not read {filepath}: {e}")
    return texts


def extract_sentences(text):
    """Split text into sentences using regex."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def analyze_vocabulary(texts):
    """Analyze vocabulary: word frequency, unique ratio, n-grams."""
    all_words = []
    for text in texts.values():
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        all_words.extend(words)

    total_words = len(all_words)
    unique_words = len(set(all_words))

    word_freq = Counter(all_words).most_common(100)
    top_50 = word_freq[:50]

    # Bigrams
    bigrams = [f"{all_words[i]} {all_words[i+1]}" for i in range(len(all_words)-1)]
    top_bigrams = Counter(bigrams).most_common(20)

    # Trigrams
    trigrams = [f"{all_words[i]} {all_words[i+1]} {all_words[i+2]}" for i in range(len(all_words)-2)]
    top_trigrams = Counter(trigrams).most_common(10)

    return {
        "total_words": total_words,
        "unique_words": unique_words,
        "unique_ratio": round(unique_words / total_words * 100, 1) if total_words else 0,
        "top_words": top_50,
        "top_bigrams": top_bigrams,
        "top_trigrams": top_trigrams,
    }


def analyze_sentences(texts):
    """Analyze sentence structure."""
    all_sentences = []
    for text in texts.values():
        all_sentences.extend(extract_sentences(text))

    lengths = [len(s.split()) for s in all_sentences]

    if not lengths:
        return {
            "count": 0,
            "avg_length": 0,
            "std_dev": 0,
            "min_length": 0,
            "max_length": 0,
            "median": 0,
            "longest_sentences": [],
            "shortest_sentences": [],
        }

    # Find longest and shortest sentences
    longest = sorted(all_sentences, key=lambda s: len(s.split()), reverse=True)[:5]
    shortest = sorted(all_sentences, key=lambda s: len(s.split()))[:5]

    return {
        "count": len(lengths),
        "avg_length": round(statistics.mean(lengths), 1),
        "std_dev": round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0,
        "min_length": min(lengths),
        "max_length": max(lengths),
        "median": round(statistics.median(lengths), 1),
        "longest_sentences": longest,
        "shortest_sentences": shortest,
    }


def analyze_punctuation(texts):
    """Analyze punctuation usage fingerprint."""
    combined = "".join(texts.values())
    total_chars = len(combined)

    punct_counts = {
        "em_dash": combined.count("\u2014") + combined.count("---"),
        "ellipsis": combined.count("\u2026") + combined.count("..."),
        "exclamation": combined.count("!"),
        "question": combined.count("?"),
        "semicolon": combined.count(";"),
        "colon": combined.count(":"),
        "comma": combined.count(","),
        "period": combined.count("."),
        "quote_single": combined.count("'"),
        "quote_double": combined.count('"'),
        "parenthesis": combined.count("(") + combined.count(")"),
    }

    total_punct = sum(punct_counts.values()) or 1
    ratios = {k: round(v / total_punct * 100, 1) for k, v in punct_counts.items()}

    return {
        "counts": punct_counts,
        "ratios": ratios,
    }


def analyze_fillers_and_connectors(texts):
    """Detect filler words and connector usage."""
    combined = " ".join(texts.values()).lower()

    filler_counts = {}
    for word in FILLER_WORDS:
        count = len(re.findall(r'\b' + re.escape(word) + r'\b', combined))
        if count > 0:
            filler_counts[word] = count

    connector_counts = {}
    for word in CONNECTORS:
        count = len(re.findall(r'\b' + re.escape(word) + r'\b', combined))
        if count > 0:
            connector_counts[word] = count

    top_fillers = sorted(filler_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    top_connectors = sorted(connector_counts.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        "filler_words": top_fillers,
        "connectors": top_connectors,
    }


def analyze_tone(texts):
    """Classify tone based on vocabulary signals."""
    combined = " ".join(texts.values()).lower()
    words = combined.split()

    formal_count = sum(1 for w in words if w in TONE_FORMAL_INDICATORS)
    informal_count = sum(1 for w in words if w in TONE_INFORMAL_INDICATORS)
    humor_count = sum(1 for w in words if w in TONE_HUMOR_INDICATORS)

    total = formal_count + informal_count or 1

    return {
        "formal_score": formal_count,
        "informal_score": informal_count,
        "humor_score": humor_count,
        "balance": "formal" if formal_count > informal_count else "informal",
        "formality_ratio": round(formal_count / total * 100, 1),
    }


def generate_style_context(vocab, sentences, punct, fillers, tone, texts):
    """Generate the style_context.md file content."""
    lines = []
    lines.append("# Style Context — VoxMea")
    lines.append("")
    lines.append("> Auto-generated linguistic profile for LLM style replication.")
    lines.append("> Generated by analyze_style.py")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"This author writes with a **{tone['balance']}** voice, using ")
    lines.append(f"an average of **{sentences['avg_length']} words per sentence** ")
    lines.append(f"with a vocabulary of **{vocab['unique_words']:,} unique words** ")
    lines.append(f"(**{vocab['unique_ratio']}%** unique ratio across {vocab['total_words']:,} total words). ")
    if tone['humor_score'] > 0:
        lines.append("The writing shows signs of humor and personality. ")
    lines.append("")
    lines.append("")

    # Vocabulary
    lines.append("## Vocabulary Characteristics")
    lines.append("")
    lines.append("### Most Frequent Words")
    lines.append("")
    top_words_str = ", ".join(f"*{w}* ({c})" for w, c in vocab["top_words"][:20])
    lines.append(f"{top_words_str}")
    lines.append("")

    if vocab["top_bigrams"]:
        lines.append("### Common Bigrams (2-word phrases)")
        lines.append("")
        bigram_str = ", ".join(f"*{bg}* ({c})" for bg, c in vocab["top_bigrams"][:10])
        lines.append(f"{bigram_str}")
        lines.append("")

    if vocab["top_trigrams"]:
        lines.append("### Common Trigrams (3-word phrases)")
        lines.append("")
        trigram_str = ", ".join(f"*{tg}* ({c})" for tg, c in vocab["top_trigrams"][:5])
        lines.append(f"{trigram_str}")
        lines.append("")

    # Sentence structure
    lines.append("## Sentence Structure")
    lines.append("")
    lines.append(f"- **Total sentences analyzed:** {sentences['count']}")
    lines.append(f"- **Average length:** {sentences['avg_length']} words")
    lines.append(f"- **Standard deviation:** {sentences['std_dev']} words")
    lines.append(f"- **Median:** {sentences['median']} words")
    lines.append(f"- **Shortest:** {sentences['min_length']} words")
    lines.append(f"- **Longest:** {sentences['max_length']} words")
    lines.append("")

    if sentences["shortest_sentences"]:
        lines.append("### Shortest Examples")
        lines.append("")
        for s in sentences["shortest_sentences"][:3]:
            lines.append(f"> {s}")
        lines.append("")

    if sentences["longest_sentences"]:
        lines.append("### Longest Examples")
        lines.append("")
        for s in sentences["longest_sentences"][:3]:
            lines.append(f"> {s}")
        lines.append("")

    # Punctuation
    lines.append("## Punctuation Fingerprint")
    lines.append("")
    lines.append("| Mark | Count | Ratio |")
    lines.append("|------|-------|-------|")
    for mark in ["period", "comma", "exclamation", "question", "semicolon", "colon",
                  "em_dash", "ellipsis", "quote_single", "quote_double", "parenthesis"]:
        if mark in punct["counts"] and punct["counts"][mark] > 0:
            lines.append(f"| {mark} | {punct['counts'][mark]} | {punct['ratios'][mark]}% |")
    lines.append("")

    # Fillers and connectors
    lines.append("## Filler Words & Connectors")
    lines.append("")

    if fillers["filler_words"]:
        lines.append("### Filler Words")
        lines.append("")
        filler_str = ", ".join(f"*{w}* ({c})" for w, c in fillers["filler_words"][:10])
        lines.append(f"{filler_str}")
        lines.append("")

    if fillers["connectors"]:
        lines.append("### Connectors / Transition Words")
        lines.append("")
        conn_str = ", ".join(f"*{w}* ({c})" for w, c in fillers["connectors"][:10])
        lines.append(f"{conn_str}")
        lines.append("")

    # Tone
    lines.append("## Tone & Personality")
    lines.append("")
    lines.append(f"- **Formal indicators:** {tone['formal_score']}")
    lines.append(f"- **Informal indicators:** {tone['informal_score']}")
    lines.append(f"- **Humor indicators:** {tone['humor_score']}")
    lines.append(f"- **Overall balance:** {tone['balance']} (ratio: {tone['formality_ratio']}% formal)")
    lines.append("")
    if tone["humor_score"] > 0:
        lines.append("The author uses humor and irony, suggesting a natural, conversational voice.")
    if tone["informal_score"] > tone["formal_score"]:
        lines.append("The writing leans casual and conversational rather than academic.")
    else:
        lines.append("The writing leans formal and structured.")
    lines.append("")

    # Writing DNA
    lines.append("## Writing DNA — Key Traits")
    lines.append("")
    traits = []
    if sentences["avg_length"] < 15:
        traits.append("Short, punchy sentences — gets to the point quickly")
    elif sentences["avg_length"] > 25:
        traits.append("Long, flowing sentences with rich detail")
    else:
        traits.append("Moderate sentence length — balanced and readable")

    if punct["ratios"].get("em_dash", 0) > 1:
        traits.append("Frequent use of em-dashes for asides and emphasis")
    if punct["ratios"].get("ellipsis", 0) > 1:
        traits.append("Ellipses used for trailing thoughts or dramatic pauses")
    if punct["ratios"].get("exclamation", 0) > 2:
        traits.append("Enthusiastic punctuation — frequent exclamation marks")
    if punct["ratios"].get("question", 0) > 2:
        traits.append("Uses rhetorical questions to engage the reader")

    if tone["informal_score"] > tone["formal_score"]:
        traits.append("Conversational and approachable tone")
    else:
        traits.append("Measured and thoughtful tone")

    traits.append(f"Vocabulary richness: {vocab['unique_ratio']}% unique words")

    for i, trait in enumerate(traits[:7], 1):
        lines.append(f"{i}. {trait}")
    lines.append("")

    # Representative fragments
    lines.append("## Representative Fragments")
    lines.append("")
    lines.append("The following excerpts exemplify the author's natural voice:")
    lines.append("")

    # Pick representative samples
    all_texts = list(texts.values())
    fragments = []
    for text in all_texts[:5]:
        sentences_list = extract_sentences(text)
        for sent in sentences_list[:2]:
            if 15 < len(sent.split()) < 40 and sent not in fragments:
                fragments.append(sent)
                if len(fragments) >= 5:
                    break
        if len(fragments) >= 5:
            break

    for frag in fragments[:5]:
        lines.append(f"> {frag}")
        lines.append("")

    # Instructions for LLM
    lines.append("---")
    lines.append("")
    lines.append("## Instructions for LLM Integration")
    lines.append("")
    lines.append("When using this profile as a system prompt:")
    lines.append("")
    lines.append("1. Present the summary as a high-level instruction.")
    lines.append("2. Reinforce key vocabulary preferences and punctuation patterns.")
    lines.append("3. Include the representative fragments as few-shot examples.")
    lines.append("4. Guard against generic/corporate language.")
    lines.append("5. Remind the model to prioritize voice over correctness.")
    lines.append("")
    lines.append("*Generated by VoxMea Style Analyzer*")
    lines.append("")

    return "\n".join(lines)


def main():
    print("VoxMea — Style Analyzer")
    print("=" * 50)

    if not CURATED_DIR.exists():
        print(f"Curated directory not found: {CURATED_DIR}")
        print("Run curate.py first to populate curated/")
        sys.exit(1)

    md_files = list(CURATED_DIR.rglob("*.md"))
    if not md_files:
        print(f"No .md files found in {CURATED_DIR}")
        print("Run curate.py first to populate curated/")
        sys.exit(1)

    print(f"Reading texts from {CURATED_DIR}/...")
    texts = read_all_texts(CURATED_DIR)
    print(f"  Found {len(texts)} text files")

    print("\nAnalyzing vocabulary...")
    vocab = analyze_vocabulary(texts)
    print(f"  {vocab['total_words']} total words, {vocab['unique_words']} unique ({vocab['unique_ratio']}%)")

    print("Analyzing sentence structure...")
    sentences = analyze_sentences(texts)
    print(f"  {sentences['count']} sentences, avg {sentences['avg_length']} words")

    print("Analyzing punctuation...")
    punct = analyze_punctuation(texts)

    print("Analyzing fillers and connectors...")
    fillers = analyze_fillers_and_connectors(texts)
    print(f"  {len(fillers['filler_words'])} filler types, {len(fillers['connectors'])} connector types")

    print("Mapping tone...")
    tone = analyze_tone(texts)
    print(f"  Balance: {tone['balance']}")

    print(f"\nGenerating {OUTPUT_FILE}...")
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    content = generate_style_context(vocab, sentences, punct, fillers, tone, texts)
    OUTPUT_FILE.write_text(content, encoding="utf-8")

    print(f"  Style profile written to {OUTPUT_FILE}")
    print("\nDone.")


if __name__ == "__main__":
    main()
