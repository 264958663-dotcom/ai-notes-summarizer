"""
Utility functions for the AI Notes Summarizer+ application.
Handles API interactions, PDF processing, and export formats.
"""

import google.generativeai as genai
import pdfplumber
import json
import re
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Cache for API responses to avoid duplicate calls
_response_cache = {}
# Track request timestamps for rate limiting
_request_timestamps = []
# Maximum requests per minute (free tier limit)
MAX_REQUESTS_PER_MINUTE = 5
# Cache duration in seconds (5 minutes)
CACHE_DURATION = 300


def _get_cache_key(text: str, operation: str) -> str:
    """Generate a cache key based on text content and operation type
    
    Args:
        text: The input text to hash
        operation: The operation type (e.g., 'summary', 'key_points', 'flashcards')
        
    Returns:
        MD5 hash string as cache key
    """
    return hashlib.md5(f"{text}:{operation}".encode()).hexdigest()


def _is_in_cache(cache_key: str) -> Optional[Any]:
    """Check if result is in cache and not expired
    
    Args:
        cache_key: The cache key to look up
        
    Returns:
        Cached result if found and not expired, None otherwise
    """
    if cache_key in _response_cache:
        timestamp, result = _response_cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return result
        else:
            # Remove expired entry
            del _response_cache[cache_key]
    return None


def _save_to_cache(cache_key: str, result: Any) -> None:
    """Save result to cache with current timestamp
    
    Args:
        cache_key: The cache key to store under
        result: The result to cache
    """
    _response_cache[cache_key] = (time.time(), result)


def _clean_old_requests() -> None:
    """Remove request timestamps older than 1 minute"""
    global _request_timestamps
    now = time.time()
    _request_timestamps = [ts for ts in _request_timestamps if now - ts < 60]


def _can_make_request() -> bool:
    """Check if we can make a request based on rate limiting
    
    Returns:
        True if we can make a request, False if rate limit exceeded
    """
    _clean_old_requests()
    return len(_request_timestamps) < MAX_REQUESTS_PER_MINUTE


def _record_request():
    """Record that a request was made"""
    _request_timestamps.append(time.time())


def configure_api(api_key):
    genai.configure(api_key=api_key)


def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def generate_summary(text):
    # Check cache first
    cache_key = _get_cache_key(text, "summary")
    cached_result = _is_in_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Check if we can make a request
    if not _can_make_request():
        raise Exception("Rate limit exceeded. Please wait before making more requests.")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    prompt = f"Summarize the following notes in 5 clear bullet points. Use simple language.\n\nNotes:\n{text}"
    response = model.generate_content(prompt)
    result = response.text
    
    # Save to cache and record request
    _save_to_cache(cache_key, result)
    _record_request()
    
    return result


def generate_key_points(text):
    # Check cache first
    cache_key = _get_cache_key(text, "key_points")
    cached_result = _is_in_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Check if we can make a request
    if not _can_make_request():
        raise Exception("Rate limit exceeded. Please wait before making more requests.")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    prompt = f"Extract the most important key points from these notes. List them as bullet points.\n\nNotes:\n{text}"
    response = model.generate_content(prompt)
    result = response.text
    
    # Save to cache and record request
    _save_to_cache(cache_key, result)
    _record_request()
    
    return result


def generate_flashcards(text):
    # Check cache first
    cache_key = _get_cache_key(text, "flashcards")
    cached_result = _is_in_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Check if we can make a request
    if not _can_make_request():
        raise Exception("Rate limit exceeded. Please wait before making more requests.")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    prompt = f"""Create 5 flashcards from the text below. Return ONLY a valid JSON array, nothing else.

Each flashcard must have "question" and "answer" fields.

Example:
[{{"question": "What is X?", "answer": "X is Y"}}]

Text:
{text}"""
    response = model.generate_content(prompt).text

    cleaned = re.sub(r"```(?:json)?\n?", "", response).strip()
    result = json.loads(cleaned)
    
    # Save to cache and record request
    _save_to_cache(cache_key, result)
    _record_request()
    
    return result


def make_csv(cards):
    """Export flashcards as CSV format"""
    lines = ["Front,Back"]
    for card in cards:
        q = card["question"].replace('"', '""')
        a = card["answer"].replace('"', '""')
        lines.append(f'"{q}","{a}"')
    return "\n".join(lines)


def make_txt(cards):
    """Export flashcards as simple text format"""
    lines = []
    for i, card in enumerate(cards, 1):
        lines.append(f"Flashcard {i}")
        lines.append(f"Q: {card['question']}")
        lines.append(f"A: {card['answer']}")
        lines.append("")  # Empty line between cards
    return "\n".join(lines)


def make_json(cards):
    """Export flashcards as JSON format"""
    return json.dumps(cards, indent=2, ensure_ascii=False)


def generate_study_questions(text):
    """Generate study questions based on the provided text
    
    Args:
        text: Input text to generate questions from
        
    Returns:
        Generated study questions as string
    """
    # Check cache first
    cache_key = _get_cache_key(text, "study_questions")
    cached_result = _is_in_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Check if we can make a request
    if not _can_make_request():
        raise Exception("Rate limit exceeded. Please wait before making more requests.")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    prompt = f"""Generate 4 study questions based on the following notes. Include a mix of:
- 1-2 open-ended explanation questions
- 1 multiple choice question (with options)
- 1 true/false question
- 1 short answer/application question

Notes:
{text}"""
    response = model.generate_content(prompt)
    result = response.text
    
    # Save to cache and record request
    _save_to_cache(cache_key, result)
    _record_request()
    
    return result
