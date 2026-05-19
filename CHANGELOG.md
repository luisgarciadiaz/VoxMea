# Changelog — VoxMea

All notable changes to this project will be documented in this file.

---

## [0.3.0] — 2026-05-19

### Added
- `start.py` — Pipeline launcher with two modes:
  - Interactive: `python start.py` shows menu (create text / rebuild voice / quit)
  - Direct: `python start.py 1 "topic" 35000` skips menu and generates
  - `[q]` option to quit
- `pipeline/` — All internal machinery lives here (scripts, curated, dataset, prompts, tests, output)
- `Documentation/` — Docs folder at root level
- `logs/` — Session logs at root level
- Iterative text generation in `voice_mode.py` — splits long requests into parts and keeps continuing until target length is reached
- Support for comma-formatted numbers like `35,000` in character count input

### Changed
- `start.py` — Quiet mode: only shows errors/warnings, no [OK] spam
- `curate.py` — All paths resolved via `Path(__file__).resolve().parent` so scripts work regardless of CWD; output lands in `pipeline/curated/`
- `voice_mode.py` — `import re` moved to top of file; `save_output` accepts `target_chars` parameter
- `.env` — Default model changed to `llama3:latest`, context window bumped to 32768
- Root folder simplified: only `sources/`, `Documentation/`, `logs/`, `pipeline/`, `start.py`, `.env`, `README.md`, `requirements.txt`, `.gitignore`, `agents.md`, `architecture.md`, `CHANGELOG.md`
- `agents.md`, `architecture.md`, `CHANGELOG.md` moved back to root level

### Fixed
- `curate.py` — CLI args no longer override module-level paths with relative defaults
- `voice_mode.py` — `NameError: name 're' is not defined` on save

---

## [0.2.0] — 2026-05-19

### Added
- Phase 1: Data Extraction & Curation — Complete pipeline implementation.
- `redaction_patterns.yaml` — Configurable regex patterns for sensitive data redaction.
- `scripts/curate.py` — Full text curation pipeline with format support (.md, .txt, .eml, .html, .docx, .pdf), YAML frontmatter stripping, code block removal, redaction, classification, and statistics.
- `scripts/analyze_style.py` — Linguistic style analysis: vocabulary, sentence structure, punctuation fingerprint, filler/connector detection, tone mapping. Generates `dataset/style_context.md`.
- `scripts/build_dataset.py` — Dataset construction: unified corpus, smart chunking, JSONL generation, token counting.
- `scripts/test_generation.py` — Multi-backend testing (Ollama, LM Studio, llama.cpp) with comparison metrics.
- `scripts/voice_mode.py` — Voice generation mode: CLI and interactive, saves to `output/`, session logging.
- `.env` — Environment configuration template.
- `requirements.txt` — Python dependencies.
- `prompts/system_prompt.md` — Base system prompt template.
- `prompts/test_prompts.md` — 10 test prompts.

---

## [0.1.0] — 2026-05-19

### Added
- Project initialization — Base VoxMea structure.
- Directory structure: `sources/`, `curated/`, `dataset/`, `scripts/`, `prompts/`, `tests/`, `docs/`.
- Initial documentation: `README.md`, `agents.md`, `architecture.md`, `CHANGELOG.md`.
