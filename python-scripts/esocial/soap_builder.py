"""
Montagem do Envelope SOAP 1.1 para envio de lotes eSocial
Namespace lote: v1_1_1
Namespace serviço: v1_1_0
Ambiente: Homologação (producaorestrita) ou Produção

Baseado no código de referência do repositório Projeto (comprovado em homologação).
"""

import re
from lxml import etree

# Homologação
URL_ENVIO_HOMOLOGACAO = (
    "https://webservices.producaorestrita.esocial.gov.br"
    "/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc"
)
URL_CONSULTA_HOMOLOGACAO = (
    "https://webservices.producaorestrita.esocial.gov.br"
    "/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc"
)

# Produção
URL_ENVIO_PRODUCAO = (
    "https://webservices.envio.esocial.gov.br"
    "/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc"
)
URL_CONSULTA_PRODUCAO = (
    "https://webservices.consulta.esocial.gov.br"
    "/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc"
)

# Backward compat aliases
URL_ENVIO = URL_ENVIO_HOMOLOGACAO
URL_CONSULTA = URL_CONSULTA_HOMOLOGACAO

SOAP_ACTION = (
    "http://www.esocial.gov.br/servicos/empregador/lote/eventos/"
    "envio/v1_1_0/ServicoEnviarLoteEventos/EnviarLoteEventos"
)

SOAP_ACTION_CONSULTA = (
    "http://www.esocial.gov.br/servicos/empregador/lote/eventos/"
    "envio/consulta/retornoProcessamento/v1_1_0/"
    "ServicoConsultarLoteEventos/ConsultarLoteEventos"
)

LOTE_NS = "http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1"

# ── Download Cirúrgico ────────────────────────────────────────────

# Consultar Identificadores de Eventos
URL_IDENTIFICADORES_HOMOLOGACAO = (
    "https://webservices.producaorestrita.esocial.gov.br"
    "/servicos/empregador/dwlcirurgico/WsConsultarIdentificadoresEventos.svc"
)
URL_IDENTIFICADORES_PRODUCAO = (
    "https://webservices.download.esocial.gov.br"
    "/servicos/empregador/dwlcirurgico/WsConsultarIdentificadoresEventos.svc"
)

# Solicitar Download de Eventos
URL_DOWNLOAD_HOMOLOGACAO = (
    "https://webservices.producaorestrita.esocial.gov.br"
    "/servicos/empregador/dwlcirurgico/WsSolicitarDownloadEventos.svc"
)
URL_DOWNLOAD_PRODUCAO = (
    "https://webservices.download.esocial.gov.br"
    "/servicos/empregador/dwlcirurgico/WsSolicitarDownloadEventos.svc"
)

# SOAP Actions — Consultar Identificadores
SOAP_ACTION_IDENT_TRABALHADOR = (
    "http://www.esocial.gov.br/servicos/empregador/consulta/"
    "identificadores-eventos/v1_0_0/"
    "ServicoConsultarIdentificadoresEventos/"
    "ConsultarIdentificadoresEventosTrabalhador"
)
SOAP_ACTION_IDENT_TABELA = (
    "http://www.esocial.gov.br/servicos/empregador/consulta/"
    "identificadores-eventos/v1_0_0/"
    "ServicoConsultarIdentificadoresEventos/"
    "ConsultarIdentificadoresEventosTabela"
)
SOAP_ACTION_IDENT_EMPREGADOR = (
    "http://www.esocial.gov.br/servicos/empregador/consulta/"
    "identificadores-eventos/v1_0_0/"
    "ServicoConsultarIdentificadoresEventos/"
    "ConsultarIdentificadoresEventosEmpregador"
)

# SOAP Actions — Download
SOAP_ACTION_DOWNLOAD_POR_ID = (
    "http://www.esocial.gov.br/servicos/empregador/download/"
    "solicitacao/v1_0_0/ServicoSolicitarDownloadEventos/"
    "SolicitarDownloadEventosPorId"
)
SOAP_ACTION_DOWNLOAD_POR_NRRECIBO = (
    "http://www.esocial.gov.br/servicos/empregador/download/"
    "solicitacao/v1_0_0/ServicoSolicitarDownloadEventos/"
    "SolicitarDownloadEventosPorNrRecibo"
)

# Envelope v1 namespaces
NS_V1_IDENT = (
    "http://www.esocial.gov.br/servicos/empregador/"
    "consulta/identificadores-eventos/v1_0_0"
)
NS_V1_DOWNLOAD = (
    "http://www.esocial.gov.br/servicos/empregador/"
    "download/solicitacao/v1_0_0"
)

# Schema namespaces for inner XML
NS_SCHEMA_IDENT_TRABALHADOR = (
    "http://www.esocial.gov.br/schema/consulta/"
    "identificadores-eventos/trabalhador/v1_0_0"
)
NS_SCHEMA_IDENT_TABELA = (
    "http://www.esocial.gov.br/schema/consulta/"
    "identificadores-eventos/tabela/v1_0_0"
)
NS_SCHEMA_IDENT_EMPREGADOR = (
    "http://www.esocial.gov.br/schema/consulta/"
    "identificadores-eventos/empregador/v1_0_0"
)
NS_SCHEMA_DOWNLOAD_POR_ID = (
    "http://www.esocial.gov.br/schema/download/"
    "solicitacao/id/v1_0_0"
)
NS_SCHEMA_DOWNLOAD_POR_NRRECIBO = (
    "http://www.esocial.gov.br/schema/download/"
    "solicitacao/nrRecibo/v1_0_0"
)


def _extrair_id_evento(xml_str: str) -> str:
    """Extrai o Id do elemento evt* dentro do XML assinado."""
    m = re.search(r'<[^>]*evt\w+[^>]*\s+Id="([^"]+)"', xml_str)
    if m:
        return m.group(1)
    raise ValueError("Id do evento não encontrado no XML assinado")


def _remover_xml_declaration(xml_str: str) -> str:
    """Remove <?xml ...?> para evitar duplicação dentro do SOAP."""
    return re.sub(r'<\?xml[^?]*\?>\s*', '', xml_str)


class SOAPEnvelopeBuilder:
    """Monta envelope SOAP 1.1 para envio de lote eSocial"""

    @staticmethod
    def montar_envio(
        eventos_assinados: list[bytes],
        empregador: dict,
        transmissor: dict,
        grupo: str = "1",
    ) -> str:
        tp_insc_emp = str(empregador["tpInsc"])
        nr_insc_emp = str(empregador["nrInsc"])[:8]  # CNPJ raiz 8 dígitos

        tp_insc_trans = str(transmissor["tpInsc"])
        nr_insc_trans = str(transmissor["nrInsc"])  # CNPJ completo 14 dígitos

        # Montar blocos <evento>
        blocos_evento = []
        for xml_bytes in eventos_assinados:
            xml_str = xml_bytes.decode("utf-8") if isinstance(xml_bytes, bytes) else xml_bytes
            evt_id = _extrair_id_evento(xml_str)
            xml_limpo = _remover_xml_declaration(xml_str)
            blocos_evento.append(
                f'            <evento Id="{evt_id}">\n'
                f"              {xml_limpo}\n"
                f"            </evento>"
            )

        eventos_xml = "\n".join(blocos_evento)

        # Montar lote (sem <?xml?>) — será inserido dentro do SOAP
        lote = (
            f'<eSocial xmlns="{LOTE_NS}">\n'
            f'  <envioLoteEventos grupo="{grupo}">\n'
            f"    <ideEmpregador>\n"
            f"      <tpInsc>{tp_insc_emp}</tpInsc>\n"
            f"      <nrInsc>{nr_insc_emp}</nrInsc>\n"
            f"    </ideEmpregador>\n"
            f"    <ideTransmissor>\n"
            f"      <tpInsc>{tp_insc_trans}</tpInsc>\n"
            f"      <nrInsc>{nr_insc_trans}</nrInsc>\n"
            f"    </ideTransmissor>\n"
            f"    <eventos>\n"
            f"{eventos_xml}\n"
            f"    </eventos>\n"
            f"  </envioLoteEventos>\n"
            f"</eSocial>"
        )

        # Envelopar em SOAP 1.1
        soap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:EnviarLoteEventos>\n"
            f"      <v1:loteEventos>{lote}</v1:loteEventos>\n"
            "    </v1:EnviarLoteEventos>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

        return soap

    @staticmethod
    def headers() -> dict:
        return {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": SOAP_ACTION,
        }

    @staticmethod
    def headers_consulta() -> dict:
        return {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": SOAP_ACTION_CONSULTA,
        }

    @staticmethod
    def montar_consulta(protocolo: str) -> str:
        """Monta envelope SOAP 1.1 para consulta de lote pelo protocolo."""
        consulta_ns = "http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v1_0_0"
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/'
            'envio/consulta/retornoProcessamento/v1_1_0">\n'
            '  <soapenv:Header/>\n'
            '  <soapenv:Body>\n'
            '    <v1:ConsultarLoteEventos>\n'
            '      <v1:consulta>\n'
            f'        <eSocial xmlns="{consulta_ns}">\n'
            '          <consultaLoteEventos>\n'
            f'            <protocoloEnvio>{protocolo}</protocoloEnvio>\n'
            '          </consultaLoteEventos>\n'
            '        </eSocial>\n'
            '      </v1:consulta>\n'
            "    </v1:ConsultarLoteEventos>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

    @staticmethod
    def url_envio(producao: bool = False) -> str:
        return URL_ENVIO_PRODUCAO if producao else URL_ENVIO_HOMOLOGACAO

    @staticmethod
    def url_consulta(producao: bool = False) -> str:
        return URL_CONSULTA_PRODUCAO if producao else URL_CONSULTA_HOMOLOGACAO

    # ── Download Cirúrgico ────────────────────────────────────────

    @staticmethod
    def url_identificadores(producao: bool = False) -> str:
        return URL_IDENTIFICADORES_PRODUCAO if producao else URL_IDENTIFICADORES_HOMOLOGACAO

    @staticmethod
    def url_download(producao: bool = False) -> str:
        return URL_DOWNLOAD_PRODUCAO if producao else URL_DOWNLOAD_HOMOLOGACAO

    @staticmethod
    def headers_ident_trabalhador() -> dict:
        return {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": SOAP_ACTION_IDENT_TRABALHADOR,
        }

    @staticmethod
    def headers_ident_tabela() -> dict:
        return {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": SOAP_ACTION_IDENT_TABELA,
        }

    @staticmethod
    def headers_ident_empregador() -> dict:
        return {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": SOAP_ACTION_IDENT_EMPREGADOR,
        }

    @staticmethod
    def headers_download_por_id() -> dict:
        return {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": SOAP_ACTION_DOWNLOAD_POR_ID,
        }

    @staticmethod
    def headers_download_por_nrrecibo() -> dict:
        return {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": SOAP_ACTION_DOWNLOAD_POR_NRRECIBO,
        }

    # ── Inner XML builders (unsigned) ─────────────────────────────

    @staticmethod
    def inner_consulta_ident_trabalhador(
        empregador: dict, cpf: str, dt_ini: str, dt_fim: str
    ) -> str:
        """Build unsigned inner eSocial XML for ConsultarIdentificadoresEventosTrabalhador."""
        tp_insc = str(empregador["tpInsc"])
        nr_insc = str(empregador["nrInsc"])[:8]
        return (
            f'<eSocial xmlns="{NS_SCHEMA_IDENT_TRABALHADOR}" '
            f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<consultaIdentificadoresEvts>"
            f"<ideEmpregador>"
            f"<tpInsc>{tp_insc}</tpInsc>"
            f"<nrInsc>{nr_insc}</nrInsc>"
            f"</ideEmpregador>"
            f"<consultaEvtsTrabalhador>"
            f"<cpfTrab>{cpf}</cpfTrab>"
            f"<dtIni>{dt_ini}</dtIni>"
            f"<dtFim>{dt_fim}</dtFim>"
            f"</consultaEvtsTrabalhador>"
            f"</consultaIdentificadoresEvts>"
            f"</eSocial>"
        )

    @staticmethod
    def inner_consulta_ident_tabela(
        empregador: dict,
        tp_evt: str,
        ch_evt: str | None = None,
        dt_ini: str | None = None,
        dt_fim: str | None = None,
    ) -> str:
        """Build unsigned inner eSocial XML for ConsultarIdentificadoresEventosTabela."""
        tp_insc = str(empregador["tpInsc"])
        nr_insc = str(empregador["nrInsc"])[:8]
        optional_filters = ""
        if ch_evt:
            optional_filters += f"<chEvt>{ch_evt}</chEvt>"
        if dt_ini:
            optional_filters += f"<dtIni>{dt_ini}</dtIni>"
        if dt_fim:
            optional_filters += f"<dtFim>{dt_fim}</dtFim>"
        return (
            f'<eSocial xmlns="{NS_SCHEMA_IDENT_TABELA}" '
            f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<consultaIdentificadoresEvts>"
            f"<ideEmpregador>"
            f"<tpInsc>{tp_insc}</tpInsc>"
            f"<nrInsc>{nr_insc}</nrInsc>"
            f"</ideEmpregador>"
            f"<consultaEvtsTabela>"
            f"<tpEvt>{tp_evt}</tpEvt>"
            f"{optional_filters}"
            f"</consultaEvtsTabela>"
            f"</consultaIdentificadoresEvts>"
            f"</eSocial>"
        )

    @staticmethod
    def inner_consulta_ident_empregador(
        empregador: dict, tp_evt: str, per_apur: str
    ) -> str:
        """Build unsigned inner eSocial XML for ConsultarIdentificadoresEventosEmpregador."""
        tp_insc = str(empregador["tpInsc"])
        nr_insc = str(empregador["nrInsc"])[:8]
        return (
            f'<eSocial xmlns="{NS_SCHEMA_IDENT_EMPREGADOR}" '
            f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<consultaIdentificadoresEvts>"
            f"<ideEmpregador>"
            f"<tpInsc>{tp_insc}</tpInsc>"
            f"<nrInsc>{nr_insc}</nrInsc>"
            f"</ideEmpregador>"
            f"<consultaEvtsEmpregador>"
            f"<tpEvt>{tp_evt}</tpEvt>"
            f"<perApur>{per_apur}</perApur>"
            f"</consultaEvtsEmpregador>"
            f"</consultaIdentificadoresEvts>"
            f"</eSocial>"
        )

    @staticmethod
    def inner_download_por_id(empregador: dict, ids: list[str]) -> str:
        """Build unsigned inner eSocial XML for SolicitarDownloadEventosPorId."""
        tp_insc = str(empregador["tpInsc"])
        nr_insc = str(empregador["nrInsc"])[:8]
        ids_xml = "".join(f"<id>{evt_id}</id>" for evt_id in ids)
        return (
            f'<eSocial xmlns="{NS_SCHEMA_DOWNLOAD_POR_ID}" '
            f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<download>"
            f"<ideEmpregador>"
            f"<tpInsc>{tp_insc}</tpInsc>"
            f"<nrInsc>{nr_insc}</nrInsc>"
            f"</ideEmpregador>"
            f"<solicDownloadEvtsPorId>"
            f"{ids_xml}"
            f"</solicDownloadEvtsPorId>"
            f"</download>"
            f"</eSocial>"
        )

    @staticmethod
    def inner_download_por_nrrecibo(empregador: dict, nr_recibos: list[str]) -> str:
        """Build unsigned inner eSocial XML for SolicitarDownloadEventosPorNrRecibo."""
        tp_insc = str(empregador["tpInsc"])
        nr_insc = str(empregador["nrInsc"])[:8]
        nrs_xml = "".join(f"<nrRec>{nr}</nrRec>" for nr in nr_recibos)
        return (
            f'<eSocial xmlns="{NS_SCHEMA_DOWNLOAD_POR_NRRECIBO}" '
            f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<download>"
            f"<ideEmpregador>"
            f"<tpInsc>{tp_insc}</tpInsc>"
            f"<nrInsc>{nr_insc}</nrInsc>"
            f"</ideEmpregador>"
            f"<solicDownloadEventosPorNrRecibo>"
            f"{nrs_xml}"
            f"</solicDownloadEventosPorNrRecibo>"
            f"</download>"
            f"</eSocial>"
        )

    # ── SOAP envelope wrappers (receive signed inner XML) ─────────

    @staticmethod
    def montar_consulta_ident_trabalhador(inner_xml_assinado: str) -> str:
        """Wrap signed inner XML in SOAP envelope for ConsultarIdentificadoresEventosTrabalhador."""
        inner = _remover_xml_declaration(inner_xml_assinado)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            f'xmlns:v1="{NS_V1_IDENT}">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:ConsultarIdentificadoresEventosTrabalhador>\n"
            f"      <v1:consultaEventosTrabalhador>{inner}</v1:consultaEventosTrabalhador>\n"
            "    </v1:ConsultarIdentificadoresEventosTrabalhador>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

    @staticmethod
    def montar_consulta_ident_tabela(inner_xml_assinado: str) -> str:
        """Wrap signed inner XML in SOAP envelope for ConsultarIdentificadoresEventosTabela."""
        inner = _remover_xml_declaration(inner_xml_assinado)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            f'xmlns:v1="{NS_V1_IDENT}">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:ConsultarIdentificadoresEventosTabela>\n"
            f"      <v1:consultaEventosTabela>{inner}</v1:consultaEventosTabela>\n"
            "    </v1:ConsultarIdentificadoresEventosTabela>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

    @staticmethod
    def montar_consulta_ident_empregador(inner_xml_assinado: str) -> str:
        """Wrap signed inner XML in SOAP envelope for ConsultarIdentificadoresEventosEmpregador."""
        inner = _remover_xml_declaration(inner_xml_assinado)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            f'xmlns:v1="{NS_V1_IDENT}">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:ConsultarIdentificadoresEventosEmpregador>\n"
            f"      <v1:consultaEventosEmpregador>{inner}</v1:consultaEventosEmpregador>\n"
            "    </v1:ConsultarIdentificadoresEventosEmpregador>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

    @staticmethod
    def montar_download_por_id(inner_xml_assinado: str) -> str:
        """Wrap signed inner XML in SOAP envelope for SolicitarDownloadEventosPorId."""
        inner = _remover_xml_declaration(inner_xml_assinado)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            f'xmlns:v1="{NS_V1_DOWNLOAD}">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:SolicitarDownloadEventosPorId>\n"
            f"      <v1:solicitacao>{inner}</v1:solicitacao>\n"
            "    </v1:SolicitarDownloadEventosPorId>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

    @staticmethod
    def montar_download_por_nrrecibo(inner_xml_assinado: str) -> str:
        """Wrap signed inner XML in SOAP envelope for SolicitarDownloadEventosPorNrRecibo."""
        inner = _remover_xml_declaration(inner_xml_assinado)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            f'xmlns:v1="{NS_V1_DOWNLOAD}">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:SolicitarDownloadEventosPorNrRecibo>\n"
            f"      <v1:solicitacao>{inner}</v1:solicitacao>\n"
            "    </v1:SolicitarDownloadEventosPorNrRecibo>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )
