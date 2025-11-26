"""create_qna_tables

Revision ID: 323c1bed465d
Revises: 8f54ac5bdbc5
Create Date: 2025-11-26 20:33:10.146145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '323c1bed465d'
down_revision: Union[str, Sequence[str], None] = '8f54ac5bdbc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 독립 테이블 먼저 생성 (categories, tags)
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False, comment='카테고리 ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='카테고리명'),
        sa.Column('display_order', sa.Integer(), nullable=False, comment='표시 순서'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='활성화 상태'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='질문 카테고리(말머리)'
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False, comment='태그 ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='태그명'),
        sa.Column('usage_count', sa.Integer(), nullable=False, comment='사용 횟수'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='활성화 상태'),
        sa.Column('is_official', sa.Boolean(), nullable=False, comment='공식 태그 여부'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='태그'
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    
    # 2. questions 테이블 생성 (accepted_answer_id FK 제외)
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False, comment='질문 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='작성자 ID'),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, comment='익명 여부'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='제목'),
        sa.Column('content', sa.Text(), nullable=False, comment='본문'),
        sa.Column('category_id', sa.Integer(), nullable=False, comment='카테고리 ID'),
        sa.Column('major_id', sa.Integer(), nullable=True, comment='전공 ID (null=전공무관, 대분류 제한 없이 전체 전공 선택 가능)'),
        sa.Column('bounty', sa.Integer(), nullable=False, comment='바운티 (TINO 토큰)'),
        sa.Column('view_count', sa.Integer(), nullable=False, comment='조회수'),
        sa.Column('interest_count', sa.Integer(), nullable=False, comment='관심 수'),
        sa.Column('answer_count', sa.Integer(), nullable=False, comment='답변 수'),
        sa.Column('is_hidden', sa.Boolean(), nullable=False, comment='숨김 여부'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='삭제 여부'),
        sa.Column('accepted_answer_id', sa.Integer(), nullable=True, comment='채택된 답변 ID'),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True, comment='채택 일시'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['major_id'], ['majors.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='질문'
    )
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)
    
    # 3. answers 테이블 생성
    op.create_table(
        'answers',
        sa.Column('id', sa.Integer(), nullable=False, comment='답변 ID'),
        sa.Column('question_id', sa.Integer(), nullable=False, comment='질문 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='작성자 ID'),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, comment='익명 여부'),
        sa.Column('content', sa.Text(), nullable=False, comment='답변 내용'),
        sa.Column('like_count', sa.Integer(), nullable=False, comment='좋아요 수'),
        sa.Column('dislike_count', sa.Integer(), nullable=False, comment='싫어요 수'),
        sa.Column('comment_count', sa.Integer(), nullable=False, comment='댓글 수'),
        sa.Column('is_accepted', sa.Boolean(), nullable=False, comment='채택 여부'),
        sa.Column('is_hidden', sa.Boolean(), nullable=False, comment='숨김 여부'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='삭제 여부'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='답변'
    )
    op.create_index(op.f('ix_answers_id'), 'answers', ['id'], unique=False)
    
    # 4. questions 테이블에 accepted_answer_id FK 추가
    op.create_foreign_key('fk_questions_accepted_answer_id', 'questions', 'answers', ['accepted_answer_id'], ['id'])
    
    # 5. question_tags 중간 테이블
    op.create_table(
        'question_tags',
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('question_id', 'tag_id'),
        comment='질문-태그 다대다 관계'
    )
    
    # 6. 이미지 테이블
    op.create_table(
        'question_images',
        sa.Column('id', sa.Integer(), nullable=False, comment='이미지 ID'),
        sa.Column('question_id', sa.Integer(), nullable=False, comment='질문 ID'),
        sa.Column('image_url', sa.String(length=500), nullable=False, comment='이미지 URL (본문에서 참조)'),
        sa.Column('image_key', sa.String(length=200), nullable=True, comment='S3 키 (또는 파일명) - 파일 삭제용'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='파일 크기 (bytes)'),
        sa.Column('mime_type', sa.String(length=50), nullable=True, comment='MIME 타입 (image/jpeg 등)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='질문 이미지 메타데이터'
    )
    op.create_index(op.f('ix_question_images_id'), 'question_images', ['id'], unique=False)
    
    op.create_table(
        'answer_images',
        sa.Column('id', sa.Integer(), nullable=False, comment='이미지 ID'),
        sa.Column('answer_id', sa.Integer(), nullable=False, comment='답변 ID'),
        sa.Column('image_url', sa.String(length=500), nullable=False, comment='이미지 URL (본문에서 참조)'),
        sa.Column('image_key', sa.String(length=200), nullable=True, comment='S3 키 (또는 파일명) - 파일 삭제용'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='파일 크기 (bytes)'),
        sa.Column('mime_type', sa.String(length=50), nullable=True, comment='MIME 타입 (image/jpeg 등)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='답변 이미지 메타데이터'
    )
    op.create_index(op.f('ix_answer_images_id'), 'answer_images', ['id'], unique=False)
    
    # 7. 인터랙션 테이블
    op.create_table(
        'answer_votes',
        sa.Column('id', sa.Integer(), nullable=False, comment='투표 ID'),
        sa.Column('answer_id', sa.Integer(), nullable=False, comment='답변 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
        sa.Column('vote_type', sa.String(length=10), nullable=False, comment='투표 타입 (LIKE/DISLIKE)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('answer_id', 'user_id', name='uq_answer_user_vote'),
        comment='답변 좋아요/싫어요'
    )
    op.create_index(op.f('ix_answer_votes_id'), 'answer_votes', ['id'], unique=False)
    
    op.create_table(
        'answer_comments',
        sa.Column('id', sa.Integer(), nullable=False, comment='댓글 ID'),
        sa.Column('answer_id', sa.Integer(), nullable=False, comment='답변 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='작성자 ID'),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, comment='익명 여부'),
        sa.Column('content', sa.String(length=500), nullable=False, comment='댓글 내용'),
        sa.Column('is_hidden', sa.Boolean(), nullable=False, comment='숨김 여부'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='삭제 여부'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='답변 댓글'
    )
    op.create_index(op.f('ix_answer_comments_id'), 'answer_comments', ['id'], unique=False)
    
    op.create_table(
        'question_interests',
        sa.Column('id', sa.Integer(), nullable=False, comment='관심 ID'),
        sa.Column('question_id', sa.Integer(), nullable=False, comment='질문 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_id', 'user_id', name='uq_question_user_interest'),
        comment='질문 관심 표시'
    )
    op.create_index(op.f('ix_question_interests_id'), 'question_interests', ['id'], unique=False)
    
    op.create_table(
        'question_bookmarks',
        sa.Column('id', sa.Integer(), nullable=False, comment='북마크 ID'),
        sa.Column('question_id', sa.Integer(), nullable=False, comment='질문 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_id', 'user_id', name='uq_question_user_bookmark'),
        comment='질문 북마크'
    )
    op.create_index(op.f('ix_question_bookmarks_id'), 'question_bookmarks', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 역순으로 테이블 삭제
    op.drop_index(op.f('ix_question_bookmarks_id'), table_name='question_bookmarks')
    op.drop_table('question_bookmarks')
    
    op.drop_index(op.f('ix_question_interests_id'), table_name='question_interests')
    op.drop_table('question_interests')
    
    op.drop_index(op.f('ix_answer_comments_id'), table_name='answer_comments')
    op.drop_table('answer_comments')
    
    op.drop_index(op.f('ix_answer_votes_id'), table_name='answer_votes')
    op.drop_table('answer_votes')
    
    op.drop_index(op.f('ix_answer_images_id'), table_name='answer_images')
    op.drop_table('answer_images')
    
    op.drop_index(op.f('ix_question_images_id'), table_name='question_images')
    op.drop_table('question_images')
    
    op.drop_table('question_tags')
    
    # accepted_answer_id FK 제거
    op.drop_constraint('fk_questions_accepted_answer_id', 'questions', type_='foreignkey')
    
    op.drop_index(op.f('ix_answers_id'), table_name='answers')
    op.drop_table('answers')
    
    op.drop_index(op.f('ix_questions_id'), table_name='questions')
    op.drop_table('questions')
    
    op.drop_index(op.f('ix_tags_id'), table_name='tags')
    op.drop_table('tags')
    
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_table('categories')
