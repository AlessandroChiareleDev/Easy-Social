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
from esocial.xml_signer import S1010XMLSigner

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

            resultado = ESocialClient._parsear_resposta_consulta(response.text)
            resultado["xml_resposta"] = response.text
            return resultado

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

            recibo = evt_el.find(".//{*}recibo/{*}nrRecibo")
            if recibo is None:
                recibo = evt_el.find(".//{*}nrRecibo")
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

    # ── Download Cirúrgico ────────────────────────────────────────

    @staticmethod
    def _fazer_request_assinado(
        inner_xml: str,
        montar_soap_fn,
        url: str,
        headers: dict,
        pfx_data: bytes,
        password: str,
    ) -> str:
        """
        Fluxo comum: assinar inner XML → montar SOAP → enviar → retornar texto.

        Raises on HTTP error. Returns response text.
        """
        # 1. Assinar inner XML
        inner_assinado = S1010XMLSigner.assinar(
            inner_xml.encode("utf-8"), pfx_data, password
        )
        inner_str = inner_assinado.decode("utf-8") if isinstance(inner_assinado, bytes) else inner_assinado

        # 2. Montar SOAP envelope
        soap = montar_soap_fn(inner_str)

        # 3. Extrair PEM e enviar
        cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, password)
        temp_cert = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pem")
        temp_key = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pem")
        try:
            temp_cert.write(cert_pem)
            temp_cert.flush()
            temp_cert.close()
            temp_key.write(key_pem)
            temp_key.flush()
            temp_key.close()

            response = requests.post(
                url=url,
                data=soap.encode("utf-8"),
                headers=headers,
                cert=(temp_cert.name, temp_key.name),
                verify=False,
                timeout=120,
            )
            response.raise_for_status()
            return response.text
        finally:
            for f in (temp_cert.name, temp_key.name):
                try:
                    os.unlink(f)
                except OSError:
                    pass

    # ── Consultar Identificadores ─────────────────────────────────

    @staticmethod
    def consultar_identificadores_trabalhador(
        cpf: str,
        dt_ini: str,
        dt_fim: str,
        pfx_data: bytes,
        password: str,
        empregador: dict,
        producao: bool = False,
    ) -> dict:
        """
        Consulta identificadores de eventos de um trabalhador por CPF e período.

        Args:
            cpf: CPF do trabalhador (11 dígitos)
            dt_ini: Data início (YYYY-MM-DD)
            dt_fim: Data fim (YYYY-MM-DD)
            pfx_data: Conteúdo do .pfx
            password: Senha do certificado
            empregador: dict com tpInsc e nrInsc
            producao: Se True, usa ambiente de produção

        Returns:
            dict com: sucesso, codigo_resposta, descricao, eventos[], xml_resposta, erro
        """
        inner_xml = SOAPEnvelopeBuilder.inner_consulta_ident_trabalhador(
            empregador, cpf, dt_ini, dt_fim
        )
        try:
            response_text = ESocialClient._fazer_request_assinado(
                inner_xml=inner_xml,
                montar_soap_fn=SOAPEnvelopeBuilder.montar_consulta_ident_trabalhador,
                url=SOAPEnvelopeBuilder.url_identificadores(producao),
                headers=SOAPEnvelopeBuilder.headers_ident_trabalhador(),
                pfx_data=pfx_data,
                password=password,
            )
        except Exception as e:
            return {
                "sucesso": False,
                "codigo_resposta": None,
                "descricao": None,
                "eventos": [],
                "erro": str(e),
            }

        resultado = ESocialClient._parsear_resposta_identificadores(response_text)
        resultado["xml_resposta"] = response_text
        return resultado

    @staticmethod
    def consultar_identificadores_empregador(
        tp_evt: str,
        per_apur: str,
        pfx_data: bytes,
        password: str,
        empregador: dict,
        producao: bool = False,
    ) -> dict:
        """
        Consulta identificadores de eventos do empregador por tipo e período.

        Args:
            tp_evt: Tipo do evento (ex: "S-1200")
            per_apur: Período de apuração (ex: "2024-01")
            pfx_data: Conteúdo do .pfx
            password: Senha do certificado
            empregador: dict com tpInsc e nrInsc
            producao: Se True, usa ambiente de produção

        Returns:
            dict com: sucesso, codigo_resposta, descricao, eventos[], xml_resposta, erro
        """
        inner_xml = SOAPEnvelopeBuilder.inner_consulta_ident_empregador(
            empregador, tp_evt, per_apur
        )
        try:
            response_text = ESocialClient._fazer_request_assinado(
                inner_xml=inner_xml,
                montar_soap_fn=SOAPEnvelopeBuilder.montar_consulta_ident_empregador,
                url=SOAPEnvelopeBuilder.url_identificadores(producao),
                headers=SOAPEnvelopeBuilder.headers_ident_empregador(),
                pfx_data=pfx_data,
                password=password,
            )
        except Exception as e:
            return {
                "sucesso": False,
                "codigo_resposta": None,
                "descricao": None,
                "eventos": [],
                "erro": str(e),
            }

        resultado = ESocialClient._parsear_resposta_identificadores(response_text)
        resultado["xml_resposta"] = response_text
        return resultado

    @staticmethod
    def _parsear_resposta_identificadores(response_text: str) -> dict:
        """Parseia resposta de consulta de identificadores de eventos."""
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

        # Status
        cd = root.find(".//{*}cdResposta")
        if cd is not None:
            resultado["codigo_resposta"] = cd.text

        desc = root.find(".//{*}descResposta")
        if desc is not None:
            resultado["descricao"] = desc.text

        # 201 = OK, 101 = em processamento, 203 = há mais eventos (paginação)
        resultado["sucesso"] = resultado["codigo_resposta"] in ("201", "101", "203")

        # Eventos identificados
        for id_el in root.findall(".//{*}id"):
            evt = {
                "id": id_el.text,
                "nrRec": None,
                "tipo": ESocialClient._inferir_tipo_evento(id_el.text) if id_el.text else None,
            }
            # Try to find sibling nrRec within the same parent
            parent = id_el.getparent() if hasattr(id_el, 'getparent') else None
            if parent is not None:
                nr_rec = parent.find("{*}nrRec")
                if nr_rec is not None:
                    evt["nrRec"] = nr_rec.text
            resultado["eventos"].append(evt)

        return resultado

    @staticmethod
    def _inferir_tipo_evento(event_id: str) -> str | None:
        """
        Infere o tipo de evento eSocial a partir do padrão do ID.
        IDs auto-gerados: ID + dígito + 19 zeros + nrRec
          dígito 1 = S-5001 (INSS), 2 = S-5002 (IRRF), 3 = S-5003
        IDs empregador: ID + CNPJ(8) + data/seq
        """
        if not event_id or len(event_id) < 22 or not event_id.startswith("ID"):
            return None
        after_id = event_id[2:]  # remove "ID"
        prefix = after_id[0]
        rest = after_id[1:20]  # chars 1-19
        if rest == "0" * 19:
            # Auto-generated totalizador
            tipo_map = {"1": "S-5001", "2": "S-5002", "3": "S-5003"}
            return tipo_map.get(prefix, f"S-500{prefix}")
        else:
            # Employer event — can't tell exact type without more context
            return "EMPREGADOR"

    # ── Solicitar Download ────────────────────────────────────────

    @staticmethod
    def solicitar_download_por_id(
        ids: list[str],
        pfx_data: bytes,
        password: str,
        empregador: dict,
        producao: bool = False,
    ) -> dict:
        """
        Solicita download de eventos por ID.

        Args:
            ids: Lista de IDs de eventos
            pfx_data: Conteúdo do .pfx
            password: Senha do certificado
            empregador: dict com tpInsc e nrInsc
            producao: Se True, usa ambiente de produção

        Returns:
            dict com: sucesso, codigo_resposta, descricao, arquivos[], xml_resposta, erro
        """
        inner_xml = SOAPEnvelopeBuilder.inner_download_por_id(empregador, ids)
        try:
            response_text = ESocialClient._fazer_request_assinado(
                inner_xml=inner_xml,
                montar_soap_fn=SOAPEnvelopeBuilder.montar_download_por_id,
                url=SOAPEnvelopeBuilder.url_download(producao),
                headers=SOAPEnvelopeBuilder.headers_download_por_id(),
                pfx_data=pfx_data,
                password=password,
            )
        except Exception as e:
            return {
                "sucesso": False,
                "codigo_resposta": None,
                "descricao": None,
                "arquivos": [],
                "erro": str(e),
            }

        resultado = ESocialClient._parsear_resposta_download(response_text)
        resultado["xml_resposta"] = response_text
        return resultado

    @staticmethod
    def solicitar_download_por_nrrecibo(
        nr_recibos: list[str],
        pfx_data: bytes,
        password: str,
        empregador: dict,
        producao: bool = False,
    ) -> dict:
        """
        Solicita download de eventos por número de recibo.

        Args:
            nr_recibos: Lista de números de recibo
            pfx_data: Conteúdo do .pfx
            password: Senha do certificado
            empregador: dict com tpInsc e nrInsc
            producao: Se True, usa ambiente de produção

        Returns:
            dict com: sucesso, codigo_resposta, descricao, arquivos[], xml_resposta, erro
        """
        inner_xml = SOAPEnvelopeBuilder.inner_download_por_nrrecibo(empregador, nr_recibos)
        try:
            response_text = ESocialClient._fazer_request_assinado(
                inner_xml=inner_xml,
                montar_soap_fn=SOAPEnvelopeBuilder.montar_download_por_nrrecibo,
                url=SOAPEnvelopeBuilder.url_download(producao),
                headers=SOAPEnvelopeBuilder.headers_download_por_nrrecibo(),
                pfx_data=pfx_data,
                password=password,
            )
        except Exception as e:
            return {
                "sucesso": False,
                "codigo_resposta": None,
                "descricao": None,
                "arquivos": [],
                "erro": str(e),
            }

        resultado = ESocialClient._parsear_resposta_download(response_text)
        resultado["xml_resposta"] = response_text
        return resultado

    @staticmethod
    def _parsear_resposta_download(response_text: str) -> dict:
        """Parseia resposta de download de eventos."""
        resultado = {
            "sucesso": False,
            "codigo_resposta": None,
            "descricao": None,
            "arquivos": [],
        }

        try:
            root = etree.fromstring(response_text.encode("utf-8"))
        except etree.XMLSyntaxError:
            resultado["erro"] = "Resposta não é XML válido"
            return resultado

        # Status geral
        status = root.find(".//{*}status")
        if status is not None:
            cd = status.find("{*}cdResposta")
            if cd is not None:
                resultado["codigo_resposta"] = cd.text
            desc = status.find("{*}descResposta")
            if desc is not None:
                resultado["descricao"] = desc.text

        resultado["sucesso"] = resultado["codigo_resposta"] in ("201", "101")

        # Arquivos (cada evento retornado)
        ns_dl = "http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0"

        # Try both retornoProcessamentoDownload and arquivo patterns
        for arquivo in root.findall(f".//{{{ns_dl}}}arquivo"):
            arq_data = ESocialClient._parsear_arquivo_download(arquivo, ns_dl)
            if arq_data:
                resultado["arquivos"].append(arq_data)

        # Fallback: try wildcard namespace
        if not resultado["arquivos"]:
            for arquivo in root.findall(".//{*}arquivo"):
                arq_data = ESocialClient._parsear_arquivo_download(arquivo)
                if arq_data:
                    resultado["arquivos"].append(arq_data)

        return resultado

    @staticmethod
    def _parsear_arquivo_download(arquivo_el, ns: str = None) -> dict | None:
        """Parseia um elemento arquivo do download."""
        # Find evento and recibo inside arquivo
        # Format 1 (download por ID): <arquivo><evento>...<recibo>...
        # Format 2 (download por nrRecibo): <arquivo><status>...<evt>...
        if ns:
            evento_el = arquivo_el.find(f"{{{ns}}}evento")
            recibo_el = arquivo_el.find(f"{{{ns}}}recibo")
        else:
            evento_el = arquivo_el.find("{*}evento")
            recibo_el = arquivo_el.find("{*}recibo")

        # Fallback: nrRecibo response uses <evt> instead of <evento>
        evt_el = None
        if evento_el is None:
            if ns:
                evt_el = arquivo_el.find(f"{{{ns}}}evt")
            else:
                evt_el = arquivo_el.find("{*}evt")

        if evento_el is None and evt_el is None:
            return None

        # Extract inner eSocial
        inner_esocial = None
        source_el = evento_el if evento_el is not None else evt_el
        for child in source_el:
            if "eSocial" in child.tag:
                inner_esocial = child
                break
        # For <evt>, the eSocial might be the element itself if it wraps directly
        if inner_esocial is None and evt_el is not None:
            inner_esocial = evt_el

        arq = {
            "evento_xml": etree.tostring(inner_esocial, encoding="unicode") if inner_esocial is not None else None,
            "nr_recibo": None,
            "cd_resposta": None,
        }

        # Extract recibo info from <recibo> element (download por ID format)
        if recibo_el is not None:
            recibo_inner = None
            for child in recibo_el:
                if "eSocial" in child.tag:
                    recibo_inner = child
                    break
            if recibo_inner is not None:
                nr_rec = recibo_inner.find(".//{*}nrRecibo")
                if nr_rec is not None:
                    arq["nr_recibo"] = nr_rec.text
                cd_resp = recibo_inner.find(".//{*}cdResposta")
                if cd_resp is not None:
                    arq["cd_resposta"] = cd_resp.text

        # Extract per-arquivo status (nrRecibo format has <status> inside <arquivo>)
        if arq["cd_resposta"] is None:
            status_el = arquivo_el.find("{*}status")
            if status_el is not None:
                cd_resp = status_el.find("{*}cdResposta")
                if cd_resp is not None:
                    arq["cd_resposta"] = cd_resp.text

        # Extract nrRecibo from inner event data if not found in recibo element
        if arq["nr_recibo"] is None and inner_esocial is not None:
            nr_rec = inner_esocial.find(".//{*}nrRecArqBase")
            if nr_rec is not None:
                arq["nr_recibo"] = nr_rec.text

        return arq
