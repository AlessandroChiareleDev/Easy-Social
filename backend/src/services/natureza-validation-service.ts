import pool from "../config/database";

export interface RubricaComProblema {
  id: number;
  codigoevento: string;
  nome_evento: string;
  natureza_atual: string;
  natureza_codigo_atual: string;
  observacao: string | null;
  sugestao_col_f: string | null;
  natureza_nova: string | null;
  data_correcao: string | null;
}

export interface NaturezaSugerida {
  id: number;
  codigo: string;
  nome: string;
  descricao: string;
  data_inicio: string;
  data_fim: string | null;
  score: number;
  origem: "sugestao_humana" | "score" | "popular";
}

export interface ProgressoValidacao {
  total_verificar: number;
  total_corrigidas: number;
  total_pendentes: number;
  percentual: number;
}

// Stopwords para o algoritmo de matching
const STOPWORDS = new Set([
  "de",
  "do",
  "da",
  "dos",
  "das",
  "em",
  "no",
  "na",
  "nos",
  "nas",
  "por",
  "para",
  "com",
  "sem",
  "sob",
  "sobre",
  "entre",
  "até",
  "ao",
  "aos",
  "à",
  "às",
  "um",
  "uma",
  "uns",
  "umas",
  "o",
  "a",
  "os",
  "as",
  "e",
  "ou",
  "que",
  "se",
  "não",
  "mes",
  "mês",
  "anterior",
  "ref",
  "outros",
  "outras",
]);

/**
 * Dicionário de siglas/abreviações comuns em folha de pagamento.
 * Cada sigla expande para as palavras-chave que devem ser buscadas nas naturezas.
 */
const SIGLAS: Record<string, string[]> = {
  dsr: ["descanso", "semanal", "remunerado", "dsr"],
  dif: ["diferenca"],
  he: ["hora", "extra", "extraordinaria"],
  hs: ["hora", "extra", "extraordinaria"],
  cct: ["convencao", "coletiva"],
  act: ["acordo", "coletivo"],
  inss: ["previdencia", "social", "inss"],
  fgts: ["fgts", "garantia"],
  irrf: ["imposto", "renda", "irrf"],
  vt: ["transporte", "vale"],
  va: ["alimentacao", "vale"],
  vr: ["refeicao", "vale"],
  pat: ["alimentacao", "pat"],
  plr: ["lucros", "resultados", "participacao"],
  ppr: ["lucros", "resultados", "participacao"],
  desc: ["desconto"],
  dev: ["devolucao"],
  reemb: ["reembolso", "ressarcimento"],
  grat: ["gratificacao"],
  adic: ["adicional"],
  adc: ["adicional"],
  compl: ["complemento"],
  contrib: ["contribuicao"],
  sest: ["sest", "senat", "transporte"],
  senat: ["sest", "senat", "transporte"],
};

/**
 * Tokeniza um texto: lowercase, remove acentos, split, filtra stopwords.
 * Aceita tokens com 2+ caracteres para não descartar siglas (DSR, HE, VT etc).
 */
function tokenize(text: string): string[] {
  const normalized = text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "") // remove acentos
    // Colapsar abreviações pontilhadas: "D.S.R." → "DSR", "H.E." → "HE"
    .replace(/\b((?:[a-z]\.){2,})/gi, (match) => match.replace(/\./g, ""))
    .replace(/[^a-z0-9\s]/g, " ") // remove pontuação restante
    .trim();

  return normalized
    .split(/\s+/)
    .filter((t) => t.length >= 2 && !STOPWORDS.has(t));
}

/**
 * Expande tokens usando o dicionário de siglas.
 * Ex: ["dif", "dsr"] → ["dif", "diferenca", "dsr", "descanso", "semanal", "remunerado"]
 */
function expandTokens(tokens: string[]): string[] {
  const expanded = new Set(tokens);
  for (const token of tokens) {
    const synonyms = SIGLAS[token];
    if (synonyms) {
      for (const s of synonyms) expanded.add(s);
    }
  }
  return [...expanded];
}

export class NaturezaValidationService {
  /**
   * Lista rubricas com status "Verificar" na analise_natureza
   */
  async getRubricasComProblemas(
    limit: number = 50,
    offset: number = 0,
    apenaPendentes: boolean = true,
  ): Promise<{ data: RubricaComProblema[]; total: number }> {
    const whereExtra = apenaPendentes ? "AND cs.id IS NULL" : "";

    const countResult = await pool.query(
      `SELECT count(*) FROM analise_natureza a
       LEFT JOIN correcoes_staging cs ON cs.analise_natureza_id = a.id AND cs.status = 'pendente'
       WHERE UPPER(TRIM(a.col_d)) = 'VERIFICAR' ${whereExtra}`,
    );
    const total = parseInt(countResult.rows[0].count);

    const result = await pool.query(
      `SELECT a.id, a.col_a as codigoevento, a.col_b as nome_evento, 
              a.col_c as natureza_atual, a.col_e as observacao,
              a.col_f as sugestao_col_f,
              cs.natureza_nova_codigo || '-' || cs.natureza_nova_nome as natureza_nova,
              cs.criado_em as data_correcao,
              cs.usuario_nome
       FROM analise_natureza a
       LEFT JOIN correcoes_staging cs ON cs.analise_natureza_id = a.id AND cs.status = 'pendente'
       WHERE UPPER(TRIM(a.col_d)) = 'VERIFICAR' ${whereExtra}
       ORDER BY a.id
       LIMIT $1 OFFSET $2`,
      [limit, offset],
    );

    const data: RubricaComProblema[] = result.rows.map((row: any) => {
      const match = row.natureza_atual?.match(/^(\d+)/);
      return {
        id: row.id,
        codigoevento: row.codigoevento,
        nome_evento: row.nome_evento,
        natureza_atual: row.natureza_atual,
        natureza_codigo_atual: match ? match[1] : "",
        observacao: row.observacao,
        sugestao_col_f: row.sugestao_col_f,
        natureza_nova: row.natureza_nova,
        data_correcao: row.data_correcao,
      };
    });

    return { data, total };
  }

  /**
   * Extrai código(s) numérico(s) de natureza do texto livre da col_f
   * Exemplos:
   *   "Natureza da Rubrica sugerida - 1810 Transporte" → ["1810"]
   *   "1012 - Descanso semanal remunerado" → ["1012"]
   *   "Natureza 1299 encerrada... sujerida 1629 - Ressarcimento" → ["1629", "1299"]
   */
  /**
   * Extrai TODOS os códigos de 4 dígitos mencionados na col_f.
   * Retorna na ordem: "sugerida/sujerida" primeiro, depois os demais.
   */
  private extrairCodigosDaColF(colF: string): string[] {
    const sugeridos: string[] = [];
    const outros: string[] = [];

    // Padrão: "sugerida XXXX" ou "sujerida XXXX" ou "sujerido XXXX"
    const sugeridaMatch = colF.match(/sujer?id[ao]\s*-?\s*(\d{4})/gi);
    if (sugeridaMatch) {
      for (const m of sugeridaMatch) {
        const num = m.match(/(\d{4})/);
        if (num) sugeridos.push(num[1]);
      }
    }

    // Pegar TODOS os códigos de 4 dígitos (incluindo os mencionados como "inativado")
    const todos = colF.match(/\b(\d{4})\b/g);
    if (todos) {
      for (const c of todos) {
        if (!sugeridos.includes(c)) outros.push(c);
      }
    }

    return [...new Set([...sugeridos, ...outros])];
  }

  /**
   * Busca naturezas sugeridas em 3 camadas:
   * 1. Sugestão humana da col_f (analise_natureza) — DESTAQUE
   * 2. Por score de matching (até 15 com score > 0)
   * 3. Naturezas mais comuns nos registros OK (completar até 30)
   */
  async buscarSimilares(
    nomeEvento: string,
    topN: number = 10,
    codigoEvento?: string,
  ): Promise<{
    sugestaoHumana: NaturezaSugerida | null;
    sugestaoTexto: string | null;
    resultados: NaturezaSugerida[];
  }> {
    // Buscar todas as naturezas do governo
    const natResult = await pool.query(
      `SELECT id, codigo, nome, descricao, data_inicio, data_fim
       FROM naturezas_esocial ORDER BY codigo`,
    );
    const naturezasMap = new Map<string, any>();
    for (const nat of natResult.rows) {
      naturezasMap.set(nat.codigo, nat);
    }

    // === CAMADA 1: Sugestão humana da col_f ===
    let sugestaoHumana: NaturezaSugerida | null = null;
    let sugestaoTexto: string | null = null;
    const codigosJaUsados = new Set<string>();

    if (codigoEvento) {
      const colFResult = await pool.query(
        `SELECT col_f FROM analise_natureza 
         WHERE col_a = $1 AND UPPER(TRIM(col_d)) = 'VERIFICAR'
         AND col_f IS NOT NULL AND TRIM(col_f) != '' AND TRIM(col_f) != '-'
         LIMIT 1`,
        [codigoEvento],
      );
      if (colFResult.rows.length > 0) {
        const colF = colFResult.rows[0].col_f;
        sugestaoTexto = colF;
        const codigos = this.extrairCodigosDaColF(colF);
        if (codigos.length > 0) {
          // Preferir natureza ATIVA (sem data_fim) entre os códigos mencionados
          let melhorNat: any = null;
          for (const cod of codigos) {
            const nat = naturezasMap.get(cod);
            if (!nat) continue;
            if (!nat.data_fim) {
              // Ativa — usar esta
              melhorNat = nat;
              break;
            }
            if (!melhorNat) melhorNat = nat; // guardar primeira (inativa) como fallback
          }
          if (melhorNat) {
            sugestaoHumana = {
              id: melhorNat.id,
              codigo: melhorNat.codigo,
              nome: melhorNat.nome,
              descricao: melhorNat.descricao,
              data_inicio: melhorNat.data_inicio,
              data_fim: melhorNat.data_fim,
              score: 100,
              origem: "sugestao_humana",
            };
            codigosJaUsados.add(melhorNat.codigo);
          }
        }
      }
    }

    // === CAMADA 2: Score de matching (até 15 com score > 0) ===
    const tokensEventoRaw = tokenize(nomeEvento);
    const tokensEvento = expandTokens(tokensEventoRaw);
    const scored: NaturezaSugerida[] = [];

    for (const nat of natResult.rows) {
      if (codigosJaUsados.has(nat.codigo)) continue;
      const textoNat = `${nat.nome} ${nat.descricao || ""}`;
      const tokensNat = tokenize(textoNat);

      let score = 0;
      const matchedTokens = new Set<string>();
      for (const token of tokensEvento) {
        for (const natToken of tokensNat) {
          if (natToken === token) {
            if (!matchedTokens.has(token)) {
              score += 3;
              matchedTokens.add(token);
            }
          } else if (natToken.includes(token) || token.includes(natToken)) {
            if (!matchedTokens.has(`${token}~${natToken}`)) {
              score += 1;
              matchedTokens.add(`${token}~${natToken}`);
            }
          }
        }
      }
      if (!nat.data_fim) {
        score += 0.5;
      }

      if (score > 0.5) {
        scored.push({
          id: nat.id,
          codigo: nat.codigo,
          nome: nat.nome,
          descricao: nat.descricao,
          data_inicio: nat.data_inicio,
          data_fim: nat.data_fim,
          score,
          origem: "score",
        });
      }
    }
    scored.sort((a, b) => b.score - a.score);
    const top15scored = scored.slice(0, 8);
    for (const s of top15scored) codigosJaUsados.add(s.codigo);

    // === CAMADA 3: Naturezas mais comuns nos OK (completar até 30) ===
    const restantes = topN - top15scored.length - (sugestaoHumana ? 1 : 0);
    let populares: NaturezaSugerida[] = [];

    if (restantes > 0) {
      const popResult = await pool.query(
        `SELECT SUBSTRING(col_c FROM '^(\\d+)') as codigo, COUNT(*) as freq
         FROM analise_natureza
         WHERE UPPER(TRIM(col_d)) = 'OK'
         AND col_c IS NOT NULL
         GROUP BY SUBSTRING(col_c FROM '^(\\d+)')
         ORDER BY freq DESC
         LIMIT $1`,
        [restantes + codigosJaUsados.size],
      );

      for (const row of popResult.rows) {
        if (codigosJaUsados.has(row.codigo)) continue;
        if (populares.length >= restantes) break;
        const nat = naturezasMap.get(row.codigo);
        if (nat) {
          populares.push({
            id: nat.id,
            codigo: nat.codigo,
            nome: nat.nome,
            descricao: nat.descricao,
            data_inicio: nat.data_inicio,
            data_fim: nat.data_fim,
            score: 0,
            origem: "popular",
          });
          codigosJaUsados.add(nat.codigo);
        }
      }
    }

    const resultados = [...top15scored, ...populares];
    return { sugestaoHumana, sugestaoTexto, resultados };
  }

  /**
   * Salva correção no staging (NÃO altera analise_natureza)
   */
  async corrigirRubrica(
    id: number,
    naturezaNovaCodigo: string,
    naturezaNovaNome: string,
    motivo: string = "",
    usuarioId?: number,
    usuarioNome: string = "sistema",
  ): Promise<boolean> {
    // Buscar dados da rubrica
    const atual = await pool.query(
      "SELECT col_a, col_b, col_c FROM analise_natureza WHERE id = $1",
      [id],
    );
    if (atual.rows.length === 0) return false;

    const {
      col_a: codigoevento,
      col_b: nome_evento,
      col_c: naturezaAnterior,
    } = atual.rows[0];

    // Upsert no staging (substitui se já existia)
    await pool.query(
      `INSERT INTO correcoes_staging
         (analise_natureza_id, codigoevento, nome_evento, natureza_anterior,
          natureza_nova_codigo, natureza_nova_nome, motivo, usuario_id, usuario_nome, status)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'pendente')
       ON CONFLICT (analise_natureza_id) DO UPDATE SET
         natureza_nova_codigo = $5,
         natureza_nova_nome = $6,
         motivo = $7,
         usuario_id = $8,
         usuario_nome = $9,
         status = 'pendente',
         criado_em = CURRENT_TIMESTAMP,
         aplicado_em = NULL`,
      [
        id,
        codigoevento,
        nome_evento,
        naturezaAnterior,
        naturezaNovaCodigo,
        naturezaNovaNome,
        motivo,
        usuarioId || null,
        usuarioNome,
      ],
    );

    return true;
  }

  /**
   * Retorna progresso geral da validação (usando staging como fonte)
   */
  async getProgresso(): Promise<ProgressoValidacao> {
    const result = await pool.query(`
      SELECT 
        count(*) FILTER (WHERE UPPER(TRIM(a.col_d)) = 'VERIFICAR') as total_verificar,
        count(*) FILTER (WHERE UPPER(TRIM(a.col_d)) = 'VERIFICAR' AND cs.id IS NOT NULL) as total_corrigidas,
        count(*) FILTER (WHERE UPPER(TRIM(a.col_d)) = 'VERIFICAR' AND cs.id IS NULL) as total_pendentes
      FROM analise_natureza a
      LEFT JOIN correcoes_staging cs ON cs.analise_natureza_id = a.id AND cs.status = 'pendente'
    `);

    const row = result.rows[0];
    const total = parseInt(row.total_verificar);
    const corrigidas = parseInt(row.total_corrigidas);
    const pendentes = parseInt(row.total_pendentes);

    return {
      total_verificar: total,
      total_corrigidas: corrigidas,
      total_pendentes: pendentes,
      percentual: total > 0 ? Math.round((corrigidas / total) * 100) : 0,
    };
  }

  /**
   * Retorna relatório com todas as correções no staging
   */
  async getRelatorioFinal(): Promise<any[]> {
    const result = await pool.query(`
      SELECT cs.analise_natureza_id as id, cs.codigoevento, cs.nome_evento,
             cs.natureza_anterior,
             CASE WHEN cs.natureza_nova_codigo = '0' THEN '(vazio)'
                  ELSE cs.natureza_nova_codigo || '-' || cs.natureza_nova_nome END as natureza_nova,
             cs.usuario_nome, cs.criado_em as data_correcao, cs.motivo, cs.status
      FROM correcoes_staging cs
      ORDER BY cs.criado_em DESC
    `);
    return result.rows;
  }

  /**
   * Desfaz uma correção (remove do staging)
   */
  async desfazerCorrecao(id: number): Promise<boolean> {
    const result = await pool.query(
      "DELETE FROM correcoes_staging WHERE analise_natureza_id = $1 AND status = 'pendente'",
      [id],
    );
    return (result.rowCount ?? 0) > 0;
  }

  /**
   * Aplica todas as correções pendentes do staging → analise_natureza (merge)
   * Retorna quantas foram aplicadas
   */
  async aplicarCorrecoes(): Promise<{ aplicadas: number }> {
    const client = await pool.connect();
    try {
      await client.query("BEGIN");

      // Buscar todas as pendentes
      const pendentes = await client.query(
        `SELECT id, analise_natureza_id, codigoevento, natureza_anterior,
                natureza_nova_codigo, natureza_nova_nome, motivo, usuario_nome
         FROM correcoes_staging WHERE status = 'pendente'`,
      );

      for (const cs of pendentes.rows) {
        // Código "0" = sem natureza (campo vazio)
        const naturezaNovaFull =
          cs.natureza_nova_codigo === "0"
            ? ""
            : `${cs.natureza_nova_codigo}-${cs.natureza_nova_nome}`;

        // Aplicar na analise_natureza_certo (tabela corrigida, original não é tocada)
        await client.query(
          `UPDATE analise_natureza_certo 
           SET col_c = $1,
               natureza_anterior = $2, 
               natureza_nova = $1,
               col_d = 'OK',
               usuario_correcao = $3,
               data_correcao = CURRENT_TIMESTAMP
           WHERE id = $4`,
          [
            naturezaNovaFull,
            cs.natureza_anterior,
            cs.usuario_nome,
            cs.analise_natureza_id,
          ],
        );

        // Registrar auditoria
        await client.query(
          `INSERT INTO auditoria_naturezas 
           (analise_natureza_id, codigoevento, natureza_anterior, natureza_nova, usuario, motivo)
           VALUES ($1, $2, $3, $4, $5, $6)`,
          [
            cs.analise_natureza_id,
            cs.codigoevento,
            cs.natureza_anterior,
            naturezaNovaFull,
            cs.usuario_nome,
            cs.motivo || "",
          ],
        );

        // Marcar staging como aplicada
        await client.query(
          `UPDATE correcoes_staging SET status = 'aplicada', aplicado_em = CURRENT_TIMESTAMP WHERE id = $1`,
          [cs.id],
        );
      }

      await client.query("COMMIT");
      return { aplicadas: pendentes.rows.length };
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Busca uma natureza pelo código exato (ex: "1002")
   */
  async buscarPorCodigo(codigo: string): Promise<any | null> {
    const result = await pool.query(
      "SELECT id, codigo, nome, descricao, data_inicio, data_fim FROM naturezas_esocial WHERE codigo = $1",
      [codigo],
    );
    return result.rows[0] || null;
  }

  /**
   * Lista todas as naturezas disponíveis no banco
   */
  async listarNaturezas(): Promise<any[]> {
    const result = await pool.query(
      "SELECT id, codigo, nome, descricao, data_inicio, data_fim FROM naturezas_esocial ORDER BY codigo",
    );
    return result.rows;
  }

  /**
   * Edita uma correção pendente no staging
   */
  async editarStaging(
    analiseNaturezaId: number,
    novoCodigo: string,
    novoNome: string,
  ): Promise<boolean> {
    const result = await pool.query(
      `UPDATE correcoes_staging
       SET natureza_nova_codigo = $1, natureza_nova_nome = $2, criado_em = CURRENT_TIMESTAMP
       WHERE analise_natureza_id = $3 AND status = 'pendente'`,
      [novoCodigo, novoNome, analiseNaturezaId],
    );
    return (result.rowCount ?? 0) > 0;
  }

  /**
   * Retorna resumo do staging para o painel
   */
  async getStagingResumo(): Promise<{
    total_pendentes: number;
    total_aplicadas: number;
    usuarios: { nome: string; count: number }[];
  }> {
    const result = await pool.query(`
      SELECT 
        count(*) FILTER (WHERE status = 'pendente') as total_pendentes,
        count(*) FILTER (WHERE status = 'aplicada') as total_aplicadas
      FROM correcoes_staging
    `);
    const usuarios = await pool.query(`
      SELECT usuario_nome as nome, count(*) as count
      FROM correcoes_staging WHERE status = 'pendente'
      GROUP BY usuario_nome ORDER BY count DESC
    `);
    return {
      total_pendentes: parseInt(result.rows[0].total_pendentes),
      total_aplicadas: parseInt(result.rows[0].total_aplicadas),
      usuarios: usuarios.rows,
    };
  }
}
