"""
FASE 8 — Testes das rotas FastAPI de orquestração eSocial S-1010

Testa o pipeline completo via API REST:
- GET /api/esocial/rubricas-pendentes
- POST /api/esocial/s1010/enviar
- GET /api/esocial/s1010/consultar/{protocolo}
- GET /api/esocial/envios
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── Fixtures ─────────────────────────────────────────────────────

CERT_ROW = {
    "id": 1,
    "cnpj": "12345678000190",
    "titular": "EMPRESA TESTE LTDA",
    "arquivo_path": "/fake/cert.pfx",
    "senha_encrypted": "gAAAAABmFake==",
    "ativo": True,
}

RUBRICA_ROW = {
    "id": 10,
    "cod_rubrica": "1",
    "descricao": "HORAS NORMAIS",
    "cod_natureza": "1000 - Vencimentos",
    "incid_inss": "11",
    "incid_irrf": "11",
    "incid_fgts": "11",
    "inss_correto": "11",
    "irrf_correto": "11",
    "fgts_correto": "11",
    "analise": "pendente",
    "corrigido": False,
    "nat_rubr": "1000",
}

ENVIO_ROW = {
    "id": 1,
    "cod_rubrica": "1",
    "nome_rubrica": "HORAS NORMAIS",
    "status": "enviado",
    "protocolo_envio": "1.2.2026030001",
    "codigo_resposta": "201",
    "descricao_resposta": "Lote recebido com sucesso",
    "created_at": "2026-03-28T10:00:00",
}


def _make_app():
    """Cria app FastAPI com as rotas eSocial para teste."""
    from esocial.esocial_routes import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return app


def _client():
    return TestClient(_make_app())


# ── Classe 1: Rubricas Pendentes ─────────────────────────────────


class TestRubricasPendentes:
    """GET /api/esocial/rubricas-pendentes"""

    @patch("esocial.esocial_routes._get_conn")
    def test_retorna_lista_rubricas(self, mock_conn):
        """Deve retornar rubricas do banco com dados para envio"""
        mock_cursor = MagicMock()
        # 14 columns: id, cod_rubrica, descricao, cod_natureza, incid_inss, incid_irrf, incid_fgts,
        #             inss_correto, irrf_correto, fgts_correto, analise, corrigido, envio_status, ini_valid_esocial
        mock_cursor.fetchall.return_value = [
            (10, "1", "HORAS NORMAIS", "1000 - Vencimentos", "11", "11", "11", "11", "11", "11", "pendente", False, "pendente", None),
            (11, "2", "HORAS EXTRAS", "1002 - HE", "11", "9", "11", "11", "11", "11", "pendente", False, "pendente", None),
        ]
        mock_cursor.fetchone.return_value = None  # _load_cert_ativo → no cert
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

        client = _client()
        resp = client.get("/api/esocial/rubricas-pendentes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rubricas"]) == 2
        assert data["rubricas"][0]["cod_rubrica"] == "1"
        assert data["rubricas"][0]["nat_rubr"] == "1000"
        assert data["rubricas"][0]["incid_inss"] == "11"
        assert data["rubricas"][0]["analise"] == "pendente"

    @patch("esocial.esocial_routes._get_conn")
    def test_retorna_vazio_sem_pendentes(self, mock_conn):
        """Deve retornar lista vazia se não houver rubricas pendentes"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = None  # _load_cert_ativo → no cert
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

        client = _client()
        resp = client.get("/api/esocial/rubricas-pendentes")
        assert resp.status_code == 200
        assert resp.json()["rubricas"] == []


# ── Classe 2: Enviar S-1010 ──────────────────────────────────────


class TestEnviarS1010:
    """POST /api/esocial/s1010/enviar"""

    @patch("esocial.esocial_routes.ESocialClient.enviar_lote")
    @patch("esocial.esocial_routes.SOAPEnvelopeBuilder.montar_envio")
    @patch("esocial.esocial_routes.S1010XMLSigner.assinar")
    @patch("esocial.esocial_routes.S1010XMLGenerator.gerar_inclusao")
    @patch("esocial.esocial_routes.CertificateManager.decrypt_password")
    @patch("esocial.esocial_routes._load_cert_ativo")
    @patch("esocial.esocial_routes._get_conn")
    def test_envio_sucesso_uma_rubrica(self, mock_conn, mock_cert, mock_decrypt, mock_gerar, mock_sign, mock_soap, mock_enviar):
        """Pipeline completo: gerar → assinar → SOAP → enviar → salvar"""
        # Mock cert ativo
        mock_cert.return_value = {
            "id": 1, "cnpj": "12345678000190", "titular": "EMPRESA TESTE",
            "arquivo_path": "/fake/cert.pfx", "senha_encrypted": "enc_pwd",
        }
        # Mock DB cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (1,),  # insert envio returning id
        ]
        # 10 columns from cruzamento_eb: cod_rubrica, descricao, cod_natureza,
        #   incid_inss, incid_irrf, incid_fgts, incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts, analise
        mock_cursor.fetchall.return_value = [
            ("1", "HORAS NORMAIS", "1000 - Vencimentos", "11", "11", "11",
             "11 - Mensal", "11 - Normal", "11 - Normal", "Rubrica regular"),
        ]
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.commit = MagicMock()

        mock_decrypt.return_value = "test1234"
        mock_gerar.return_value = b"<xml>fake</xml>"
        mock_sign.return_value = b"<xml>signed</xml>"
        mock_soap.return_value = "<soap:Envelope>...</soap:Envelope>"

        # Mock pfx file read
        with patch("builtins.open", MagicMock(return_value=MagicMock(
            __enter__=lambda s: MagicMock(read=lambda: b"fake_pfx_data"),
            __exit__=MagicMock(return_value=False),
        ))):
            mock_enviar.return_value = {
                "sucesso": True,
                "codigo_resposta": "201",
                "descricao": "Lote recebido com sucesso",
                "protocolo": "1.2.2026030001",
                "dh_recepcao": "2026-03-28T10:00:00",
                "ocorrencias": [],
            }

            client = _client()
            resp = client.post("/api/esocial/s1010/enviar", json={
                "rubrica_ids": ["1"],
                "ini_valid": "2026-03",
                "modo": "inclusao",
                "ambiente": "2",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["sucesso"] is True
        assert data["protocolo"] == "1.2.2026030001"
        assert data["eventos_enviados"] == 1

    @patch("esocial.esocial_routes._get_conn")
    def test_envio_sem_certificado_ativo(self, mock_conn):
        """Deve retornar 400 se não houver certificado ativo"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # sem cert ativo
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

        client = _client()
        resp = client.post("/api/esocial/s1010/enviar", json={
            "rubrica_ids": ["1"],
            "ini_valid": "2026-03",
        })
        assert resp.status_code == 400
        assert "certificado" in resp.json()["detail"].lower()

    @patch("esocial.esocial_routes._get_conn")
    def test_envio_sem_rubricas(self, mock_conn):
        """Deve retornar 400 se rubrica_ids estiver vazio"""
        client = _client()
        resp = client.post("/api/esocial/s1010/enviar", json={
            "rubrica_ids": [],
            "ini_valid": "2026-03",
        })
        assert resp.status_code == 400
        assert "rubrica" in resp.json()["detail"].lower()

    @patch("esocial.esocial_routes._get_conn")
    def test_envio_max_50_rubricas(self, mock_conn):
        """Deve retornar 400 se mais de 50 rubricas"""
        client = _client()
        resp = client.post("/api/esocial/s1010/enviar", json={
            "rubrica_ids": [str(i) for i in range(1, 52)],  # 51 IDs
            "ini_valid": "2026-03",
        })
        assert resp.status_code == 400
        assert "50" in resp.json()["detail"]


# ── Classe 3: Consultar Resultado ────────────────────────────────


class TestConsultarResultado:
    """GET /api/esocial/s1010/consultar/{protocolo}"""

    @patch("esocial.esocial_routes.ESocialClient.consultar_lote")
    @patch("esocial.esocial_routes.CertificateManager.decrypt_password")
    @patch("esocial.esocial_routes._load_cert_ativo")
    @patch("esocial.esocial_routes._get_conn")
    def test_consulta_sucesso(self, mock_conn, mock_cert, mock_decrypt, mock_consultar):
        """Deve retornar resultado da consulta e atualizar DB"""
        mock_cert.return_value = {
            "id": 1, "cnpj": "12345678000190", "titular": "EMPRESA TESTE",
            "arquivo_path": "/fake/cert.pfx", "senha_encrypted": "enc_pwd",
        }
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.commit = MagicMock()

        mock_decrypt.return_value = "test1234"

        with patch("builtins.open", MagicMock(return_value=MagicMock(
            __enter__=lambda s: MagicMock(read=lambda: b"fake_pfx_data"),
            __exit__=MagicMock(return_value=False),
        ))):
            mock_consultar.return_value = {
                "sucesso": True,
                "codigo_resposta_lote": "201",
                "descricao_lote": "Lote processado",
                "eventos": [
                    {
                        "id_evento": "ID1234",
                        "codigo_resposta": "201",
                        "descricao": "Sucesso",
                        "nr_recibo": "1.2.0000000001",
                        "ocorrencias": [],
                    }
                ],
            }

            client = _client()
            resp = client.get("/api/esocial/s1010/consultar/1.2.2026030001")

        assert resp.status_code == 200
        data = resp.json()
        assert data["sucesso"] is True
        assert len(data["eventos"]) == 1
        assert data["eventos"][0]["nr_recibo"] == "1.2.0000000001"

    @patch("esocial.esocial_routes._get_conn")
    def test_consulta_sem_certificado(self, mock_conn):
        """Deve retornar 400 sem certificado ativo"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

        client = _client()
        resp = client.get("/api/esocial/s1010/consultar/1.2.2026030001")
        assert resp.status_code == 400


# ── Classe 4: Histórico de Envios ────────────────────────────────


class TestHistoricoEnvios:
    """GET /api/esocial/envios"""

    @patch("esocial.esocial_routes._get_conn")
    def test_historico_retorna_envios(self, mock_conn):
        """Deve retornar lista de envios do banco"""
        mock_cursor = MagicMock()
        # 16 columns: id, tipo_evento, modo, status, protocolo_envio,
        #   codigo_resposta, descricao_resposta, total_eventos, created_at,
        #   ambiente, ini_valid, rubrica_detalhes, rubrica_ids, recibo_consulta, updated_at, nr_recibo
        rubrica_det = json.dumps([{"cod_rubrica": "1", "descricao": "HORAS NORMAIS", "nat_rubr": "1000", "inss_correto": "11", "irrf_correto": "11", "fgts_correto": "11"}])
        mock_cursor.fetchall.return_value = [
            (1, "S-1010", "inclusao", "enviado", "1.2.2026030001",
             "201", "Sucesso", 3, "2026-03-28T10:00:00",
             "2", "2026-03", rubrica_det, '["1"]', None, "2026-03-28T10:00:00", "1.2.0000000001"),
        ]
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

        client = _client()
        resp = client.get("/api/esocial/envios")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["envios"]) == 1
        assert data["envios"][0]["protocolo_envio"] == "1.2.2026030001"
        assert data["envios"][0]["ambiente"] == "2"
        assert data["envios"][0]["ini_valid"] == "2026-03"
        assert len(data["envios"][0]["rubrica_detalhes"]) == 1
        assert data["envios"][0]["rubrica_detalhes"][0]["cod_rubrica"] == "1"

    @patch("esocial.esocial_routes._get_conn")
    def test_historico_vazio(self, mock_conn):
        """Deve retornar lista vazia sem envios"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.return_value.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

        client = _client()
        resp = client.get("/api/esocial/envios")
        assert resp.status_code == 200
        assert resp.json()["envios"] == []


# ── Classe 5: Validação de Entrada ───────────────────────────────


class TestValidacaoEntrada:
    """Validações de entrada das rotas"""

    def test_enviar_sem_body(self):
        """Deve retornar 422 sem body"""
        client = _client()
        resp = client.post("/api/esocial/s1010/enviar")
        assert resp.status_code == 422

    def test_enviar_ini_valid_formato_invalido(self):
        """Deve retornar 400 com formato inválido de iniValid"""
        client = _client()
        resp = client.post("/api/esocial/s1010/enviar", json={
            "rubrica_ids": ["1"],
            "ini_valid": "2026/03",  # formato errado
        })
        assert resp.status_code == 400
        assert "formato" in resp.json()["detail"].lower()
