from pathlib import Path
from typing import Optional
import jinja2
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from weasyprint import HTML
from app.models.bdi import BDI
from app.models.empresa import Empresa
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.obra import Obra
from app.models.proposta_config import PropostaConfig
from app.models.versao import Versao

_template_dir = Path(__file__).resolve().parent.parent / "templates"
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_template_dir)),
    autoescape=False,
)


async def gerar_pdf_bytes(versao_id: int, db: AsyncSession) -> bytes:
    """Carrega todos os dados e retorna o PDF em bytes. Levanta 404 se PropostaConfig não existe."""
    pc_result = await db.execute(
        select(PropostaConfig).where(PropostaConfig.versao_id == versao_id)
    )
    pc = pc_result.scalar_one_or_none()
    if pc is None:
        raise HTTPException(status_code=404, detail="Proposta não configurada")

    versao_result = await db.execute(
        select(Versao).options(selectinload(Versao.obra)).where(Versao.id == versao_id)
    )
    versao = versao_result.scalar_one()
    obra: Obra = versao.obra

    empresa_result = await db.execute(select(Empresa).where(Empresa.id == obra.empresa_id))
    empresa = empresa_result.scalar_one()

    bdi_result = await db.execute(select(BDI).where(BDI.versao_id == versao_id))
    bdi: Optional[BDI] = bdi_result.scalar_one_or_none()

    grupos_result = await db.execute(
        select(Grupo)
        .where(Grupo.versao_id == versao_id)
        .options(selectinload(Grupo.itens).selectinload(Item.composicao))
        .order_by(Grupo.ordem)
    )
    grupos = grupos_result.scalars().all()

    html_str = _jinja_env.get_template("proposta.html.j2").render(
        empresa=empresa,
        obra=obra,
        versao=versao,
        proposta=pc,
        bdi=bdi,
        grupos=grupos,
    )
    return HTML(string=html_str).write_pdf()
