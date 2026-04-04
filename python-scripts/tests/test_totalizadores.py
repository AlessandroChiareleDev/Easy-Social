"""
Testes — Rotas de Totalizadores (S-5001 / S-5002 / S-5012)

Testa:
- GET /api/esocial/consultar/{protocolo}         — consulta genérica
- GET /api/esocial/totalizadores/{cpf}/{per_apur} — consulta DB
- GET /api/esocial/totalizadores/comparar/{cpf}/{per_apur} — antes/depois
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── App / Client ─────────────────────────────────────────────────

def _make_app():
    from esocial.esocial_routes import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return app


def _client():
    return TestClient(_make_app())


# ── Fixtures ─────────────────────────────────────────────────────

CERT_ROW = {
    "id": 1,
    "cnpj": "12345678000190",
    "titular": "EMPRESA TESTE",
    "arquivo_path": "/fake/cert.pfx",
    "senha_encrypted": "gAAAAABmFake==",
    "ativo": True,
}

DADOS_S5001 = json.dumps({
    "infoCpCalc": [
        {"tpCR": "108301", "vrCpSeg": "1500.00", "vrDescSeg": "165.00"}
    ]
})

DADOS_S5002 = json.dumps({
    "infoIR": [
        {"tpInfoIR": "11", "valor": "5000.00"},
        {"tpInfoIR": "7900", "valor": "800.00"},
    ],
    "totApurMen_CRMen": "056107",
    "totApurMen_vlrRendTrib": "4200.00",
    "totApurMen_vlrPrevOficial": "800.00",
    "totApurMen_vlrCRMen": "126.00",
})

DADOS_S5002_ANTES = json.dumps({
    "infoIR": [{"tpInfoIR": "11", "valor": "5000.00"}],
    "totApurMen_vlrRendTrib": "5000.00",
    "totApurMen_vlrPrevOficial": "0.00",
    "totApurMen_vlrCRMen": "285.00",
})

DADOS_S5002_DEPOIS = json.dumps({
    "infoIR": [
        {"tpInfoIR": "11", "valor": "5000.00"},
        {"tpInfoIR": "7900", "valor": "800.00"},
    ],
    "totApurMen_vlrRendTrib": "4200.00",
    "totApurMen_vlrPrevOficial": "800.00",
    "totApurMen_vlrCRMen": "126.00",
})

DADOS_S5012 = json.dumps({
    "CRMen": "056107",
    "vlrCRMen": "2500.00",
})


# ── Helpers para mock de conexão ─────────────────────────────────

def _setup_mock_conn(mock_get_conn):
    """Retorna (mock_conn, mock_cursor) prontos para uso."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn, mock_cursor


# ══════════════════════════════════════════════════════════════════
# Classe 1: Consulta Genérica de Protocolo
# ══════════════════════════════════════════════════════════════════

class TestConsultarProtocolo:
    """GET /api/esocial/consultar/{protocolo}"""

    @patch("esocial.esocial_routes.ESocialClient")
    @patch("esocial.esocial_routes.SOAPEnvelopeBuilder")
    @patch("esocial.esocial_routes.CertificateManager")
    @patch("esocial.esocial_routes._load_cert_ativo")
    @patch("esocial.esocial_routes._get_conn")
    @patch("builtins.open", create=True)
    def test_consulta_sucesso(self, mock_open, mock_conn_fn, mock_load_cert,
                               mock_cert_mgr, mock_soap, mock_client):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_load_cert.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_soap.url_consulta.return_value = "https://fake.esocial.gov.br/consulta"

        mock_client.consultar_lote.return_value = {
            "sucesso": True,
            "codigo_resposta": "201",
            "descricao": "Lote processado com sucesso",
            "xml_resposta": "<xml/>",
            "eventos": [
                {"id": "ID1", "codigo_resposta": "201", "descricao": "OK",
                 "nr_recibo": "1.2.000.2026042800001"},
            ],
        }

        client = _client()
        resp = client.get("/api/esocial/consultar/1.2.2026040001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sucesso"] is True
        assert data["codigo_resposta"] == "201"
        assert len(data["eventos"]) == 1
        assert data["eventos"][0]["nr_recibo"] == "1.2.000.2026042800001"

    @patch("esocial.esocial_routes.ESocialClient")
    @patch("esocial.esocial_routes.SOAPEnvelopeBuilder")
    @patch("esocial.esocial_routes.CertificateManager")
    @patch("esocial.esocial_routes._load_cert_ativo")
    @patch("esocial.esocial_routes._get_conn")
    @patch("builtins.open", create=True)
    def test_consulta_erro_processamento(self, mock_open, mock_conn_fn,
                                          mock_load_cert, mock_cert_mgr,
                                          mock_soap, mock_client):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_load_cert.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_soap.url_consulta.return_value = "https://fake.esocial.gov.br/consulta"

        mock_client.consultar_lote.return_value = {
            "sucesso": True,
            "codigo_resposta": "201",
            "descricao": "Lote processado",
            "xml_resposta": "<xml/>",
            "eventos": [
                {"id": "ID1", "codigo_resposta": "402", "descricao": "Erro validação",
                 "nr_recibo": None, "ocorrencias": [{"codigo": 218}]},
            ],
        }

        client = _client()
        resp = client.get("/api/esocial/consultar/1.2.2026040002")
        assert resp.status_code == 200
        data = resp.json()
        # Lote OK mas evento com erro → status_final = "erro"
        assert data["eventos"][0]["codigo_resposta"] == "402"

    @patch("esocial.esocial_routes._load_cert_ativo")
    @patch("esocial.esocial_routes._get_conn")
    def test_consulta_sem_certificado(self, mock_conn_fn, mock_load_cert):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_load_cert.return_value = None

        client = _client()
        resp = client.get("/api/esocial/consultar/1.2.2026040001")
        assert resp.status_code == 400
        assert "certificado" in resp.json()["detail"].lower()

    @patch("esocial.esocial_routes.ESocialClient")
    @patch("esocial.esocial_routes.SOAPEnvelopeBuilder")
    @patch("esocial.esocial_routes.CertificateManager")
    @patch("esocial.esocial_routes._load_cert_ativo")
    @patch("esocial.esocial_routes._get_conn")
    @patch("builtins.open", create=True)
    def test_consulta_ambiente_producao(self, mock_open, mock_conn_fn,
                                         mock_load_cert, mock_cert_mgr,
                                         mock_soap, mock_client):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_load_cert.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_soap.url_consulta.return_value = "https://producao.esocial.gov.br/consulta"

        mock_client.consultar_lote.return_value = {
            "sucesso": True, "codigo_resposta": "201", "descricao": "OK",
            "xml_resposta": "<xml/>", "eventos": [],
        }

        client = _client()
        resp = client.get("/api/esocial/consultar/1.2.PROD001?ambiente=1")
        assert resp.status_code == 200
        mock_soap.url_consulta.assert_called_with(producao=True)

    @patch("esocial.esocial_routes.ESocialClient")
    @patch("esocial.esocial_routes.SOAPEnvelopeBuilder")
    @patch("esocial.esocial_routes.CertificateManager")
    @patch("esocial.esocial_routes._load_cert_ativo")
    @patch("esocial.esocial_routes._get_conn")
    @patch("builtins.open", create=True)
    def test_consulta_atualiza_envio_no_banco(self, mock_open, mock_conn_fn,
                                               mock_load_cert, mock_cert_mgr,
                                               mock_soap, mock_client):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_load_cert.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_soap.url_consulta.return_value = "https://fake.esocial.gov.br/consulta"

        mock_client.consultar_lote.return_value = {
            "sucesso": True, "codigo_resposta": "201", "descricao": "OK",
            "xml_resposta": "<xml/>",
            "eventos": [
                {"id": "ID1", "codigo_resposta": "201", "nr_recibo": "REC001"},
            ],
        }

        client = _client()
        resp = client.get("/api/esocial/consultar/1.2.UPDATE001")
        assert resp.status_code == 200

        # Verifica que UPDATE foi chamado no banco
        calls = [str(c) for c in mock_cursor.execute.call_args_list]
        update_calls = [c for c in calls if "UPDATE esocial_envios" in c]
        assert len(update_calls) > 0

    @patch("esocial.esocial_routes.ESocialClient")
    @patch("esocial.esocial_routes.SOAPEnvelopeBuilder")
    @patch("esocial.esocial_routes.CertificateManager")
    @patch("esocial.esocial_routes._load_cert_ativo")
    @patch("esocial.esocial_routes._get_conn")
    @patch("builtins.open", create=True)
    def test_consulta_sem_xml_resposta(self, mock_open, mock_conn_fn,
                                        mock_load_cert, mock_cert_mgr,
                                        mock_soap, mock_client):
        """xml_resposta é removida do retorno (via pop)"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_load_cert.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_soap.url_consulta.return_value = "https://fake"

        mock_client.consultar_lote.return_value = {
            "sucesso": True, "codigo_resposta": "201", "descricao": "OK",
            "xml_resposta": "<huge_xml/>", "eventos": [],
        }

        client = _client()
        resp = client.get("/api/esocial/consultar/1.2.NOXMLRES")
        data = resp.json()
        assert "xml_resposta" not in data


# ══════════════════════════════════════════════════════════════════
# Classe 2: Consulta Totalizadores no DB
# ══════════════════════════════════════════════════════════════════

class TestConsultarTotalizadores:
    """GET /api/esocial/totalizadores/{cpf}/{per_apur}"""

    @patch("esocial.esocial_routes._get_conn")
    def test_retorna_todos_totalizadores(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)

        # S-5001, S-5002, S-5012 — cada fetchone retorna uma vez
        mock_cursor.fetchone.side_effect = [
            ("REC5001", DADOS_S5001, "2025-01-15 10:00:00", "ID5001AAA"),
            ("REC5002", DADOS_S5002, "2025-01-15 10:00:00", "ID5002BBB"),
            ("REC5012", DADOS_S5012, "2025-01-15 10:00:00", "ID5012CCC"),
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/12345678901/2025-01")
        assert resp.status_code == 200
        data = resp.json()

        assert data["cpf"] == "12345678901"
        assert data["per_apur"] == "2025-01"

        # S-5001
        assert data["s5001_inss_fgts"] is not None
        assert data["s5001_inss_fgts"]["nr_recibo"] == "REC5001"
        calc = data["s5001_inss_fgts"]["dados"]["infoCpCalc"]
        assert calc[0]["tpCR"] == "108301"
        assert calc[0]["vrCpSeg"] == "1500.00"

        # S-5002
        assert data["s5002_irrf_cpf"] is not None
        assert data["s5002_irrf_cpf"]["nr_recibo"] == "REC5002"

        # S-5012
        assert data["s5012_irrf_total"] is not None
        assert data["s5012_irrf_total"]["nr_recibo"] == "REC5012"

        # Resumo
        assert data["resumo"]["vlrRendTrib"] == "4200.00"
        assert data["resumo"]["vlrPrevOficial"] == "800.00"
        assert data["resumo"]["vlrCRMen"] == "126.00"
        assert data["resumo"]["infoCpCalc"] is not None

    @patch("esocial.esocial_routes._get_conn")
    def test_retorna_parcial_sem_s5012(self, mock_conn_fn):
        """S-5012 pode não existir (é consolidado, poucos registros)"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.side_effect = [
            ("REC5001", DADOS_S5001, "2025-01-15 10:00:00", "ID5001"),
            ("REC5002", DADOS_S5002, "2025-01-15 10:00:00", "ID5002"),
            None,  # S-5012 não encontrado
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/12345678901/2025-01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["s5001_inss_fgts"] is not None
        assert data["s5002_irrf_cpf"] is not None
        assert data["s5012_irrf_total"] is None

    @patch("esocial.esocial_routes._get_conn")
    def test_nenhum_totalizador_encontrado(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.side_effect = [None, None, None]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/99999999999/2025-06")
        assert resp.status_code == 200
        data = resp.json()
        assert data["s5001_inss_fgts"] is None
        assert data["s5002_irrf_cpf"] is None
        assert data["s5012_irrf_total"] is None
        assert data["resumo"]["vlrRendTrib"] is None
        assert data["resumo"]["infoCpCalc"] is None

    @patch("esocial.esocial_routes._get_conn")
    def test_validacao_per_apur_formato_invalido(self, mock_conn_fn):
        client = _client()
        resp = client.get("/api/esocial/totalizadores/12345678901/202501")
        assert resp.status_code == 400
        assert "AAAA-MM" in resp.json()["detail"]

    @patch("esocial.esocial_routes._get_conn")
    def test_validacao_per_apur_com_dia(self, mock_conn_fn):
        client = _client()
        resp = client.get("/api/esocial/totalizadores/12345678901/2025-01-15")
        assert resp.status_code == 400

    @patch("esocial.esocial_routes._get_conn")
    def test_validacao_cpf_nao_numerico(self, mock_conn_fn):
        client = _client()
        resp = client.get("/api/esocial/totalizadores/abc/2025-01")
        assert resp.status_code == 400
        assert "CPF" in resp.json()["detail"]

    @patch("esocial.esocial_routes._get_conn")
    def test_dados_json_como_dict(self, mock_conn_fn):
        """dados_json já pode vir como dict (não precisa json.loads)"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        dados_dict = {"infoCpCalc": [{"tpCR": "108301", "vrCpSeg": "500.00"}]}
        mock_cursor.fetchone.side_effect = [
            ("REC", dados_dict, "2025-01-15", "IDEVT"),
            None,
            None,
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/12345678901/2025-01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["s5001_inss_fgts"]["dados"]["infoCpCalc"][0]["vrCpSeg"] == "500.00"

    @patch("esocial.esocial_routes._get_conn")
    def test_dados_json_none(self, mock_conn_fn):
        """S-5012 frequentemente tem dados_json=None"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.side_effect = [
            None,
            None,
            ("REC5012", None, "2025-01-15", "ID5012"),  # dados_json is None
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/12345678901/2025-01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["s5012_irrf_total"]["dados"] == {}

    @patch("esocial.esocial_routes._get_conn")
    def test_resumo_s5002_com_prevoficial_zero(self, mock_conn_fn):
        """Antes da correção, vlrPrevOficial costuma ser 0.00"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        dados_antes = json.dumps({
            "totApurMen_vlrRendTrib": "5000.00",
            "totApurMen_vlrPrevOficial": "0.00",
            "totApurMen_vlrCRMen": "285.00",
        })
        mock_cursor.fetchone.side_effect = [
            None,
            ("REC", dados_antes, "2025-01-15", "ID"),
            None,
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/12345678901/2025-01")
        data = resp.json()
        assert data["resumo"]["vlrPrevOficial"] == "0.00"
        assert data["resumo"]["vlrCRMen"] == "285.00"


# ══════════════════════════════════════════════════════════════════
# Classe 3: Comparação Antes/Depois
# ══════════════════════════════════════════════════════════════════

class TestCompararTotalizadores:
    """GET /api/esocial/totalizadores/comparar/{cpf}/{per_apur}"""

    @patch("esocial.esocial_routes._get_conn")
    def test_comparar_antes_depois(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = [
            ("REC_ANTES", DADOS_S5002_ANTES, "2025-01-15 10:00:00", "ID_ANTES"),
            ("REC_DEPOIS", DADOS_S5002_DEPOIS, "2025-04-28 15:00:00", "ID_DEPOIS"),
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/comparar/12345678901/2025-01")
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_registros"] == 2
        assert data["antes"]["nr_recibo"] == "REC_ANTES"
        assert data["depois"]["nr_recibo"] == "REC_DEPOIS"

        # Antes: sem dedução INSS
        assert data["antes"]["vlrPrevOficial"] == "0.00"
        assert data["antes"]["vlrCRMen"] == "285.00"

        # Depois: com dedução
        assert data["depois"]["vlrPrevOficial"] == "800.00"
        assert data["depois"]["vlrCRMen"] == "126.00"

    @patch("esocial.esocial_routes._get_conn")
    def test_comparar_registro_unico(self, mock_conn_fn):
        """Com apenas 1 registro, 'depois' deve ser None"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = [
            ("REC_UNICO", DADOS_S5002, "2025-01-15", "ID_UNICO"),
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/comparar/12345678901/2025-01")
        data = resp.json()
        assert data["total_registros"] == 1
        assert data["antes"]["nr_recibo"] == "REC_UNICO"
        assert data["depois"] is None

    @patch("esocial.esocial_routes._get_conn")
    def test_comparar_sem_registros(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = []

        client = _client()
        resp = client.get("/api/esocial/totalizadores/comparar/99999999999/2025-06")
        data = resp.json()
        assert data["total_registros"] == 0
        assert data["antes"] is None
        assert data["depois"] is None
        assert data["historico_s5002"] == []

    @patch("esocial.esocial_routes._get_conn")
    def test_comparar_multiplos_registros(self, mock_conn_fn):
        """Três ou mais registros: antes=primeiro, depois=último"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = [
            ("REC1", DADOS_S5002_ANTES, "2025-01-15", "ID1"),
            ("REC2", DADOS_S5002, "2025-03-20", "ID2"),
            ("REC3", DADOS_S5002_DEPOIS, "2025-04-28", "ID3"),
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/comparar/12345678901/2025-01")
        data = resp.json()
        assert data["total_registros"] == 3
        assert data["antes"]["nr_recibo"] == "REC1"
        assert data["depois"]["nr_recibo"] == "REC3"
        assert len(data["historico_s5002"]) == 3

    @patch("esocial.esocial_routes._get_conn")
    def test_comparar_validacao_per_apur(self, mock_conn_fn):
        client = _client()
        resp = client.get("/api/esocial/totalizadores/comparar/12345678901/2025")
        assert resp.status_code == 400

    @patch("esocial.esocial_routes._get_conn")
    def test_comparar_historico_campos_irrf(self, mock_conn_fn):
        """Cada item do histórico deve ter vlrRendTrib, vlrPrevOficial, vlrCRMen, infoIR"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = [
            ("REC1", DADOS_S5002, "2025-01-15", "ID1"),
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/comparar/12345678901/2025-01")
        item = resp.json()["historico_s5002"][0]
        assert "vlrRendTrib" in item
        assert "vlrPrevOficial" in item
        assert "vlrCRMen" in item
        assert "infoIR" in item
        assert isinstance(item["infoIR"], list)

    @patch("esocial.esocial_routes._get_conn")
    def test_comparar_dados_json_none(self, mock_conn_fn):
        """dados_json None → campos retornam None/[]"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = [
            ("REC", None, "2025-01-15", "ID"),
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/comparar/12345678901/2025-01")
        item = resp.json()["historico_s5002"][0]
        assert item["vlrRendTrib"] is None
        assert item["infoIR"] == []

    @patch("esocial.esocial_routes._get_conn")
    def test_comparar_ordenacao_ascendente(self, mock_conn_fn):
        """Histórico deve vir em ordem ascendente de dt_processamento"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = [
            ("REC1", DADOS_S5002_ANTES, "2025-01-15", "ID1"),
            ("REC2", DADOS_S5002_DEPOIS, "2025-04-28", "ID2"),
        ]

        client = _client()
        resp = client.get("/api/esocial/totalizadores/comparar/12345678901/2025-01")
        hist = resp.json()["historico_s5002"]
        assert hist[0]["dt_processamento"] < hist[1]["dt_processamento"]
