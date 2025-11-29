"""create_tinostory_tables

Revision ID: a1b2c3d4e5f6
Revises: 2021af522224
Create Date: 2025-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '2021af522224'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. stories 테이블 생성 (메인 테이블)
    op.create_table(
        'stories',
        sa.Column('id', sa.Integer(), nullable=False, comment='게시글 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='작성자 ID'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='제목'),
        sa.Column('content', sa.Text(), nullable=False, comment='본문'),
        sa.Column('recruitment_type', sa.Enum('CLUB', 'STUDY', 'PROJECT', 'ACTIVITY', 'OTHER', name='recruitmenttype'), nullable=False, comment='모집 타입 (CLUB, STUDY, PROJECT, ACTIVITY, OTHER)'),
        sa.Column('recruitment_status', sa.Enum('RECRUITING', 'COMPLETED', 'CLOSED', name='recruitmentstatus'), nullable=False, comment='모집 상태 (RECRUITING, COMPLETED, CLOSED)'),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=False, comment='모집 마감일'),
        sa.Column('open_chat_link', sa.String(length=500), nullable=False, comment='오픈채팅 링크 (또는 외부 지원 링크)'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0', comment='조회수'),
        sa.Column('like_count', sa.Integer(), nullable=False, server_default='0', comment='좋아요 수'),
        sa.Column('bookmark_count', sa.Integer(), nullable=False, server_default='0', comment='북마크 수'),
        sa.Column('comment_count', sa.Integer(), nullable=False, server_default='0', comment='댓글 수'),
        sa.Column('is_hidden', sa.Boolean(), nullable=False, server_default='false', comment='숨김 여부'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', comment='삭제 여부'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='티노스토리 게시글'
    )
    op.create_index(op.f('ix_stories_id'), 'stories', ['id'], unique=False)

    # 2. story_tags 중간 테이블 (기존 tags 테이블 재사용)
    op.create_table(
        'story_tags',
        sa.Column('story_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('story_id', 'tag_id'),
        comment='스토리-태그 다대다 관계'
    )

    # 3. story_images 테이블
    op.create_table(
        'story_images',
        sa.Column('id', sa.Integer(), nullable=False, comment='이미지 ID'),
        sa.Column('story_id', sa.Integer(), nullable=False, comment='스토리 ID'),
        sa.Column('image_url', sa.String(length=500), nullable=False, comment='이미지 URL'),
        sa.Column('image_key', sa.String(length=200), nullable=True, comment='S3 키 (또는 파일명) - 파일 삭제용'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0', comment='표시 순서'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='파일 크기 (bytes)'),
        sa.Column('mime_type', sa.String(length=50), nullable=True, comment='MIME 타입 (image/jpeg 등)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='스토리 이미지 메타데이터'
    )
    op.create_index(op.f('ix_story_images_id'), 'story_images', ['id'], unique=False)

    # 4. story_likes 테이블
    op.create_table(
        'story_likes',
        sa.Column('id', sa.Integer(), nullable=False, comment='좋아요 ID'),
        sa.Column('story_id', sa.Integer(), nullable=False, comment='스토리 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('story_id', 'user_id', name='uq_story_user_like'),
        comment='스토리 좋아요'
    )
    op.create_index(op.f('ix_story_likes_id'), 'story_likes', ['id'], unique=False)

    # 5. story_bookmarks 테이블
    op.create_table(
        'story_bookmarks',
        sa.Column('id', sa.Integer(), nullable=False, comment='북마크 ID'),
        sa.Column('story_id', sa.Integer(), nullable=False, comment='스토리 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('story_id', 'user_id', name='uq_story_user_bookmark'),
        comment='스토리 북마크'
    )
    op.create_index(op.f('ix_story_bookmarks_id'), 'story_bookmarks', ['id'], unique=False)

    # 6. story_comments 테이블
    op.create_table(
        'story_comments',
        sa.Column('id', sa.Integer(), nullable=False, comment='댓글 ID'),
        sa.Column('story_id', sa.Integer(), nullable=False, comment='스토리 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='작성자 ID'),
        sa.Column('content', sa.String(length=500), nullable=False, comment='댓글 내용'),
        sa.Column('is_hidden', sa.Boolean(), nullable=False, server_default='false', comment='숨김 여부'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', comment='삭제 여부'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='스토리 댓글'
    )
    op.create_index(op.f('ix_story_comments_id'), 'story_comments', ['id'], unique=False)

    # 7. story_reports 테이블
    op.create_table(
        'story_reports',
        sa.Column('id', sa.Integer(), nullable=False, comment='신고 ID'),
        sa.Column('reporter_id', sa.Integer(), nullable=False, comment='신고자 ID'),
        sa.Column('story_id', sa.Integer(), nullable=True, comment='신고된 스토리 ID'),
        sa.Column('comment_id', sa.Integer(), nullable=True, comment='신고된 댓글 ID'),
        sa.Column('reason', sa.String(length=50), nullable=False, comment='신고 사유 (SPAM, ABUSE, INAPPROPRIATE, FALSE_INFO, OTHER)'),
        sa.Column('description', sa.Text(), nullable=True, comment='상세 설명'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING', comment='처리 상태 (PENDING, REVIEWED, RESOLVED, REJECTED)'),
        sa.Column('admin_note', sa.Text(), nullable=True, comment='관리자 메모'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True, comment='처리 일시'),
        sa.Column('processed_by', sa.Integer(), nullable=True, comment='처리자 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='신고 일시'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 일시'),
        sa.ForeignKeyConstraint(['comment_id'], ['story_comments.id'], ),
        sa.ForeignKeyConstraint(['processed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reporter_id', 'story_id', name='uq_reporter_story'),
        sa.UniqueConstraint('reporter_id', 'comment_id', name='uq_reporter_story_comment'),
        comment='스토리/댓글 신고'
    )
    op.create_index(op.f('ix_story_reports_id'), 'story_reports', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 역순으로 테이블 삭제
    op.drop_index(op.f('ix_story_reports_id'), table_name='story_reports')
    op.drop_table('story_reports')

    op.drop_index(op.f('ix_story_comments_id'), table_name='story_comments')
    op.drop_table('story_comments')

    op.drop_index(op.f('ix_story_bookmarks_id'), table_name='story_bookmarks')
    op.drop_table('story_bookmarks')

    op.drop_index(op.f('ix_story_likes_id'), table_name='story_likes')
    op.drop_table('story_likes')

    op.drop_index(op.f('ix_story_images_id'), table_name='story_images')
    op.drop_table('story_images')

    op.drop_table('story_tags')

    op.drop_index(op.f('ix_stories_id'), table_name='stories')
    op.drop_table('stories')

    # Enum 타입 삭제
    op.execute('DROP TYPE IF EXISTS recruitmenttype')
    op.execute('DROP TYPE IF EXISTS recruitmentstatus')
