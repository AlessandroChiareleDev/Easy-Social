"""
Rotas para o Parser de XML Payload Completo.
Endpoints para extrair dm_devs / info_pgtos de XMLs do eSocial (Denis).
"""
import os
import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from esocial.xml_payload_parser import (
    parse_xml_completo,
    parse_pasta,
    construir_input_pipeline,
)

logger = logging.getLogger("parser_routes")

router = APIRouter(prefix="/api/parser", tags=["parser"])

# Pasta padrão de XMLs do Denis (configurável via query param)
DEFAULT_XML_DIR = os.path.join(os.path.dirname(__file__), "..", "recibos_s1010")


@router.get("/pasta")
async def listar_pasta(pasta: str = Query(None)):
    """Lista XMLs disponíveis na pasta."""
    pasta_real = pasta or DEFAULT_XML_DIR
    if not os.path.isdir(pasta_real):
        raise HTTPException(404, f"Pasta não encontrada: {pasta_real}")

    xmls = [f for f in os.listdir(pasta_real) if f.lower().endswith(".xml")]
    return {"pasta": pasta_real, "total": len(xmls), "arquivos": sorted(xmls)}


@router.get("/arquivo")
async def parse_arquivo(filepath: str):
    """Parseia um único XML e retorna payload completo."""
    if not os.path.isfile(filepath):
        raise HTTPException(404, f"Arquivo não encontrado: {filepath}")

    resultado, erro = parse_xml_completo(filepath)
    if erro:
        raise HTTPException(400, erro)

    return resultado


@router.get("/extrair")
async def extrair_pasta(
    pasta: str = Query(None),
    tipo: str = Query(None, description="S-1200 ou S-1210"),
    cpf: str = Query(None, description="Filtrar por CPF (11 dígitos)"),
):
    """Extrai payloads completos de todos os XMLs da pasta."""
    pasta_real = pasta or DEFAULT_XML_DIR
    tipos = [tipo] if tipo else None
    resultado = parse_pasta(pasta_real, tipos=tipos, cpf_filtro=cpf)
    return resultado


@router.get("/input-pipeline")
async def montar_input_pipeline(
    pasta: str = Query(None),
    cpf: str = Query(..., description="CPF do trabalhador (11 dígitos)"),
    per_apur: str = Query(..., description="Período de apuração (AAAA-MM)"),
):
    """
    Busca XMLs de S-1200 e S-1210 para um CPF/período e retorna
    o input pronto para o pipeline de retificação.
    """
    pasta_real = pasta or DEFAULT_XML_DIR
    resultado, erro = construir_input_pipeline(pasta_real, cpf, per_apur)
    if erro:
        raise HTTPException(404, erro)

    return resultado
