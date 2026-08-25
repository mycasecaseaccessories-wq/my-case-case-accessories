from uuid import uuid4

from app.auth import User, _decode_token, _hash_password, _make_token, _verify_password


def test_password_hash_round_trip() -> None:
    encoded = _hash_password("correct-horse-battery")
    assert encoded != "correct-horse-battery"
    assert _verify_password("correct-horse-battery", encoded)
    assert not _verify_password("wrong-password", encoded)


def test_signed_token_round_trip() -> None:
    user = User(id=uuid4(), email="person@example.com", password_hash="unused", role="customer")
    token = _make_token(user)
    claims = _decode_token(token)
    assert claims["sub"] == str(user.id)
    assert claims["role"] == "customer"
