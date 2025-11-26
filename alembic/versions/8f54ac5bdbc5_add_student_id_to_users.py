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
    # 1. users 테이블에 student_id 컬럼 추가 (nullable=True로 먼저 추가)
    op.add_column('users', sa.Column('student_id', sa.String(length=20), nullable=True, comment='학번'))
    
    # 2. 기존 데이터에 기본값 설정 (이메일에서 추출하거나 임시값 설정)
    # 이메일 형식이 student_id@domain.com인 경우 student_id 추출, 아니면 'TEMP_' + user_id
    op.execute("""
        UPDATE users 
        SET student_id = COALESCE(
            CASE 
                WHEN email ~ '^[0-9]+@' THEN SUBSTRING(email FROM '^([0-9]+)@')
                ELSE 'TEMP_' || id::text
            END,
            'TEMP_' || id::text
        )
        WHERE student_id IS NULL
    """)
    
    # 3. nullable=False로 변경
    op.alter_column('users', 'student_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # users 테이블에서 student_id 컬럼 제거
    op.drop_column('users', 'student_id')
