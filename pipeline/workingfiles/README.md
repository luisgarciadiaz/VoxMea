# workingfiles/ — what you need

This folder is your workspace. Everything you need to touch is here.

## Quick start

1. **Add your texts** → `sources/` folder (`.md`, `.txt`, `.eml`, `.html`, `.docx`, `.pdf`)
2. **Configure** → copy `.env.example` from the project root to `.env` and edit it
3. **Run** → `python start.py` from the project root
4. **Get output** → `output/` folder

## Structure

| Item | What to do |
|---|---|
| `sources/` | Drop your personal texts here |
| `control_text.md` | (optional) A sample of your writing for comparison |
| `output/` | Generated texts appear here |
| `.env` | Configure your LLM backend |

## Notes

- Everything else in the project root (`scripts/`, `curated/`, `dataset/`, etc.) is handled automatically by the pipeline. You don't need to touch it.
- Run `python start.py` from the project root, not from inside `workingfiles/`.
