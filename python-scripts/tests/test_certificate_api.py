"""
Testes de integração para os endpoints de certificados A1.
Testa a API REST via TestClient do FastAPI.
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import os

# Adicionar raiz ao path para importar bot_api
sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CERT_VALID_PATH = FIXTURES_DIR / "cert_valid.pfx"
CERT_VALID_PASSWORD = "test1234"


@pytest.fixture(scope="module")
def client():
    from bot_api import app
    return TestClient(app)


class TestCertificateEndpoints:
    """Testes de integração dos endpoints REST de certificados"""

    def test_upload_valid_cert(self, client):
        """POST /api/certificados/upload com cert válido → 200"""
        with open(CERT_VALID_PATH, "rb") as f:
            response = client.post(
                "/api/certificados/upload",
                files={"file": ("cert.pfx", f, "application/x-pkcs12")},
                data={"senha": CERT_VALID_PASSWORD},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["cnpj"] == "12345678000190"
        assert data["ativo"] is True

    def test_upload_wrong_password(self, client):
        """POST /api/certificados/upload com senha errada → 400"""
        with open(CERT_VALID_PATH, "rb") as f:
            response = client.post(
                "/api/certificados/upload",
                files={"file": ("cert.pfx", f, "application/x-pkcs12")},
                data={"senha": "errada"},
            )
        assert response.status_code == 400
        assert "Senha" in response.json()["detail"] or "senha" in response.json()["detail"]

    def test_get_active_cert(self, client):
        """GET /api/certificados/ativo → retorna certificado sem senha"""
        # Primeiro faz upload
        with open(CERT_VALID_PATH, "rb") as f:
            client.post(
                "/api/certificados/upload",
                files={"file": ("cert.pfx", f, "application/x-pkcs12")},
                data={"senha": CERT_VALID_PASSWORD},
            )
        response = client.get("/api/certificados/ativo")
        assert response.status_code == 200
        data = response.json()
        assert "cnpj" in data
        assert "senha" not in str(data).lower()
        assert "password" not in str(data).lower()
        assert "encrypted" not in str(data).lower()

    def test_delete_cert(self, client):
        """DELETE /api/certificados/{id} → remove certificado"""
        # Upload
        with open(CERT_VALID_PATH, "rb") as f:
            resp = client.post(
                "/api/certificados/upload",
                files={"file": ("cert.pfx", f, "application/x-pkcs12")},
                data={"senha": CERT_VALID_PASSWORD},
            )
        cert_id = resp.json()["id"]
        # Delete
        response = client.delete(f"/api/certificados/{cert_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True
