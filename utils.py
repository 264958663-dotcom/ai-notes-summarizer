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
MAX_REQUESTS_PER_MINUTE = 15
# Cache duration in seconds (5 minutes)
CACHE_DURATION = 300


def _get_cache_key(text: str, operation: str, detail_level: str = "", language: str = "") -> str:
    return hashlib.md5(f"{text}:{operation}:{detail_level}:{language}".encode()).hexdigest()


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


_DETAIL_MAP = {
    "Brief": "Be very concise",
    "Normal": "Provide a balanced amount of detail",
    "Detailed": "Be comprehensive and thorough",
}

def generate_summary(text, detail_level="Normal", language="English"):
    cache_key = _get_cache_key(text, "summary", detail_level, language)
    cached_result = _is_in_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    if not _can_make_request():
        raise Exception("Rate limit exceeded. Please wait before making more requests.")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    bullet_count = {"Brief": "2-3", "Normal": "5", "Detailed": "8-10"}
    prompt = f"Summarize the following notes in {bullet_count[detail_level]} clear bullet points. {_DETAIL_MAP[detail_level]}. Use simple language. Respond in {language}.\n\nNotes:\n{text}"
    response = model.generate_content(prompt)
    result = response.text
    
    _save_to_cache(cache_key, result)
    _record_request()
    
    return result


def generate_key_points(text, detail_level="Normal", language="English"):
    cache_key = _get_cache_key(text, "key_points", detail_level, language)
    cached_result = _is_in_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    if not _can_make_request():
        raise Exception("Rate limit exceeded. Please wait before making more requests.")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    bullet_count = {"Brief": "3-4", "Normal": "5-6", "Detailed": "8-10"}
    prompt = f"Extract the most important key points from these notes. List {bullet_count[detail_level]} bullet points. {_DETAIL_MAP[detail_level]}. Respond in {language}.\n\nNotes:\n{text}"
    response = model.generate_content(prompt)
    result = response.text
    
    _save_to_cache(cache_key, result)
    _record_request()
    
    return result


def generate_flashcards(text, detail_level="Normal", language="English"):
    cache_key = _get_cache_key(text, "flashcards", detail_level, language)
    cached_result = _is_in_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    if not _can_make_request():
        raise Exception("Rate limit exceeded. Please wait before making more requests.")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    card_count = {"Brief": "3", "Normal": "5", "Detailed": "8"}
    prompt = f"""Create {card_count[detail_level]} flashcards from the text below. Return ONLY a valid JSON array, nothing else.

Each flashcard must have "question" and "answer" fields. Respond in {language}.

Example:
[{{"question": "What is X?", "answer": "X is Y"}}]

Text:
{text}"""
    response = model.generate_content(prompt).text

    cleaned = re.sub(r"```(?:json)?\n?", "", response).strip()
    result = json.loads(cleaned)
    
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


def generate_study_questions(text, detail_level="Normal", language="English"):
    cache_key = _get_cache_key(text, "study_questions", detail_level, language)
    cached_result = _is_in_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    if not _can_make_request():
        raise Exception("Rate limit exceeded. Please wait before making more requests.")
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    question_count = {"Brief": "2", "Normal": "4", "Detailed": "6"}
    prompt = f"""Generate {question_count[detail_level]} study questions based on the following notes. {_DETAIL_MAP[detail_level]}. Include a mix of:
- Open-ended explanation questions
- Multiple choice questions (with options)
- True/false questions
- Short answer questions
Respond in {language}.

Notes:
{text}"""
    response = model.generate_content(prompt)
    result = response.text
    
    _save_to_cache(cache_key, result)
    _record_request()
    
    return result
