# Python 3.12 slim 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# pipenv 설치
RUN pip install --no-cache-dir pipenv

# Pipfile 복사
COPY Pipfile ./

# Pipfile.lock이 있으면 복사 (없어도 에러 안남)
COPY Pipfile.lock* ./

# Python 경로 명시적으로 지정하여 의존성 설치
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --system --deploy --python $(which python3)

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
