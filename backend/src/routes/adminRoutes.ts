import { Router, Request, Response } from "express";
import { masterPool } from "../config/masterDatabase";
import { requireAuth, requireAdmin } from "../middleware/auth";

const router = Router();

/**
 * GET /admin/atividades - lista atividades com filtros
 * Query params: usuario_id, metodo, rota, desde, ate, limit, offset
 */
router.get(
  "/admin/atividades",
  requireAuth,
  requireAdmin,
  async (req: Request, res: Response) => {
    try {
      const {
        usuario_id,
        metodo,
        rota,
        desde,
        ate,
        limit = "50",
        offset = "0",
      } = req.query;

      const conditions: string[] = [];
      const params: any[] = [];
      let paramIndex = 1;

      if (usuario_id) {
        conditions.push(`a.usuario_id = $${paramIndex++}`);
        params.push(parseInt(usuario_id as string));
      }
      if (metodo) {
        conditions.push(`a.metodo = $${paramIndex++}`);
        params.push((metodo as string).toUpperCase());
      }
      if (rota) {
        conditions.push(`a.rota ILIKE $${paramIndex++}`);
        params.push(`%${rota}%`);
      }
      if (desde) {
        conditions.push(`a.criado_em >= $${paramIndex++}`);
        params.push(desde);
      }
      if (ate) {
        conditions.push(`a.criado_em <= $${paramIndex++}`);
        params.push(ate);
      }

      const where =
        conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

      // Total count
      const countResult = await masterPool.query(
        `SELECT COUNT(*) FROM master_atividades a ${where}`,
        params,
      );

      const safeLimit = Math.min(parseInt(limit as string) || 50, 200);
      const safeOffset = parseInt(offset as string) || 0;

      // Activities
      const result = await masterPool.query(
        `SELECT a.id, a.usuario_id, a.username, a.metodo, a.rota, 
                a.status_code, a.duracao_ms, a.ip, a.empresa_id, 
                a.body_resumo, a.criado_em
         FROM master_atividades a
         ${where}
         ORDER BY a.criado_em DESC
         LIMIT $${paramIndex++} OFFSET $${paramIndex++}`,
        [...params, safeLimit, safeOffset],
      );

      res.json({
        success: true,
        total: parseInt(countResult.rows[0].count),
        atividades: result.rows,
      });
    } catch (error: any) {
      console.error("Erro ao buscar atividades:", error);
      res.status(500).json({ error: "Erro ao buscar atividades" });
    }
  },
);

/**
 * GET /admin/atividades/resumo - resumo por operador
 * Query params: desde, ate
 */
router.get(
  "/admin/atividades/resumo",
  requireAuth,
  requireAdmin,
  async (req: Request, res: Response) => {
    try {
      const { desde, ate } = req.query;
      const conditions: string[] = [];
      const params: any[] = [];
      let paramIndex = 1;

      if (desde) {
        conditions.push(`criado_em >= $${paramIndex++}`);
        params.push(desde);
      }
      if (ate) {
        conditions.push(`criado_em <= $${paramIndex++}`);
        params.push(ate);
      }

      const where =
        conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

      const result = await masterPool.query(
        `SELECT 
          usuario_id,
          username,
          COUNT(*) as total_acoes,
          COUNT(*) FILTER (WHERE metodo = 'GET') as gets,
          COUNT(*) FILTER (WHERE metodo = 'POST') as posts,
          COUNT(*) FILTER (WHERE metodo = 'PUT') as puts,
          COUNT(*) FILTER (WHERE metodo = 'DELETE') as deletes,
          COUNT(*) FILTER (WHERE status_code >= 400) as erros,
          ROUND(AVG(duracao_ms)) as duracao_media_ms,
          MIN(criado_em) as primeiro_acesso,
          MAX(criado_em) as ultimo_acesso,
          COUNT(DISTINCT DATE(criado_em)) as dias_ativos,
          array_agg(DISTINCT ip) FILTER (WHERE ip IS NOT NULL) as ips
         FROM master_atividades
         ${where}
         GROUP BY usuario_id, username
         ORDER BY total_acoes DESC`,
        params,
      );

      res.json({ success: true, resumo: result.rows });
    } catch (error: any) {
      console.error("Erro ao buscar resumo:", error);
      res.status(500).json({ error: "Erro ao buscar resumo" });
    }
  },
);

/**
 * GET /admin/atividades/timeline - atividades por hora (últimas 24h ou período)
 */
router.get(
  "/admin/atividades/timeline",
  requireAuth,
  requireAdmin,
  async (req: Request, res: Response) => {
    try {
      const { desde, ate } = req.query;
      const params: any[] = [];
      let paramIndex = 1;
      const conditions: string[] = [];

      if (desde) {
        conditions.push(`criado_em >= $${paramIndex++}`);
        params.push(desde);
      } else {
        conditions.push(`criado_em >= NOW() - INTERVAL '24 hours'`);
      }
      if (ate) {
        conditions.push(`criado_em <= $${paramIndex++}`);
        params.push(ate);
      }

      const where = `WHERE ${conditions.join(" AND ")}`;

      const result = await masterPool.query(
        `SELECT 
          DATE_TRUNC('hour', criado_em) as hora,
          username,
          COUNT(*) as total
         FROM master_atividades
         ${where}
         GROUP BY hora, username
         ORDER BY hora`,
        params,
      );

      res.json({ success: true, timeline: result.rows });
    } catch (error: any) {
      console.error("Erro ao buscar timeline:", error);
      res.status(500).json({ error: "Erro ao buscar timeline" });
    }
  },
);

/**
 * GET /admin/atividades/rotas-populares - rotas mais acessadas
 */
router.get(
  "/admin/atividades/rotas-populares",
  requireAuth,
  requireAdmin,
  async (req: Request, res: Response) => {
    try {
      const { desde, ate, limit = "20" } = req.query;
      const conditions: string[] = [];
      const params: any[] = [];
      let paramIndex = 1;

      if (desde) {
        conditions.push(`criado_em >= $${paramIndex++}`);
        params.push(desde);
      }
      if (ate) {
        conditions.push(`criado_em <= $${paramIndex++}`);
        params.push(ate);
      }

      const where =
        conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
      const safeLimit = Math.min(parseInt(limit as string) || 20, 100);

      const result = await masterPool.query(
        `SELECT 
          rota,
          metodo,
          COUNT(*) as total,
          ROUND(AVG(duracao_ms)) as duracao_media_ms,
          COUNT(*) FILTER (WHERE status_code >= 400) as erros
         FROM master_atividades
         ${where}
         GROUP BY rota, metodo
         ORDER BY total DESC
         LIMIT $${paramIndex++}`,
        [...params, safeLimit],
      );

      res.json({ success: true, rotas: result.rows });
    } catch (error: any) {
      console.error("Erro ao buscar rotas:", error);
      res.status(500).json({ error: "Erro ao buscar rotas populares" });
    }
  },
);

/**
 * GET /admin/envios - lista envios ao eSocial (da tabela esocial_envios)
 * Query params: tipo_evento, ambiente, status, desde, ate, limit, offset
 */
router.get(
  "/admin/envios",
  requireAuth,
  requireAdmin,
  async (req: Request, res: Response) => {
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

      // Check if table exists
      const tableCheck = await masterPool.query(
        `SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'esocial_envios')`,
      );
      if (!tableCheck.rows[0].exists) {
        res.json({ success: true, total: 0, envios: [] });
        return;
      }

      const countResult = await masterPool.query(
        `SELECT COUNT(*) FROM esocial_envios ${where}`,
        params,
      );

      const result = await masterPool.query(
        `SELECT id, tipo_evento, modo, status, protocolo_envio,
                codigo_resposta, descricao_resposta, total_eventos,
                created_at, ambiente, ini_valid, rubrica_detalhes,
                rubrica_ids, nr_recibo, updated_at, ocorrencias
         FROM esocial_envios
         ${where}
         ORDER BY created_at DESC
         LIMIT $${pi++} OFFSET $${pi++}`,
        [...params, safeLimit, safeOffset],
      );

      res.json({
        success: true,
        total: parseInt(countResult.rows[0].count),
        envios: result.rows,
      });
    } catch (error: any) {
      console.error("Erro ao buscar envios:", error);
      res.status(500).json({ error: "Erro ao buscar envios" });
    }
  },
);

/**
 * GET /admin/envios/resumo - resumo de envios (totais por tipo, status, ambiente)
 */
router.get(
  "/admin/envios/resumo",
  requireAuth,
  requireAdmin,
  async (_req: Request, res: Response) => {
    try {
      const tableCheck = await masterPool.query(
        `SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'esocial_envios')`,
      );
      if (!tableCheck.rows[0].exists) {
        res.json({
          success: true,
          resumo: { total: 0, por_tipo: [], por_status: [], por_ambiente: [] },
        });
        return;
      }

      const [totalRes, porTipoRes, porStatusRes, porAmbienteRes] =
        await Promise.all([
          masterPool.query(`SELECT COUNT(*) FROM esocial_envios`),
          masterPool.query(
            `SELECT tipo_evento, COUNT(*) as total FROM esocial_envios GROUP BY tipo_evento ORDER BY total DESC`,
          ),
          masterPool.query(
            `SELECT status, COUNT(*) as total FROM esocial_envios GROUP BY status ORDER BY total DESC`,
          ),
          masterPool.query(
            `SELECT ambiente, COUNT(*) as total FROM esocial_envios GROUP BY ambiente ORDER BY total DESC`,
          ),
        ]);

      res.json({
        success: true,
        resumo: {
          total: parseInt(totalRes.rows[0].count),
          por_tipo: porTipoRes.rows,
          por_status: porStatusRes.rows,
          por_ambiente: porAmbienteRes.rows,
        },
      });
    } catch (error: any) {
      console.error("Erro ao buscar resumo envios:", error);
      res.status(500).json({ error: "Erro ao buscar resumo de envios" });
    }
  },
);

/**
 * GET /admin/pipelines - lista pipeline de correções
 * Query params: cpf, status, ambiente, desde, ate, limit, offset
 */
router.get(
  "/admin/pipelines",
  requireAuth,
  requireAdmin,
  async (req: Request, res: Response) => {
    try {
      const {
        cpf,
        status,
        ambiente,
        desde,
        ate,
        limit = "50",
        offset = "0",
      } = req.query;

      const conditions: string[] = [];
      const params: any[] = [];
      let pi = 1;

      if (cpf) {
        conditions.push(`cpf = $${pi++}`);
        params.push(cpf);
      }
      if (status) {
        conditions.push(`status = $${pi++}`);
        params.push(status);
      }
      if (ambiente) {
        conditions.push(`ambiente = $${pi++}`);
        params.push(ambiente);
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

      const tableCheck = await masterPool.query(
        `SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pipeline_correcao')`,
      );
      if (!tableCheck.rows[0].exists) {
        res.json({ success: true, total: 0, pipelines: [] });
        return;
      }

      const countResult = await masterPool.query(
        `SELECT COUNT(*) FROM pipeline_correcao ${where}`,
        params,
      );

      const result = await masterPool.query(
        `SELECT id, cpf, per_apur, ambiente, status, step_atual,
                s1010_protocolo, s1010_nr_recibo,
                s1298_protocolo, s1298_nr_recibo,
                s1200_protocolo, s1200_nr_recibo,
                s1210_protocolo, s1210_nr_recibo,
                s1299_protocolo, s1299_nr_recibo,
                steps_log, erro, created_at, updated_at
         FROM pipeline_correcao
         ${where}
         ORDER BY created_at DESC
         LIMIT $${pi++} OFFSET $${pi++}`,
        [...params, safeLimit, safeOffset],
      );

      res.json({
        success: true,
        total: parseInt(countResult.rows[0].count),
        pipelines: result.rows,
      });
    } catch (error: any) {
      console.error("Erro ao buscar pipelines:", error);
      res.status(500).json({ error: "Erro ao buscar pipelines" });
    }
  },
);

export default router;
