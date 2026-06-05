"""add cliente and fornecedor tables, obra.cliente_id FK

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cliente',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('tipo', sa.String(2), nullable=False),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('cpf_cnpj', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('telefone', sa.String(30), nullable=True),
        sa.Column('endereco', sa.String(300), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('estado', sa.String(2), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_cliente_empresa_id', 'cliente', ['empresa_id'])
    op.execute(
        "CREATE UNIQUE INDEX uq_cliente_empresa_cpfcnpj "
        "ON cliente(empresa_id, cpf_cnpj) WHERE cpf_cnpj IS NOT NULL"
    )

    op.create_table(
        'fornecedor',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('cnpj', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('telefone', sa.String(30), nullable=True),
        sa.Column('endereco', sa.String(300), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('estado', sa.String(2), nullable=True),
        sa.Column('categorias', sa.String(100), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_fornecedor_empresa_id', 'fornecedor', ['empresa_id'])
    op.execute(
        "CREATE UNIQUE INDEX uq_fornecedor_empresa_cnpj "
        "ON fornecedor(empresa_id, cnpj) WHERE cnpj IS NOT NULL"
    )

    op.add_column('obra', sa.Column(
        'cliente_id', sa.Integer(),
        sa.ForeignKey('cliente.id', ondelete='SET NULL'),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column('obra', 'cliente_id')
    op.drop_table('fornecedor')
    op.drop_table('cliente')
