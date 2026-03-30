"""
FASE 1 — Testes TDD para Gestão de Certificados A1
Estes testes DEFINEM o comportamento esperado do CertificateManager.
TDD: escrever testes → rodar (RED) → implementar → rodar (GREEN)
"""
import os
import pytest
from pathlib import Path

# O módulo que VAMOS criar
from esocial.certificate_manager import CertificateManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CERT_VALID_PATH = FIXTURES_DIR / "cert_valid.pfx"
CERT_VALID_PASSWORD = "test1234"
CERT_EXPIRED_PATH = FIXTURES_DIR / "cert_expired.pfx"
CERT_EXPIRED_PASSWORD = "expired123"


class TestCertUploadValid:
    """TEST-CERT-01: Upload .pfx válido + senha correta → sucesso"""

    def test_validate_pfx_returns_dict(self):
        """validate_pfx com cert válido retorna dict com informações"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        result = CertificateManager.validate_pfx(pfx_data, CERT_VALID_PASSWORD)
        assert isinstance(result, dict)

    def test_validate_pfx_has_required_fields(self):
        """Resultado contém cnpj, nome_titular, emissor, numero_serie, validade, valido"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        result = CertificateManager.validate_pfx(pfx_data, CERT_VALID_PASSWORD)
        for field in ("cnpj", "nome_titular", "emissor", "numero_serie", "validade", "valido"):
            assert field in result, f"Campo '{field}' ausente no resultado"

    def test_validate_pfx_extracts_cnpj(self):
        """Extrai CNPJ do subject do certificado"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        result = CertificateManager.validate_pfx(pfx_data, CERT_VALID_PASSWORD)
        assert result["cnpj"] == "12345678000190"

    def test_validate_pfx_extracts_titular(self):
        """Extrai nome do titular (Common Name)"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        result = CertificateManager.validate_pfx(pfx_data, CERT_VALID_PASSWORD)
        assert result["nome_titular"] == "TESTE EMPRESA LTDA"

    def test_validate_pfx_valid_is_true(self):
        """Certificado válido retorna valido=True"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        result = CertificateManager.validate_pfx(pfx_data, CERT_VALID_PASSWORD)
        assert result["valido"] is True

    def test_save_certificate_creates_file(self, tmp_path):
        """save_certificate salva arquivo .pfx no disco"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        filepath = CertificateManager.save_certificate(
            pfx_data, "12345678000190", "ABC123", base_dir=str(tmp_path)
        )
        assert os.path.exists(filepath)
        assert filepath.endswith(".pfx")


class TestCertUploadWrongPassword:
    """TEST-CERT-02: Upload .pfx + senha errada → ValueError"""

    def test_wrong_password_raises_valueerror(self):
        """Senha incorreta levanta ValueError"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        with pytest.raises(ValueError, match="[Ss]enha"):
            CertificateManager.validate_pfx(pfx_data, "senha_errada")

    def test_empty_password_raises_valueerror(self):
        """Senha vazia levanta ValueError"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        with pytest.raises(ValueError):
            CertificateManager.validate_pfx(pfx_data, "")


class TestCertExpired:
    """TEST-CERT-03: Upload .pfx vencido → ValueError"""

    def test_expired_cert_raises_valueerror(self):
        """Certificado vencido levanta ValueError com mensagem sobre vencimento"""
        pfx_data = CERT_EXPIRED_PATH.read_bytes()
        with pytest.raises(ValueError, match="[Vv]encido"):
            CertificateManager.validate_pfx(pfx_data, CERT_EXPIRED_PASSWORD)


class TestCertListActive:
    """TEST-CERT-04: Listar certificado ativo → sem expor senha"""

    def test_info_does_not_contain_password(self):
        """Resultado de validate_pfx NÃO contém campo 'senha' ou 'password'"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        result = CertificateManager.validate_pfx(pfx_data, CERT_VALID_PASSWORD)
        for key in result:
            assert "senha" not in key.lower()
            assert "password" not in key.lower()

    def test_encrypted_password_not_equals_original(self):
        """Senha criptografada é diferente da original"""
        encrypted = CertificateManager.encrypt_password(CERT_VALID_PASSWORD)
        assert encrypted != CERT_VALID_PASSWORD


class TestCertFernetRoundTrip:
    """TEST-CERT-05: Descriptografar senha → igual à original"""

    def test_encrypt_then_decrypt_roundtrip(self):
        """encrypt → decrypt retorna senha original"""
        original = "minha_senha_super_secreta_123"
        encrypted = CertificateManager.encrypt_password(original)
        decrypted = CertificateManager.decrypt_password(encrypted)
        assert decrypted == original

    def test_encrypt_different_passwords_different_output(self):
        """Senhas diferentes geram criptografias diferentes"""
        enc1 = CertificateManager.encrypt_password("senha1")
        enc2 = CertificateManager.encrypt_password("senha2")
        assert enc1 != enc2

    def test_decrypt_invalid_token_raises(self):
        """Token inválido levanta exceção"""
        with pytest.raises(Exception):
            CertificateManager.decrypt_password("token_invalido_lixo")

    def test_load_certificate_from_disk(self, tmp_path):
        """Salvar e recarregar certificado do disco funciona"""
        pfx_data = CERT_VALID_PATH.read_bytes()
        filepath = CertificateManager.save_certificate(
            pfx_data, "12345678000190", "ABC123", base_dir=str(tmp_path)
        )
        private_key, certificate, _ = CertificateManager.load_certificate(
            filepath, CERT_VALID_PASSWORD
        )
        assert private_key is not None
        assert certificate is not None
