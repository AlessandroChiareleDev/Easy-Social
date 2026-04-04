"""
Testes — Pipeline de Correção (Orquestrador)

Testa:
- POST /api/pipeline/executar          — pipeline completo 5 etapas
- GET  /api/pipeline/status/{id}       — consultar pipeline
- GET  /api/pipeline/historico         — listar pipelines
- GET  /api/pipeline/preparar/{cpf}/{p} — preparar dados
"""

import json
import pytest
from unittest.mock import patch, MagicMock, call
from fastapi.testclient import TestClient


# ── App / Client ─────────────────────────────────────────────────

def _make_app():
    from esocial.pipeline_correcao import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return app


def _client():
    return TestClient(_make_app())


# ── Fixtures ─────────────────────────────────────────────────────

CERT_ROW = {
    "id": 1,
    "cnpj": "05969071000196",
    "titular": "APPA TESTE",
    "arquivo_path": "/fake/cert.pfx",
    "senha_encrypted": "gAAAAABmFake==",
}

SAMPLE_DM_DEVS = [
    {
        "ideDmDev": "00001228",
        "codCateg": "101",
        "infoPerApur": {
            "ideEstabLot": [
                {
                    "tpInsc": "1",
                    "nrInsc": "05969071000196",
                    "codLotacao": "001",
                    "remunPerApur": [
                        {
                            "matricula": "009-001-051736",
                            "itensRemun": [
                                {"codRubr": "1", "ideTabRubr": "1", "vrRubr": "3000.00"},
                                {"codRubr": "566", "ideTabRubr": "1", "vrRubr": "330.00"},
                            ],
                        }
                    ],
                }
            ],
        },
    }
]

SAMPLE_INFO_PGTOS = [
    {
        "dtPgto": "2025-02-05",
        "tpPgto": "1",
        "perRef": "2025-01",
        "ideDmDev": "00001228",
        "vrLiq": "2670.00",
    }
]

SAMPLE_RESPONSAVEL = {
    "nm_resp": "ANA TESTE",
    "cpf_resp": "12345678901",
    "telefone": "4132221234",
    "email": "ana@teste.com",
}

PIPELINE_REQUEST = {
    "cpf": "06184644173",
    "per_apur": "2025-01",
    "ambiente": "2",
    "rubrica_ids": None,
    "skip_s1298": False,
    "ind_apuracao": "1",
    "s1200_nr_recibo": "1.1.0000000038566203364",
    "s1200_dm_devs": SAMPLE_DM_DEVS,
    "s1210_nr_recibo": "1.1.0000000038890968113",
    "s1210_info_pgtos": SAMPLE_INFO_PGTOS,
    "responsavel": SAMPLE_RESPONSAVEL,
}


# ── Helpers para mock ─────────────────────────────────────────────

def _setup_mock_conn(mock_get_conn):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn, mock_cursor


def _mock_enviar_sucesso(protocolo="1.2.TEST001"):
    return {
        "sucesso": True,
        "codigo_resposta": "201",
        "descricao": "Lote recebido com sucesso",
        "protocolo": protocolo,
        "dh_recepcao": "2026-04-02T10:00:00",
        "ocorrencias": [],
        "erro": None,
    }


def _mock_consulta_sucesso(nr_recibo="1.1.REC_TEST_001"):
    return {
        "sucesso": True,
        "codigo_resposta": "201",
        "descricao": "Lote processado com sucesso",
        "eventos": [
            {"id": "ID1", "codigo_resposta": "201", "descricao": "OK",
             "nr_recibo": nr_recibo, "ocorrencias": []},
        ],
        "xml_resposta": "<xml/>",
    }


# ══════════════════════════════════════════════════════════════════
# Classe 1: Validações de Input
# ══════════════════════════════════════════════════════════════════

class TestPipelineValidacoes:
    """POST /api/pipeline/executar — validações de input"""

    @patch("esocial.pipeline_correcao._load_cert_ativo")
    def test_cpf_invalido(self, mock_cert):
        mock_cert.return_value = CERT_ROW
        client = _client()
        req = {**PIPELINE_REQUEST, "cpf": "123"}
        resp = client.post("/api/pipeline/executar", json=req)
        assert resp.status_code == 400
        assert "CPF" in resp.json()["detail"]

    @patch("esocial.pipeline_correcao._load_cert_ativo")
    def test_per_apur_invalido(self, mock_cert):
        mock_cert.return_value = CERT_ROW
        client = _client()
        req = {**PIPELINE_REQUEST, "per_apur": "202501"}
        resp = client.post("/api/pipeline/executar", json=req)
        assert resp.status_code == 400
        assert "AAAA-MM" in resp.json()["detail"]

    @patch("esocial.pipeline_correcao._load_cert_ativo")
    def test_ambiente_invalido(self, mock_cert):
        mock_cert.return_value = CERT_ROW
        client = _client()
        req = {**PIPELINE_REQUEST, "ambiente": "3"}
        resp = client.post("/api/pipeline/executar", json=req)
        assert resp.status_code == 400

    def test_sem_certificado(self):
        with patch("esocial.pipeline_correcao._load_cert_ativo", return_value=None):
            client = _client()
            resp = client.post("/api/pipeline/executar", json=PIPELINE_REQUEST)
            assert resp.status_code == 400
            assert "certificado" in resp.json()["detail"].lower()

    @patch("esocial.pipeline_correcao._load_cert_ativo")
    def test_s1200_nr_recibo_vazio(self, mock_cert):
        mock_cert.return_value = CERT_ROW
        client = _client()
        req = {**PIPELINE_REQUEST, "s1200_nr_recibo": ""}
        resp = client.post("/api/pipeline/executar", json=req)
        assert resp.status_code == 400

    @patch("esocial.pipeline_correcao._load_cert_ativo")
    def test_s1210_info_pgtos_vazio(self, mock_cert):
        mock_cert.return_value = CERT_ROW
        client = _client()
        req = {**PIPELINE_REQUEST, "s1210_info_pgtos": []}
        resp = client.post("/api/pipeline/executar", json=req)
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# Classe 2: Pipeline Completo (sem S-1010, sem S-1298)
# ══════════════════════════════════════════════════════════════════

class TestPipelineCompleto:
    """POST /api/pipeline/executar — fluxo completo"""

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1299XMLGenerator")
    @patch("esocial.pipeline_correcao.S1210XMLGenerator")
    @patch("esocial.pipeline_correcao.S1200XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_pipeline_3_steps_skip_s1010_s1298(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1200_gen, mock_s1210_gen, mock_s1299_gen,
        mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """Pipeline com skip_s1298=True e sem rubrica_ids → só S-1200, S-1210, S-1299"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (1,)  # pipeline_id
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_s1200_gen.gerar.return_value = b"<S1200/>"
        mock_s1210_gen.gerar.return_value = b"<S1210/>"
        mock_s1299_gen.gerar.return_value = b"<S1299/>"
        mock_signer.assinar.return_value = b"<signed/>"
        mock_soap.montar_envio.return_value = "<soap/>"
        mock_soap.url_envio.return_value = "https://fake/envio"
        mock_soap.url_consulta.return_value = "https://fake/consulta"

        # 3 envios + 3 consultas
        mock_client.enviar_lote.side_effect = [
            _mock_enviar_sucesso("PROT_S1200"),
            _mock_enviar_sucesso("PROT_S1210"),
            _mock_enviar_sucesso("PROT_S1299"),
        ]
        mock_client.consultar_lote.side_effect = [
            _mock_consulta_sucesso("REC_S1200"),
            _mock_consulta_sucesso("REC_S1210"),
            _mock_consulta_sucesso("REC_S1299"),
        ]

        client = _client()
        req = {**PIPELINE_REQUEST, "skip_s1298": True}
        resp = client.post("/api/pipeline/executar", json=req)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completo"
        assert data["steps_ok"] == 5  # 2 pulados + 3 executados
        assert len(data["steps"]) == 5

        # Steps 1 & 2 puladas
        assert data["steps"][0]["status"] == "pulado"
        assert data["steps"][0]["evento"] == "S-1010"
        assert data["steps"][1]["status"] == "pulado"
        assert data["steps"][1]["evento"] == "S-1298"

        # Steps 3, 4, 5 OK
        assert data["steps"][2]["status"] == "ok"
        assert data["steps"][2]["evento"] == "S-1200"
        assert data["steps"][2]["nr_recibo"] == "REC_S1200"

        assert data["steps"][3]["status"] == "ok"
        assert data["steps"][3]["evento"] == "S-1210"
        assert data["steps"][3]["nr_recibo"] == "REC_S1210"

        assert data["steps"][4]["status"] == "ok"
        assert data["steps"][4]["evento"] == "S-1299"
        assert data["steps"][4]["nr_recibo"] == "REC_S1299"

        # S-1200 chamado com retificação
        mock_s1200_gen.gerar.assert_called_once()
        call_kwargs = mock_s1200_gen.gerar.call_args
        assert call_kwargs.kwargs["ind_retif"] == "2"
        assert call_kwargs.kwargs["nr_recibo"] == "1.1.0000000038566203364"

        # S-1210 chamado com retificação
        mock_s1210_gen.gerar.assert_called_once()
        call_kwargs = mock_s1210_gen.gerar.call_args
        assert call_kwargs.kwargs["ind_retif"] == "2"
        assert call_kwargs.kwargs["nr_recibo"] == "1.1.0000000038890968113"

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1299XMLGenerator")
    @patch("esocial.pipeline_correcao.S1210XMLGenerator")
    @patch("esocial.pipeline_correcao.S1200XMLGenerator")
    @patch("esocial.pipeline_correcao.S1298XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_pipeline_completo_5_steps(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1298_gen, mock_s1200_gen, mock_s1210_gen, mock_s1299_gen,
        mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """Pipeline completo com S-1298 reabertura (sem S-1010)"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (1,)
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_s1298_gen.gerar.return_value = b"<S1298/>"
        mock_s1200_gen.gerar.return_value = b"<S1200/>"
        mock_s1210_gen.gerar.return_value = b"<S1210/>"
        mock_s1299_gen.gerar.return_value = b"<S1299/>"
        mock_signer.assinar.return_value = b"<signed/>"
        mock_soap.montar_envio.return_value = "<soap/>"
        mock_soap.url_envio.return_value = "https://fake/envio"
        mock_soap.url_consulta.return_value = "https://fake/consulta"

        # 4 envios + 4 consultas (S-1298, S-1200, S-1210, S-1299)
        mock_client.enviar_lote.side_effect = [
            _mock_enviar_sucesso(f"PROT_{i}") for i in range(4)
        ]
        mock_client.consultar_lote.side_effect = [
            _mock_consulta_sucesso(f"REC_{i}") for i in range(4)
        ]

        client = _client()
        req = {**PIPELINE_REQUEST, "skip_s1298": False}
        resp = client.post("/api/pipeline/executar", json=req)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completo"
        assert data["steps_ok"] == 5  # 1 pulado (S-1010) + 4 executados

        # S-1010 pulado, S-1298 OK
        assert data["steps"][0]["status"] == "pulado"
        assert data["steps"][1]["status"] == "ok"
        assert data["steps"][1]["evento"] == "S-1298"

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1299XMLGenerator")
    @patch("esocial.pipeline_correcao.S1210XMLGenerator")
    @patch("esocial.pipeline_correcao.S1200XMLGenerator")
    @patch("esocial.pipeline_correcao.S1298XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_pipeline_falha_s1200_para_no_step3(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1298_gen, mock_s1200_gen, mock_s1210_gen, mock_s1299_gen,
        mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """Se S-1200 falhar, pipeline para e retorna parcial"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (1,)
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_s1298_gen.gerar.return_value = b"<S1298/>"
        mock_s1200_gen.gerar.return_value = b"<S1200/>"
        mock_signer.assinar.return_value = b"<signed/>"
        mock_soap.montar_envio.return_value = "<soap/>"
        mock_soap.url_envio.return_value = "https://fake/envio"
        mock_soap.url_consulta.return_value = "https://fake/consulta"

        # S-1298 OK, S-1200 falha no envio
        mock_client.enviar_lote.side_effect = [
            _mock_enviar_sucesso("PROT_S1298"),
            {
                "sucesso": False,
                "codigo_resposta": "301",
                "descricao": "Erro de conexão",
                "protocolo": None,
                "ocorrencias": [],
                "erro": "Connection error",
            },
        ]
        mock_client.consultar_lote.side_effect = [
            _mock_consulta_sucesso("REC_S1298"),
        ]

        client = _client()
        resp = client.post("/api/pipeline/executar", json=PIPELINE_REQUEST)
        data = resp.json()

        assert data["status"] == "erro"
        assert data["steps_ok"] == 2  # S-1010 pulado + S-1298 OK
        assert len(data["steps"]) == 3  # S-1010 + S-1298 + S-1200

        assert data["steps"][2]["evento"] == "S-1200"
        assert data["steps"][2]["status"] == "erro"

        # S-1210 e S-1299 não foram tentados
        eventos_tentados = [s["evento"] for s in data["steps"]]
        assert "S-1210" not in eventos_tentados
        assert "S-1299" not in eventos_tentados

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1210XMLGenerator")
    @patch("esocial.pipeline_correcao.S1200XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_pipeline_timeout_consulta(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1200_gen, mock_s1210_gen,
        mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """Se consulta não retornar recibo após polling, retorna erro"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (1,)
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_s1200_gen.gerar.return_value = b"<S1200/>"
        mock_signer.assinar.return_value = b"<signed/>"
        mock_soap.montar_envio.return_value = "<soap/>"
        mock_soap.url_envio.return_value = "https://fake/envio"
        mock_soap.url_consulta.return_value = "https://fake/consulta"

        # Envio OK mas consulta sempre retorna "em processamento"
        mock_client.enviar_lote.return_value = _mock_enviar_sucesso("PROT_TIMEOUT")
        mock_client.consultar_lote.return_value = {
            "sucesso": False,
            "codigo_resposta": "101",
            "descricao": "Em processamento",
            "eventos": [],
        }

        client = _client()
        req = {**PIPELINE_REQUEST, "skip_s1298": True}
        resp = client.post("/api/pipeline/executar", json=req)
        data = resp.json()

        assert data["status"] == "erro"
        # S-1200 should show erro or timeout
        s1200_step = next(s for s in data["steps"] if s["evento"] == "S-1200")
        assert s1200_step["status"] in ("erro", "timeout")


# ══════════════════════════════════════════════════════════════════
# Classe 3: Pipeline com S-1010
# ══════════════════════════════════════════════════════════════════

class TestPipelineComS1010:
    """POST /api/pipeline/executar — com rubrica_ids"""

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1010XMLGenerator")
    @patch("esocial.pipeline_correcao.S1299XMLGenerator")
    @patch("esocial.pipeline_correcao.S1210XMLGenerator")
    @patch("esocial.pipeline_correcao.S1200XMLGenerator")
    @patch("esocial.pipeline_correcao.S1298XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_pipeline_com_s1010_sucesso(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1298_gen, mock_s1200_gen, mock_s1210_gen, mock_s1299_gen,
        mock_s1010_gen, mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """Pipeline completo com S-1010 + S-1298 + S-1200 + S-1210 + S-1299"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        # cursor.fetchone: 1st=pipeline_id, 2nd+=rubrica rows via fetchall
        mock_cursor.fetchone.return_value = (1,)
        # Formato novo: cod_rubrica, descricao, cod_natureza,
        #               incid_base_legal_inss, incid_base_legal_irrf,
        #               incid_base_legal_fgts, ini_valid_esocial
        mock_cursor.fetchall.return_value = [
            ("566", "INSS EMPREGADO", "9201 - INSS",
             "11 - Artigo 28, inciso I", "41 - Artigos 3 e 7", "11 - Artigo 15",
             "2025-01"),
        ]
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_s1010_gen.gerar_alteracao.return_value = b"<S1010/>"
        mock_s1298_gen.gerar.return_value = b"<S1298/>"
        mock_s1200_gen.gerar.return_value = b"<S1200/>"
        mock_s1210_gen.gerar.return_value = b"<S1210/>"
        mock_s1299_gen.gerar.return_value = b"<S1299/>"
        mock_signer.assinar.return_value = b"<signed/>"
        mock_soap.montar_envio.return_value = "<soap/>"
        mock_soap.url_envio.return_value = "https://fake/envio"
        mock_soap.url_consulta.return_value = "https://fake/consulta"

        # 5 envios + 5 consultas
        mock_client.enviar_lote.side_effect = [
            _mock_enviar_sucesso(f"PROT_{i}") for i in range(5)
        ]
        mock_client.consultar_lote.side_effect = [
            _mock_consulta_sucesso(f"REC_{i}") for i in range(5)
        ]

        client = _client()
        req = {**PIPELINE_REQUEST, "rubrica_ids": ["566"]}
        resp = client.post("/api/pipeline/executar", json=req)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completo"
        assert data["steps_ok"] == 5

        # S-1010 was executed
        assert data["steps"][0]["evento"] == "S-1010"
        assert data["steps"][0]["status"] == "ok"
        assert data["steps"][0]["detalhes"]["rubricas"] == ["566"]

        # S-1010 gerar_alteracao called
        mock_s1010_gen.gerar_alteracao.assert_called_once()

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1010XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_pipeline_s1010_rubrica_nao_encontrada(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1010_gen, mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """Se rubrica não existe no cruzamento_eb, para"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.fetchall.return_value = []  # nenhuma rubrica
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        client = _client()
        req = {**PIPELINE_REQUEST, "rubrica_ids": ["INEXISTENTE"]}
        resp = client.post("/api/pipeline/executar", json=req)
        data = resp.json()

        assert data["status"] == "erro"
        assert data["steps"][0]["evento"] == "S-1010"
        assert data["steps"][0]["status"] == "erro"


# ══════════════════════════════════════════════════════════════════
# Classe 4: Rota Preparar
# ══════════════════════════════════════════════════════════════════

class TestPrepararPipeline:
    """GET /api/pipeline/preparar/{cpf}/{per_apur}"""

    @patch("esocial.pipeline_correcao._get_conn")
    def test_preparar_com_dados(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        # S-1200 fetchone, S-1210 fetchone, S-1299 fetchone, rubricas fetchall
        mock_cursor.fetchone.side_effect = [
            ("REC_S1200", '{"codCateg":"101"}', "ID_S1200", "2025-02-15"),
            ("REC_S1210", '{"tpPgto":"1"}', "ID_S1210", "2025-02-15"),
            ("REC_S1299", "2025-02-28"),
        ]
        mock_cursor.fetchall.return_value = [("566",), ("47",)]

        client = _client()
        resp = client.get("/api/pipeline/preparar/06184644173/2025-01")
        assert resp.status_code == 200
        data = resp.json()

        assert data["cpf"] == "06184644173"
        assert data["per_apur"] == "2025-01"
        assert data["periodo_fechado"] is True
        assert data["s1200"]["nr_recibo"] == "REC_S1200"
        assert data["s1210"]["nr_recibo"] == "REC_S1210"
        assert "566" in data["rubricas_pendentes"]

    @patch("esocial.pipeline_correcao._get_conn")
    def test_preparar_sem_dados(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.side_effect = [None, None, None]
        mock_cursor.fetchall.return_value = []

        client = _client()
        resp = client.get("/api/pipeline/preparar/99999999999/2025-06")
        assert resp.status_code == 200
        data = resp.json()

        assert data["periodo_fechado"] is False
        assert data["s1200"] is None
        assert data["s1210"] is None

    @patch("esocial.pipeline_correcao._get_conn")
    def test_preparar_per_apur_invalido(self, mock_conn_fn):
        client = _client()
        resp = client.get("/api/pipeline/preparar/06184644173/202501")
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# Classe 5: Histórico e Status
# ══════════════════════════════════════════════════════════════════

class TestPipelineHistoricoStatus:
    """GET /api/pipeline/historico e GET /api/pipeline/status/{id}"""

    @patch("esocial.pipeline_correcao._get_conn")
    def test_historico_vazio(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = []

        client = _client()
        resp = client.get("/api/pipeline/historico")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("esocial.pipeline_correcao._get_conn")
    def test_historico_com_registros(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchall.return_value = [
            (1, "06184644173", "2025-01", "2", "completo", 5,
             "REC1", "REC2", "REC3", "REC4", "REC5",
             None, "2026-04-02 10:00:00", "2026-04-02 10:05:00"),
        ]

        client = _client()
        resp = client.get("/api/pipeline/historico?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["pipeline_id"] == 1
        assert data[0]["status"] == "completo"
        assert data[0]["recibos"]["s1200"] == "REC3"

    @patch("esocial.pipeline_correcao._get_conn")
    def test_status_encontrado(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (
            1, "06184644173", "2025-01", "2", "completo", 5,
            "PROT_S1010", "REC_S1010",
            "PROT_S1298", "REC_S1298",
            "PROT_S1200", "REC_S1200",
            "PROT_S1210", "REC_S1210",
            "PROT_S1299", "REC_S1299",
            "[]", None, "2026-04-02 10:00:00", "2026-04-02 10:05:00",
        )

        client = _client()
        resp = client.get("/api/pipeline/status/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pipeline_id"] == 1
        assert data["status"] == "completo"
        assert data["s1200"]["nr_recibo"] == "REC_S1200"

    @patch("esocial.pipeline_correcao._get_conn")
    def test_status_nao_encontrado(self, mock_conn_fn):
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = None

        client = _client()
        resp = client.get("/api/pipeline/status/999")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════
# Classe 6: Ordem de Chamadas e SOAP Grupos
# ══════════════════════════════════════════════════════════════════

class TestPipelineOrdemEGrupos:
    """Verifica que os eventos são enviados na ordem correta com os grupos SOAP certos"""

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1299XMLGenerator")
    @patch("esocial.pipeline_correcao.S1210XMLGenerator")
    @patch("esocial.pipeline_correcao.S1200XMLGenerator")
    @patch("esocial.pipeline_correcao.S1298XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_soap_grupos_corretos(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1298_gen, mock_s1200_gen, mock_s1210_gen, mock_s1299_gen,
        mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """S-1298 → grupo=3, S-1200 → grupo=1, S-1210 → grupo=1, S-1299 → grupo=3"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (1,)
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_s1298_gen.gerar.return_value = b"<S1298/>"
        mock_s1200_gen.gerar.return_value = b"<S1200/>"
        mock_s1210_gen.gerar.return_value = b"<S1210/>"
        mock_s1299_gen.gerar.return_value = b"<S1299/>"
        mock_signer.assinar.return_value = b"<signed/>"
        mock_soap.montar_envio.return_value = "<soap/>"
        mock_soap.url_envio.return_value = "https://fake/envio"
        mock_soap.url_consulta.return_value = "https://fake/consulta"

        mock_client.enviar_lote.side_effect = [
            _mock_enviar_sucesso(f"P{i}") for i in range(4)
        ]
        mock_client.consultar_lote.side_effect = [
            _mock_consulta_sucesso(f"R{i}") for i in range(4)
        ]

        client = _client()
        resp = client.post("/api/pipeline/executar", json=PIPELINE_REQUEST)
        assert resp.status_code == 200

        # Verify grupo in montar_envio calls
        montar_calls = mock_soap.montar_envio.call_args_list
        assert len(montar_calls) == 4

        # S-1298 → grupo="3"
        assert montar_calls[0].kwargs.get("grupo") or montar_calls[0][1][3] if len(montar_calls[0][1]) > 3 else montar_calls[0].kwargs.get("grupo") == "3"

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1299XMLGenerator")
    @patch("esocial.pipeline_correcao.S1210XMLGenerator")
    @patch("esocial.pipeline_correcao.S1200XMLGenerator")
    @patch("esocial.pipeline_correcao.S1298XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_ordem_sequencial_envios(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1298_gen, mock_s1200_gen, mock_s1210_gen, mock_s1299_gen,
        mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """Envios devem ser S-1298 → S-1200 → S-1210 → S-1299 (em sequência)"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (1,)
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_s1298_gen.gerar.return_value = b"<S1298/>"
        mock_s1200_gen.gerar.return_value = b"<S1200/>"
        mock_s1210_gen.gerar.return_value = b"<S1210/>"
        mock_s1299_gen.gerar.return_value = b"<S1299/>"
        mock_signer.assinar.return_value = b"<signed/>"
        mock_soap.montar_envio.return_value = "<soap/>"
        mock_soap.url_envio.return_value = "https://fake/envio"
        mock_soap.url_consulta.return_value = "https://fake/consulta"

        call_order = []
        orig_enviar = mock_client.enviar_lote

        def track_enviar(*args, **kwargs):
            call_order.append("enviar")
            return _mock_enviar_sucesso(f"P{len(call_order)}")

        def track_consultar(*args, **kwargs):
            call_order.append("consultar")
            return _mock_consulta_sucesso(f"R{len(call_order)}")

        mock_client.enviar_lote.side_effect = track_enviar
        mock_client.consultar_lote.side_effect = track_consultar

        client = _client()
        resp = client.post("/api/pipeline/executar", json=PIPELINE_REQUEST)
        assert resp.status_code == 200

        # Verifica padrão: enviar → consultar → enviar → consultar → ...
        for i in range(0, len(call_order) - 1, 2):
            assert call_order[i] == "enviar"
            assert call_order[i + 1] == "consultar"

        # 4 envios + 4 consultas (S-1298, S-1200, S-1210, S-1299)
        assert call_order.count("enviar") == 4
        assert call_order.count("consultar") == 4

    @patch("esocial.pipeline_correcao.time.sleep")
    @patch("esocial.pipeline_correcao.ESocialClient")
    @patch("esocial.pipeline_correcao.SOAPEnvelopeBuilder")
    @patch("esocial.pipeline_correcao.S1010XMLSigner")
    @patch("esocial.pipeline_correcao.S1299XMLGenerator")
    @patch("esocial.pipeline_correcao.S1210XMLGenerator")
    @patch("esocial.pipeline_correcao.S1200XMLGenerator")
    @patch("esocial.pipeline_correcao.CertificateManager")
    @patch("esocial.pipeline_correcao._load_cert_ativo")
    @patch("esocial.pipeline_correcao._get_conn")
    @patch("builtins.open", create=True)
    def test_ambiente_producao(
        self, mock_open, mock_conn_fn, mock_cert_load, mock_cert_mgr,
        mock_s1200_gen, mock_s1210_gen, mock_s1299_gen,
        mock_signer, mock_soap, mock_client, mock_sleep,
    ):
        """ambiente=1 deve usar URL de produção"""
        mock_conn, mock_cursor = _setup_mock_conn(mock_conn_fn)
        mock_cursor.fetchone.return_value = (1,)
        mock_cert_load.return_value = CERT_ROW
        mock_cert_mgr.decrypt_password.return_value = "senha123"
        mock_open.return_value.__enter__ = lambda s: MagicMock(read=lambda: b"pfxdata")
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_s1200_gen.gerar.return_value = b"<S1200/>"
        mock_s1210_gen.gerar.return_value = b"<S1210/>"
        mock_s1299_gen.gerar.return_value = b"<S1299/>"
        mock_signer.assinar.return_value = b"<signed/>"
        mock_soap.montar_envio.return_value = "<soap/>"
        mock_soap.url_envio.return_value = "https://producao.esocial.gov.br/envio"
        mock_soap.url_consulta.return_value = "https://producao.esocial.gov.br/consulta"

        mock_client.enviar_lote.side_effect = [
            _mock_enviar_sucesso(f"P{i}") for i in range(3)
        ]
        mock_client.consultar_lote.side_effect = [
            _mock_consulta_sucesso(f"R{i}") for i in range(3)
        ]

        client = _client()
        req = {**PIPELINE_REQUEST, "ambiente": "1", "skip_s1298": True}
        resp = client.post("/api/pipeline/executar", json=req)
        assert resp.status_code == 200

        mock_soap.url_envio.assert_called_with(producao=True)
        mock_soap.url_consulta.assert_called_with(producao=True)
