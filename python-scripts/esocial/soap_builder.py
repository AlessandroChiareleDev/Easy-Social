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
