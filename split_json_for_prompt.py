import os
import json
from pathlib import Path
from typing import List

# === CONFIGURATION ===
INPUT_FILE = "DATA/neuralink-summer-2025.json"
OUTPUT_ROOT = "output"
WORDS_PER_CHUNK = 500


def load_input(filepath: str) -> dict:
    """Loads a JSON object from file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def split_transcript(transcript: str, words_per_chunk: int) -> List[str]:
    """Splits transcript into roughly 500-word chunks."""
    words = transcript.split()
    return [
        " ".join(words[i : i + words_per_chunk])
        for i in range(0, len(words), words_per_chunk)
    ]


def save_chunks(video_id: str, chunks: List[str]):
    """Saves each chunk in a nested folder named after the video_id."""
    folder_path = os.path.join(OUTPUT_ROOT, video_id)
    Path(folder_path).mkdir(parents=True, exist_ok=True)

    for i, chunk in enumerate(chunks):
        chunk_data = {"video_id": video_id, "chunk_index": i, "text": chunk}
        file_path = os.path.join(folder_path, f"chunk_{i}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)


def main():
    data = load_input(INPUT_FILE)

    if not isinstance(data, dict) or "video_id" not in data or "transcript" not in data:
        print(
            "❌ Input JSON must be a dictionary with 'video_id' and 'transcript' keys."
        )
        return

    video_id = data["video_id"]
    transcript = data["transcript"]

    chunks = split_transcript(transcript, WORDS_PER_CHUNK)
    save_chunks(video_id, chunks)
    print(
        f"✅ {len(chunks)} chunks saved to: {os.path.abspath(os.path.join(OUTPUT_ROOT, video_id))}"
    )


if __name__ == "__main__":
    main()
