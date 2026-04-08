"""
Tracking centralizado de envios eSocial.

Toda vez que um evento é enviado ao governo (por qualquer caminho: rota direta,
pipeline de correção, pipeline de recuperação), esta função registra em
`esocial_envios` para rastreabilidade completa.
"""

import json
import logging

logger = logging.getLogger(__name__)


def registrar_envio(
    conn,
    *,
    tipo_evento: str,
    modo: str,
    ambiente: str,
    ini_valid: str = "",
    status: str = "enviado",
    protocolo_envio: str | None = None,
    codigo_resposta: str | None = None,
    descricao_resposta: str | None = None,
    total_eventos: int = 1,
    nr_recibo: str | None = None,
    rubrica_ids: list | None = None,
    rubrica_detalhes: list | None = None,
    xml_enviado: str | None = None,
    xml_retorno: str | None = None,
    ocorrencias: list | None = None,
    origem: str = "pipeline",
    cpf: str | None = None,
    per_apur: str | None = None,
) -> int | None:
    """
    Insere um registro em esocial_envios.

    Retorna o ID do registro criado, ou None se falhar (nunca levanta exceção).
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO esocial_envios
                   (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                    codigo_resposta, descricao_resposta, total_eventos, nr_recibo,
                    rubrica_ids, rubrica_detalhes, xml_enviado, xml_retorno, ocorrencias)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (
                    tipo_evento,
                    modo,
                    ambiente,
                    ini_valid or per_apur or "",
                    status,
                    protocolo_envio,
                    codigo_resposta,
                    descricao_resposta,
                    total_eventos,
                    nr_recibo,
                    json.dumps(rubrica_ids) if rubrica_ids else None,
                    json.dumps(rubrica_detalhes) if rubrica_detalhes else None,
                    (xml_enviado or "")[:50000] if xml_enviado else None,
                    (xml_retorno or "")[:50000] if xml_retorno else None,
                    json.dumps(ocorrencias) if ocorrencias else json.dumps([]),
                ),
            )
            envio_id = cur.fetchone()[0]
            conn.commit()
            logger.info(
                f"[TRACKER] {tipo_evento} {modo} registrado → envio #{envio_id} "
                f"(protocolo={protocolo_envio}, recibo={nr_recibo}, origem={origem})"
            )
            return envio_id
    except Exception as e:
        logger.error(f"[TRACKER] Erro ao registrar envio {tipo_evento}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None


def registrar_do_result(
    conn,
    *,
    tipo_evento: str,
    modo: str,
    ambiente: str,
    result: dict,
    ini_valid: str = "",
    rubrica_ids: list | None = None,
    origem: str = "pipeline",
    cpf: str | None = None,
    per_apur: str | None = None,
) -> int | None:
    """
    Atalho: registra a partir do dict retornado por _enviar_e_consultar().
    """
    return registrar_envio(
        conn,
        tipo_evento=tipo_evento,
        modo=modo,
        ambiente=ambiente,
        ini_valid=ini_valid,
        status="processado" if result.get("nr_recibo") else ("enviado" if result.get("sucesso") else "erro"),
        protocolo_envio=result.get("protocolo"),
        codigo_resposta=result.get("codigo_resposta"),
        descricao_resposta=result.get("descricao"),
        nr_recibo=result.get("nr_recibo"),
        rubrica_ids=rubrica_ids,
        ocorrencias=[
            ev.get("ocorrencias", [])
            for ev in result.get("eventos", [])
            if ev.get("ocorrencias")
        ] or None,
        origem=origem,
        cpf=cpf,
        per_apur=per_apur,
    )


def registrar_consulta(
    conn,
    *,
    tipo_consulta: str,
    ambiente: str,
    resultado: dict,
    cpf: str | None = None,
    per_apur: str | None = None,
    xml_resposta: str | None = None,
    origem: str = "script",
) -> int | None:
    """
    Registra tentativa de consulta/download ao eSocial em esocial_envios.

    Captura bloqueios (dias 1-7), erros e sucessos de consultas/downloads.

    tipo_consulta: 'CONSULTA-IDENT', 'DOWNLOAD-S5002', 'DOWNLOAD-S5001', etc.
    """
    descricao = str(resultado.get("descricao", "") or resultado.get("erro", ""))
    codigo = str(resultado.get("codigo_resposta", "") or "")

    if "dias 1 e 7" in descricao:
        status = "bloqueado"
    elif codigo == "405" or "limite está esgotado" in descricao:
        status = "limite_esgotado"
    elif resultado.get("sucesso"):
        status = "sucesso"
    else:
        status = "erro"

    return registrar_envio(
        conn,
        tipo_evento=tipo_consulta,
        modo="consulta",
        ambiente=ambiente,
        ini_valid=per_apur or "",
        status=status,
        protocolo_envio=None,
        codigo_resposta=codigo,
        descricao_resposta=descricao[:500] if descricao else None,
        total_eventos=len(resultado.get("eventos", [])),
        nr_recibo=None,
        rubrica_ids=None,
        xml_retorno=xml_resposta[:50000] if xml_resposta else None,
        ocorrencias=[{
            "tipo": "bloqueio_dias_1_7" if "dias 1 e 7" in descricao else "consulta",
            "cpf": cpf,
            "periodo": per_apur,
            "mensagem": descricao,
        }] if descricao else None,
        origem=origem,
        cpf=cpf,
        per_apur=per_apur,
    )
