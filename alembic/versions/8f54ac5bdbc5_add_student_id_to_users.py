"""add_student_id_to_users

Revision ID: 8f54ac5bdbc5
Revises: e343a5fe59ad
Create Date: 2025-11-26 17:14:29.105154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f54ac5bdbc5'
down_revision: Union[str, Sequence[str], None] = 'e343a5fe59ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # users 테이블에 student_id 컬럼 추가
    op.add_column('users', sa.Column('student_id', sa.String(length=20), nullable=True, comment='학번'))
    
    # 기존 데이터가 있을 경우를 대비해 임시로 nullable=True로 추가 후
    # 기본값 설정 또는 데이터 마이그레이션을 수행한 뒤 nullable=False로 변경
    # 여기서는 개발 초기 단계로 가정하고 바로 nullable=False로 변경
    op.alter_column('users', 'student_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # users 테이블에서 student_id 컬럼 제거
    op.drop_column('users', 'student_id')
