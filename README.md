# TinoLife Backend API

FastAPI 기반의 TinoLife 백엔드 API 서버입니다.

## 기술 스택

- **FastAPI**: 모던하고 빠른 Python 웹 프레임워크
- **Pipenv**: Python 패키지 관리 도구
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 설정 관리
- **Pytest**: 테스트 프레임워크

## 프로젝트 구조

도메인 중심 설계(Domain-Driven Design)를 따르는 구조입니다:

```bash
tinolife-be/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── core/                # 핵심 설정 및 공통 기능
│   │   ├── __init__.py
│   │   └── config.py        # 환경 설정
│   ├── common/              # 공통 유틸리티
│   │   ├── __init__.py
│   │   ├── exceptions.py    # 공통 예외 처리
│   │   ├── responses.py     # 공통 응답 모델
│   │   └── utils.py         # 유틸리티 함수
│   └── domains/             # 도메인별 비즈니스 로직
│       ├── __init__.py
│       ├── users/           # 사용자 도메인
│       │   ├── __init__.py
│       │   ├── router.py    # API 엔드포인트
│       │   ├── service.py   # 비즈니스 로직
│       │   ├── schema.py    # Pydantic 스키마
│       │   └── model.py     # 데이터베이스 모델
│       └── auth/            # 인증 도메인
│           ├── __init__.py
│           ├── router.py
│           ├── service.py
│           └── schema.py
├── tests/                   # 테스트 파일
├── docs/                    # 문서
├── Makefile                 # Make 명령어
├── Pipfile                  # Pipenv 의존성 파일
└── README.md
```

### 도메인 구조 설명

- **core/**: 애플리케이션의 핵심 설정 (config, database 등)
- **common/**: 여러 도메인에서 공통으로 사용하는 유틸리티
- **domains/**: 비즈니스 도메인별로 구분된 모듈
  - 각 도메인은 독립적인 router, service, schema, model을 가집니다
  - 새로운 도메인 추가 시 동일한 구조를 따릅니다

## 설치 및 실행

### 1. 의존성 설치

```bash
make install
```

### 2. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 설정합니다:

```bash
cp .env.example .env
```

### 3. 개발 서버 실행

```bash
make dev
```

서버가 실행되면 다음 URL에서 확인할 수 있습니다:

- API: http://localhost:8000
- Swagger 문서: http://localhost:8000/docs
- ReDoc 문서: http://localhost:8000/redoc

## Makefile 명령어

| 명령어 | 설명 |
|--------|------|
| `make help` | 사용 가능한 명령어 목록 표시 |
| `make install` | 의존성 설치 |
| `make dev` | 개발 서버 실행 (자동 재시작) |
| `make run` | 프로덕션 서버 실행 |
| `make test` | 테스트 실행 |
| `make test-cov` | 커버리지와 함께 테스트 실행 |
| `make lint` | 코드 린트 실행 |
| `make format` | 코드 포맷팅 (Black) |
| `make clean` | 캐시 파일 정리 |
| `make shell` | Pipenv 쉘 열기 |
| `make update` | 의존성 업데이트 |
| `make lock` | 의존성 잠금 |

## 개발 가이드

### 코드 스타일

- Python 코드는 [Black](https://github.com/psf/black) 포맷터를 사용합니다
- 린팅은 [Flake8](https://flake8.pycqa.org/)과 [MyPy](http://mypy-lang.org/)를 사용합니다

코드 포맷팅:

```bash
make format
```

린트 확인:

```bash
make lint
```

### 테스트

테스트는 pytest를 사용합니다:

```bash
# 테스트 실행
make test

# 커버리지와 함께 테스트 실행
make test-cov
```

### API 엔드포인트

#### 기본 엔드포인트

- `GET /`: 루트 엔드포인트
- `GET /health`: 헬스 체크

#### 사용자 관리 (`/api/v1/users`)

- `GET /api/v1/users`: 사용자 목록 조회
- `GET /api/v1/users/{user_id}`: 특정 사용자 조회
- `POST /api/v1/users`: 새 사용자 생성
- `PUT /api/v1/users/{user_id}`: 사용자 정보 수정
- `DELETE /api/v1/users/{user_id}`: 사용자 삭제

#### 인증 (`/api/v1/auth`)

- `POST /api/v1/auth/login`: 로그인
- `POST /api/v1/auth/logout`: 로그아웃
- `GET /api/v1/auth/me`: 현재 사용자 정보

더 많은 엔드포인트는 개발 진행에 따라 추가됩니다.

### 새 도메인 추가하기

새로운 도메인을 추가하려면 다음 단계를 따르세요:

1. `app/domains/` 아래에 새 도메인 폴더 생성
2. 필요한 파일 생성:
   - `__init__.py`: 도메인 초기화
   - `router.py`: API 엔드포인트 정의
   - `service.py`: 비즈니스 로직
   - `schema.py`: Pydantic 모델
   - `model.py`: 데이터베이스 모델 (선택)
3. `app/main.py`에 라우터 등록:

   ```python
   from app.domains.your_domain.router import router as your_router
   app.include_router(your_router, prefix="/api/v1")
   ```

## 환경 변수

주요 환경 변수는 `.env.example` 파일을 참고하세요.

## 라이선스

TBD
