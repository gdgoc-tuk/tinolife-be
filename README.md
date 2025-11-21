# TinoLife Backend API

FastAPI 기반의 TinoLife 백엔드 API 서버입니다.

## 기술 스택

- **FastAPI**: 모던하고 빠른 Python 웹 프레임워크
- **SQLAlchemy**: ORM (동기/비동기 지원)
- **Alembic**: 데이터베이스 마이그레이션
- **PostgreSQL**: 메인 데이터베이스
- **Docker & Docker Compose**: 컨테이너화된 개발 환경
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

### Docker를 사용한 실행 (권장)

#### 1. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 설정합니다:

```bash
cp .env.example .env
```

#### 2. 개발 환경 시작

```bash
make dev
```

이 명령은 다음 작업을 자동으로 수행합니다:
- Docker 컨테이너 빌드 및 시작
- PostgreSQL 데이터베이스 초기화
- **Alembic 마이그레이션 자동 실행** 🔄
- FastAPI 애플리케이션 시작

서버가 실행되면 다음 URL에서 확인할 수 있습니다:

- API: <http://localhost:8000>
- Swagger 문서: <http://localhost:8000/docs>
- ReDoc 문서: <http://localhost:8000/redoc>

#### 3. Docker 관련 유용한 명령어

```bash
# 로그 확인
make docker-logs

# 앱 로그만 확인
docker compose logs -f app

# 컨테이너 중지
make docker-down

# 컨테이너 재시작
make docker-restart

# 완전히 삭제 (볼륨 포함)
docker compose down -v
```

### 로컬 환경에서 실행 (Docker 없이)

#### 1. 의존성 설치

```bash
make install
```

#### 2. PostgreSQL 설치 및 실행

로컬에 PostgreSQL을 설치하고 실행해야 합니다.

#### 3. 환경 변수 설정

`.env` 파일에서 데이터베이스 호스트를 `localhost`로 변경:

```env
DATABASE_URL=postgresql://tinolife:tinolife123@localhost:5432/tinolife
ASYNC_DATABASE_URL=postgresql+asyncpg://tinolife:tinolife123@localhost:5432/tinolife
```

#### 4. 마이그레이션 실행

```bash
make migrate-up
```

#### 5. 개발 서버 실행

```bash
make dev-local
```

## Makefile 명령어

### Docker 명령어

| 명령어 | 설명 |
|--------|------|
| `make dev` | Docker Compose로 개발 환경 시작 (자동 마이그레이션 포함) |
| `make docker-up` | Docker 컨테이너 시작 |
| `make docker-down` | Docker 컨테이너 중지 |
| `make docker-restart` | Docker 컨테이너 재시작 |
| `make docker-logs` | Docker 로그 확인 |
| `make docker-clean` | 컨테이너, 볼륨 완전 삭제 |

### 데이터베이스 마이그레이션

| 명령어 | 설명 |
|--------|------|
| `make migrate-create` | 새 마이그레이션 생성 (autogenerate) |
| `make migrate-up` | 마이그레이션 적용 |
| `make migrate-down` | 마이그레이션 롤백 (1단계) |
| `make migrate-history` | 마이그레이션 히스토리 조회 |
| `make migrate-current` | 현재 마이그레이션 버전 확인 |
| `make db-reset` | 데이터베이스 리셋 (주의!) |

**참고:** Docker 환경에서 마이그레이션 명령 실행 시:

```bash
docker compose exec app pipenv run alembic upgrade head
```

### 로컬 개발 명령어

| 명령어 | 설명 |
|--------|------|
| `make install` | 의존성 설치 |
| `make dev-local` | 로컬 개발 서버 실행 |
| `make run` | 프로덕션 서버 실행 |
| `make shell` | Pipenv 쉘 열기 |

### 테스트 및 코드 품질

| 명령어 | 설명 |
|--------|------|
| `make test` | 테스트 실행 |
| `make test-cov` | 커버리지와 함께 테스트 실행 |
| `make lint` | 코드 린트 실행 |
| `make format` | 코드 포맷팅 (Black) |
| `make clean` | 캐시 파일 정리 |

### 의존성 관리

| 명령어 | 설명 |
|--------|------|
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
