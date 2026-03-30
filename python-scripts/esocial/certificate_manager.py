"""
Gerenciador de Certificados Digitais A1
Validação, leitura e manipulação de certificados .pfx para eSocial

Baseado no código de referência do repositório Projeto (comprovado em homologação).
"""

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.fernet import Fernet
from datetime import datetime, timezone
import os


class CertificateManager:
    """Gerencia certificados digitais A1 para eSocial"""

    _ENCRYPTION_KEY = os.environ.get(
        "SECRET_KEY",
        "VeO-WGEJAv51ZXFdGO0MV06Bl2lI1XkYMiqV_WOpy_g=",
    ).encode()

    @staticmethod
    def encrypt_password(password: str) -> str:
        encrypted = Fernet(CertificateManager._ENCRYPTION_KEY).encrypt(password.encode())
        return encrypted.decode()

    @staticmethod
    def decrypt_password(encrypted_password: str) -> str:
        decrypted = Fernet(CertificateManager._ENCRYPTION_KEY).decrypt(encrypted_password.encode())
        return decrypted.decode()

    @staticmethod
    def validate_pfx(pfx_data: bytes, password: str) -> dict:
        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                password.encode(),
                backend=default_backend(),
            )
        except Exception as e:
            if "password" in str(e).lower() or "decrypt" in str(e).lower() or "mac" in str(e).lower():
                raise ValueError("Senha do certificado incorreta")
            raise ValueError(f"Erro ao validar certificado: {e}")

        if certificate is None:
            raise ValueError("Certificado não encontrado no arquivo PFX")

        subject = certificate.subject
        issuer = certificate.issuer

        cnpj = None
        for attr in subject:
            if attr.oid.dotted_string == "2.5.4.5":  # serialNumber
                val = attr.value
                cnpj = val.split(":")[-1] if ":" in val else val
                break

        nome_titular = None
        for attr in subject:
            if attr.oid == x509.oid.NameOID.COMMON_NAME:
                nome_titular = attr.value
                break

        # Fallback: extract CNPJ from CN if not found in serialNumber
        if not cnpj and nome_titular and ":" in nome_titular:
            candidate = nome_titular.split(":")[-1].strip()
            if candidate.isdigit() and len(candidate) in (11, 14):
                cnpj = candidate

        emissor = None
        for attr in issuer:
            if attr.oid == x509.oid.NameOID.COMMON_NAME:
                emissor = attr.value
                break

        numero_serie = format(certificate.serial_number, "x").upper()

        validade = certificate.not_valid_after_utc.replace(tzinfo=None)
        if validade < datetime.now():
            raise ValueError("Certificado vencido")

        return {
            "cnpj": cnpj,
            "nome_titular": nome_titular or "Não identificado",
            "emissor": emissor or "Não identificado",
            "numero_serie": numero_serie,
            "validade": validade,
            "valido": True,
        }

    @staticmethod
    def save_certificate(pfx_data: bytes, cnpj: str, numero_serie: str, base_dir: str | None = None) -> str:
        cert_dir = base_dir or os.path.join(os.path.dirname(__file__), "..", "certificados")
        os.makedirs(cert_dir, exist_ok=True)
        filename = f"cert_{cnpj}_{numero_serie}.pfx"
        filepath = os.path.join(cert_dir, filename)
        with open(filepath, "wb") as f:
            f.write(pfx_data)
        return filepath

    @staticmethod
    def load_certificate(filepath: str, password: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError("Arquivo de certificado não encontrado")
        with open(filepath, "rb") as f:
            pfx_data = f.read()
        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                password.encode(),
                backend=default_backend(),
            )
            return private_key, certificate, additional_certs
        except Exception as e:
            if "password" in str(e).lower() or "decrypt" in str(e).lower() or "mac" in str(e).lower():
                raise ValueError("Senha do certificado incorreta")
            raise ValueError(f"Erro ao carregar certificado: {e}")
