# 📋 Changelog — VoxMea

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

---

## Roadmap

### [0.2.0] — Phase 1: Extraction & Curation
- [ ] `curate.py` script for automated text filtering.
- [ ] Regex patterns for sensitive data redaction.
- [ ] Control text selection.

### [0.3.0] — Phase 2: Formatting & Structuring
- [ ] `build_dataset.py` script for consolidation.
- [ ] Generation of `style_context.md`.
- [ ] (Optional) Generation of `dataset.jsonl`.

### [0.4.0] — Phase 3: Integration & Testing
- [ ] Ollama / LM Studio integration.
- [ ] RAG configuration (Smart Connections).
- [ ] Generation test suite.

### [1.0.0] — Release
- [ ] Complete and validated pipeline.
- [ ] Final documentation.
- [ ] Refined and approved style profile.
