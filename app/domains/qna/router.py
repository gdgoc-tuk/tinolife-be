from fastapi import APIRouter, HTTPException, status, Query, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.qna.schema import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
    QuestionListItem,
    AnswerCreate,
    AnswerUpdate,
    AnswerResponse,
    AnswerListResponse,
    AnswerVoteRequest,
    AnswerCommentCreate,
    AnswerCommentUpdate,
    AnswerCommentResponse,
    AnswerCommentListResponse,
    InterestResponse,
    BookmarkResponse,
    BookmarkListResponse,
    SearchResponse,
    ReportCreate,
    ReportResponse,
    ImageUploadResponse,
)
from app.domains.qna.service import (
    CategoryService,
    get_category_service,
    QuestionService,
    get_question_service,
    AnswerService,
    get_answer_service,
    AnswerCommentService,
    get_answer_comment_service,
    InterestService,
    get_interest_service,
    BookmarkService,
    get_bookmark_service,
    SearchService,
    get_search_service,
    ReportService,
    get_report_service,
)
from app.common.dependencies import get_current_user
from app.common.image_upload import ImageUploader, get_image_uploader
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


# =================================================================
# Questions Endpoints
# =================================================================


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


@router.post("/questions/{question_id}/answers", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_answer(
    question_id: int,
    answer_data: AnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AnswerService = Depends(get_answer_service),
):
    """
    답변 생성
    
    - **question_id**: 질문 ID
    - **content**: 답변 내용
    - **is_anonymous**: 익명 여부 (기본값: false)
    - 답변 등록 시 2 TINO 보상 지급
    """
    answer = await service.create_answer(db, question_id, answer_data, current_user.id)
    return answer


@router.get("/questions/{question_id}/answers", response_model=AnswerListResponse)
async def get_answers(
    question_id: int,
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(50, ge=1, le=100, description="조회할 항목 수"),
    db: Session = Depends(get_db),
    service: AnswerService = Depends(get_answer_service),
):
    """
    질문에 대한 답변 목록 조회
    
    - **question_id**: 질문 ID
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    """
    answers, total = await service.get_answers(db, question_id, skip=skip, limit=limit)
    return AnswerListResponse(answers=answers, total=total)


@router.put("/answers/{answer_id}", response_model=AnswerResponse)
async def update_answer(
    answer_id: int,
    answer_data: AnswerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AnswerService = Depends(get_answer_service),
):
    """
    답변 수정
    
    - **answer_id**: 답변 ID
    - 작성자 본인만 수정 가능
    - 채택된 답변은 수정 불가
    """
    answer = await service.update_answer(db, answer_id, answer_data, current_user.id)
    return answer


@router.delete("/answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AnswerService = Depends(get_answer_service),
):
    """
    답변 삭제 (소프트 삭제)
    
    - **answer_id**: 답변 ID
    - 작성자 본인만 삭제 가능
    - 채택된 답변은 삭제 불가
    """
    await service.delete_answer(db, answer_id, current_user.id)
    return None


@router.post("/answers/{answer_id}/vote", response_model=AnswerResponse)
async def vote_answer(
    answer_id: int,
    vote_data: AnswerVoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AnswerService = Depends(get_answer_service),
):
    """
    답변에 좋아요/싫어요 투표
    
    - **answer_id**: 답변 ID
    - **vote_type**: "like" 또는 "dislike"
    - 동일한 투표를 다시 하면 투표 취소
    - 좋아요 5개 달성 시 답변 작성자에게 3 TINO 보상
    """
    answer = await service.vote_answer(db, answer_id, current_user.id, vote_data.vote_type)
    return answer


@router.post("/questions/{question_id}/accept/{answer_id}", response_model=QuestionResponse)
async def accept_answer(
    question_id: int,
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AnswerService = Depends(get_answer_service),
):
    """
    답변 채택
    
    - **question_id**: 질문 ID
    - **answer_id**: 채택할 답변 ID
    - 질문 작성자만 채택 가능
    - 한 번 채택하면 변경 불가
    - 채택 시 답변 작성자에게 10 TINO + 바운티 지급
    """
    question = await service.accept_answer(db, question_id, answer_id, current_user.id)
    return question


@router.post("/answers/{answer_id}/comments", response_model=AnswerCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_answer_comment(
    answer_id: int,
    comment_data: AnswerCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AnswerCommentService = Depends(get_answer_comment_service),
):
    """
    답변 댓글 생성
    
    - **answer_id**: 답변 ID
    - **content**: 댓글 내용 (최대 500자)
    """
    comment = await service.create_comment(db, answer_id, comment_data, current_user.id)
    return comment


@router.get("/answers/{answer_id}/comments", response_model=AnswerCommentListResponse)
async def get_answer_comments(
    answer_id: int,
    db: Session = Depends(get_db),
    service: AnswerCommentService = Depends(get_answer_comment_service),
):
    """
    답변 댓글 목록 조회
    
    - **answer_id**: 답변 ID
    """
    comments, total = await service.get_comments(db, answer_id)
    return AnswerCommentListResponse(comments=comments, total=total)


@router.put("/comments/{comment_id}", response_model=AnswerCommentResponse)
async def update_answer_comment(
    comment_id: int,
    comment_data: AnswerCommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AnswerCommentService = Depends(get_answer_comment_service),
):
    """
    답변 댓글 수정
    
    - **comment_id**: 댓글 ID
    - 작성자 본인만 수정 가능
    """
    comment = await service.update_comment(db, comment_id, comment_data, current_user.id)
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AnswerCommentService = Depends(get_answer_comment_service),
):
    """
    답변 댓글 삭제 (소프트 삭제)
    
    - **comment_id**: 댓글 ID
    - 작성자 본인만 삭제 가능
    """
    await service.delete_comment(db, comment_id, current_user.id)
    return None


@router.post("/questions/{question_id}/interest", response_model=InterestResponse)
async def toggle_interest(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: InterestService = Depends(get_interest_service),
):
    """
    질문에 관심 표시 토글
    
    - **question_id**: 질문 ID
    - 이미 관심 표시한 경우 취소, 아닌 경우 추가
    - 관심 표시 수는 추천순 정렬에 활용됩니다
    """
    result = await service.toggle_interest(db, question_id, current_user.id)
    return InterestResponse(**result)


@router.post("/questions/{question_id}/bookmark", response_model=BookmarkResponse)
async def toggle_bookmark(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """
    질문 북마크 토글
    
    - **question_id**: 질문 ID
    - 이미 북마크한 경우 삭제, 아닌 경우 추가
    """
    result = await service.toggle_bookmark(db, question_id, current_user.id)
    return BookmarkResponse(**result)


@router.get("/bookmarks", response_model=BookmarkListResponse)
async def get_my_bookmarks(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(get_bookmark_service),
):
    """
    내 북마크 목록 조회
    
    - **page**: 페이지 번호 (기본값: 1)
    - **page_size**: 페이지 크기 (기본값: 20, 최대: 100)
    """
    result = await service.get_user_bookmarks(db, current_user.id, page, page_size)
    return BookmarkListResponse(**result)


@router.get("/search", response_model=SearchResponse)
async def search_questions(
    q: str = Query(..., min_length=1, max_length=100, description="검색어"),
    category_id: int = Query(None, description="카테고리 ID 필터"),
    major_id: int = Query(None, description="전공 ID 필터"),
    sort_by: str = Query("recent", description="정렬 기준 (recent, interest, bounty, unanswered)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db),
    service: SearchService = Depends(get_search_service),
):
    """
    질문 검색
    
    제목, 본문, 태그에서 검색어를 찾습니다.
    
    - **q**: 검색어 (필수)
    - **category_id**: 카테고리 필터 (선택)
    - **major_id**: 전공 필터 (선택)
    - **sort_by**: 정렬 기준
      - recent: 최신순 (기본값)
      - interest: 관심순
      - bounty: 바운티 높은 순
      - unanswered: 답변 대기순
    - **page**: 페이지 번호 (기본값: 1)
    - **page_size**: 페이지 크기 (기본값: 20, 최대: 100)
    """
    result = await service.search_questions(
        db, q, category_id, major_id, sort_by, page, page_size
    )
    
    # QuestionListItem으로 변환
    question_items = [
        QuestionListItem(
            id=q.id,
            title=q.title,
            category=q.category,
            major={"id": q.major.id, "name": q.major.name} if q.major else None,
            tags=q.tags,
            bounty=q.bounty,
            view_count=q.view_count,
            interest_count=q.interest_count,
            answer_count=q.answer_count,
            is_anonymous=q.is_anonymous,
            accepted_answer_id=q.accepted_answer_id,
            created_at=q.created_at
        )
        for q in result["questions"]
    ]
    
    return SearchResponse(
        questions=question_items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        query=result["query"]
    )


@router.post("/questions/{question_id}/report", response_model=ReportResponse)
async def report_question(
    question_id: int,
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """
    질문 신고
    
    - **question_id**: 신고할 질문 ID
    - **reason**: 신고 사유 (SPAM, ABUSE, INAPPROPRIATE, OTHER)
    - **description**: 상세 설명 (선택)
    """
    result = await service.report_question(
        db, question_id, current_user.id, report_data.reason, report_data.description
    )
    return ReportResponse(**result)


@router.post("/answers/{answer_id}/report", response_model=ReportResponse)
async def report_answer(
    answer_id: int,
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """
    답변 신고
    
    - **answer_id**: 신고할 답변 ID
    - **reason**: 신고 사유 (SPAM, ABUSE, INAPPROPRIATE, OTHER)
    - **description**: 상세 설명 (선택)
    """
    result = await service.report_answer(
        db, answer_id, current_user.id, report_data.reason, report_data.description
    )
    return ReportResponse(**result)


@router.post("/images/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="업로드할 이미지 파일"),
    image_type: str = Query("question", description="이미지 타입 (question, answer)"),
    current_user: User = Depends(get_current_user),
    uploader: ImageUploader = Depends(get_image_uploader),
):
    """
    이미지 업로드
    
    질문 또는 답변 본문에 삽입할 이미지를 업로드합니다.
    
    - **file**: 이미지 파일 (JPEG, PNG, GIF, WebP)
    - **image_type**: 이미지 용도 (question 또는 answer)
    - 최대 파일 크기: 5MB
    
    업로드 후 반환된 image_url을 본문에 삽입하여 사용합니다.
    """
    # prefix 설정
    prefix = f"qna/{image_type}s"
    
    # 이미지 업로드
    image_url, image_key, file_size, mime_type = await uploader.upload(file, prefix)
    
    return ImageUploadResponse(
        image_url=image_url,
        image_key=image_key,
        file_size=file_size,
        mime_type=mime_type,
        message="이미지가 성공적으로 업로드되었습니다"
    )
