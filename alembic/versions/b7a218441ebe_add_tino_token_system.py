"""add_tino_token_system

Revision ID: b7a218441ebe
Revises: 323c1bed465d
Create Date: 2025-11-26 21:07:59.434384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7a218441ebe'
down_revision: Union[str, Sequence[str], None] = '323c1bed465d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. users 테이블에 tino_balance 추가
    op.add_column(
        'users',
        sa.Column('tino_balance', sa.Integer(), nullable=False, server_default='100', comment='TINO 토큰 잔액')
    )
    
    # 2. tino_transactions 테이블 생성
    op.create_table(
        'tino_transactions',
        sa.Column('id', sa.Integer(), nullable=False, comment='거래 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
        sa.Column('amount', sa.Integer(), nullable=False, comment='거래 금액 (양수=입금, 음수=출금)'),
        sa.Column('balance_after', sa.Integer(), nullable=False, comment='거래 후 잔액'),
        sa.Column('transaction_type', sa.String(length=50), nullable=False, comment='거래 타입'),
        sa.Column('question_id', sa.Integer(), nullable=True, comment='관련 질문 ID'),
        sa.Column('answer_id', sa.Integer(), nullable=True, comment='관련 답변 ID'),
        sa.Column('description', sa.String(length=200), nullable=True, comment='거래 설명'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='거래 일시'),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='TINO 토큰 거래 이력'
    )
    op.create_index(op.f('ix_tino_transactions_id'), 'tino_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_tino_transactions_transaction_type'), 'tino_transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_tino_transactions_user_id'), 'tino_transactions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tino_transactions_user_id'), table_name='tino_transactions')
    op.drop_index(op.f('ix_tino_transactions_transaction_type'), table_name='tino_transactions')
    op.drop_index(op.f('ix_tino_transactions_id'), table_name='tino_transactions')
    op.drop_table('tino_transactions')
    op.drop_column('users', 'tino_balance')
