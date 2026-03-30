import { Router } from "express";
import { NaturezaValidationService } from "../services/natureza-validation-service";

const router = Router();
const service = new NaturezaValidationService();

/**
 * GET /api/naturezas
 * Lista todas as naturezas carregadas do TXT
 */
router.get("/naturezas", async (_req, res) => {
  try {
    const naturezas = await service.listarNaturezas();
    return res
      .status(200)
      .json({ success: true, data: naturezas, total: naturezas.length });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/naturezas/buscar-similares
 * Busca naturezas similares ao nome do evento (3 camadas)
 * Query: nomeEvento, topN, codigoEvento
 */
router.get("/naturezas/buscar-similares", async (req, res) => {
  try {
    const nomeEvento = req.query.nomeEvento as string;
    if (!nomeEvento) {
      return res.status(400).json({ error: "nomeEvento é obrigatório" });
    }
    const topN = parseInt(req.query.topN as string) || 30;
    const codigoEvento = req.query.codigoEvento as string | undefined;
    const resultado = await service.buscarSimilares(
      nomeEvento,
      topN,
      codigoEvento,
    );
    return res.status(200).json({ success: true, ...resultado });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/naturezas/por-codigo/:codigo
 * Busca natureza pelo código exato
 */
router.get("/naturezas/por-codigo/:codigo", async (req, res) => {
  try {
    const nat = await service.buscarPorCodigo(req.params.codigo);
    if (!nat) {
      return res
        .status(404)
        .json({ success: false, error: "Código não encontrado" });
    }
    return res.status(200).json({ success: true, data: nat });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/rubricas/com-problemas
 * Lista rubricas com status "Verificar"
 * Query: limit, offset, apenaPendentes (true/false)
 */
router.get("/rubricas/com-problemas", async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 50;
    const offset = parseInt(req.query.offset as string) || 0;
    const apenaPendentes = req.query.apenaPendentes !== "false";
    const resultado = await service.getRubricasComProblemas(
      limit,
      offset,
      apenaPendentes,
    );
    return res.status(200).json({ success: true, ...resultado });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/rubricas/corrigir
 * Aplica correção de natureza a uma rubrica
 * Body: { id, naturezaCodigo, naturezaNome, motivo }
 */
router.post("/rubricas/corrigir", async (req, res) => {
  try {
    const { id, naturezaCodigo, naturezaNome, motivo, usuarioNome } = req.body;

    if (!id || !naturezaCodigo || !naturezaNome) {
      return res.status(400).json({
        error: "Campos obrigatórios: id, naturezaCodigo, naturezaNome",
      });
    }

    const ok = await service.corrigirRubrica(
      id,
      naturezaCodigo,
      naturezaNome,
      motivo || "",
      undefined,
      usuarioNome || "sistema",
    );
    if (!ok) {
      return res.status(404).json({ error: "Rubrica não encontrada" });
    }
    return res
      .status(200)
      .json({ success: true, message: "Correção salva no staging" });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/rubricas/desfazer/:id
 * Desfaz uma correção
 */
router.post("/rubricas/desfazer/:id", async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ error: "ID inválido" });
    }
    const ok = await service.desfazerCorrecao(id);
    if (!ok) {
      return res.status(404).json({ error: "Rubrica não encontrada" });
    }
    return res
      .status(200)
      .json({ success: true, message: "Correção desfeita" });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/rubricas/progresso
 * Retorna estatísticas de progresso da validação
 */
router.get("/rubricas/progresso", async (_req, res) => {
  try {
    const progresso = await service.getProgresso();
    return res.status(200).json({ success: true, ...progresso });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/rubricas/relatorio-final
 * Retorna todas as correções realizadas
 */
router.get("/rubricas/relatorio-final", async (_req, res) => {
  try {
    const relatorio = await service.getRelatorioFinal();
    return res
      .status(200)
      .json({ success: true, data: relatorio, total: relatorio.length });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/rubricas/aplicar-correcoes
 * Merge: aplica todas as correções pendentes do staging → analise_natureza
 */
router.post("/rubricas/aplicar-correcoes", async (_req, res) => {
  try {
    const resultado = await service.aplicarCorrecoes();
    return res.status(200).json({
      success: true,
      message: `${resultado.aplicadas} correções aplicadas com sucesso`,
      ...resultado,
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/rubricas/staging-resumo
 * Resumo do staging (pendentes, aplicadas, por usuário)
 */
router.get("/rubricas/staging-resumo", async (_req, res) => {
  try {
    const resumo = await service.getStagingResumo();
    return res.status(200).json({ success: true, ...resumo });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * PUT /api/rubricas/staging/:id
 * Edita uma correção pendente no staging (muda código/nome da natureza)
 */
router.put("/rubricas/staging/:id", async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ error: "ID inválido" });
    }
    const { naturezaCodigo, naturezaNome } = req.body;
    if (!naturezaCodigo || !naturezaNome) {
      return res
        .status(400)
        .json({ error: "naturezaCodigo e naturezaNome são obrigatórios" });
    }
    const ok = await service.editarStaging(id, naturezaCodigo, naturezaNome);
    if (!ok) {
      return res
        .status(404)
        .json({ error: "Correção pendente não encontrada" });
    }
    return res
      .status(200)
      .json({ success: true, message: "Correção atualizada" });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

export default router;
