import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.main import app
from app.database import get_db
from app.models import Base
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.obra import Obra
from app.models.versao import Versao
from app.services.auth_service import hash_password, create_access_token
from datetime import date

_default_test_db = "postgresql+asyncpg://orcaavml:orcaavml@localhost:5432/orcaavml_test"
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", _default_test_db)


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL)
    TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def empresa(db_session: AsyncSession) -> Empresa:
    e = Empresa(nome="Engenharia Teste Ltda", cnpj="00.000.000/0001-00")
    db_session.add(e)
    await db_session.flush()
    return e


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, empresa: Empresa) -> Usuario:
    u = Usuario(
        empresa_id=empresa.id,
        nome="Admin Teste",
        email="admin@teste.com",
        senha_hash=hash_password("senha123"),
        papel="admin",
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def auth_headers(admin_user: Usuario) -> dict:
    token = create_access_token({
        "sub": str(admin_user.id),
        "papel": admin_user.papel,
        "empresa_id": admin_user.empresa_id,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def obra(db_session: AsyncSession, empresa: Empresa) -> Obra:
    o = Obra(
        empresa_id=empresa.id,
        nome="Rodovia Teste SP-150",
        tipo_obra="rodovia",
        estado="em_elaboracao",
        data_criacao=date.today(),
    )
    db_session.add(o)
    await db_session.flush()
    return o


@pytest_asyncio.fixture
async def versao_ativa(db_session: AsyncSession, obra: Obra, admin_user: Usuario) -> Versao:
    v = Versao(obra_id=obra.id, numero=1, criada_por=admin_user.id)
    db_session.add(v)
    await db_session.flush()
    return v
