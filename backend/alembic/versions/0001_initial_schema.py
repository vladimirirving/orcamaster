"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('empresa',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False),
        sa.Column('cnpj', sa.String(length=18), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cnpj'),
    )
    op.create_table('usuario',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('senha_hash', sa.String(length=200), nullable=False),
        sa.Column('papel', sa.String(length=20), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_table('obra',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=300), nullable=False),
        sa.Column('numero_processo', sa.String(length=100), nullable=True),
        sa.Column('cliente', sa.String(length=200), nullable=True),
        sa.Column('uf', sa.String(length=2), nullable=True),
        sa.Column('municipio', sa.String(length=100), nullable=True),
        sa.Column('tipo_obra', sa.String(length=50), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('responsavel_id', sa.Integer(), nullable=True),
        sa.Column('data_criacao', sa.Date(), nullable=False),
        sa.Column('data_prazo', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.ForeignKeyConstraint(['responsavel_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('versao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('obra_id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=True),
        sa.Column('criada_em', sa.DateTime(), nullable=False),
        sa.Column('criada_por', sa.Integer(), nullable=True),
        sa.Column('bloqueada', sa.Boolean(), nullable=False),
        sa.Column('total_sem_bdi', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_com_bdi', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('deletada_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['criada_por'], ['usuario.id'], ),
        sa.ForeignKeyConstraint(['obra_id'], ['obra.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('composicao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        sa.Column('origem', sa.String(length=10), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('descricao', sa.String(length=500), nullable=False),
        sa.Column('unidade', sa.String(length=20), nullable=False),
        sa.Column('preco_unitario', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('data_referencia', sa.Date(), nullable=True),
        sa.Column('base_origem_id', sa.Integer(), nullable=True),
        sa.Column('requer_revisao', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['base_origem_id'], ['composicao.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('grupo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('versao_id', sa.Integer(), nullable=False),
        sa.Column('pai_id', sa.Integer(), nullable=True),
        sa.Column('ordem', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=300), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['pai_id'], ['grupo.id'], ),
        sa.ForeignKeyConstraint(['versao_id'], ['versao.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('bdi',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('versao_id', sa.Integer(), nullable=False),
        sa.Column('ac', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('sg', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('r', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('df', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('lucro', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('iss', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('pis', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('cofins', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('bdi_composto', sa.Numeric(precision=8, scale=6), nullable=False),
        sa.Column('historico_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['versao_id'], ['versao.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('versao_id'),
    )
    op.create_table('insumo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('composicao_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('descricao', sa.String(length=300), nullable=False),
        sa.Column('unidade', sa.String(length=20), nullable=False),
        sa.Column('coeficiente', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('preco_unitario', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.ForeignKeyConstraint(['composicao_id'], ['composicao.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('medicao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('versao_id', sa.Integer(), nullable=False),
        sa.Column('periodo_inicio', sa.Date(), nullable=False),
        sa.Column('periodo_fim', sa.Date(), nullable=False),
        sa.Column('criada_por', sa.Integer(), nullable=True),
        sa.Column('linhas_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['criada_por'], ['usuario.id'], ),
        sa.ForeignKeyConstraint(['versao_id'], ['versao.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grupo_id', sa.Integer(), nullable=False),
        sa.Column('ordem', sa.Integer(), nullable=False),
        sa.Column('composicao_id', sa.Integer(), nullable=True),
        sa.Column('quantidade', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('unidade', sa.String(length=20), nullable=False),
        sa.Column('preco_unitario_sem_bdi', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('preco_unitario_com_bdi', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('total', sa.Numeric(precision=15, scale=6),
            sa.Computed('quantidade * COALESCE(preco_unitario_sem_bdi, 0)', persisted=True),
            nullable=False),
        sa.Column('etiqueta_revisao', sa.Boolean(), nullable=False),
        sa.Column('requer_revisao', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['composicao_id'], ['composicao.id'], ),
        sa.ForeignKeyConstraint(['grupo_id'], ['grupo.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('cronograma_linha',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('distribuicao_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['item.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_id'),
    )
    op.create_table('pacote_job',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('versao_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False),
        sa.Column('url_download', sa.String(length=500), nullable=True),
        sa.Column('erro_mensagem', sa.String(length=1000), nullable=True),
        sa.Column('gerado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['versao_id'], ['versao.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('pacote_job')
    op.drop_table('cronograma_linha')
    op.drop_table('item')
    op.drop_table('medicao')
    op.drop_table('bdi')
    op.drop_table('insumo')
    op.drop_table('grupo')
    op.drop_table('composicao')
    op.drop_table('versao')
    op.drop_table('obra')
    op.drop_table('usuario')
    op.drop_table('empresa')
