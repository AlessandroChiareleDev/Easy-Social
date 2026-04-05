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
                    rubrica_ids, rubrica_detalhes, xml_enviado, ocorrencias)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
