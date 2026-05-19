# 📋 Changelog — VoxMea

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.2.0] — 2026-05-19

### Added
- 🎉 **Phase 1: Data Extraction & Curation** — Complete pipeline implementation.
- 📄 `redaction_patterns.yaml` — Configurable regex patterns for sensitive data redaction (emails, phones, SSNs, credit cards, URLs, IPs, addresses).
- 🐍 `scripts/curate.py` — Full text curation pipeline:
  - Format support: `.md`, `.txt`, `.eml`, `.html`, `.docx`, `.pdf`.
  - YAML frontmatter stripping (Obsidian-style `---` blocks).
  - Code block detection and removal.
  - Sensitive data redaction with configurable patterns.
  - Text classification via keyword heuristics (narrative, argumentative, informal, technical).
  - Statistics output (files processed, words, redactions, classification breakdown).
  - CLI arguments for source/output/config paths and verbose mode.
- 🐍 `scripts/analyze_style.py` — Linguistic style analysis:
  - Vocabulary frequency, unique word ratio, bigram/trigram detection.
  - Sentence structure: average length, std deviation, median, longest/shortest examples.
  - Punctuation fingerprint: em-dashes, ellipses, exclamations, etc.
  - Filler word and connector detection.
  - Tone mapping (formal/informal balance, humor markers).
  - Generates `dataset/style_context.md` — a natural-language system prompt.
- 🐍 `scripts/build_dataset.py` — Dataset construction:
  - Unified corpus (`dataset/unified_corpus.txt`) with document headers.
  - Smart chunking respecting paragraph boundaries (configurable size/overlap).
  - JSONL generation (`dataset/dataset.jsonl`) for fine-tuning.
  - Token counting via tiktoken (optional) or character-based estimation.
  - Chunk storage for RAG integration.
- 🐍 `scripts/test_generation.py` — Generation testing:
  - Multi-backend support: Ollama (`/api/generate`), LM Studio (`/v1/chat/completions`), llama.cpp (`/completion`).
  - Loads test prompts from `prompts/test_prompts.md`.
  - Comparison metrics: lexical similarity, sentence length, punctuation similarity, readability.
  - Timestamped result reports in `tests/results/`.
- 🐍 `scripts/voice_mode.py` — Voice generation mode:
  - CLI usage: `python scripts/voice_mode.py --topic "morning routines" --chars 2000`.
  - Interactive fallback when no arguments given.
  - Saves output to `output/` as timestamped `.md` files.
  - Session logging to `docs/logs/`.
- 📄 `.env` — Environment configuration template (backend, endpoints, model, context settings).
- 📄 `requirements.txt` — Python dependencies (beautifulsoup4, pyyaml, requests, python-dotenv, python-docx, pymupdf, tiktoken).
- 💬 `prompts/system_prompt.md` — Base system prompt template with style profile placeholder, instructions, and guardrails.
- 💬 `prompts/test_prompts.md` — 10 test prompts covering same-topic, new-topic, opinion, casual, short-form, long-form, technical, emotional, descriptive, and abstract writing.
- 📂 `output/` — Directory for generated voice mode outputs.

### Changed
- 📦 Removed stale `.gitkeep` files from directories now containing real files.
- 🔒 Updated `.gitignore` — uncommented `sources/` protection and added `output/`.

---

## [0.1.0] — 2026-05-19

### Added
- 🎉 **Project initialization** — Base VoxMea structure.
- 📁 Directory structure:
  - `sources/` — Ingestion folder for raw unprocessed texts.
    - `obsidian/` — Exported Obsidian notes.
    - `emails/` — Exported emails.
    - `articles/` — Articles and posts.
  - `curated/` — Filtered and classified texts.
    - Subdirectories by type: `narrative/`, `argumentative/`, `informal/`, `technical/`.
  - `dataset/` — Final dataset for the LLM.
  - `scripts/` — Python processing scripts.
  - `prompts/` — System prompts and templates.
  - `tests/` — Control texts and results.
  - `docs/` — Documentation and logs.
- 📄 Initial documentation:
  - `README.md` — Project overview, phases, and quickstart.
  - `agents.md` — Definition of 4 agents: Curator, Analyst, Builder, Tester.
  - `architecture.md` — Technical architecture, data flows, and design decisions.
  - `CHANGELOG.md` — This file.
- 🔧 `.gitkeep` files in empty directories to preserve structure in Git.
