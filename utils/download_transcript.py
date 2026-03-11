"""This module will download a transcript of a youtube video."""

import argparse
import re
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


# Function to validate URL
def is_valid_url(url):
    # Basic URL regex (you can make this more complex)
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # ...or ipv4
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # ...or ipv6
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return re.match(regex, url) is not None


# Function to extract the video id
def extract_video_id(url):
    # Regular expression to extract the video ID
    regex = r"v=([a-zA-Z0-9_-]+)"

    # Search for the video ID in the URL
    match = re.search(regex, url)

    if match:
        video_id = match.group(1)
        print(f"Video ID: {video_id}")
        return video_id
    else:
        print("Video ID not found.")
        return None


def download_transcript(video_url):
    # Extract video ID from URL
    video_id = video_url.split("v=")[-1]

    try:
        # Fetch the transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        formatted_transcript = " ".join([line["text"] for line in transcript])

        # Save to a text file
        with open(f"{video_id}_transcript.txt", "w") as file:
            file.write(formatted_transcript)

        print(f"Transcript saved as {video_id}_transcript.txt")

    except Exception as e:
        print(f"Error: {e}")


# Parse command line arguments
def main():
    parser = argparse.ArgumentParser(description="Process a URL")
    parser.add_argument("url", type=str, help="The URL to process")

    args = parser.parse_args()

    # Validate URL
    if not is_valid_url(args.url):
        print("Invalid URL. Please provide a valid URL.")
        return

    # Extract Video ID:
    video_id = extract_video_id(args.url)
    # if video_id is not None:
    # print(f"Processing URL: {args.url}")
    print(f"Processing Video ID: {video_id}")
    tqdm(download_transcript(args.url))


if __name__ == "__main__":
    main()
# Example usage
# video_url = "https://www.youtube.com/watch?v=rVSb0u9OTtM&list=PL9rU625vkl4XmGq7i-zZbVuVw3g5ezl6o&index=15"
# download_transcript(video_url)
