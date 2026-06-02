from app.config import settings

def test_settings_loads():
    assert settings.secret_key is not None
    assert len(settings.secret_key) >= 32
    assert "postgresql" in settings.database_url
