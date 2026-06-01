import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.scheduler import purge_versoes_job, expire_pacotes_job


@pytest.mark.asyncio
async def test_purge_versoes_job_runs_without_error():
    # Mock the session to avoid actual database connection
    mock_session = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.delete = AsyncMock()

    # Create a context manager mock for AsyncSessionLocal
    mock_session_cls = AsyncMock()
    mock_session_cls.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.__aexit__ = AsyncMock(return_value=None)

    with patch("app.scheduler.AsyncSessionLocal", return_value=mock_session_cls):
        await purge_versoes_job()  # should not raise


@pytest.mark.asyncio
async def test_expire_pacotes_job_runs_without_error():
    # Mock the session to avoid actual database connection
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    # Create a context manager mock for AsyncSessionLocal
    mock_session_cls = AsyncMock()
    mock_session_cls.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.__aexit__ = AsyncMock(return_value=None)

    with patch("app.scheduler.AsyncSessionLocal", return_value=mock_session_cls):
        await expire_pacotes_job()  # should not raise
