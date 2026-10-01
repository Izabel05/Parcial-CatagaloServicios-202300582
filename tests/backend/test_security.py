import base64
import secrets
import unittest


try:
    from backend.app.security.encryption import AesGcmCipher
    from backend.app.security.passwords import PasswordService
except ModuleNotFoundError:  # Dependencias instaladas dentro de Docker/requirements.
    AesGcmCipher = None
    PasswordService = None


@unittest.skipIf(PasswordService is None, "Instalar argon2-cffi para ejecutar la prueba de contraseñas")
class SecurityTest(unittest.TestCase):
    def test_passwords_are_hashed_and_verified(self) -> None:
        service = PasswordService()
        password_hash = service.hash("una-clave-local-segura")
        self.assertNotEqual(password_hash, "una-clave-local-segura")
        self.assertTrue(service.verify(password_hash, "una-clave-local-segura"))
        self.assertFalse(service.verify(password_hash, "otra-clave"))

    @unittest.skipIf(AesGcmCipher is None, "Instalar cryptography para ejecutar la prueba AES")
    def test_profile_data_round_trips_with_aes_gcm(self) -> None:
        key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        cipher = AesGcmCipher(key)
        encrypted = cipher.encrypt_json({"phone": "+50200000000"})
        self.assertNotIn("+50200000000", encrypted)
        self.assertEqual(cipher.decrypt_json(encrypted)["phone"], "+50200000000")


if __name__ == "__main__":
    unittest.main()
