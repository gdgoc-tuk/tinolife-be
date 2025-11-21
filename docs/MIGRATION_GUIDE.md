# Migration 관리 가이드

## 🎯 개요

이 프로젝트는 **Alembic**을 사용하여 데이터베이스 마이그레이션을 관리합니다.
도메인 중심 구조에서 각 도메인의 모델 변경사항을 추적하고 관리합니다.

## 📁 구조

```
tinolife-be/
├── alembic/                      # Alembic 설정 디렉토리
│   ├── versions/                 # 마이그레이션 파일들
│   │   └── xxxx_create_users_table.py
│   ├── env.py                    # Alembic 환경 설정
│   └── script.py.mako            # 마이그레이션 템플릿
├── alembic.ini                   # Alembic 설정 파일
└── app/
    ├── core/
    │   └── database.py           # DB 연결 및 Base 정의
    └── domains/
        ├── users/
        │   └── model.py          # User 모델
        └── auth/
            └── model.py          # Auth 관련 모델
```

## 🔧 설정

### 1. 환경 변수 설정

`.env` 파일에 데이터베이스 URL 설정:

```bash
# 동기 URL (Alembic용)
DATABASE_URL=postgresql://user:password@localhost:5432/tinolife

# 비동기 URL (FastAPI용)
ASYNC_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/tinolife
```

### 2. Alembic 설정

`alembic/env.py`에서 모든 모델을 자동으로 감지하도록 설정됨:

```python
# 모든 도메인의 모델 import
from app.domains.users.model import User
from app.domains.auth.model import RefreshToken, LoginHistory
# 새 도메인 추가 시 여기에 import 추가
```

## 📝 도메인별 스키마 관리 전략

### 원칙

1. **각 도메인은 자신의 테이블을 정의**
   - `app/domains/{domain}/model.py`에 SQLAlchemy 모델 작성

2. **모든 모델은 `alembic/env.py`에 import**
   - Alembic이 변경사항을 자동으로 감지할 수 있도록

3. **마이그레이션은 중앙 집중식 관리**
   - `alembic/versions/`에 모든 변경사항 저장
   - 도메인별로 파일을 나누지 않음 (복잡도 증가 방지)

4. **명확한 마이그레이션 메시지 사용**
   - 형식: `{action}_{domain}_{description}`
   - 예시: `create_users_table`, `add_users_email_index`

### 워크플로우

#### 새 도메인 추가 시

1. 도메인 모델 작성
```python
# app/domains/posts/model.py
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
```

2. `alembic/env.py`에 import 추가
```python
from app.domains.posts.model import Post  # noqa
```

3. 마이그레이션 생성
```bash
make migrate-create
# 메시지: create_posts_table
```

#### 기존 모델 수정 시

1. 모델 파일 수정
```python
# app/domains/users/model.py
# 새 컬럼 추가
phone_number = Column(String(20), nullable=True)
```

2. 마이그레이션 생성
```bash
make migrate-create
# 메시지: add_users_phone_number
```

3. 마이그레이션 검토 후 적용
```bash
# 생성된 파일 확인
cat alembic/versions/xxxx_add_users_phone_number.py

# 적용
make migrate-up
```

## 🚀 사용법

### 기본 명령어

```bash
# 1. 의존성 설치
make install

# 2. 데이터베이스 준비
# PostgreSQL 실행 확인 후

# 3. 마이그레이션 생성 (자동)
make migrate-create
# 메시지 입력: create_initial_tables

# 4. 마이그레이션 적용
make migrate-up

# 5. 마이그레이션 히스토리 확인
make migrate-history

# 6. 현재 버전 확인
make migrate-current
```

### 세부 명령어

| 명령어 | 설명 | 사용 시기 |
|--------|------|-----------|
| `make migrate-create` | 자동 마이그레이션 생성 | 모델 변경 후 |
| `make migrate-head` | 빈 마이그레이션 생성 | 데이터 마이그레이션 등 |
| `make migrate-up` | 마이그레이션 적용 | 배포 전 |
| `make migrate-down` | 마지막 마이그레이션 롤백 | 실수 시 |
| `make migrate-history` | 히스토리 확인 | 상태 파악 |
| `make migrate-current` | 현재 버전 확인 | 디버깅 시 |

### 개발 환경 전용

```bash
# 개발 중 DB 초기화 (주의: 모든 데이터 삭제)
make db-reset
```

## 🎨 예시 시나리오

### 시나리오 1: Users 도메인에 컬럼 추가

```bash
# 1. model.py 수정
# app/domains/users/model.py에 bio 컬럼 추가

# 2. 마이그레이션 생성
make migrate-create
# 메시지: add_users_bio_field

# 3. 생성된 파일 확인
ls -la alembic/versions/

# 4. 적용
make migrate-up
```

### 시나리오 2: 새 도메인(Posts) 추가

```bash
# 1. 도메인 폴더 및 파일 생성
mkdir -p app/domains/posts
touch app/domains/posts/{__init__.py,model.py,schema.py,service.py,router.py}

# 2. model.py 작성
# Post 모델 정의

# 3. alembic/env.py에 import 추가
# from app.domains.posts.model import Post

# 4. 마이그레이션 생성
make migrate-create
# 메시지: create_posts_table

# 5. 적용
make migrate-up
```

### 시나리오 3: 인덱스 추가

```bash
# 1. model.py에서 index=True 설정
# email = Column(String, index=True)

# 2. 마이그레이션 생성
make migrate-create
# 메시지: add_users_email_index

# 3. 적용
make migrate-up
```

## ⚠️ 주의사항

### DO ✅

- 마이그레이션 전 데이터베이스 백업
- 마이그레이션 파일 리뷰 후 적용
- 명확한 마이그레이션 메시지 작성
- 프로덕션 배포 전 스테이징에서 테스트

### DON'T ❌

- 적용된 마이그레이션 파일 직접 수정 금지
- 마이그레이션 파일 순서 변경 금지
- 프로덕션에서 `db-reset` 사용 금지
- 자동 생성된 마이그레이션 무검증 적용 금지

## 🔍 트러블슈팅

### 문제: 마이그레이션이 변경사항을 감지하지 못함

**해결:**
```bash
# 1. alembic/env.py에 모델이 import 되어 있는지 확인
# 2. 캐시 삭제
make clean
# 3. 다시 시도
make migrate-create
```

### 문제: 마이그레이션 충돌

**해결:**
```bash
# 현재 상태 확인
make migrate-current

# 문제되는 마이그레이션 롤백
make migrate-down

# 재생성
make migrate-create
```

### 문제: 데이터베이스 연결 오류

**해결:**
```bash
# 1. .env 파일의 DATABASE_URL 확인
# 2. PostgreSQL 실행 여부 확인
# 3. 데이터베이스 존재 여부 확인
psql -U user -d tinolife
```

## 📚 참고

- [Alembic 공식 문서](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 공식 문서](https://www.sqlalchemy.org/)
- 프로젝트 구조: 도메인 중심 설계 (DDD)
