from app.core.security import decrypt, encrypt


def test_encrypt_decrypt_round_trip() -> None:
    plaintext = "super-secret-access-token"

    ciphertext = encrypt(plaintext)

    assert ciphertext != plaintext
    assert decrypt(ciphertext) == plaintext


def test_encrypt_produces_different_ciphertext_each_time() -> None:
    plaintext = "same-input"

    first = encrypt(plaintext)
    second = encrypt(plaintext)

    assert first != second
    assert decrypt(first) == decrypt(second) == plaintext
