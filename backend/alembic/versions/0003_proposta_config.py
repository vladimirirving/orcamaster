"""add proposta_config table and empresa representante fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('empresa', sa.Column('representante_nome', sa.String(200), nullable=True))
    op.add_column('empresa', sa.Column('representante_cpf', sa.String(14), nullable=True))
    op.add_column('empresa', sa.Column('declaracoes_padrao', sa.Text(), nullable=True))

    op.create_table(
        'proposta_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('versao_id', sa.Integer(),
                  sa.ForeignKey('versao.id', ondelete='CASCADE'), nullable=False),
        sa.Column('validade_dias', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('data_proposta', sa.Date(), nullable=False),
        sa.Column('declaracoes', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('versao_id'),
    )


def downgrade() -> None:
    op.drop_table('proposta_config')
    op.drop_column('empresa', 'declaracoes_padrao')
    op.drop_column('empresa', 'representante_cpf')
    op.drop_column('empresa', 'representante_nome')
