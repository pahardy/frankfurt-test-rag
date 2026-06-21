"""
video.py — Combine an MP3 with Pexels stock footage to produce an MP4.

Usage: uv run video.py output/lecture1.mp3
Output: output/lecture1.mp4
"""

import config
import os
import sys
import tempfile
from pathlib import Path

import requests
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip

PEXELS_API = "https://api.pexels.com/videos/search"
SEARCH_TERMS = [
    "ancient library", "manuscript", "philosophy", "candlelight",
    "cathedral", "stone architecture", "old books", "classical art",
]
CLIPS_PER_TERM = 1


def fetch_video_urls(api_key: str, duration_needed: float) -> list[str]:
    """Search Pexels and return enough video URLs to cover the audio duration."""
    headers = {"Authorization": api_key}
    urls = []
    total = 0.0

    for term in SEARCH_TERMS:
        if total >= duration_needed:
            break
        resp = requests.get(PEXELS_API, headers=headers, params={
            "query": term, "per_page": CLIPS_PER_TERM, "orientation": "landscape",
        })
        resp.raise_for_status()
        for video in resp.json().get("videos", []):
            # Pick the highest-quality file under 1080p
            files = sorted(video["video_files"], key=lambda f: f.get("width", 0), reverse=True)
            for f in files:
                if f.get("width", 0) <= 1920 and f.get("link"):
                    urls.append(f["link"])
                    total += video.get("duration", 10)
                    break

    return urls


def download_clip(url: str, dest: Path) -> None:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        dest.write_bytes(r.content)


def make_video(mp3_path: str) -> str:
    api_key = os.getenv("PEXELS_API_KEY")
    audio = AudioFileClip(mp3_path)
    duration = audio.duration
    print(f"Audio duration: {duration:.1f}s")

    print("Fetching Pexels video URLs...")
    urls = fetch_video_urls(api_key, duration)
    if not urls:
        raise RuntimeError("No videos returned from Pexels.")

    with tempfile.TemporaryDirectory() as tmp:
        clips = []
        for i, url in enumerate(urls):
            dest = Path(tmp) / f"clip_{i}.mp4"
            print(f"  Downloading clip {i + 1}/{len(urls)}...")
            download_clip(url, dest)
            clips.append(VideoFileClip(str(dest)))

        # Loop clips until we have enough footage
        combined = concatenate_videoclips(clips, method="compose")
        while combined.duration < duration:
            combined = concatenate_videoclips([combined] + clips, method="compose")

        video = combined.subclipped(0, duration).with_audio(audio)

        out_path = str(Path(mp3_path).with_suffix(".mp4"))
        print(f"Rendering {out_path}...")
        video.write_videofile(out_path, codec="libx264", audio_codec="aac", logger=None)

    print(f"Saved: {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run video.py <path/to/file.mp3>")
        sys.exit(1)
    make_video(sys.argv[1])
