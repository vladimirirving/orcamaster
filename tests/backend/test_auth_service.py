import pytest
from app.services.auth_service import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
)


def test_hash_and_verify_password():
    hashed = hash_password("minha_senha_123")
    assert verify_password("minha_senha_123", hashed)
    assert not verify_password("senha_errada", hashed)


def test_create_and_decode_access_token():
    token = create_access_token({"sub": "42", "papel": "orcamentista"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["papel"] == "orcamentista"


def test_decode_invalid_token_raises():
    with pytest.raises(Exception):
        decode_access_token("token.invalido.aqui")
