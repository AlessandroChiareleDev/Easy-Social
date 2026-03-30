import { Router } from "express";
import { DatabaseService } from "../services/database-service";
import pool from "../config/database";
import path from "path";

const router = Router();
const databaseService = new DatabaseService();

/** Whitelist of allowed table names */
const ALLOWED_TABLES = [
  "analise_natureza",
  "analise_natureza_certo",
  "dinamica",
  "tabela_eventos_gl",
  "tabela_eb",
  "tabela_cruzamento",
  "tabela3_esocial_oficial",
  "eb_skills_base_legal",
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
        AND table_name IN ('analise_natureza', 'analise_natureza_certo', 'dinamica', 'tabela_eventos_gl', 'tabela_eb', 'tabela_cruzamento');
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
