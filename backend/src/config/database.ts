import { Pool } from "pg";
import dotenv from "dotenv";

dotenv.config();

const useSSL = process.env.DB_SSL === "true";

const pool = new Pool({
  host: process.env.DB_HOST || "localhost",
  port: parseInt(process.env.DB_PORT || "5432"),
  user: process.env.DB_USER || "easy_social_user",
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME || "easy_social_db",
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
  ...(useSSL ? { ssl: { rejectUnauthorized: false } } : {}),
});

pool.on("error", (err) => {
  console.error("Erro inesperado no cliente PostgreSQL", err);
  process.exit(-1);
});

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
 * Criar tabelas se não existirem
 */
export async function initializeDatabase() {
  const client = await pool.connect();
  try {
    const result = await client.query(
      "SELECT current_database(), current_user",
    );
    console.log(
      `✅ Conectado ao banco: ${result.rows[0].current_database} (user: ${result.rows[0].current_user})`,
    );
  } catch (error: any) {
    console.error("❌ Erro ao conectar ao banco de dados:", error);
    throw error;
  } finally {
    client.release();
  }
}

export default pool;
