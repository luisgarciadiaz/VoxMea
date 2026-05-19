# 🎙️ VoxMea — Writing Style Cloning for AI

> *Your voice, amplified by artificial intelligence.*

**VoxMea** is a personal pipeline for extracting, processing, and structuring your writings to train or contextualize a local LLM that replicates your unique writing style.

---

## 🎯 Objective

Create a writing style clone that allows a local language model (Ollama / LM Studio) to generate text that sounds authentically like you — preserving your tone, vocabulary, structure, and narrative personality.

## 🧩 Project Structure

```
VoxMea/
├── sources/              # Raw text sources (Obsidian notes, articles, emails)
│   ├── obsidian/         #   Exported Obsidian notes
│   ├── emails/           #   Exported emails (.eml, .txt)
│   └── articles/         #   Articles and blog posts
├── curated/              # Filtered and curated texts (no sensitive data)
│   ├── narrative/        #   Narrative/reflective writing
│   ├── argumentative/    #   Opinion pieces
│   ├── informal/         #   Casual communication
│   └── technical/        #   Technical writing with personal voice
├── dataset/              # Final structured dataset for the LLM
│   ├── style_context.md  #   System prompt with style analysis
│   └── unified_corpus.txt#   Consolidated texts
├── scripts/              # Processing scripts (Python)
├── prompts/              # System prompts and test templates
├── tests/                # Control texts and test results
├── docs/                 # Additional documentation
├── agents.md             # AI agent definitions for the project
├── architecture.md       # Technical system architecture
├── CHANGELOG.md          # Change log
└── README.md             # This file
```

## 🚀 Project Phases

### Phase 1: Data Extraction & Curation
- Identify and collect text sources with the strongest "identity" (Obsidian notes, articles, sent emails).
- Filter and remove sensitive information, irrelevant hard data, or plain text that doesn't contribute to "style".
- Select a control dataset (a reference text to measure clone success).

### Phase 2: Formatting & Structuring (Dataset Preparation)
- Create a Python script to consolidate curated texts into a unified file.
- Generate `style_context.md` with a system directive (System Prompt) describing how to analyze the content.
- (Optional) Structure a JSONL file for local AI Fine-Tuning if the context method isn't sufficient.

### Phase 3: Integration & Testing in Local Environment
- Configure the context prompt in the local backend (Ollama / LM Studio) to test tone replication.
- Configure and index the style file/folder via a RAG plugin (such as Smart Connections in Obsidian).
- Run generation tests with the control text and refine prompt instructions based on results.

## 🛠️ Tech Stack

| Component       | Tool                               |
|-----------------|-------------------------------------|
| Language        | Python 3.11+                        |
| Local LLM       | Ollama / LM Studio                  |
| RAG             | Smart Connections (Obsidian)        |
| Notes           | Obsidian                            |
| Version Control | Git                                 |

## 📋 Requirements

- Python 3.11+
- Obsidian (for sources and RAG plugin)
- Ollama or LM Studio installed locally
- Git

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/luisgarciadiaz/VoxMea.git
cd VoxMea

# 2. Place your source texts in /sources
#    (Obsidian .md notes, articles, exported emails)

# 3. Run the curation script (Phase 2)
python scripts/curate.py

# 4. Build the dataset
python scripts/build_dataset.py

# 5. Test with your local LLM
#    Load style_context.md as a system prompt in Ollama/LM Studio
```

## 📄 License

Personal project for private use. All source texts are property of the author.

---

*Created by Luis Garcia Diaz — May 2026*
