import base64
import json
import secrets
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AesGcmCipher:
    """Cifrado autenticado AES-256-GCM para datos sensibles que sí deben recuperarse."""

    _prefix = "v1"
    _associated_data = b"catalogo-servicios:user-profile:v1"

    def __init__(self, encoded_key: str) -> None:
        try:
            padding = "=" * (-len(encoded_key) % 4)
            key = base64.urlsafe_b64decode(encoded_key + padding)
        except (ValueError, base64.binascii.Error) as error:
            raise ValueError("APP_ENCRYPTION_KEY debe ser Base64 URL-safe") from error
        if len(key) != 32:
            raise ValueError("APP_ENCRYPTION_KEY debe representar exactamente 32 bytes")
        self._cipher = AESGCM(key)

    def encrypt_json(self, value: dict[str, Any]) -> str:
        nonce = secrets.token_bytes(12)
        plaintext = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ciphertext = self._cipher.encrypt(nonce, plaintext, self._associated_data)
        payload = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
        return f"{self._prefix}:{payload}"

    def decrypt_json(self, value: str) -> dict[str, Any]:
        prefix, separator, payload = value.partition(":")
        if separator != ":" or prefix != self._prefix:
            raise ValueError("Formato de perfil cifrado no reconocido")
        raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        plaintext = self._cipher.decrypt(raw[:12], raw[12:], self._associated_data)
        decoded = json.loads(plaintext.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("El perfil cifrado debe ser un objeto JSON")
        return decoded
