import { Router, Request, Response } from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import * as XLSX from "xlsx";
import pool from "../config/database";

const router = Router();

// Upload dir
const uploadDir = path.join(__dirname, "..", "..", "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadDir),
  filename: (_req, file, cb) => {
    const timestamp = Date.now();
    const safeName = file.originalname.replace(/[^a-zA-Z0-9._-]/g, "_");
    cb(null, `cruzamento-${timestamp}-${safeName}`);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 200 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    const allowed = [
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "application/vnd.ms-excel",
    ];
    if (allowed.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error("Envie apenas arquivos .xlsx ou .xls"));
    }
  },
});

/**
 * Converts 0-based index to column name: 0→col_a, 25→col_z, 26→col_aa
 */
function colNameForIndex(i: number): string {
  let letter = "";
  let num = i;
  while (num >= 0) {
    letter = String.fromCharCode(97 + (num % 26)) + letter;
    num = Math.floor(num / 26) - 1;
  }
  return `col_${letter}`;
}

/**
 * POST /api/cruzamento/upload
 * Recebe um arquivo Excel com 2 abas, separa nas tabelas A e B
 */
router.post(
  "/cruzamento/upload",
  upload.single("file"),
  async (req: Request, res: Response) => {
    const client = await pool.connect();
    try {
      if (!req.file) {
        return res.status(400).json({ error: "Nenhum arquivo enviado" });
      }

      const filePath = req.file.path;
      const buf = fs.readFileSync(filePath);
      const wb = XLSX.read(buf, { type: "buffer" });

      if (wb.SheetNames.length < 2) {
        return res.status(400).json({
          error: `O arquivo precisa ter pelo menos 2 abas. Encontradas: ${wb.SheetNames.length} (${wb.SheetNames.join(", ")})`,
        });
      }

      await client.query("BEGIN");

      // Limpar dados anteriores
      await client.query("DELETE FROM cruzamento_tabela_b");
      await client.query("DELETE FROM cruzamento_tabela_a");
      await client.query("DELETE FROM cruzamento_uploads");

      // Registrar upload
      const uploadRes = await client.query(
        `INSERT INTO cruzamento_uploads (filename, original_name, file_size, sheet_count, sheet_names)
         VALUES ($1, $2, $3, $4, $5) RETURNING id`,
        [
          req.file.filename,
          req.file.originalname,
          req.file.size,
          wb.SheetNames.length,
          wb.SheetNames,
        ],
      );
      const uploadId = uploadRes.rows[0].id;

      // Processar as 2 primeiras abas
      const tables = ["cruzamento_tabela_a", "cruzamento_tabela_b"];
      const sheetInfo: { name: string; rows: number; columns: string[] }[] = [];

      for (let s = 0; s < 2; s++) {
        const sheetName = wb.SheetNames[s];
        const sheet = wb.Sheets[sheetName];
        const rows: any[] = XLSX.utils.sheet_to_json(sheet, { header: 1 });

        if (rows.length === 0) {
          sheetInfo.push({ name: sheetName, rows: 0, columns: [] });
          continue;
        }

        // Primeira linha = cabeçalhos
        const headers = (rows[0] as any[]).map((h: any) =>
          h != null ? String(h) : "",
        );
        const dataRows = rows.slice(1);
        const maxCols = Math.min(54, headers.length);

        // Inserir dados
        let inserted = 0;
        for (let r = 0; r < dataRows.length; r++) {
          const row = dataRows[r] as any[];
          if (
            !row ||
            row.every((c: any) => c == null || String(c).trim() === "")
          )
            continue;

          const colNames: string[] = ["cruzamento_upload_id", "row_number"];
          const vals: any[] = [uploadId, r + 1];
          const placeholders: string[] = ["$1", "$2"];
          let pi = 3;

          for (let c = 0; c < maxCols; c++) {
            colNames.push(colNameForIndex(c));
            vals.push(row[c] != null ? String(row[c]) : null);
            placeholders.push(`$${pi++}`);
          }

          // raw_data
          const rawObj: any = {};
          for (let c = 0; c < row.length; c++) {
            rawObj[headers[c] || `Col${c}`] = row[c];
          }
          colNames.push("raw_data");
          vals.push(JSON.stringify(rawObj));
          placeholders.push(`$${pi++}`);

          await client.query(
            `INSERT INTO ${tables[s]} (${colNames.join(", ")}) VALUES (${placeholders.join(", ")})`,
            vals,
          );
          inserted++;
        }

        sheetInfo.push({ name: sheetName, rows: inserted, columns: headers });
      }

      await client.query("COMMIT");

      return res.status(200).json({
        success: true,
        message: `Arquivo processado: ${sheetInfo.map((s) => `${s.name} (${s.rows} linhas)`).join(" + ")}`,
        uploadId,
        sheets: sheetInfo,
      });
    } catch (error: any) {
      await client.query("ROLLBACK");
      return res.status(500).json({ error: error.message });
    } finally {
      client.release();
    }
  },
);

/**
 * GET /api/cruzamento/status
 * Retorna info do último upload de cruzamento
 */
router.get("/cruzamento/status", async (_req: Request, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT cu.*,
              (SELECT COUNT(*) FROM cruzamento_tabela_a WHERE cruzamento_upload_id = cu.id) as rows_a,
              (SELECT COUNT(*) FROM cruzamento_tabela_b WHERE cruzamento_upload_id = cu.id) as rows_b
       FROM cruzamento_uploads cu ORDER BY cu.id DESC LIMIT 1`,
    );
    if (result.rows.length === 0) {
      return res.json({ success: true, hasData: false });
    }
    const u = result.rows[0];
    return res.json({
      success: true,
      hasData: true,
      upload: {
        id: u.id,
        originalName: u.original_name,
        uploadDate: u.upload_date,
        sheetNames: u.sheet_names,
        rowsA: parseInt(u.rows_a),
        rowsB: parseInt(u.rows_b),
      },
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/cruzamento/tabela/:side
 * Retorna dados da tabela A ou B  (side = 'a' | 'b')
 */
router.get("/cruzamento/tabela/:side", async (req: Request, res: Response) => {
  try {
    const side = (req.params.side as string)?.toLowerCase();
    if (side !== "a" && side !== "b") {
      return res.status(400).json({ error: "Use /tabela/a ou /tabela/b" });
    }

    const tableName =
      side === "a" ? "cruzamento_tabela_a" : "cruzamento_tabela_b";
    const limit = parseInt(req.query.limit as string) || 100;
    const offset = parseInt(req.query.offset as string) || 0;

    const countRes = await pool.query(
      `SELECT COUNT(*) as total FROM ${tableName}`,
    );
    const total = parseInt(countRes.rows[0].total);

    const dataRes = await pool.query(
      `SELECT * FROM ${tableName} ORDER BY row_number LIMIT $1 OFFSET $2`,
      [limit, offset],
    );

    return res.json({ success: true, data: dataRes.rows, total });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/cruzamento/colunas/:side
 * Retorna nomes das colunas da tabela A ou B
 */
router.get("/cruzamento/colunas/:side", async (req: Request, res: Response) => {
  try {
    const side = (req.params.side as string)?.toLowerCase();
    if (side !== "a" && side !== "b") {
      return res.status(400).json({ error: "Use /colunas/a ou /colunas/b" });
    }

    // Pegar headers do primeiro row de raw_data
    const tableName =
      side === "a" ? "cruzamento_tabela_a" : "cruzamento_tabela_b";
    const result = await pool.query(
      `SELECT raw_data FROM ${tableName} ORDER BY row_number LIMIT 1`,
    );

    if (result.rows.length === 0) {
      return res.json({ success: true, columns: [] });
    }

    const rawData =
      typeof result.rows[0].raw_data === "string"
        ? JSON.parse(result.rows[0].raw_data)
        : result.rows[0].raw_data;

    const keys = Object.keys(rawData);
    const columns = keys.map((name, i) => {
      let letter = "";
      let num = i;
      while (num >= 0) {
        letter = String.fromCharCode(65 + (num % 26)) + letter;
        num = Math.floor(num / 26) - 1;
      }
      return { letter, name };
    });

    return res.json({ success: true, columns });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/cruzamento/cruzar
 * Executa o cruzamento: INNER JOIN tabela_a com tabela_b pelo código (col_a)
 * Resultado: código, nome_evento (de A), natureza (de A), FGTS/INSS/IRRF (de B)
 * Só entram códigos que existem em tabela_a
 */
router.post("/cruzamento/cruzar", async (_req: Request, res: Response) => {
  const client = await pool.connect();
  try {
    // Verificar se há dados
    const uploadRes = await client.query(
      "SELECT id FROM cruzamento_uploads ORDER BY id DESC LIMIT 1",
    );
    if (uploadRes.rows.length === 0) {
      return res
        .status(400)
        .json({ error: "Nenhum upload encontrado. Envie o arquivo primeiro." });
    }
    const uploadId = uploadRes.rows[0].id;

    // Primeiro, descobre qual chave do raw_data tem FGTS, INSS, IRRF na tabela_b
    const sampleRes = await client.query(
      "SELECT raw_data FROM cruzamento_tabela_b LIMIT 1",
    );
    if (sampleRes.rows.length === 0) {
      await client.query("ROLLBACK");
      return res.status(400).json({ error: "Tabela B está vazia." });
    }

    const rawSample =
      typeof sampleRes.rows[0].raw_data === "string"
        ? JSON.parse(sampleRes.rows[0].raw_data)
        : sampleRes.rows[0].raw_data;

    const rawKeys = Object.keys(rawSample);
    const findKey = (pattern: string) =>
      rawKeys.find((k) => k.toLowerCase().includes(pattern)) || "";

    const fgtsKey = findKey("fgts");
    const inssKey = findKey("inss");
    const irrfKey = findKey("irrf");

    await client.query("BEGIN");

    // Limpar resultado anterior
    await client.query("DELETE FROM cruzamento_resultado");

    // INNER JOIN: tabela_a (natureza) × tabela_b (impostos) pelo código
    // Extrai FGTS/INSS/IRRF do raw_data JSONB pela chave do header (ignora posição da coluna)
    const joinQuery = `
      INSERT INTO cruzamento_resultado 
        (cruzamento_upload_id, codigo, nome_evento, natureza_esocial, cod_inss, cod_irrf, cod_fgts, row_number)
      SELECT 
        $1,
        TRIM(a.col_a),
        a.col_b,
        a.col_c,
        b.raw_data->>$2,
        b.raw_data->>$3,
        b.raw_data->>$4,
        ROW_NUMBER() OVER (ORDER BY CAST(TRIM(a.col_a) AS INTEGER))
      FROM cruzamento_tabela_a a
      INNER JOIN cruzamento_tabela_b b ON TRIM(a.col_a) = TRIM(b.col_a)
      ORDER BY CAST(TRIM(a.col_a) AS INTEGER)
    `;

    const result = await client.query(joinQuery, [
      uploadId,
      inssKey,
      irrfKey,
      fgtsKey,
    ]);

    await client.query("COMMIT");

    return res.json({
      success: true,
      message: `Cruzamento concluído: ${result.rowCount} registros na tabela final`,
      total: result.rowCount,
    });
  } catch (error: any) {
    await client.query("ROLLBACK");
    return res.status(500).json({ error: error.message });
  } finally {
    client.release();
  }
});

/**
 * GET /api/cruzamento/resultado
 * Retorna dados do cruzamento final com paginação
 */
router.get("/cruzamento/resultado", async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 100;
    const offset = parseInt(req.query.offset as string) || 0;

    const countRes = await pool.query(
      "SELECT COUNT(*) as total FROM cruzamento_resultado",
    );
    const total = parseInt(countRes.rows[0].total);

    if (total === 0) {
      return res.json({ success: true, data: [], total: 0, hasData: false });
    }

    const dataRes = await pool.query(
      "SELECT codigo, nome_evento, natureza_esocial, cod_inss, cod_irrf, cod_fgts FROM cruzamento_resultado ORDER BY row_number LIMIT $1 OFFSET $2",
      [limit, offset],
    );

    return res.json({
      success: true,
      data: dataRes.rows,
      total,
      hasData: true,
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/cruzamento/salvar-em-tabelas
 * Copia cruzamento_resultado para tabela_cruzamento (formato col_a..col_f)
 * para que apareça no visualizador de tabelas
 */
router.post(
  "/cruzamento/salvar-em-tabelas",
  async (_req: Request, res: Response) => {
    const client = await pool.connect();
    try {
      const countRes = await client.query(
        "SELECT COUNT(*) as total FROM cruzamento_resultado",
      );
      if (parseInt(countRes.rows[0].total) === 0) {
        return res.status(400).json({
          error:
            "Nenhum cruzamento para salvar. Execute o cruzamento primeiro.",
        });
      }

      await client.query("BEGIN");
      await client.query("DELETE FROM tabela_cruzamento");

      const insertQuery = `
        INSERT INTO tabela_cruzamento (row_number, col_a, col_b, col_c, col_d, col_e, col_f, raw_data)
        SELECT 
          row_number,
          codigo,
          nome_evento,
          natureza_esocial,
          cod_inss,
          cod_irrf,
          cod_fgts,
          jsonb_build_object(
            'Código', codigo,
            'Nome Evento', nome_evento,
            'Natureza E-social', natureza_esocial,
            'Cód. INSS', cod_inss,
            'Cód. IRRF', cod_irrf,
            'Cód. FGTS', cod_fgts
          )
        FROM cruzamento_resultado
        ORDER BY row_number
      `;

      const result = await client.query(insertQuery);
      await client.query("COMMIT");

      return res.json({
        success: true,
        message: `${result.rowCount} registros salvos na aba de tabelas`,
        total: result.rowCount,
      });
    } catch (error: any) {
      await client.query("ROLLBACK");
      return res.status(500).json({ error: error.message });
    } finally {
      client.release();
    }
  },
);

/**
 * POST /cruzamento/reset
 * Limpa todas as tabelas de cruzamento para começar do zero
 */
router.post("/cruzamento/reset", async (_req: Request, res: Response) => {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("TRUNCATE cruzamento_resultado");
    await client.query("TRUNCATE cruzamento_tabela_a");
    await client.query("TRUNCATE cruzamento_tabela_b");
    await client.query("DELETE FROM cruzamento_uploads");
    await client.query("COMMIT");
    return res.json({
      success: true,
      message: "Cruzamento resetado. Envie um novo arquivo.",
    });
  } catch (error: any) {
    await client.query("ROLLBACK");
    return res.status(500).json({ error: error.message });
  } finally {
    client.release();
  }
});

export default router;
