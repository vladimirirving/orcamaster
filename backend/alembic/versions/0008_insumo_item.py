"""add insumo_item table

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'insumo_item',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('banco', sa.String(10), nullable=False),
        sa.Column('codigo', sa.String(50), nullable=False),
        sa.Column('descricao', sa.String(500), nullable=False),
        sa.Column('unidade', sa.String(20), nullable=False),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('preco_nao_desonerado', sa.Numeric(15, 6), nullable=False),
        sa.Column('preco_desonerado', sa.Numeric(15, 6), nullable=False),
        sa.Column('estado', sa.String(2), nullable=True),
        sa.Column('data_referencia', sa.Date(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresa.id'), nullable=True),
    )
    op.create_index('ix_insumo_item_banco_estado_data', 'insumo_item',
                    ['banco', 'estado', 'data_referencia'])
    op.create_index('ix_insumo_item_empresa_id', 'insumo_item', ['empresa_id'])


def downgrade() -> None:
    op.drop_index('ix_insumo_item_empresa_id', table_name='insumo_item')
    op.drop_index('ix_insumo_item_banco_estado_data', table_name='insumo_item')
    op.drop_table('insumo_item')
