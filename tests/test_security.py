from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.security import ALGORITHM, SECRET_KEY, create_access_token, verify_token


def test_valid_token():
    token = create_access_token({"sub": "alice"})
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "alice"


def test_tampered_token_returns_none():
    token = create_access_token({"sub": "alice"})
    assert verify_token(token + "tampered") is None


def test_fake_token_returns_none():
    assert verify_token("totally.fake.token") is None


def test_expired_token_returns_none():
    expired_token = jwt.encode(
        {"sub": "alice", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    assert verify_token(expired_token) is None


def test_payload_contains_exp():
    token = create_access_token({"sub": "alice"})
    payload = verify_token(token)
    assert "exp" in payload


def test_custom_expiry():
    token = create_access_token({"sub": "alice"}, expires_delta=120)
    payload = verify_token(token)
    assert payload is not None
