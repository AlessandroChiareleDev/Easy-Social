import { Router } from "express";
import { DatabaseService } from "../services/database-service";
import pool from "../config/database";
import path from "path";

const router = Router();
const databaseService = new DatabaseService();

/** Whitelist of allowed table names */
const ALLOWED_TABLES = [
  "cruzamento_eb",
  "rubrica_corrections",
  "esocial_depara",
  "eb_skills_base_legal",
  "esocial_envios",
  "tabela3_esocial_oficial",
  "tabela_marcos",
];

/**
 * GET /api/tables
 * Retorna lista de todas as 6 tabelas processadas
 */
router.get("/tables", async (_req, res) => {
  try {
    const client = await pool.connect();
    try {
      const result = await client.query(`
        SELECT DISTINCT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('cruzamento_eb', 'rubrica_corrections', 'esocial_depara', 'eb_skills_base_legal', 'esocial_envios', 'tabela3_esocial_oficial', 'tabela_marcos');
      `);
      const tableNames = result.rows.map((row: any) => row.table_name);
      return res.status(200).json({ tables: tableNames });
    } finally {
      client.release();
    }
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/tables/:tableName
 * Retorna dados de uma tabela específica
 */
router.get("/tables/:tableName", async (req, res) => {
  try {
    const { tableName } = req.params;

    if (!ALLOWED_TABLES.includes(tableName)) {
      return res.status(400).json({ error: "Nome de tabela inválido" });
    }

    const limit = parseInt(req.query.limit as string) || 100;
    const offset = parseInt(req.query.offset as string) || 0;

    // Parse column filters: ?filter_col_a=value&filter_col_b=value
    const filters: { column: string; value: string }[] = [];
    for (const [key, val] of Object.entries(req.query)) {
      if (key.startsWith("filter_") && typeof val === "string" && val.trim()) {
        const col = key.replace("filter_", "");
        // Validate column name format (col_a through col_zz)
        if (/^col_[a-z]{1,2}$/.test(col)) {
          filters.push({ column: col, value: val.trim() });
        }
      }
    }

    const data = await databaseService.getTableData(
      tableName,
      limit,
      offset,
      filters,
    );
    const count = await databaseService.getTableCount(tableName, filters);

    return res.status(200).json({ data, total: count });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/tables/:tableName/export
 * Retorna todos os dados da tabela para exportação
 */
router.get("/tables/:tableName/export", async (req, res) => {
  try {
    const { tableName } = req.params;

    if (!ALLOWED_TABLES.includes(tableName)) {
      return res.status(400).json({ error: "Nome de tabela inválido" });
    }

    const count = await databaseService.getTableCount(tableName);
    const data = await databaseService.getTableData(
      tableName,
      parseInt(count),
      0,
    );
    const columns = await databaseService.getColumnNames(tableName);

    return res.status(200).json({ data, columns });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/tables/:tableName/columns
 * Retorna referência de colunas (A, B, C, D, E, F, etc.)
 */
router.get("/tables/:tableName/columns", async (req, res) => {
  try {
    const { tableName } = req.params;

    if (!ALLOWED_TABLES.includes(tableName)) {
      return res.status(400).json({ error: "Nome de tabela inválido" });
    }

    const columns = await databaseService.getColumnNames(tableName);
    return res.status(200).json({ columns });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/envios
 * Lista envios ao eSocial com filtros (sem exigir admin)
 */
router.get("/envios", async (req, res) => {
  try {
    const {
      tipo_evento,
      ambiente,
      status,
      desde,
      ate,
      limit = "50",
      offset = "0",
    } = req.query;

    const conditions: string[] = [];
    const params: any[] = [];
    let pi = 1;

    if (tipo_evento) {
      conditions.push(`tipo_evento = $${pi++}`);
      params.push(tipo_evento);
    }
    if (ambiente) {
      conditions.push(`ambiente = $${pi++}`);
      params.push(ambiente);
    }
    if (status) {
      conditions.push(`status = $${pi++}`);
      params.push(status);
    }
    if (desde) {
      conditions.push(`created_at >= $${pi++}`);
      params.push(desde);
    }
    if (ate) {
      conditions.push(`created_at <= $${pi++}`);
      params.push(ate);
    }

    const where =
      conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
    const safeLimit = Math.min(parseInt(limit as string) || 50, 200);
    const safeOffset = parseInt(offset as string) || 0;

    const client = await pool.connect();
    try {
      const tableCheck = await client.query(
        `SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'esocial_envios')`,
      );
      if (!tableCheck.rows[0].exists) {
        return res.json({ success: true, total: 0, envios: [] });
      }

      const countResult = await client.query(
        `SELECT COUNT(*) FROM esocial_envios ${where}`,
        params,
      );

      const result = await client.query(
        `SELECT id, tipo_evento, modo, status, protocolo_envio,
                codigo_resposta, descricao_resposta, total_eventos,
                created_at, ambiente, ini_valid, rubrica_detalhes,
                rubrica_ids, nr_recibo, updated_at, ocorrencias
         FROM esocial_envios ${where}
         ORDER BY created_at DESC
         LIMIT $${pi++} OFFSET $${pi++}`,
        [...params, safeLimit, safeOffset],
      );

      return res.json({
        success: true,
        total: parseInt(countResult.rows[0].count),
        envios: result.rows,
      });
    } finally {
      client.release();
    }
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/envios/resumo
 * Resumo de envios (totais por tipo, status, ambiente) — sem exigir admin
 */
router.get("/envios/resumo", async (_req, res) => {
  try {
    const client = await pool.connect();
    try {
      const tableCheck = await client.query(
        `SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'esocial_envios')`,
      );
      if (!tableCheck.rows[0].exists) {
        return res.json({
          success: true,
          resumo: { total: 0, por_tipo: [], por_status: [], por_ambiente: [] },
        });
      }

      const [totalRes, porTipoRes, porStatusRes, porAmbienteRes] =
        await Promise.all([
          client.query(`SELECT COUNT(*) FROM esocial_envios`),
          client.query(
            `SELECT tipo_evento, COUNT(*) as total FROM esocial_envios GROUP BY tipo_evento ORDER BY total DESC`,
          ),
          client.query(
            `SELECT status, COUNT(*) as total FROM esocial_envios GROUP BY status ORDER BY total DESC`,
          ),
          client.query(
            `SELECT ambiente, COUNT(*) as total FROM esocial_envios GROUP BY ambiente ORDER BY total DESC`,
          ),
        ]);

      return res.json({
        success: true,
        resumo: {
          total: parseInt(totalRes.rows[0].count),
          por_tipo: porTipoRes.rows,
          por_status: porStatusRes.rows,
          por_ambiente: porAmbienteRes.rows,
        },
      });
    } finally {
      client.release();
    }
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * DELETE /api/tables/:tableName
 * Exclui todos os dados de uma tabela (TRUNCATE)
 */
router.delete("/tables/:tableName", async (req, res) => {
  try {
    const { tableName } = req.params;
    const { confirmation } = req.body;

    if (!ALLOWED_TABLES.includes(tableName)) {
      return res.status(400).json({ error: "Nome de tabela inválido" });
    }

    if (confirmation !== "delete") {
      return res.status(400).json({
        error: "Confirmação inválida. Envie { confirmation: 'delete' }",
      });
    }

    const client = await pool.connect();
    try {
      await client.query(`TRUNCATE TABLE ${tableName}`);
      return res.status(200).json({
        success: true,
        message: `Tabela ${tableName} excluída com sucesso`,
      });
    } finally {
      client.release();
    }
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/process
 * Inicia processamento e normalização dos dados
 */
router.post("/process", async (req, res) => {
  try {
    const { uploadId, filePath } = req.body;

    if (!uploadId || !filePath) {
      return res.status(400).json({
        error: "uploadId e filePath são obrigatórios para processamento",
      });
    }

    // Validar que filePath está dentro do diretório de uploads
    const uploadsDir = path.resolve(path.join(__dirname, "../../uploads"));
    const resolvedPath = path.resolve(filePath);
    if (!resolvedPath.startsWith(uploadsDir)) {
      return res.status(400).json({ error: "Caminho de arquivo inválido" });
    }

    // Atualizar status do upload para 'processing'
    const client = await pool.connect();
    try {
      await client.query(
        `UPDATE uploads SET status = 'processing' WHERE id = $1`,
        [uploadId],
      );
    } finally {
      client.release();
    }

    // Iniciar o processamento em background
    databaseService
      .insertNormalizedData(uploadId, resolvedPath)
      .then(() => {
        pool.query(`UPDATE uploads SET status = 'completed' WHERE id = $1`, [
          uploadId,
        ]);
        console.log(
          `Processamento do upload ${uploadId} concluído com sucesso.`,
        );
      })
      .catch((err) => {
        pool.query(`UPDATE uploads SET status = 'failed' WHERE id = $1`, [
          uploadId,
        ]);
        console.error(`Erro no processamento do upload ${uploadId}:`, err);
      });

    return res.status(202).json({
      success: true,
      message: "Processamento iniciado em segundo plano",
      uploadId,
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

export default router;
