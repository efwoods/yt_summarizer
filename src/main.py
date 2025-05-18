import re
import os
from fastapi import FastAPI, UploadFile, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Optional
from pydantic import BaseModel, HttpUrl
import logging
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed
import redis
import json

app = FastAPI(title="YouTube Transcript Downloader API")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client setup
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=6379,
        decode_responses=True
    )
    redis_client.ping() # Test connection
    logger.info("Connected to Redis")
except redis.RedisError as e:
    logger.error(f"Failed ot connect to Redis: {str(e)}")
    redis_client = None

# Pydantic model for single URL request
class UrlRequest(BaseModel):
    url: HttpUrl

# Pydantic model for response, allowing nullable fields
class TranscriptResponse(BaseModel):
    video_id: Optional[str] = None
    transcript: Optional[str] = None
    status: str
    error: Optional[str] = None

# Function to validate URL
def is_valid_url(url: str) -> bool:
    try:
        pattern = (
            r"^(?:http|ftp)s?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
            r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$"
        )
        regex = re.compile(pattern, re.IGNORECASE)
        return bool(regex.match(url))
    except Exception as e:
        logger.error(f"Error in URL validation for {url}: {str(e)}")
        return False

# Function to extract video ID
def extract_video_id(url: str) -> str:
    try:
        regex = r"v=([a-zA-Z0-9_-]+)"
        match = re.search(regex, url)
        logger.info(f"match: {match}")
        logger.info(f"url: {url}")
        if match:
            return match.group(1)
        logger.warning(f"No video ID found in URL: {url}")
        return ""
    except Exception as e:
        logger.error(f"Error extracting video ID from {url}: {str(e)}")
        return ""

# Function to fetch transcript with retry logic
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.info(f"Retrying transcript fetch for {retry_state.fn.__name__}, attempt {retry_state.attempt_number}")
)
def fetch_transcript(transcript_obj):
    return transcript_obj.fetch()

# Function to download transcript
async def download_transcript(video_url: str) -> Dict:
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"video_id": "", "transcript": "", "status": "error", "error": "Invalid video ID"}

    # Check cache
    cache_key = f"transcript:{video_id}"
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for video_id: {video_id}")
                return json.loads(cached_result)
        except redis.RedisError as e:
            logger.error(f"Redis cache error for {video_id}: {str(e)}")

    # Cache miss, fetch transcript
    try:
        # Check available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        # Try manual transcripts first, then auto-generated
        for t in transcript_list:
            try:
                if t.is_translatable or t.is_generated:
                    logger.info(f"Attempting to fetch transcript {t.language_code} for {video_id}")
                    transcript = fetch_transcript(t)
                    break
            except Exception as e:
                logger.warning(f"Failed to fetch transcript {t.language_code} for {video_id}: {str(e)}")
                continue

        if not transcript:
            return {"video_id": video_id, "transcript": "", "status": "error", "error": "No transcript available"}

        # Handle different transcript types
        formatted_transcript = ""
        if isinstance(transcript, list):
            # Standard case: list of dictionaries
            formatted_transcript = " ".join(
                entry.get("text", "") for entry in transcript if isinstance(entry, dict) and "text" in entry
            )
        else:
            # Handle non-standard cases (e.g., FetchedTranscriptSnippet)
            try:
                # Attempt to access snippets if available
                if hasattr(transcript, 'snippets') and isinstance(transcript.snippets, list):
                    formatted_transcript = " ".join(
                        snippet.text for snippet in transcript.snippets if hasattr(snippet, 'text')
                    )
                else:
                    logger.warning(f"Unsupported transcript format for {video_id}: {type(transcript)}")
                    return {"video_id": video_id, "transcript": "", "status": "error", "error": "Unsupported transcript format"}
            except Exception as e:
                logger.error(f"Error processing transcript for {video_id}: {str(e)}")
                return {"video_id": video_id, "transcript": "", "status": "error", "error": f"Transcript processing failed: {str(e)}"}

        if not formatted_transcript.strip():
            return {"video_id": video_id, "transcript": "", "status": "error", "error": "No valid transcript text found"}

        # Cache succesful results
        result = {"video_id": video_id, "transcript": formatted_transcript, "status": "success"}
        if redis_client:
            try:
                redis_client.setex(cache_key, 86400, json.dumps(result)) # Cache for 24 hours
                logger.info(f"Cached result for video_id: {video_id}")
            except redis.RedisError as e:
                logger.error(f"Failed to cache result for {video_id}: {str(e)}")
        return result
    except Exception as e:
        logger.error(f"Error downloading transcript for {video_id}: {str(e)}")
        return {"video_id": video_id, "transcript": "", "status": "error", "error": str(e)}

# FastAPI endpoint to process URLs from a file
@app.post("/transcripts/", response_model=List[TranscriptResponse])
async def get_transcripts(file: UploadFile):
    if not file.filename.endswith(('.txt')):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    try:
        content = await file.read()
        urls = content.decode('utf-8').splitlines()
        urls = [url.strip() for url in urls if url.strip() and not url.strip().startswith("#")]
        #logging.info(urls)

        if not urls:
            raise HTTPException(status_code=400, detail="File is empty or contains no valid URLs")

        results = []
        for url in urls:
            logger.info(f"Processing URL: {url}")
            if not is_valid_url(url):
                logger.info(f"is_valid_url(url): {is_valid_url(url)}")
                logger.warning(f"Invalid URL skipped: {url}")
                results.append(TranscriptResponse(video_id="", transcript="", status="error", error="Invalid URL"))
                continue
            else:
                logger.info(f"is_valid_url(url): {is_valid_url(url)}")
                result = await download_transcript(url)
                results.append(TranscriptResponse(**result))
        return results
    except UnicodeDecodeError as e:
        logger.error(f"Error decoding file: {str(e)}")
        raise HTTPException(status_code=400, detail="File must be a valid UTF-8 encoded text file")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# FastAPI endpoint to process a single URL
@app.post("/transcript/", response_model=TranscriptResponse)
async def get_single_transcript(request: UrlRequest):
    url = str(request.url)
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    logger.info(f"Processing URL: {url}")
    result = await download_transcript(url)
    logger.info(f"Result: {result}")
    return TranscriptResponse(**result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)