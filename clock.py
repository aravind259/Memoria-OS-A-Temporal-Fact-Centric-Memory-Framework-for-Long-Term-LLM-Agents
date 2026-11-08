from datetime import datetime
from typing import Optional, Union

_override_now: Optional[datetime] = None


def set_now(dt: Optional[Union[datetime, str]]):
    """
    Sets the current time for clock.get_now().
    Accepts a datetime instance, an ISO format string, or None to reset.
    """
    global _override_now
    if dt is None:
        _override_now = None
    elif isinstance(dt, str):
        import re
        clean_str = dt.replace("Z", "+00:00")
        try:
            _override_now = datetime.fromisoformat(clean_str)
        except Exception:
            try:
                _override_now = datetime.fromisoformat(dt.replace("Z", ""))
            except Exception:
                try:
                    stripped = re.sub(r"\s*\([A-Za-z]+\)\s*", " ", dt).strip()
                    _override_now = datetime.strptime(stripped, "%Y/%m/%d %H:%M")
                except Exception:
                    _override_now = datetime.strptime(dt[:10], "%Y-%m-%d")
    elif isinstance(dt, datetime):
        _override_now = dt
    else:
        raise ValueError(f"Unsupported datetime type: {type(dt)}")


def get_now() -> datetime:
    """
    Returns the current time. If an override has been set via set_now(),
    returns that value; otherwise defaults to datetime.utcnow().
    """
    global _override_now
    if _override_now is not None:
        return _override_now
    return datetime.utcnow()


def reset_now():
    """
    Resets clock to default datetime.utcnow() behavior.
    """
    global _override_now
    _override_now = None
