import json
import logging
from typing import AsyncGenerator, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.composicao import Composicao
from app.models.insumo import Insumo

logger = logging.getLogger(__name__)

_GRUPOS_TIPICOS: dict[str, list[str]] = {
    "rodovia": [
        "Terraplenagem", "Drenagem Superficial", "Pavimentação",
        "Obras de Arte Correntes", "Sinalização", "Obras Complementares",
    ],
    "saneamento": [
        "Serviços Preliminares", "Escavação e Movimento de Terra",
        "Redes Coletoras", "Estações Elevatórias", "ETE/ETA",
        "Ligações Domiciliares",
    ],
    "ponte": [
        "Fundações", "Subestrutura", "Superestrutura",
        "Aparelhos de Apoio", "Tabuleiro", "Guarda-rodas e Defensas",
    ],
    "rede_eletrica": [
        "Serviços Preliminares", "Fundações e Estruturas",
        "Equipamentos", "Cabos e Condutores", "Proteções e Medição",
    ],
}
_GRUPOS_GENERICOS = [
    "Serviços Preliminares", "Infraestrutura",
    "Superestrutura", "Instalações", "Acabamentos",
]


async def buscar_composicao_tool(
    query: str,
    origem: Optional[str],
    empresa_id: int,
    db: AsyncSession,
) -> list[dict]:
    stmt = select(Composicao).where(
        or_(Composicao.empresa_id.is_(None), Composicao.empresa_id == empresa_id)
    )
    if origem:
        stmt = stmt.where(Composicao.origem == origem)
    q_like = f"%{query}%"
    stmt = stmt.where(
        or_(Composicao.codigo.ilike(q_like), Composicao.descricao.ilike(q_like))
    ).limit(10)
    result = await db.execute(stmt)
    return [
        {
            "id": c.id,
            "codigo": c.codigo,
            "descricao": c.descricao,
            "unidade": c.unidade,
            "preco_unitario": str(c.preco_unitario),
            "origem": c.origem,
        }
        for c in result.scalars().all()
    ]


def listar_grupos_tipicos_tool(tipo_obra: str) -> list[str]:
    return _GRUPOS_TIPICOS.get(tipo_obra, _GRUPOS_GENERICOS)


async def obter_composicao_tool(
    composicao_id: int,
    empresa_id: int,
    db: AsyncSession,
) -> Optional[dict]:
    result = await db.execute(
        select(Composicao).where(
            Composicao.id == composicao_id,
            or_(Composicao.empresa_id.is_(None), Composicao.empresa_id == empresa_id),
        )
    )
    c = result.scalar_one_or_none()
    if c is None:
        return None
    r_ins = await db.execute(select(Insumo).where(Insumo.composicao_id == composicao_id))
    insumos = [
        {
            "descricao": i.descricao,
            "tipo": i.tipo,
            "unidade": i.unidade,
            "coeficiente": str(i.coeficiente),
            "preco_unitario": str(i.preco_unitario),
        }
        for i in r_ins.scalars().all()
    ]
    return {
        "id": c.id,
        "codigo": c.codigo,
        "descricao": c.descricao,
        "unidade": c.unidade,
        "preco_unitario": str(c.preco_unitario),
        "origem": c.origem,
        "insumos": insumos,
    }


async def gerar_proposta_stream(
    descricao: str,
    versao_id: int,
    empresa_id: int,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    yield 'data: {"type": "error", "msg": "Agente não implementado"}\n\n'
