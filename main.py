from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import re

app = FastAPI()

# ==============================
# Load Mistral once at startup
# ==============================
print("🚀 Loading Mistral-7B-Instruct model...")
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto",
)
summarizer = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=300,
    do_sample=True,
    temperature=0.7,
    top_p=0.9
)
print("✅ Model ready.")

# ==============================
# Pydantic request schema
# ==============================
class YouTubeRequest(BaseModel):
    url: str

# ==============================
# Utility functions
# ==============================
def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL."""
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if not match:
        raise ValueError("Invalid YouTube URL.")
    return match.group(1)

def download_transcript(video_id: str) -> str:
    """Downloads transcript and returns it as plain text."""
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    formatter = TextFormatter()
    return formatter.format_transcript(transcript)

def summarize_text(text: str) -> str:
    """Summarizes the text using local Mistral pipeline."""
    input_text = f"[INST] Summarize the following YouTube transcript:\n{text}\n[/INST]"
    result = summarizer(input_text)[0]["generated_text"]
    return result.split("[/INST]")[-1].strip()

# ==============================
# Main endpoint
# ==============================
@app.post("/summarize-youtube")
def summarize_youtube(request: YouTubeRequest):
    try:
        video_id = extract_video_id(request.url)
        transcript_text = download_transcript(video_id)
        transcript_text = transcript_text[:4000]  # Truncate for long videos
        summary = summarize_text(transcript_text)
        return {"video_id": video_id, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
