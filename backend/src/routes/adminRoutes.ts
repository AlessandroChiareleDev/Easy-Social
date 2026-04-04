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

export default router;
