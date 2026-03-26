import { Router } from "express";
import { RubricaValidationService } from "../services/rubrica-validation-service";

const router = Router();
const validationService = new RubricaValidationService();

/**
 * POST /api/validacao/detectar
 * Executa a detecção de divergências (compara D/E/F vs H/I/J)
 */
router.post("/validacao/detectar", async (_req, res) => {
  try {
    const resultado = await validationService.detectarDivergencias();
    return res.status(200).json({
      success: true,
      message: `Análise concluída: ${resultado.divergentes} divergências encontradas em ${resultado.total} rubricas`,
      ...resultado,
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/validacao/resumo
 * Retorna resumo geral (totais, pendentes, corrigidas, verificadas)
 */
router.get("/validacao/resumo", async (_req, res) => {
  try {
    const resumo = await validationService.getResumo();
    return res.status(200).json(resumo);
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/validacao/divergencias
 * Lista divergências com paginação e filtro
 * Query params: status (pendente|corrigido|verificado), limit, offset
 */
router.get("/validacao/divergencias", async (req, res) => {
  try {
    const status = req.query.status as string | undefined;
    const limit = parseInt(req.query.limit as string) || 50;
    const offset = parseInt(req.query.offset as string) || 0;

    const resultado = await validationService.getDivergencias(
      status,
      limit,
      offset,
    );
    return res.status(200).json(resultado);
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/validacao/proxima
 * Retorna a próxima rubrica pendente para o wizard de correção
 */
router.get("/validacao/proxima", async (_req, res) => {
  try {
    const proxima = await validationService.getProximaPendente();
    if (!proxima) {
      return res
        .status(200)
        .json({ data: null, message: "Todas as divergências foram tratadas" });
    }
    return res.status(200).json({ data: proxima });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * PATCH /api/validacao/:id/corrigir
 * Marca uma correção como realizada
 */
router.patch("/validacao/:id/corrigir", async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ error: "ID inválido" });
    }

    const { observacao } = req.body;
    const resultado = await validationService.marcarCorrigido(id, observacao);

    if (!resultado) {
      return res.status(404).json({ error: "Correção não encontrada" });
    }
    return res.status(200).json({ success: true, data: resultado });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * PATCH /api/validacao/:id/verificar
 * Marca como verificado (validação final)
 */
router.patch("/validacao/:id/verificar", async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ error: "ID inválido" });
    }

    const resultado = await validationService.marcarVerificado(id);
    if (!resultado) {
      return res.status(404).json({ error: "Correção não encontrada" });
    }
    return res.status(200).json({ success: true, data: resultado });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * PATCH /api/validacao/:id/resetar
 * Reseta uma correção de volta para pendente
 */
router.patch("/validacao/:id/resetar", async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    if (isNaN(id)) {
      return res.status(400).json({ error: "ID inválido" });
    }

    const resultado = await validationService.resetarCorrecao(id);
    if (!resultado) {
      return res.status(404).json({ error: "Correção não encontrada" });
    }
    return res.status(200).json({ success: true, data: resultado });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

export default router;
