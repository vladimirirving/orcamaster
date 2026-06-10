import os
from datetime import datetime
from pathlib import Path
import jinja2
from weasyprint import HTML
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.diario import DiarioObra, DiarioFoto
from app.models.empresa import Empresa
from app.models.obra import Obra
from app.models.usuario import Usuario

_template_dir = Path(__file__).resolve().parent.parent / "templates"
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_template_dir)),
    autoescape=jinja2.select_autoescape(["html", "htm", "j2", "xml"]),
)

_CLIMA_LABELS = {
    "ensolarado": "Ensolarado",
    "parcialmente_nublado": "Parcialmente Nublado",
    "nublado": "Nublado",
    "chuvoso": "Chuvoso",
}

_TURNO_LABELS = {
    "manha": "Manhã",
    "tarde": "Tarde",
    "noite": "Noite",
}


async def gerar_rdo_bytes(entry_id: int, db: AsyncSession) -> bytes:
    entry_r = await db.execute(select(DiarioObra).where(DiarioObra.id == entry_id))
    entry = entry_r.scalar_one_or_none()
    if entry is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Entrada não encontrada")

    obra_r = await db.execute(select(Obra).where(Obra.id == entry.obra_id))
    obra = obra_r.scalar_one()

    empresa_r = await db.execute(select(Empresa).where(Empresa.id == entry.empresa_id))
    empresa = empresa_r.scalar_one()

    responsavel = "—"
    if entry.criado_por:
        user_r = await db.execute(select(Usuario).where(Usuario.id == entry.criado_por))
        user = user_r.scalar_one_or_none()
        if user:
            responsavel = user.nome

    fotos_r = await db.execute(
        select(DiarioFoto).where(DiarioFoto.diario_id == entry_id).order_by(DiarioFoto.id)
    )
    fotos_data = []
    for foto in fotos_r.scalars().all():
        path_abs = os.path.join(settings.diario_dir, foto.caminho)
        if os.path.exists(path_abs):
            fotos_data.append({"nome_original": foto.nome_original, "path_abs": path_abs})

    clima_label = _CLIMA_LABELS.get(entry.clima, entry.clima)
    turnos_label = None
    if entry.turnos:
        parts = [_TURNO_LABELS.get(t.strip(), t.strip()) for t in entry.turnos.split(",")]
        turnos_label = " · ".join(parts)

    tmpl = _jinja_env.get_template("rdo.html.j2")
    html = tmpl.render(
        empresa=empresa,
        obra=obra,
        entrada=entry,
        clima_label=clima_label,
        turnos_label=turnos_label,
        fotos=fotos_data,
        responsavel=responsavel,
        gerado_em=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )
    return HTML(string=html).write_pdf()
