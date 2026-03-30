"""
Cliente eSocial — Envio e Consulta de lotes via SOAP 1.1 + mTLS
Ambiente: Homologação (producaorestrita) — exclusivamente

Baseado no código de referência do repositório Projeto (comprovado em homologação).
"""

import os
import re
import tempfile
import requests
import urllib3
from lxml import etree
from cryptography.hazmat.primitives.serialization import (
    pkcs12,
    Encoding,
    PrivateFormat,
    NoEncryption,
)
from cryptography.hazmat.backends import default_backend

from esocial.soap_builder import SOAPEnvelopeBuilder

# Homologação tem problemas de SSL — suprimir warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ESocialClient:
    """Envia e consulta lotes de eventos eSocial via SOAP + mTLS"""

    # ── PFX → PEM ────────────────────────────────────────────────

    @staticmethod
    def _extrair_pem(pfx_data: bytes, password: str) -> tuple[bytes, bytes]:
        """
        Extrai certificado e chave privada do PFX em formato PEM.

        Returns:
            (cert_pem, key_pem)

        Raises:
            ValueError: se senha incorreta ou PFX inválido
        """
        try:
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                pfx_data,
                password.encode(),
                backend=default_backend(),
            )
        except Exception as e:
            msg = str(e).lower()
            if "password" in msg or "decrypt" in msg or "mac" in msg:
                raise ValueError("Senha do certificado incorreta")
            raise ValueError(f"Erro ao carregar certificado: {e}")

        if certificate is None or private_key is None:
            raise ValueError("Certificado ou chave privada não encontrados no PFX")

        cert_pem = certificate.public_bytes(Encoding.PEM)
        key_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=NoEncryption(),
        )
        return cert_pem, key_pem

    # ── Envio ─────────────────────────────────────────────────────

    @staticmethod
    def enviar_lote(soap_envelope: str, pfx_data: bytes, password: str, url: str = None) -> dict:
        """
        Envia envelope SOAP ao eSocial via HTTPS + mTLS.

        Args:
            soap_envelope: XML SOAP completo (str)
            pfx_data: conteúdo do .pfx
            password: senha do certificado
            url: URL do webservice (se None, usa homologação)

        Returns:
            dict com: sucesso, codigo_resposta, descricao, protocolo,
                      dh_recepcao, ocorrencias, erro (se houver)
        """
        # Extrair PEM
        cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, password)

        # Criar tempfiles PEM para requests
        temp_cert = tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=".pem"
        )
        temp_key = tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=".pem"
        )
        try:
            temp_cert.write(cert_pem)
            temp_cert.flush()
            temp_cert.close()

            temp_key.write(key_pem)
            temp_key.flush()
            temp_key.close()

            # Enviar
            try:
                response = requests.post(
                    url=url or SOAPEnvelopeBuilder.url_envio(),
                    data=soap_envelope.encode("utf-8"),
                    headers=SOAPEnvelopeBuilder.headers(),
                    cert=(temp_cert.name, temp_key.name),
                    verify=False,  # Homologação tem problemas de SSL
                    timeout=60,
                )
                response.raise_for_status()
            except Exception as e:
                return {
                    "sucesso": False,
                    "codigo_resposta": None,
                    "descricao": None,
                    "protocolo": None,
                    "dh_recepcao": None,
                    "ocorrencias": [],
                    "erro": str(e),
                }

            # Parsear resposta
            return ESocialClient._parsear_resposta_envio(response.text)

        finally:
            # Limpar tempfiles
            for f in (temp_cert.name, temp_key.name):
                try:
                    os.unlink(f)
                except OSError:
                    pass

    # ── Parsing da resposta de envio ──────────────────────────────

    @staticmethod
    def _parsear_resposta_envio(response_text: str) -> dict:
        """
        Extrai cdResposta, protocoloEnvio, ocorrências do XML de retorno.
        """
        resultado = {
            "sucesso": False,
            "codigo_resposta": None,
            "descricao": None,
            "protocolo": None,
            "dh_recepcao": None,
            "ocorrencias": [],
        }

        try:
            root = etree.fromstring(response_text.encode("utf-8"))
        except etree.XMLSyntaxError:
            resultado["erro"] = "Resposta não é XML válido"
            return resultado

        # Tentar múltiplas estratégias de namespace
        ns_retorno = "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0"

        # cdResposta
        cd = root.find(f".//{{{ns_retorno}}}cdResposta")
        if cd is None:
            cd = root.find(".//{*}cdResposta")
        if cd is not None:
            resultado["codigo_resposta"] = cd.text

        # descResposta
        desc = root.find(f".//{{{ns_retorno}}}descResposta")
        if desc is None:
            desc = root.find(".//{*}descResposta")
        if desc is not None:
            resultado["descricao"] = desc.text

        # protocoloEnvio
        proto = root.find(f".//{{{ns_retorno}}}protocoloEnvio")
        if proto is None:
            proto = root.find(".//{*}protocoloEnvio")
        if proto is not None:
            resultado["protocolo"] = proto.text

        # dhRecepcao
        dh = root.find(f".//{{{ns_retorno}}}dhRecepcao")
        if dh is None:
            dh = root.find(".//{*}dhRecepcao")
        if dh is not None:
            resultado["dh_recepcao"] = dh.text

        # ocorrencias
        ocorrencias = root.findall(f".//{{{ns_retorno}}}ocorrencia")
        if not ocorrencias:
            ocorrencias = root.findall(".//{*}ocorrencia")
        for oc in ocorrencias:
            tipo_el = oc.find(f"{{{ns_retorno}}}tipo")
            if tipo_el is None:
                tipo_el = oc.find("{*}tipo")
            codigo_el = oc.find(f"{{{ns_retorno}}}codigo")
            if codigo_el is None:
                codigo_el = oc.find("{*}codigo")
            desc_el = oc.find(f"{{{ns_retorno}}}descricao")
            if desc_el is None:
                desc_el = oc.find("{*}descricao")

            resultado["ocorrencias"].append({
                "tipo": tipo_el.text if tipo_el is not None else None,
                "codigo": codigo_el.text if codigo_el is not None else None,
                "descricao": desc_el.text if desc_el is not None else None,
            })

        # Sucesso = código 201
        resultado["sucesso"] = resultado["codigo_resposta"] == "201"

        return resultado

    # ── Consulta ──────────────────────────────────────────────────

    @staticmethod
    def consultar_lote(protocolo: str, pfx_data: bytes, password: str, url: str = None) -> dict:
        """
        Consulta o resultado do processamento de um lote via protocolo.

        Args:
            protocolo: protocolo retornado pelo enviar_lote
            pfx_data: conteúdo do .pfx
            password: senha do certificado
            url: URL do webservice de consulta (se None, usa homologação)

        Returns:
            dict com: sucesso, codigo_resposta, descricao, eventos[]
        """
        cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, password)

        temp_cert = tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=".pem"
        )
        temp_key = tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=".pem"
        )
        try:
            temp_cert.write(cert_pem)
            temp_cert.flush()
            temp_cert.close()

            temp_key.write(key_pem)
            temp_key.flush()
            temp_key.close()

            soap_consulta = SOAPEnvelopeBuilder.montar_consulta(protocolo)

            try:
                response = requests.post(
                    url=url or SOAPEnvelopeBuilder.url_consulta(),
                    data=soap_consulta.encode("utf-8"),
                    headers=SOAPEnvelopeBuilder.headers_consulta(),
                    cert=(temp_cert.name, temp_key.name),
                    verify=False,
                    timeout=60,
                )
                response.raise_for_status()
            except Exception as e:
                return {
                    "sucesso": False,
                    "codigo_resposta": None,
                    "descricao": None,
                    "eventos": [],
                    "erro": str(e),
                }

            return ESocialClient._parsear_resposta_consulta(response.text)

        finally:
            for f in (temp_cert.name, temp_key.name):
                try:
                    os.unlink(f)
                except OSError:
                    pass

    # ── Parsing da resposta de consulta ───────────────────────────

    @staticmethod
    def _parsear_resposta_consulta(response_text: str) -> dict:
        """
        Parseia resposta de consulta: status do lote + status por evento.
        """
        resultado = {
            "sucesso": False,
            "codigo_resposta": None,
            "descricao": None,
            "eventos": [],
        }

        try:
            root = etree.fromstring(response_text.encode("utf-8"))
        except etree.XMLSyntaxError:
            resultado["erro"] = "Resposta não é XML válido"
            return resultado

        # Status do lote (primeiro cdResposta encontrado)
        cd = root.find(".//{*}retornoProcessamentoLoteEventos/{*}status/{*}cdResposta")
        if cd is None:
            cd = root.find(".//{*}cdResposta")
        if cd is not None:
            resultado["codigo_resposta"] = cd.text

        desc = root.find(".//{*}retornoProcessamentoLoteEventos/{*}status/{*}descResposta")
        if desc is None:
            desc = root.find(".//{*}descResposta")
        if desc is not None:
            resultado["descricao"] = desc.text

        resultado["sucesso"] = resultado["codigo_resposta"] == "201"

        # Eventos individuais
        eventos = root.findall(".//{*}retornoEventos/{*}evento")
        for evt_el in eventos:
            evt_data = {
                "id": evt_el.get("Id"),
                "codigo_resposta": None,
                "descricao": None,
                "nr_recibo": None,
                "ocorrencias": [],
            }

            # cdResposta do processamento do evento
            proc_cd = evt_el.find(".//{*}processamento/{*}cdResposta")
            if proc_cd is not None:
                evt_data["codigo_resposta"] = proc_cd.text

            proc_desc = evt_el.find(".//{*}processamento/{*}descResposta")
            if proc_desc is not None:
                evt_data["descricao"] = proc_desc.text

            recibo = evt_el.find(".//{*}processamento/{*}nrRecibo")
            if recibo is not None:
                evt_data["nr_recibo"] = recibo.text

            # Ocorrências do evento
            for oc in evt_el.findall(".//{*}ocorrencia"):
                tipo_el = oc.find("{*}tipo")
                codigo_el = oc.find("{*}codigo")
                desc_el = oc.find("{*}descricao")
                evt_data["ocorrencias"].append({
                    "tipo": tipo_el.text if tipo_el is not None else None,
                    "codigo": codigo_el.text if codigo_el is not None else None,
                    "descricao": desc_el.text if desc_el is not None else None,
                })

            resultado["eventos"].append(evt_data)

        return resultado
