from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import re

app = FastAPI(title="YouTube Summarizer")

# Load Mistral v0.3
model_id = "mistralai/Mistral-7B-Instruct-v0.3"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype=torch.float16)
summarizer = pipeline("text-generation", model=model, tokenizer=tokenizer)

class YouTubeRequest(BaseModel):
    url: str

def extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)

def get_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry["text"] for entry in transcript])
        return text
    except Exception as e:
        raise RuntimeError(f"Could not get transcript: {e}")

def generate_summary(transcript: str) -> str:
    prompt = f"<s>[INST] Summarize the following transcript:\n\n{transcript}\n\n[/INST]"
    result = summarizer(prompt, max_new_tokens=512, do_sample=True, temperature=0.7)
    return result[0]["generated_text"]

@app.post("/summarize")
def summarize_video(request: YouTubeRequest):
    try:
        video_id = extract_video_id(request.url)
        transcript = get_transcript(video_id)
        summary = generate_summary(transcript)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
