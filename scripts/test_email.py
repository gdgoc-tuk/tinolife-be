"""이메일 전송 테스트 스크립트"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.email import EmailService


def test_send_verification_code():
    """인증 코드 이메일 전송 테스트"""
    email_service = EmailService()
    
    # 테스트용 이메일 주소 입력받기
    test_email = input("테스트할 이메일 주소를 입력하세요: ").strip()
    
    if not test_email:
        print("❌ 이메일 주소가 입력되지 않았습니다.")
        return
    
    # 테스트 인증 코드
    test_code = "123456"
    
    print(f"\n📧 이메일 전송 중...")
    print(f"   수신자: {test_email}")
    print(f"   인증 코드: {test_code}")
    
    # 이메일 전송
    success = email_service.send_verification_code(
        to_email=test_email,
        code=test_code,
        expires_minutes=5
    )
    
    if success:
        print("\n✅ 이메일 전송 성공!")
        print("   이메일 수신함을 확인해주세요.")
    else:
        print("\n❌ 이메일 전송 실패!")
        print("   SMTP 설정을 확인해주세요.")
        print("\n📝 확인 사항:")
        print("   1. .env 파일의 SMTP_* 설정이 올바른지 확인")
        print("   2. Gmail 사용 시 앱 비밀번호 생성 여부 확인")
        print("   3. SMTP 서버 연결 가능 여부 확인")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TinoLife 이메일 전송 테스트")
    print("=" * 60)
    
    test_send_verification_code()
    
    print("\n" + "=" * 60)
