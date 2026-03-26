import pool from "../config/database";
import { DIRFParser } from "./dirf-parser";
import fs from "fs";

/** Whitelist of allowed table names to prevent SQL injection */
const ALLOWED_TABLES = [
  "analise_natureza",
  "dinamica",
  "tabela_eventos_gl",
  "tabela_eb",
];

function validateTableName(tableName: string): void {
  if (!ALLOWED_TABLES.includes(tableName)) {
    throw new Error(`Tabela "${tableName}" não é permitida`);
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

        // Construir INSERT em lote com múltiplos VALUES
        const colCount = Math.min(10, columnLetters.length);
        const colNames = ["upload_id", "row_number", "raw_data"];
        for (let c = 0; c < colCount; c++) {
          colNames.push(`col_${String.fromCharCode(97 + c)}`);
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
  ) {
    validateTableName(tableName);
    const client = await pool.connect();
    try {
      const query = `SELECT * FROM ${tableName} LIMIT $1 OFFSET $2`;
      const result = await client.query(query, [limit, offset]);
      return result.rows;
    } finally {
      client.release();
    }
  }

  /**
   * Conta total de registros em uma tabela
   */
  async getTableCount(tableName: string) {
    validateTableName(tableName);
    const client = await pool.connect();
    try {
      const query = `SELECT COUNT(*) as count FROM ${tableName}`;
      const result = await client.query(query);
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
      dinamica: "Dinamica",
      tabela_eventos_gl: "Tabela Eventos GI",
      tabela_eb: "Tabela EB",
    };

    const sheetName = tableNameToSheet[tableName];
    const client = await pool.connect();
    try {
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

      const count = Math.min(10, tableInfo.columns.length);
      const columns = [];
      for (let i = 0; i < count; i++) {
        columns.push({
          letter: String.fromCharCode(65 + i),
          name:
            tableInfo.columns[i] != null
              ? String(tableInfo.columns[i])
              : `Col ${String.fromCharCode(65 + i)}`,
        });
      }
      return columns;
    } finally {
      client.release();
    }
  }
}
