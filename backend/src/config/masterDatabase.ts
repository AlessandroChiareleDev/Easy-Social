import { Pool } from "pg";
import dotenv from "dotenv";

dotenv.config();

/**
 * Pool de conexão ao banco MASTER (autenticação, empresas)
 */
const masterPool = new Pool({
  host: process.env.DB_HOST || "localhost",
  port: parseInt(process.env.DB_PORT || "5432"),
  user: process.env.DB_USER || "easy_social_user",
  password: process.env.DB_PASSWORD || "",
  database: "easy_social_master",
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

masterPool.on("error", (err) => {
  console.error("Erro no pool master:", err);
});

/**
 * Cache de pools por empresa (criados sob demanda)
 */
const companyPools: Map<string, { pool: Pool; lastUsed: number }> = new Map();

/**
 * Retorna um pool de conexão para o banco de uma empresa específica
 */
export function getCompanyPool(dbName: string): Pool {
  const existing = companyPools.get(dbName);
  if (existing) {
    existing.lastUsed = Date.now();
    return existing.pool;
  }

  const pool = new Pool({
    host: process.env.DB_HOST || "localhost",
    port: parseInt(process.env.DB_PORT || "5432"),
    user: process.env.DB_USER || "easy_social_user",
    password: process.env.DB_PASSWORD || "",
    database: dbName,
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
  });

  pool.on("error", (err) => {
    console.error(`Erro no pool empresa (${dbName}):`, err);
  });

  companyPools.set(dbName, { pool, lastUsed: Date.now() });
  console.log(`Pool criado para empresa: ${dbName}`);
  return pool;
}

/**
 * Limpa pools inativos (mais de 30 min sem uso)
 */
setInterval(
  () => {
    const now = Date.now();
    for (const [dbName, entry] of companyPools) {
      if (now - entry.lastUsed > 30 * 60 * 1000) {
        entry.pool.end();
        companyPools.delete(dbName);
        console.log(`Pool removido por inatividade: ${dbName}`);
      }
    }
  },
  5 * 60 * 1000,
);

export { masterPool };
