import pool from "../config/database";
import { DIRFParser } from "./dirf-parser";
import fs from "fs";

/** Whitelist of allowed table names to prevent SQL injection */
const ALLOWED_TABLES = [
  "cruzamento_eb",
  "rubrica_corrections",
  "esocial_depara",
  "eb_skills_base_legal",
  "esocial_envios",
  "tabela3_esocial_oficial",
  "tabela_marcos",
];

/** System columns to exclude from display */
const SYSTEM_COLUMNS = new Set([
  "id",
  "upload_id",
  "row_number",
  "raw_data",
  "created_at",
  "updated_at",
]);

/** Cache: column info per table (null = not yet detected) */
const _colInfoCache: Record<string, { names: string[]; needsRemap: boolean }> =
  {};

function validateTableName(tableName: string): void {
  if (!ALLOWED_TABLES.includes(tableName)) {
    throw new Error(`Tabela "${tableName}" não é permitida`);
  }
}

/**
 * Converts 0-based index to column name: 0→col_a, 25→col_z, 26→col_aa, 53→col_bb
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
 * Convert col_a key to 0-based index: col_a→0, col_b→1, col_z→25, col_aa→26
 */
function colKeyToIndex(colKey: string): number {
  const letters = colKey.replace("col_", "");
  let index = 0;
  for (let i = 0; i < letters.length; i++) {
    index = index * 26 + (letters.charCodeAt(i) - 96);
  }
  return index - 1;
}

/**
 * Converts 0-based index to uppercase Excel letter: 0→A, 25→Z, 26→AA
 */
function indexToLetter(i: number): string {
  let letter = "";
  let num = i;
  while (num >= 0) {
    letter = String.fromCharCode(65 + (num % 26)) + letter;
    num = Math.floor(num / 26) - 1;
  }
  return letter;
}

/**
 * Detect displayable columns for a table from information_schema.
 * needsRemap=true means the table has real column names (not col_a pattern)
 * and data must be remapped to col_a format for the frontend.
 */
async function detectDisplayColumns(
  tableName: string,
): Promise<{ names: string[]; needsRemap: boolean }> {
  if (_colInfoCache[tableName]) return _colInfoCache[tableName];
  const client = await pool.connect();
  try {
    const result = await client.query(
      `SELECT column_name FROM information_schema.columns
       WHERE table_schema = 'public' AND table_name = $1
       ORDER BY ordinal_position`,
      [tableName],
    );
    const allCols: string[] = result.rows.map((r: any) => r.column_name);
    const colPatternCols = allCols.filter((c) => /^col_[a-z]{1,2}$/.test(c));

    let info: { names: string[]; needsRemap: boolean };
    if (colPatternCols.length > 0) {
      // Table uses col_a, col_b, ... format — no remapping needed
      info = { names: colPatternCols, needsRemap: false };
    } else {
      // Table has real column names — must remap to col_a for frontend
      const displayCols = allCols.filter((c) => !SYSTEM_COLUMNS.has(c));
      info = { names: displayCols, needsRemap: true };
    }

    _colInfoCache[tableName] = info;
    return info;
  } finally {
    client.release();
  }
}

export class DatabaseService {
  /**
   * Insere dados normalizados no PostgreSQL
   */
  async insertNormalizedData(uploadId: number, filePath: string) {
    const parser = new DIRFParser(filePath);
    const analysis = await parser.analyzeDIRF();

    const tableMapping: { [key: string]: string } = {
      "ANALISE NATUREZA": "analise_natureza",
      Dinamica: "dinamica",
      "Tabela Eventos GI": "tabela_eventos_gl",
      "Tabela EB": "tabela_eb",
    };

    const client = await pool.connect();
    try {
      await client.query("BEGIN");

      for (const table of analysis.tables) {
        const tableName = tableMapping[table.name];
        if (!tableName) continue;

        const data = await parser.extractTableData(table.name);
        await this.insertTableData(
          client,
          uploadId,
          tableName,
          data,
          table.columnLetters,
        );
      }

      await client.query("COMMIT");
      console.log(
        `\u2705 Transaction conclu\u00edda com sucesso para upload ${uploadId}`,
      );

      // Remover o arquivo após o processamento bem-sucedido
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    } catch (error) {
      await client.query("ROLLBACK");
      console.error(
        `\u274c ROLLBACK completo - nenhum dado foi salvo. Arquivo mantido: ${filePath}`,
        error,
      );
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Insere dados de uma tabela específica
   */
  private async insertTableData(
    client: any,
    uploadId: number,
    tableName: string,
    data: any[],
    columnLetters: string[],
  ) {
    validateTableName(tableName);

    const BATCH_SIZE = 500;
    let inserted = 0;

    try {
      for (
        let batchStart = 0;
        batchStart < data.length;
        batchStart += BATCH_SIZE
      ) {
        const batch = data.slice(batchStart, batchStart + BATCH_SIZE);

        // Construir INSERT em lote com múltiplos VALUES (até 54 colunas: col_a a col_bb)
        const MAX_COLS = 54;
        const colCount = Math.min(MAX_COLS, columnLetters.length);
        const colNames = ["upload_id", "row_number", "raw_data"];
        for (let c = 0; c < colCount; c++) {
          colNames.push(colNameForIndex(c));
        }

        const allValues: any[] = [];
        const rowPlaceholders: string[] = [];
        const paramsPerRow = colNames.length;

        for (let i = 0; i < batch.length; i++) {
          const row = batch[i];
          const rowNumber = batchStart + i + 1;
          const base = i * paramsPerRow;
          const ph: string[] = [];

          allValues.push(uploadId, rowNumber, JSON.stringify(row));
          ph.push(`$${base + 1}`, `$${base + 2}`, `$${base + 3}`);

          for (let c = 0; c < colCount; c++) {
            const colLetter = columnLetters[c];
            let colValue = row[colLetter];
            if (colValue === undefined) {
              const originalColumnName = Object.keys(row)[c];
              colValue = row[originalColumnName];
            }
            allValues.push(colValue != null ? String(colValue) : null);
            ph.push(`$${base + 4 + c}`);
          }

          rowPlaceholders.push(`(${ph.join(", ")})`);
        }

        const query = `INSERT INTO ${tableName} (${colNames.join(", ")}) VALUES ${rowPlaceholders.join(", ")}`;
        await client.query(query, allValues);

        inserted += batch.length;
        if (data.length > BATCH_SIZE) {
          console.log(
            `  ⏳ ${tableName}: ${inserted}/${data.length} linhas inseridas`,
          );
        }
      }

      console.log(`✅ Dados inseridos em ${tableName}: ${inserted} linhas`);
    } catch (error: any) {
      console.error(`❌ Erro ao inserir dados em ${tableName}:`, error);
      throw error;
    }
  }

  /**
   * Recupera dados de uma tabela
   */
  async getTableData(
    tableName: string,
    limit: number = 100,
    offset: number = 0,
    filters: { column: string; value: string }[] = [],
  ) {
    validateTableName(tableName);
    const colInfo = await detectDisplayColumns(tableName);
    const client = await pool.connect();
    try {
      const params: any[] = [limit, offset];
      let whereClause = "";

      if (filters.length > 0) {
        const conditions = filters.map((f, i) => {
          params.push(`%${f.value}%`);
          if (colInfo.needsRemap) {
            // Map col_a → real column name for WHERE clause
            const idx = colKeyToIndex(f.column);
            const realCol = colInfo.names[idx];
            if (!realCol) return "TRUE";
            return `CAST("${realCol}" AS TEXT) ILIKE $${i + 3}`;
          }
          return `CAST(${f.column} AS TEXT) ILIKE $${i + 3}`;
        });
        whereClause = ` WHERE ${conditions.join(" AND ")}`;
      }

      const query = `SELECT * FROM ${tableName}${whereClause} LIMIT $1 OFFSET $2`;
      const result = await client.query(query, params);

      if (colInfo.needsRemap) {
        // Transform real column names → col_a, col_b, ... for frontend
        return result.rows.map((row: any) => {
          const mapped: any = {};
          colInfo.names.forEach((realCol, i) => {
            mapped[colNameForIndex(i)] = row[realCol];
          });
          return mapped;
        });
      }

      return result.rows;
    } finally {
      client.release();
    }
  }

  /**
   * Conta total de registros em uma tabela
   */
  async getTableCount(
    tableName: string,
    filters: { column: string; value: string }[] = [],
  ) {
    validateTableName(tableName);
    const colInfo = await detectDisplayColumns(tableName);
    const client = await pool.connect();
    try {
      const params: any[] = [];
      let whereClause = "";

      if (filters.length > 0) {
        const conditions = filters.map((f, i) => {
          params.push(`%${f.value}%`);
          if (colInfo.needsRemap) {
            const idx = colKeyToIndex(f.column);
            const realCol = colInfo.names[idx];
            if (!realCol) return "TRUE";
            return `CAST("${realCol}" AS TEXT) ILIKE $${i + 1}`;
          }
          return `CAST(${f.column} AS TEXT) ILIKE $${i + 1}`;
        });
        whereClause = ` WHERE ${conditions.join(" AND ")}`;
      }

      const query = `SELECT COUNT(*) as count FROM ${tableName}${whereClause}`;
      const result = await client.query(query, params);
      return result.rows[0].count;
    } finally {
      client.release();
    }
  }

  /**
   * Retorna as colunas com letra e nome para o frontend
   */
  async getColumnNames(tableName: string) {
    validateTableName(tableName);

    // Hardcoded headers for known tables
    const hardcoded: Record<string, { letter: string; name: string }[]> = {
      tabela3_esocial_oficial: [
        { letter: "A", name: "Código" },
        { letter: "B", name: "Nome" },
        { letter: "C", name: "Dt Início" },
        { letter: "D", name: "Dt Fim" },
        { letter: "E", name: "Descrição" },
        { letter: "F", name: "Incid. Exclusiva Empregado" },
      ],
      eb_skills_base_legal: [
        { letter: "A", name: "Código" },
        { letter: "B", name: "Nome Rubrica" },
        { letter: "C", name: "Natureza eSocial" },
        { letter: "D", name: "Cód. INSS" },
        { letter: "E", name: "Cód. IRRF" },
        { letter: "F", name: "Cód. FGTS" },
        { letter: "G", name: "Observação" },
        { letter: "H", name: "Base Legal INSS" },
        { letter: "I", name: "Base Legal IRRF" },
        { letter: "J", name: "Base Legal FGTS" },
      ],
    };

    if (hardcoded[tableName]) return hardcoded[tableName];

    // Auto-detect columns from database
    const colInfo = await detectDisplayColumns(tableName);
    return colInfo.names.map((colName, i) => ({
      letter: indexToLetter(i),
      name: colInfo.needsRemap
        ? colName
        : colName.replace(/^col_/, "").toUpperCase(),
    }));
  }
}
