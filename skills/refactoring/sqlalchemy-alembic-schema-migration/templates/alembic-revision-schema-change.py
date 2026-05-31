"""<short description>

Revision ID: <new_id>
Revises: <prev_id>
Create Date: YYYY-MM-DD
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '<new_id>'
down_revision: Union[str, Sequence[str], None] = '<prev_id>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 신규 컬럼 추가 (server_default로 기존 row 처리)
    op.add_column('target_table', sa.Column('score_new', sa.Integer, nullable=False, server_default='0'))

    # 2. 기존 테이블 → 신규 컬럼 데이터 이전
    op.execute("""
        UPDATE target_table t
        INNER JOIN (
            SELECT fk_id, score
            FROM source_table
            WHERE (fk_id, dt) IN (SELECT fk_id, MAX(dt) FROM source_table GROUP BY fk_id)
        ) latest ON t.id = latest.fk_id
        SET t.score_new = latest.score
    """)

    # 3. 구 테이블 DROP
    op.drop_table('source_table')

    # 4. 컬럼 rename
    op.alter_column('some_table', 'old_col', new_column_name='new_col',
                    existing_type=sa.Integer, nullable=False)


def downgrade() -> None:
    # 4. 컬럼 rename 원복
    op.alter_column('some_table', 'new_col', new_column_name='old_col',
                    existing_type=sa.Integer, nullable=False)

    # 3. 구 테이블 재생성
    op.create_table(
        'source_table',
        sa.Column('fk_id', sa.Integer, sa.ForeignKey('target_table.id'), nullable=False),
        sa.Column('score', sa.Integer, nullable=False),
        sa.Column('dt', sa.Date, nullable=False),
        sa.PrimaryKeyConstraint('fk_id', 'dt'),
    )

    # 1. 신규 컬럼 제거
    op.drop_column('target_table', 'score_new')
