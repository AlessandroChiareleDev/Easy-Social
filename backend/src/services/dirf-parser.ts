import XLSX from "xlsx";
import fs from "fs";
import path from "path";

interface TableInfo {
  name: string;
  sheetName: string;
  rowCount: number;
  columnCount: number;
  columns: string[];
  columnLetters: string[]; // A, B, C, D, E, F, etc.
}

interface DIRFAnalysis {
  fileName: string;
  fileSize: number;
  tables: TableInfo[];
  totalSheets: number;
  analysisDate: string;
  uploadId?: number;
  filePath?: string;
}

export class DIRFParser {
  private filePath: string;
  private workbook: XLSX.WorkBook | null = null;

  constructor(filePath: string) {
    this.filePath = filePath;
  }

  /**
   * Lê o arquivo DIRF.xlsx e retorna análise completa
   */
  async analyzeDIRF(): Promise<DIRFAnalysis> {
    try {
      // Ler arquivo
      const fileBuffer = fs.readFileSync(this.filePath);
      this.workbook = XLSX.read(fileBuffer, {
        cellFormula: false,
        cellStyles: false,
      });

      // Mapear tabelas esperadas (4 tabelas ativas)
      const expectedTables = [
        "ANALISE NATUREZA",
        "Dinamica",
        "Tabela Eventos GI",
        "Tabela EB",
      ];

      const tables: TableInfo[] = [];

      for (const tableName of expectedTables) {
        const sheet = this.workbook.Sheets[tableName];
        if (sheet) {
          const tableInfo = this.extractTableInfo(sheet, tableName);
          tables.push(tableInfo);
        }
      }

      const fileStats = fs.statSync(this.filePath);

      return {
        fileName: path.basename(this.filePath),
        fileSize: fileStats.size,
        tables,
        totalSheets: this.workbook.SheetNames.length,
        analysisDate: new Date().toISOString(),
        filePath: this.filePath,
      };
    } catch (error: any) {
      throw new Error(`Erro ao analisar DIRF.xlsx: ${error.message}`);
    }
  }

  /**
   * Extrai informações de uma tabela específica
   */
  private extractTableInfo(
    sheet: XLSX.WorkSheet,
    tableName: string,
  ): TableInfo {
    const range = XLSX.utils.decode_range(sheet["!ref"] || "A1");
    const rowCount = range.e.r + 1;
    const columnCount = range.e.c + 1;

    // Gerar referências de letras (A, B, C, D, E, F, etc.)
    const columnLetters = this.generateColumnLetters(columnCount);

    // Extrair nomes das colunas (primeira linha)
    const firstRow = XLSX.utils.sheet_to_json(sheet, {
      header: 1,
    })[0] as string[];
    const columns = firstRow ? firstRow.slice(0, columnCount) : columnLetters;

    return {
      name: tableName,
      sheetName: tableName,
      rowCount,
      columnCount,
      columns,
      columnLetters,
    };
  }

  /**
   * Gera referências de letras (A, B, C, ..., Z, AA, AB, etc.)
   */
  private generateColumnLetters(count: number): string[] {
    const letters: string[] = [];
    for (let i = 0; i < count; i++) {
      let letter = "";
      let num = i;
      while (num >= 0) {
        letter = String.fromCharCode(65 + (num % 26)) + letter;
        num = Math.floor(num / 26) - 1;
      }
      letters.push(letter);
    }
    return letters;
  }

  /**
   * Extrai dados de uma tabela específica
   */
  async extractTableData(tableName: string, limit?: number): Promise<any[]> {
    if (!this.workbook) {
      await this.analyzeDIRF();
    }

    const sheet = this.workbook!.Sheets[tableName];
    if (!sheet) {
      throw new Error(`Tabela ${tableName} não encontrada`);
    }

    const data = XLSX.utils.sheet_to_json(sheet);
    return limit ? data.slice(0, limit) : data;
  }
}
