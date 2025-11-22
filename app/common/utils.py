from datetime import datetime
from typing import Optional
import random
import string


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """날짜시간을 ISO 8601 형식으로 변환"""
    if dt is None:
        return None
    return dt.isoformat()


def truncate_string(text: str, max_length: int = 100) -> str:
    """문자열을 지정된 길이로 자르기"""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def generate_verification_code(length: int = 6) -> str:
    """
    랜덤 인증 코드를 생성합니다.

    Args:
        length: 인증 코드 길이 (기본값: 6)

    Returns:
        str: 숫자로만 구성된 인증 코드

    Examples:
        >>> code = generate_verification_code()
        >>> len(code)
        6
        >>> code.isdigit()
        True
    """
    return "".join(random.choices(string.digits, k=length))
