from datetime import datetime
from typing import Optional


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """날짜시간을 ISO 8601 형식으로 변환"""
    if dt is None:
        return None
    return dt.isoformat()


def truncate_string(text: str, max_length: int = 100) -> str:
    """문자열을 지정된 길이로 자르기"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
