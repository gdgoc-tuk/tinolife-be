from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.qna.schema import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    TagListResponse,
    TagSearchResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
)
from app.domains.qna.service import (
    CategoryService,
    get_category_service,
    TagService,
    get_tag_service,
    QuestionService,
    get_question_service,
)
from app.common.dependencies import get_current_user
from app.domains.users.model import User

router = APIRouter(prefix="/qna", tags=["qna"])


@router.get("/categories", response_model=CategoryListResponse)
async def get_categories(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=100, description="조회할 항목 수"),
    include_inactive: bool = Query(False, description="비활성 카테고리 포함 여부"),
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
):
    """
    카테고리 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    - **include_inactive**: 비활성 카테고리 포함 여부 (기본값: false)
    """
    categories = await service.get_categories(
        db, skip=skip, limit=limit, include_inactive=include_inactive
    )
    total = await service.count_categories(db, include_inactive=include_inactive)

    return CategoryListResponse(categories=categories, total=total)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
):
    """
    카테고리 상세 조회
    
    - **category_id**: 카테고리 ID
    """
    category = await service.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="카테고리를 찾을 수 없습니다."
        )
    return category


@router.post(
    "/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
):
    """
    카테고리 생성 (관리자 전용)
    
    - **name**: 카테고리명
    - **display_order**: 표시 순서 (기본값: 0)
    
    TODO: 관리자 권한 체크 추가
    """
    # TODO: 관리자 권한 체크
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    category = await service.create_category(db, category_data)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
):
    """
    카테고리 수정 (관리자 전용)
    
    - **name**: 카테고리명 (선택)
    - **display_order**: 표시 순서 (선택)
    - **is_active**: 활성화 상태 (선택)
    
    TODO: 관리자 권한 체크 추가
    """
    # TODO: 관리자 권한 체크
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    category = await service.update_category(db, category_id, category_data)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
):
    """
    카테고리 삭제 (관리자 전용)
    
    - **category_id**: 카테고리 ID
    
    주의: 사용 중인 카테고리는 삭제할 수 없습니다.
    
    TODO: 관리자 권한 체크 추가
    """
    # TODO: 관리자 권한 체크
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    await service.delete_category(db, category_id)
    return None


@router.get("/tags", response_model=TagListResponse)
async def get_tags(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=100, description="조회할 항목 수"),
    sort_by: str = Query("usage", pattern="^(usage|recent)$", description="정렬 기준"),
    include_inactive: bool = Query(False, description="비활성 태그 포함 여부"),
    db: Session = Depends(get_db),
    service: TagService = Depends(get_tag_service),
):
    """
    태그 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    - **sort_by**: 정렬 기준 ("usage": 사용 빈도순, "recent": 최신순)
    - **include_inactive**: 비활성 태그 포함 여부
    """
    tags = await service.get_tags(
        db, skip=skip, limit=limit, sort_by=sort_by, include_inactive=include_inactive
    )
    total = await service.count_tags(db, include_inactive=include_inactive)

    return TagListResponse(tags=tags, total=total)


@router.get("/tags/search", response_model=TagSearchResponse)
async def search_tags(
    q: str = Query(..., min_length=1, max_length=50, description="검색 쿼리"),
    limit: int = Query(10, ge=1, le=50, description="최대 결과 수"),
    db: Session = Depends(get_db),
    service: TagService = Depends(get_tag_service),
):
    """
    태그 검색 (자동완성용)
    
    - **q**: 검색 쿼리
    - **limit**: 최대 결과 수 (기본값: 10)
    
    Returns:
        태그명 리스트 (사용 빈도 순)
    """
    tags = await service.search_tags(db, q, limit)
    return TagSearchResponse(tags=tags)


@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    질문 생성
    
    - **title**: 질문 제목 (1-200자)
    - **content**: 질문 본문
    - **category_id**: 카테고리 ID (필수)
    - **major_id**: 전공 ID (선택, null=전공무관)
    - **bounty**: 바운티 토큰 (기본값: 0)
    - **is_anonymous**: 익명 여부 (기본값: false)
    - **tag_names**: 태그명 리스트 (최대 10개)
    """
    question = await service.create_question(db, question_data, current_user.id)
    return question


@router.get("/questions", response_model=QuestionListResponse)
async def get_questions(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(20, ge=1, le=100, description="조회할 항목 수"),
    category_id: int = Query(None, description="카테고리 필터"),
    major_id: int = Query(None, description="전공 필터"),
    tag_name: str = Query(None, description="태그 필터"),
    sort_by: str = Query("recent", description="정렬 기준 (recent, interest, bounty, unanswered)"),
    db: Session = Depends(get_db),
    service: QuestionService = Depends(get_question_service),
):
    """
    질문 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    - **category_id**: 카테고리 필터
    - **major_id**: 전공 필터
    - **tag_name**: 태그 필터
    - **sort_by**: 정렬 기준
      - recent: 최신순 (기본값)
      - interest: 관심순
      - bounty: 바운티 높은 순
      - unanswered: 답변 대기 순
    """
    questions, total = await service.get_questions(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        major_id=major_id,
        tag_name=tag_name,
        sort_by=sort_by,
    )
    
    page = skip // limit + 1 if limit > 0 else 1
    
    return QuestionListResponse(
        questions=questions,
        total=total,
        page=page,
        page_size=limit
    )


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    service: QuestionService = Depends(get_question_service),
):
    """
    질문 상세 조회
    
    - **question_id**: 질문 ID
    """
    question = await service.get_question_by_id(db, question_id, increment_view=True)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"질문을 찾을 수 없습니다: {question_id}"
        )
    
    if question.is_deleted or question.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="삭제되었거나 숨겨진 질문입니다"
        )
    
    return question


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    질문 수정
    
    - **question_id**: 질문 ID
    - 작성자 본인만 수정 가능
    - 채택된 질문은 수정 불가
    """
    question = await service.update_question(db, question_id, question_data, current_user.id)
    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service),
):
    """
    질문 삭제 (소프트 삭제)
    
    - **question_id**: 질문 ID
    - 작성자 본인만 삭제 가능
    - 답변이 있는 질문은 삭제 불가
    """
    await service.delete_question(db, question_id, current_user.id)
    return None
