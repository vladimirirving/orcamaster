"""add contrato and aditivo tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'contrato',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('obra_id', sa.Integer(), sa.ForeignKey('obra.id', ondelete='CASCADE'), nullable=False),
        sa.Column('numero', sa.String(100), nullable=True),
        sa.Column('objeto', sa.Text(), nullable=False),
        sa.Column('valor_original', sa.Numeric(15, 2), nullable=False),
        sa.Column('data_assinatura', sa.Date(), nullable=True),
        sa.Column('data_inicio', sa.Date(), nullable=True),
        sa.Column('data_fim', sa.Date(), nullable=True),
        sa.Column('contratante_nome', sa.String(255), nullable=True),
        sa.Column('contratante_cnpj', sa.String(18), nullable=True),
        sa.Column('contratado_nome', sa.String(255), nullable=True),
        sa.Column('contratado_cnpj', sa.String(18), nullable=True),
        sa.Column('arquivo_path', sa.String(500), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_contrato_obra_id', 'contrato', ['obra_id'])

    op.create_table(
        'aditivo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('contrato_id', sa.Integer(), sa.ForeignKey('contrato.id', ondelete='CASCADE'), nullable=False),
        sa.Column('numero', sa.String(100), nullable=True),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('delta_valor', sa.Numeric(15, 2), nullable=True),
        sa.Column('nova_data_fim', sa.Date(), nullable=True),
        sa.Column('justificativa', sa.Text(), nullable=True),
        sa.Column('data_assinatura', sa.Date(), nullable=True),
        sa.Column('arquivo_path', sa.String(500), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_aditivo_contrato_id', 'aditivo', ['contrato_id'])


def downgrade() -> None:
    op.drop_table('aditivo')
    op.drop_table('contrato')
