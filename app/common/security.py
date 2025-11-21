"""비밀번호 해싱 및 검증 유틸리티"""
from passlib.context import CryptContext

# bcrypt 해싱 컨텍스트 생성
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    비밀번호를 bcrypt로 해싱합니다.
    
    Args:
        password: 평문 비밀번호
        
    Returns:
        str: 해싱된 비밀번호
        
    Examples:
        >>> hashed = hash_password("mypassword123")
        >>> len(hashed) > 0
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해싱된 비밀번호를 비교합니다.
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해싱된 비밀번호
        
    Returns:
        bool: 비밀번호 일치 여부
        
    Examples:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)
