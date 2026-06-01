import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.main import app
from app.database import get_db
from app.models import Base
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.services.auth_service import hash_password

TEST_DB_URL = "postgresql+asyncpg://orcaavml:orcaavml@localhost:5432/orcaavml_test"

engine = create_async_engine(TEST_DB_URL)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_test_db):
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


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
