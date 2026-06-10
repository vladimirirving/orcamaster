from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, usuarios, obras, versoes, grupos, composicoes, bdi, cronograma
from app.routers import medicoes
from app.routers import dashboard
from app.routers import curva_abc
from app.routers import empresa
from app.routers import proposta
from app.routers import pacote
from app.routers import agente
from app.routers import planilha_import
from app.routers.clientes import router as clientes_router
from app.routers.fornecedores import router as fornecedores_router
from app.routers.diario import router as diario_router
from app.routers.relatorios import router as relatorios_router
from app.routers.contratos import router as contratos_router
from app.routers.alertas import router as alertas_router
from app.routers.insumo_item import router as insumo_item_router
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="OrçaAVML API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(obras.router)
app.include_router(versoes.router)
app.include_router(grupos.router)
app.include_router(composicoes.router)
app.include_router(bdi.router)
app.include_router(cronograma.router)
app.include_router(medicoes.router)
app.include_router(dashboard.router)
app.include_router(curva_abc.router)
app.include_router(empresa.router)
app.include_router(proposta.router)
app.include_router(pacote.router)
app.include_router(agente.router)
app.include_router(planilha_import.router)
app.include_router(clientes_router)
app.include_router(fornecedores_router)
app.include_router(diario_router)
app.include_router(relatorios_router)
app.include_router(contratos_router)
app.include_router(alertas_router)
app.include_router(insumo_item_router)
