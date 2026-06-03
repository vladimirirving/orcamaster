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
