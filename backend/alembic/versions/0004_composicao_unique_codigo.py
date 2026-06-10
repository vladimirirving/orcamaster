"""unique constraint on composicao(empresa_id, codigo)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-05
"""
from alembic import op

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_composicao_empresa_codigo',
        'composicao',
        ['empresa_id', 'codigo'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_composicao_empresa_codigo', 'composicao', type_='unique')
