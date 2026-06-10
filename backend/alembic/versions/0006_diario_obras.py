"""add diario_obra and diario_foto tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'diario_obra',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('obra_id', sa.Integer(), sa.ForeignKey('obra.id', ondelete='CASCADE'), nullable=False),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('clima', sa.String(25), nullable=False),
        sa.Column('turnos', sa.String(30), nullable=True),
        sa.Column('efetivo', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('equipes', sa.Text(), nullable=True),
        sa.Column('equipamentos', sa.Text(), nullable=True),
        sa.Column('atividades', sa.Text(), nullable=False),
        sa.Column('ocorrencias', sa.Text(), nullable=True),
        sa.Column('criado_por', sa.Integer(), sa.ForeignKey('usuario.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('obra_id', 'data', name='uq_diario_obra_data'),
    )
    op.create_index('ix_diario_obra_obra_id', 'diario_obra', ['obra_id'])
    op.create_index('ix_diario_obra_empresa_id', 'diario_obra', ['empresa_id'])

    op.create_table(
        'diario_foto',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('diario_id', sa.Integer(), sa.ForeignKey('diario_obra.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nome_original', sa.String(255), nullable=False),
        sa.Column('caminho', sa.String(500), nullable=False),
        sa.Column('tamanho_bytes', sa.Integer(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_diario_foto_diario_id', 'diario_foto', ['diario_id'])


def downgrade() -> None:
    op.drop_table('diario_foto')
    op.drop_table('diario_obra')
