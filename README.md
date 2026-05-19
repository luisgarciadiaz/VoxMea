# VoxMea — Writing Style Cloning for AI

> *Your voice, amplified by artificial intelligence.*

**VoxMea** is a pipeline that extracts, analyzes, and structures your personal writings so a local LLM (Ollama / LM Studio) can generate text that sounds authentically like you.

---

## Quick Start

```
python start.py
```

First run detects no curated texts, rebuilds your voice from `sources/`, then launches voice mode. Subsequent runs show a menu:

```
  What you want to do today?

    [1] Create new text   - Write something in your voice
    [2] Rebuild voice     - Re-process sources and remake style profile
    [q] Quit
```

**Direct mode** (skips menu):

```
python start.py 1 "your topic" 35000
python start.py 2
```

---

## Project Structure

```
VoxMea/
├── sources/              # Drop your personal texts here
├── Documentation/        # Project docs
├── logs/                 # Generation session logs
├── pipeline/             # Internal machinery
│   ├── scripts/          #   curate.py, analyze_style.py, etc.
│   ├── curated/          #   Cleaned texts (auto-generated)
│   ├── dataset/          #   style_context.md, corpus (auto-generated)
│   ├── prompts/          #   System prompt templates
│   ├── tests/            #   Control text and results
│   ├── output/           #   Generated texts appear here
│   └── workingfiles/     #   Quick reference guide
├── start.py              # Entry point
├── .env                  # LLM configuration
├── requirements.txt      # Python dependencies
├── agents.md             # AI agent definitions
├── architecture.md       # Technical architecture
├── CHANGELOG.md          # Change log
└── README.md             # This file
```

---

## Setup

1. **Place your texts** in `sources/` (`.md`, `.txt`, `.eml`, `.html`, `.docx`, `.pdf`)
2. **Install dependencies** — `pip install -r requirements.txt`
3. **Configure** — Edit `.env` with your LLM backend and model
4. **Run** — `python start.py`

---

## Usage

| Command | What it does |
|---|---|
| `python start.py` | Menu: create text, rebuild voice, or quit |
| `python start.py 1 "topic" 5000` | Generate text directly (skips menu) |
| `python start.py 2` | Rebuild voice from sources |
| `python start.py 1` | Interactive mode — prompts for topic and length |

---

## Requirements

- Python 3.11+
- Ollama, LM Studio, or llama.cpp running locally
- Your personal texts in `sources/`

---

*Created by Luis Garcia Diaz — May 2026*
