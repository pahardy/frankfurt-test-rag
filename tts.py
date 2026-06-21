"""
tts.py — Convert a markdown file to an MP3 using OpenAI TTS.

Usage: uv run tts.py output/lecture1.md
Output: output/lecture1.mp3  (same name, .mp3 extension)

Voices: alloy, echo, fable, onyx, nova, shimmer
"""

import config
import os
import re
import sys
from pathlib import Path

from openai import OpenAI

MODEL = "tts-1-hd"
VOICE = "onyx"
MAX_CHARS = 4000  # OpenAI limit is 4096; stay safely under


def strip_markdown(text: str) -> str:
    """Remove markdown syntax so TTS reads clean prose."""
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)  # horizontal rules
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)  # headings
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)               # bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)                   # italic
    text = re.sub(r'`(.+?)`', r'\1', text)                     # inline code
    return text.strip()


def split_chunks(text: str) -> list[str]:
    """Split at sentence boundaries to stay under MAX_CHARS."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 <= MAX_CHARS:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return chunks


def to_audio(input_path: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    text = strip_markdown(Path(input_path).read_text(encoding="utf-8"))
    chunks = split_chunks(text)
    print(f"{len(chunks)} chunk(s) to synthesise...")

    audio = b""
    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i}/{len(chunks)}...")
        audio += client.audio.speech.create(model=MODEL, voice=VOICE, input=chunk).content

    out_path = str(Path(input_path).with_suffix(".mp3"))
    Path(out_path).write_bytes(audio)
    print(f"Saved: {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run tts.py <path/to/file.md>")
        sys.exit(1)
    to_audio(sys.argv[1])
