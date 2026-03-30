/**
 * Master database pool — Supabase (tudo no mesmo banco agora)
 *
 * Antes: banco separado "easy_social_master"
 * Agora: mesmo banco Supabase, tabelas com prefixo "master_"
 */
import { Pool } from "pg";
import pool from "./database";

export const masterPool: Pool = pool;
