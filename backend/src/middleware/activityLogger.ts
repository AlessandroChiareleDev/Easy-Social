import { Request, Response, NextFunction } from "express";
import { masterPool } from "../config/masterDatabase";

/**
 * Middleware que registra toda atividade de usuários autenticados.
 * Loga: método HTTP, rota, status, duração, IP, user-agent.
 * Cria a tabela master_atividades se não existir.
 */

let tableReady = false;

async function ensureTable() {
  if (tableReady) return;
  await masterPool.query(`
    CREATE TABLE IF NOT EXISTS master_atividades (
      id SERIAL PRIMARY KEY,
      usuario_id INTEGER NOT NULL,
      username VARCHAR(100) NOT NULL,
      metodo VARCHAR(10) NOT NULL,
      rota VARCHAR(500) NOT NULL,
      status_code INTEGER,
      duracao_ms INTEGER,
      ip VARCHAR(50),
      user_agent VARCHAR(500),
      empresa_id INTEGER,
      body_resumo VARCHAR(500),
      criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_atividades_usuario ON master_atividades(usuario_id);
    CREATE INDEX IF NOT EXISTS idx_atividades_criado ON master_atividades(criado_em);
    CREATE INDEX IF NOT EXISTS idx_atividades_rota ON master_atividades(rota);
  `);
  tableReady = true;
}

// Inicializa a tabela ao carregar o módulo
ensureTable().catch((err) =>
  console.error("Erro ao criar tabela master_atividades:", err),
);

function sanitizeBody(body: any): string | null {
  if (!body || Object.keys(body).length === 0) return null;
  const safe = { ...body };
  // Nunca logar senhas
  delete safe.senha;
  delete safe.password;
  delete safe.senha_hash;
  const str = JSON.stringify(safe);
  return str.length > 500 ? str.substring(0, 497) + "..." : str;
}

export function activityLogger(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const start = Date.now();

  // Hook no finish — neste ponto req.user já foi populado pelo requireAuth
  res.on("finish", () => {
    if (!req.user) return; // Requisição pública (login, health), não loga

    const duracao = Date.now() - start;
    const metodo = req.method;
    const rota = req.originalUrl;
    const ip =
      (req.headers["x-forwarded-for"] as string)?.split(",")[0]?.trim() ||
      req.socket.remoteAddress ||
      "";
    const userAgent = (req.headers["user-agent"] || "").substring(0, 500);
    const empresaId = parseInt(req.headers["x-empresa-id"] as string) || null;
    const bodyResumo = metodo !== "GET" ? sanitizeBody(req.body) : null;

    masterPool
      .query(
        `INSERT INTO master_atividades 
        (usuario_id, username, metodo, rota, status_code, duracao_ms, ip, user_agent, empresa_id, body_resumo)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
        [
          req.user.userId,
          req.user.username,
          metodo,
          rota,
          res.statusCode,
          duracao,
          ip,
          userAgent,
          empresaId,
          bodyResumo,
        ],
      )
      .catch((err) => console.error("Erro ao logar atividade:", err));
  });

  next();
}
