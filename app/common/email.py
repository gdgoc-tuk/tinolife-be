"""이메일 전송 서비스"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

from app.core.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


class EmailService:
    """이메일 전송을 담당하는 서비스"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.smtp_from_name = settings.SMTP_FROM_NAME
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> bool:
        """
        이메일을 전송합니다.
        
        Args:
            to_email: 수신자 이메일
            subject: 이메일 제목
            html_content: HTML 형식 본문
            plain_content: 평문 형식 본문 (선택)
            
        Returns:
            bool: 전송 성공 여부
        """
        try:
            # MIME 메시지 생성
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.smtp_from_name} <{self.smtp_from}>"
            message["To"] = to_email
            
            # 평문 파트 추가 (선택)
            if plain_content:
                plain_part = MIMEText(plain_content, "plain", "utf-8")
                message.attach(plain_part)
            
            # HTML 파트 추가
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # TLS 보안 연결
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"이메일 전송 성공: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 전송 실패: {to_email}, 오류: {str(e)}")
            return False
    
    def send_verification_code(
        self,
        to_email: str,
        code: str,
        expires_minutes: int = 5
    ) -> bool:
        """
        인증 코드 이메일을 전송합니다.
        
        Args:
            to_email: 수신자 이메일
            code: 6자리 인증 코드
            expires_minutes: 만료 시간 (분)
            
        Returns:
            bool: 전송 성공 여부
        """
        subject = "[TinoLife] 이메일 인증 코드"
        
        # HTML 템플릿
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .code-box {{
                    background: #f8f9fa;
                    border: 2px dashed #667eea;
                    border-radius: 8px;
                    padding: 25px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .code {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #667eea;
                    letter-spacing: 8px;
                    font-family: 'Courier New', monospace;
                }}
                .info {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px 30px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .footer a {{
                    color: #667eea;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>TinoLife</h1>
                    <p>이메일 인증</p>
                </div>
                <div class="content">
                    <h2>안녕하세요!</h2>
                    <p>TinoLife 회원가입을 위한 이메일 인증 코드입니다.</p>
                    <p>아래 인증 코드를 입력하여 이메일 인증을 완료해주세요.</p>
                    
                    <div class="code-box">
                        <div class="code">{code}</div>
                    </div>
                    
                    <div class="info">
                        <strong>⏰ 유효 시간:</strong> {expires_minutes}분<br>
                        <strong>⚠️ 주의:</strong> 이 코드는 일회용이며, 타인에게 공유하지 마세요.
                    </div>
                    
                    <p>본인이 요청하지 않은 경우, 이 이메일을 무시하셔도 됩니다.</p>
                </div>
                <div class="footer">
                    <p>© 2025 TinoLife. All rights reserved.</p>
                    <p>문의사항이 있으신가요? <a href="mailto:tinolifeofficial@gmail.com">tinolifeofficial@gmail.com</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 평문 버전 (HTML을 지원하지 않는 이메일 클라이언트용)
        plain_content = f"""
[TinoLife] 이메일 인증

안녕하세요!

TinoLife 회원가입을 위한 이메일 인증 코드입니다.

인증 코드: {code}

유효 시간: {expires_minutes}분
주의: 이 코드는 일회용이며, 타인에게 공유하지 마세요.

본인이 요청하지 않은 경우, 이 이메일을 무시하셔도 됩니다.

© 2025 TinoLife. All rights reserved.
        """
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content
        )


def get_email_service() -> EmailService:
    """EmailService 의존성 주입"""
    return EmailService()
