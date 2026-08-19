"""
YouTube transcript extraction service.

Uses youtube_transcript_api to fetch existing captions from YouTube videos.
This is the lightweight approach (no Whisper, no audio download needed).

The reference project (reference/utils/audio_processor.py) uses yt_dlp + Whisper
for full audio transcription. That heavier path can be added as a fallback later.

Reused concepts from reference:
  - Video ID extraction from URL
  - Timestamp formatting (reference/core/transcriber.py format_timestamp)
  - Segment structure with start/end times
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """
    Extract YouTube video ID from various URL formats.

    Supports:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - https://www.youtube.com/embed/VIDEO_ID
      - https://youtube-nocookie.com/embed/VIDEO_ID

    Raises:
        ValueError: If the video ID cannot be extracted.
    """
    url = url.strip()
    parsed = urlparse(url)

    # youtu.be/VIDEO_ID
    if parsed.hostname and "youtu.be" in parsed.hostname:
        video_id = parsed.path.lstrip("/")
        if video_id:
            return video_id.split("/")[0].split("?")[0]

    # youtube.com/watch?v=VIDEO_ID
    if parsed.hostname and "youtube" in parsed.hostname:
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]
        # /embed/VIDEO_ID or /v/VIDEO_ID
        match = re.match(r"/(embed|v)/([^/?&]+)", parsed.path)
        if match:
            return match.group(2)

    raise ValueError(
        f"Could not extract video ID from URL: {url}. "
        "Provide a standard YouTube URL (e.g. https://www.youtube.com/watch?v=...)."
    )


def _format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS (reused concept from reference/core/transcriber.py)."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02}:{secs:02}"


def fetch_transcript(url: str) -> dict:
    """
    Fetch the transcript for a YouTube video.

    Args:
        url: YouTube video URL.

    Returns:
        dict with keys:
          - text: full transcript as a single string
          - video_id: the extracted video ID
          - title: video title (derived from video_id if API doesn't provide it)
          - segments: list of { start, end, text } dicts with timestamps

    Raises:
        ValueError: If the video ID cannot be extracted or no transcript is available.
    """
    video_id = extract_video_id(url)

    try:
        # youtube_transcript_api v1.2.4+ uses instance-based API
        ytt_api = YouTubeTranscriptApi()
        entries = ytt_api.fetch(video_id, languages=["en"])

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            f"Failed to fetch transcript for video {video_id}: {str(e)}. "
            "The video may be private, unavailable, or have no captions."
        )

    # Build segments with timestamps (inspired by reference transcriber.py)
    segments: list[dict] = []
    text_parts: list[str] = []

    for entry in entries:
        start = entry.start
        duration = entry.duration
        segment_text = entry.text.strip() if entry.text else ""
        if segment_text:
            segments.append({
                "start": start,
                "end": start + duration,
                "text": segment_text,
            })
            text_parts.append(segment_text)

    full_text = " ".join(text_parts)

    if not full_text.strip():
        raise ValueError(f"Transcript for video {video_id} is empty.")

    return {
        "text": full_text,
        "video_id": video_id,
        "title": f"YouTube: {video_id}",
        "segments": segments,
    }
