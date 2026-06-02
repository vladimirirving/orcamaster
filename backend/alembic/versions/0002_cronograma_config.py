"""add cronograma_inicio e fim to versao

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('versao', sa.Column('cronograma_inicio', sa.String(7), nullable=True))
    op.add_column('versao', sa.Column('cronograma_fim', sa.String(7), nullable=True))


def downgrade() -> None:
    op.drop_column('versao', 'cronograma_fim')
    op.drop_column('versao', 'cronograma_inicio')
