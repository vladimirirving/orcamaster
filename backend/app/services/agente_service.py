import json
import logging
from typing import AsyncGenerator, Optional

import anthropic
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
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

_TOOLS = [
    {
        "name": "buscar_composicao",
        "description": "Busca composições no banco local (SINAPI, SICRO ou próprias) por código ou descrição.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto para busca por código ou descrição"},
                "origem": {
                    "type": "string",
                    "enum": ["sinapi", "sicro", "propria"],
                    "description": "Filtrar por origem (opcional)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "listar_grupos_tipicos",
        "description": "Retorna os grupos de serviço típicos para o tipo de obra.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo_obra": {
                    "type": "string",
                    "enum": ["rodovia", "saneamento", "ponte", "rede_eletrica", "outro"],
                },
            },
            "required": ["tipo_obra"],
        },
    },
    {
        "name": "obter_composicao",
        "description": "Retorna detalhes completos de uma composição incluindo insumos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "composicao_id": {"type": "integer"},
            },
            "required": ["composicao_id"],
        },
    },
]

_SYSTEM_PROMPT = """Você é um assistente de orçamentação de obras de infraestrutura brasileiras.
O usuário descreve uma obra e você deve sugerir uma estrutura de planilha orçamentária
com grupos de serviço e itens, usando composições do banco local (SINAPI, SICRO ou próprias).

Passos obrigatórios:
1. Chame listar_grupos_tipicos com o tipo de obra identificado
2. Para cada grupo relevante, chame buscar_composicao para encontrar composições adequadas
3. Use obter_composicao para verificar detalhes quando necessário
4. Sugira quantidades típicas com base no porte da obra descrito
5. Responda APENAS com um JSON válido no formato abaixo (sem markdown, sem texto extra):
{"grupos": [{"nome": "Nome do Grupo", "itens": [{"composicao_id": 123, "descricao": "...", "codigo": "...", "unidade": "M3", "quantidade": 1000.0}]}]}

Regras:
- Use apenas composições encontradas pelas ferramentas (nunca invente códigos ou IDs)
- Prefira SINAPI para edificações/serviços gerais, SICRO para rodovias/infraestrutura
- Quantidades são estimativas — o orçamentista irá ajustá-las na revisão
- Inclua apenas grupos e itens relevantes para a obra descrita"""


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


def _sse(event_type: str, payload) -> str:
    if event_type in ("progress", "error"):
        data = {"type": event_type, "msg": payload}
    else:
        data = {"type": event_type, "data": payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _progress_msg(name: str, tool_input: dict, result) -> str:
    if name == "listar_grupos_tipicos":
        tipo = tool_input.get("tipo_obra", "")
        count = len(result) if isinstance(result, list) else 0
        return f"Grupos identificados para {tipo}: {count} grupos típicos"
    if name == "buscar_composicao":
        query = tool_input.get("query", "")
        count = len(result) if isinstance(result, list) else 0
        return f"Buscando '{query}'… {count} composições encontradas"
    if name == "obter_composicao":
        if isinstance(result, dict):
            return f"Composição {result.get('codigo', '')}: {result.get('descricao', '')}"
        return f"Composição {tool_input.get('composicao_id', '')} não encontrada"
    return f"Executando {name}…"


async def _execute_tool(
    name: str, tool_input: dict, empresa_id: int, db: AsyncSession
):
    if name == "buscar_composicao":
        return await buscar_composicao_tool(
            tool_input["query"], tool_input.get("origem"), empresa_id, db
        )
    if name == "listar_grupos_tipicos":
        return listar_grupos_tipicos_tool(tool_input["tipo_obra"])
    if name == "obter_composicao":
        return await obter_composicao_tool(tool_input["composicao_id"], empresa_id, db)
    return {"error": f"Ferramenta desconhecida: {name}"}


async def gerar_proposta_stream(
    descricao: str,
    versao_id: int,
    empresa_id: int,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Gerador assíncrono que emite eventos SSE enquanto o agente executa tool calls."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": descricao}]

    yield _sse("progress", "Analisando descrição da obra…")

    try:
        for _ in range(10):
            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                tools=_TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text_block = next(
                    (b for b in response.content if b.type == "text"), None
                )
                if text_block is None:
                    yield _sse("error", "Agente não gerou resposta estruturada")
                    return
                proposta = json.loads(text_block.text)
                yield _sse("proposta", proposta)
                return

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    result = await _execute_tool(block.name, block.input, empresa_id, db)
                    yield _sse("progress", _progress_msg(block.name, block.input, result))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
                messages.append({"role": "user", "content": tool_results})

        yield _sse("error", "Limite de iterações atingido sem resposta final")

    except json.JSONDecodeError:
        yield _sse("error", "Agente retornou resposta não estruturada")
    except Exception:
        logger.exception("gerar_proposta_stream versao_id=%s failed", versao_id)
        yield _sse("error", "Erro interno ao gerar proposta")
