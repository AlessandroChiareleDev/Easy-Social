import pool from "../config/database";
import { DIRFParser } from "./dirf-parser";
import fs from "fs";

/** Whitelist of allowed table names to prevent SQL injection */
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
    const client = await pool.connect();
    try {
      const params: any[] = [limit, offset];
      let whereClause = "";

      if (filters.length > 0) {
        const conditions = filters.map((f, i) => {
          params.push(`%${f.value}%`);
          return `CAST(${f.column} AS TEXT) ILIKE $${i + 3}`;
        });
        whereClause = ` WHERE ${conditions.join(" AND ")}`;
      }

      const query = `SELECT * FROM ${tableName}${whereClause} LIMIT $1 OFFSET $2`;
      const result = await client.query(query, params);
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
    const client = await pool.connect();
    try {
      const params: any[] = [];
      let whereClause = "";

      if (filters.length > 0) {
        const conditions = filters.map((f, i) => {
          params.push(`%${f.value}%`);
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
   * Retorna as colunas com letra e nome real do Excel
   */
  async getColumnNames(tableName: string) {
    validateTableName(tableName);

    const tableNameToSheet: { [key: string]: string } = {
      analise_natureza: "ANALISE NATUREZA",
      analise_natureza_certo: "ANALISE NATUREZA",
      dinamica: "Dinamica",
      tabela_eventos_gl: "Tabela Eventos GI",
      tabela_eb: "Tabela EB",
      tabela_cruzamento: "__cruzamento__",
      tabela3_esocial_oficial: "__tabela3_oficial__",
    };

    const sheetName = tableNameToSheet[tableName];
    const client = await pool.connect();
    try {
      // tabela_cruzamento: hardcoded headers matching col_a..col_f mapping
      if (sheetName === "__cruzamento__") {
        return [
          { letter: "A", name: "Código" },
          { letter: "B", name: "Nome Evento" },
          { letter: "C", name: "Natureza E-social" },
          { letter: "D", name: "Cód. INSS" },
          { letter: "E", name: "Cód. IRRF" },
          { letter: "F", name: "Cód. FGTS" },
        ];
      }

      // tabela3_esocial_oficial: hardcoded headers
      if (sheetName === "__tabela3_oficial__") {
        return [
          { letter: "A", name: "Código" },
          { letter: "B", name: "Nome" },
          { letter: "C", name: "Dt Início" },
          { letter: "D", name: "Dt Fim" },
          { letter: "E", name: "Descrição" },
          { letter: "F", name: "Incid. Exclusiva Empregado" },
        ];
      }

      const result = await client.query(
        `SELECT analysis_data FROM uploads ORDER BY id DESC LIMIT 1`,
      );
      if (result.rows.length === 0) return [];

      const analysisData =
        typeof result.rows[0].analysis_data === "string"
          ? JSON.parse(result.rows[0].analysis_data)
          : result.rows[0].analysis_data;

      const tableInfo = analysisData.tables.find(
        (t: any) => t.name === sheetName || t.sheetName === sheetName,
      );
      if (!tableInfo) return [];

      const count = Math.min(54, tableInfo.columns.length);
      const columns = [];
      for (let i = 0; i < count; i++) {
        // Generate Excel-style letter: 0→A, 25→Z, 26→AA, 53→BB
        let letter = "";
        let num = i;
        while (num >= 0) {
          letter = String.fromCharCode(65 + (num % 26)) + letter;
          num = Math.floor(num / 26) - 1;
        }
        columns.push({
          letter,
          name:
            tableInfo.columns[i] != null
              ? String(tableInfo.columns[i])
              : `Col ${letter}`,
        });
      }
      return columns;
    } finally {
      client.release();
    }
  }
}
