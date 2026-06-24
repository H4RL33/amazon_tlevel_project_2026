import time

import pytest
from jose.utils import base64url_decode, long_to_base64
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt as jose_jwt

from app.config import get_settings
from app.dependencies.auth import decode_id_token, get_current_user, get_current_user_optional
from app.models.user import User


@pytest.fixture(scope="module")
def rsa_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()
    return private_key, public_numbers


@pytest.fixture(scope="module")
def jwks(rsa_key_pair):
    _, public_numbers = rsa_key_pair
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": long_to_base64(public_numbers.n).decode("ascii"),
                "e": long_to_base64(public_numbers.e).decode("ascii"),
            }
        ]
    }


def _make_token(rsa_key_pair, *, audience=None, issuer=None, exp_offset=3600, sub="test-sub"):
    private_key, _ = rsa_key_pair
    settings = get_settings()
    pem = private_key.private_bytes(
        encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.PEM,
        format=__import__(
            "cryptography.hazmat.primitives.serialization", fromlist=["PrivateFormat"]
        ).PrivateFormat.PKCS8,
        encryption_algorithm=__import__(
            "cryptography.hazmat.primitives.serialization", fromlist=["NoEncryption"]
        ).NoEncryption(),
    )
    claims = {
        "sub": sub,
        "aud": audience if audience is not None else settings.COGNITO_CLIENT_ID,
        "iss": issuer
        if issuer is not None
        else f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}",
        "exp": int(time.time()) + exp_offset,
        "given_name": "Test",
        "family_name": "User",
        "email": "test@example.com",
    }
    return jose_jwt.encode(claims, pem, algorithm="RS256", headers={"kid": "test-kid"})


@pytest.fixture(autouse=True)
def _settings_and_jwks(monkeypatch, jwks):
    monkeypatch.setattr(get_settings(), "COGNITO_USER_POOL_ID", "test-pool")
    monkeypatch.setattr(get_settings(), "COGNITO_CLIENT_ID", "test-client")
    monkeypatch.setattr(get_settings(), "COGNITO_REGION", "eu-west-2")
    import app.dependencies.auth as auth_module

    monkeypatch.setattr(auth_module, "_cached_jwks", lambda: jwks)


async def test_decode_id_token_returns_claims_for_a_valid_token(rsa_key_pair):
    token = _make_token(rsa_key_pair)
    claims = decode_id_token(token)
    assert claims["sub"] == "test-sub"
    assert claims["given_name"] == "Test"


async def test_decode_id_token_rejects_expired_token(rsa_key_pair):
    token = _make_token(rsa_key_pair, exp_offset=-3600)
    with pytest.raises(Exception):
        decode_id_token(token)


async def test_decode_id_token_rejects_wrong_audience(rsa_key_pair):
    token = _make_token(rsa_key_pair, audience="someone-else")
    with pytest.raises(Exception):
        decode_id_token(token)


async def test_decode_id_token_rejects_wrong_issuer(rsa_key_pair):
    token = _make_token(rsa_key_pair, issuer="https://evil.example.com/pool")
    with pytest.raises(Exception):
        decode_id_token(token)


async def test_get_current_user_optional_returns_none_without_authorization_header() -> None:
    result = await get_current_user_optional(authorization=None, db=None)
    assert result is None


async def test_get_current_user_raises_401_for_missing_header() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=None, db=None)
    assert exc_info.value.status_code == 401


async def test_get_current_user_resolves_user_by_cognito_sub(db_session, rsa_key_pair):
    user = User(cognito_sub="test-sub", email="test@example.com", first_name="Test", last_name="User")
    db_session.add(user)
    await db_session.commit()

    token = _make_token(rsa_key_pair, sub="test-sub")
    result = await get_current_user(authorization=f"Bearer {token}", db=db_session)
    assert result.cognito_sub == "test-sub"


async def test_get_current_user_raises_401_when_user_row_missing(db_session, rsa_key_pair):
    from fastapi import HTTPException

    token = _make_token(rsa_key_pair, sub="no-such-user")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=f"Bearer {token}", db=db_session)
    assert exc_info.value.status_code == 401
