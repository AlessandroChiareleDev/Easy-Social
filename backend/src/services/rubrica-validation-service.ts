import pool from "../config/database";

export interface Divergencia {
  id: number;
  tabela_eb_id: number;
  cod_rubrica: string;
  descricao: string;
  inss_antes: string;
  irrf_antes: string;
  fgts_antes: string;
  inss_correto: string;
  irrf_correto: string;
  fgts_correto: string;
  status: string;
  corrigido_em: string | null;
  observacao: string | null;
}

export interface ResumoValidacao {
  total_rubricas: number;
  total_divergentes: number;
  total_pendentes: number;
  total_corrigidas: number;
  total_verificadas: number;
}

/**
 * Extrai o código numérico do início de um valor como "11 - Artigo 28..."
 * Handles both regular space and non-breaking space (\u00A0) after the dash.
 */
function extractCode(fullText: string | null): string {
  if (!fullText) return "";
  const trimmed = fullText.trim();
  // Match " - " or " -\u00A0" (non-breaking space from Excel encoding)
  const match = trimmed.match(/^(.+?)\s-[\s\u00A0]/);
  if (match) {
    return match[1].trim();
  }
  return trimmed;
}

export class RubricaValidationService {
  /**
   * Detecta divergências comparando D/E/F vs códigos extraídos de H/I/J
   * e popula a tabela rubrica_corrections
   */
  async detectarDivergencias(): Promise<{
    inseridas: number;
    total: number;
    divergentes: number;
  }> {
    const client = await pool.connect();
    try {
      // Buscar todas as rubricas da Tabela EB
      const result = await client.query(
        `SELECT id, col_a, col_b, col_d, col_e, col_f, col_h, col_i, col_j
         FROM tabela_eb
         ORDER BY id`,
      );

      const rows = result.rows;
      let divergentes = 0;
      let inseridas = 0;

      // Limpar correções existentes com status 'pendente' para re-análise
      // (mantém as que já foram corrigidas/verificadas)
      await client.query(
        `DELETE FROM rubrica_corrections WHERE status = 'pendente'`,
      );

      for (const row of rows) {
        const codD = (row.col_d || "").trim();
        const codE = (row.col_e || "").trim();
        const codF = (row.col_f || "").trim();

        const codH = extractCode(row.col_h);
        const codI = extractCode(row.col_i);
        const codJ = extractCode(row.col_j);

        const inssDiv = codD !== codH;
        const irrfDiv = codE !== codI;
        const fgtsDiv = codF !== codJ;

        if (inssDiv || irrfDiv || fgtsDiv) {
          divergentes++;

          // Verificar se já existe correção corrigida/verificada para esta rubrica
          const existing = await client.query(
            `SELECT id FROM rubrica_corrections
             WHERE tabela_eb_id = $1 AND status IN ('corrigido', 'verificado')`,
            [row.id],
          );

          if (existing.rows.length === 0) {
            await client.query(
              `INSERT INTO rubrica_corrections
               (tabela_eb_id, cod_rubrica, descricao, inss_antes, irrf_antes, fgts_antes, inss_correto, irrf_correto, fgts_correto, status)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'pendente')`,
              [
                row.id,
                row.col_a || "",
                row.col_b || "",
                codD,
                codE,
                codF,
                codH,
                codI,
                codJ,
              ],
            );
            inseridas++;
          }
        }
      }

      return { inseridas, total: rows.length, divergentes };
    } finally {
      client.release();
    }
  }

  /**
   * Retorna resumo geral da validação
   */
  async getResumo(): Promise<ResumoValidacao> {
    const client = await pool.connect();
    try {
      const totalResult = await client.query(
        `SELECT COUNT(*) as count FROM tabela_eb`,
      );
      const total_rubricas = parseInt(totalResult.rows[0].count);

      const statsResult = await client.query(
        `SELECT
           COUNT(*) as total,
           COUNT(*) FILTER (WHERE status = 'pendente') as pendentes,
           COUNT(*) FILTER (WHERE status = 'corrigido') as corrigidas,
           COUNT(*) FILTER (WHERE status = 'verificado') as verificadas
         FROM rubrica_corrections`,
      );

      const stats = statsResult.rows[0];

      return {
        total_rubricas,
        total_divergentes: parseInt(stats.total),
        total_pendentes: parseInt(stats.pendentes),
        total_corrigidas: parseInt(stats.corrigidas),
        total_verificadas: parseInt(stats.verificadas),
      };
    } finally {
      client.release();
    }
  }

  /**
   * Retorna lista de divergências com paginação e filtro por status
   */
  async getDivergencias(
    status?: string,
    limit: number = 50,
    offset: number = 0,
  ): Promise<{ data: Divergencia[]; total: number }> {
    const client = await pool.connect();
    try {
      const allowedStatuses = ["pendente", "corrigido", "verificado"];
      let whereClause = "";
      const params: any[] = [];

      if (status && allowedStatuses.includes(status)) {
        whereClause = "WHERE rc.status = $1";
        params.push(status);
      }

      const countQuery = `SELECT COUNT(*) as count FROM rubrica_corrections rc ${whereClause}`;
      const countResult = await client.query(countQuery, params);
      const total = parseInt(countResult.rows[0].count);

      const dataParams = [...params];
      const limitIdx = dataParams.length + 1;
      const offsetIdx = dataParams.length + 2;
      dataParams.push(limit, offset);

      const dataQuery = `
        SELECT rc.*, eb.col_h, eb.col_i, eb.col_j
        FROM rubrica_corrections rc
        JOIN tabela_eb eb ON eb.id = rc.tabela_eb_id
        ${whereClause}
        ORDER BY rc.cod_rubrica::int, rc.id
        LIMIT $${limitIdx} OFFSET $${offsetIdx}
      `;

      const dataResult = await client.query(dataQuery, dataParams);

      return { data: dataResult.rows, total };
    } finally {
      client.release();
    }
  }

  /**
   * Retorna a próxima rubrica pendente para correção (wizard step-by-step)
   */
  async getProximaPendente(): Promise<Divergencia | null> {
    const client = await pool.connect();
    try {
      const result = await client.query(
        `SELECT rc.*, eb.col_h, eb.col_i, eb.col_j
         FROM rubrica_corrections rc
         JOIN tabela_eb eb ON eb.id = rc.tabela_eb_id
         WHERE rc.status = 'pendente'
         ORDER BY rc.cod_rubrica::int, rc.id
         LIMIT 1`,
      );

      return result.rows.length > 0 ? result.rows[0] : null;
    } finally {
      client.release();
    }
  }

  /**
   * Marca uma correção como realizada
   */
  async marcarCorrigido(
    id: number,
    observacao?: string,
  ): Promise<Divergencia | null> {
    const client = await pool.connect();
    try {
      const result = await client.query(
        `UPDATE rubrica_corrections
         SET status = 'corrigido', corrigido_em = NOW(), observacao = $2
         WHERE id = $1
         RETURNING *`,
        [id, observacao || null],
      );

      return result.rows.length > 0 ? result.rows[0] : null;
    } finally {
      client.release();
    }
  }

  /**
   * Marca como verificado (validação final: estado no eSocial = H/I/J)
   */
  async marcarVerificado(id: number): Promise<Divergencia | null> {
    const client = await pool.connect();
    try {
      const result = await client.query(
        `UPDATE rubrica_corrections
         SET status = 'verificado'
         WHERE id = $1
         RETURNING *`,
        [id],
      );

      return result.rows.length > 0 ? result.rows[0] : null;
    } finally {
      client.release();
    }
  }

  /**
   * Reseta uma correção de volta para 'pendente'
   */
  async resetarCorrecao(id: number): Promise<Divergencia | null> {
    const client = await pool.connect();
    try {
      const result = await client.query(
        `UPDATE rubrica_corrections
         SET status = 'pendente', corrigido_em = NULL, observacao = NULL
         WHERE id = $1
         RETURNING *`,
        [id],
      );

      return result.rows.length > 0 ? result.rows[0] : null;
    } finally {
      client.release();
    }
  }
}
