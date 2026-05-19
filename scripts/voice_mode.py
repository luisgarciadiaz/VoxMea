#!/usr/bin/env python3
"""VoxMea — Voice Mode (Phase 4)

Generate original text in the author's voice from a simple prompt.
Connects to the configured LLM with style_context.md as system prompt.
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

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
DATASET_DIR = PROJECT_DIR / "dataset"
STYLE_CONTEXT = DATASET_DIR / "style_context.md"
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "docs" / "logs"


def get_config():
    """Load configuration from environment variables."""
    return {
        "backend": os.getenv("LLM_BACKEND", "ollama"),
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "lmstudio_host": os.getenv("LMSTUDIO_HOST", "http://localhost:1234/v1"),
        "llamacpp_host": os.getenv("LLAMACPP_HOST", "http://localhost:8080"),
        "model": os.getenv("MODEL_NAME", "llama3.2"),
    }


def load_style_context():
    """Load the style context / system prompt."""
    if STYLE_CONTEXT.exists():
        return STYLE_CONTEXT.read_text(encoding="utf-8")
    base_path = PROJECT_DIR / "prompts" / "system_prompt.md"
    if base_path.exists():
        return base_path.read_text(encoding="utf-8")
    return "Write in a natural, personal voice."


def call_ollama(host, model, system_prompt, user_prompt, max_tokens):
    """Call Ollama API."""
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json().get("response", "")


def call_lmstudio(host, model, system_prompt, user_prompt, max_tokens):
    """Call LM Studio API."""
    url = f"{host}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def call_llamacpp(host, system_prompt, user_prompt, max_tokens):
    """Call llama.cpp server API."""
    url = f"{host}/completion"
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    payload = {
        "prompt": full_prompt,
        "temperature": 0.7,
        "n_predict": max_tokens,
    }
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json().get("content", "")


def generate_text(config, system_prompt, topic, char_count):
    """Generate text in the author's voice."""
    max_tokens = min(char_count // 2 + 200, int(os.getenv("MAX_CONTEXT_TOKENS", 8192)))

    user_prompt = (
        f"Write in your natural voice. "
        f"Topic: {topic}\n\n"
        f"The response should be approximately {char_count} characters long. "
        f"Write naturally — do not pad or cut short artificially."
    )

    host = config["ollama_host"] if config["backend"] == "ollama" \
        else config["lmstudio_host"] if config["backend"] == "lmstudio" \
        else config["llamacpp_host"]

    if config["backend"] == "ollama":
        return call_ollama(host, config["model"], system_prompt, user_prompt, max_tokens)
    elif config["backend"] == "lmstudio":
        return call_lmstudio(host, config["model"], system_prompt, user_prompt, max_tokens)
    elif config["backend"] == "llamacpp":
        return call_llamacpp(host, system_prompt, user_prompt, max_tokens)
    else:
        raise ValueError(f"Unknown backend: {config['backend']}")


def save_output(topic, text):
    """Save generated text to output/ directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')[:40]
    filename = f"{datetime.now().strftime('%Y-%m-%d')}_{safe_topic}.md"
    filepath = OUTPUT_DIR / filename

    content = f"# {topic}\n\n"
    content += f"Generated: {datetime.now().isoformat()}\n"
    content += f"Character target: ~{char_count}\n"
    content += f"Actual characters: {len(text)}\n"
    content += f"Actual words: {len(text.split())}\n\n"
    content += "---\n\n"
    content += text

    filepath.write_text(content, encoding="utf-8")
    return filepath


def log_session(topic, char_count, output_path, success=True):
    """Log generation session to docs/logs/."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "voice_mode_log.md"

    entry = (
        f"- **{datetime.now().isoformat()}** | "
        f"Topic: \"{topic}\" | "
        f"Target: {char_count} chars | "
        f"{'✓' if success else '✗'} "
        f"Output: {output_path}\n"
    )

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)


def main():
    parser = argparse.ArgumentParser(
        description="VoxMea — Voice Mode: Generate text in the author's voice."
    )
    parser.add_argument("--topic", "-t", help="Topic or phrase to write about")
    parser.add_argument("--chars", "-c", type=int, help="Target character count")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive mode (prompt for topic and chars)")
    args = parser.parse_args()

    # Determine mode
    if args.topic and args.chars:
        topic = args.topic
        char_count = args.chars
    elif args.interactive or not (args.topic and args.chars):
        print("VoxMea — Voice Mode (Interactive)")
        print("=" * 50)
        topic = input("Topic or phrase to write about: ").strip()
        while not topic:
            topic = input("Topic cannot be empty: ").strip()
        char_input = input("Target character count (e.g. 500, 2000): ").strip()
        char_count = int(char_input) if char_input.isdigit() else 2000
    else:
        parser.print_help()
        sys.exit(0)

    print(f"\nTopic: \"{topic}\"")
    print(f"Target: ~{char_count} characters")
    print()

    # Load config and style context
    config = get_config()
    system_prompt = load_style_context()

    print(f"Backend: {config['backend']} ({config['model']})")
    print("Generating...")

    try:
        start = time.time()
        text = generate_text(config, system_prompt, topic, char_count)
        elapsed = time.time() - start

        actual_chars = len(text)
        actual_words = len(text.split())

        print(f"\nGenerated {actual_words} words ({actual_chars} chars) in {elapsed:.1f}s")
        print("\n" + "=" * 50)
        print("OUTPUT")
        print("=" * 50)
        print(text)
        print()

        if actual_chars < char_count * 0.3:
            print(f"Note: Output ({actual_chars} chars) is significantly shorter "
                  f"than target ({char_count}). Consider using a larger model or "
                  f"adjusting max tokens.")

        # Save
        import re
        output_path = save_output(topic, text)
        print(f"Saved to: {output_path}")

        log_session(topic, char_count, output_path, success=True)

    except requests.exceptions.ConnectionError:
        print(f"\nCould not connect to {config['backend']}.")
        print(f"Make sure the service is running at the configured host.")
        log_session(topic, char_count, "N/A", success=False)
        sys.exit(1)
    except Exception as e:
        print(f"\nError during generation: {e}")
        log_session(topic, char_count, "N/A", success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
