import threading
from typing import Dict, Any, List

_lock = threading.Lock()
_hits = 0
_misses = 0
_prompt_chars = 0
_response_chars = 0
_total_seconds = 0.0
_calls: List[Dict[str, Any]] = []


def record_call(hit: bool, prompt_chars: int, response_chars: int, seconds: float):
    global _hits, _misses, _prompt_chars, _response_chars, _total_seconds, _calls
    with _lock:
        if hit:
            _hits += 1
        else:
            _misses += 1
        _prompt_chars += prompt_chars
        _response_chars += response_chars
        _total_seconds += seconds
        _calls.append({
            "hit": hit,
            "prompt_chars": prompt_chars,
            "response_chars": response_chars,
            "seconds": seconds,
        })


def snapshot() -> Dict[str, Any]:
    global _hits, _misses, _prompt_chars, _response_chars, _total_seconds, _calls
    with _lock:
        return {
            "hits": _hits,
            "misses": _misses,
            "total_calls": _hits + _misses,
            "llm_calls": _misses,  # remote API calls made
            "prompt_chars": _prompt_chars,
            "response_chars": _response_chars,
            "seconds": round(_total_seconds, 4),
            "total_seconds": round(_total_seconds, 4),
            "calls": list(_calls),
        }


def reset():
    global _hits, _misses, _prompt_chars, _response_chars, _total_seconds, _calls
    with _lock:
        _hits = 0
        _misses = 0
        _prompt_chars = 0
        _response_chars = 0
        _total_seconds = 0.0
        _calls.clear()
