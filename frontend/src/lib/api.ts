/**
 * Centralized API URL configuration.
 *
 * LOCAL  (localhost / 127.0.0.1):
 *   - Node backend  → Vite proxy "/api" → localhost:3333
 *   - Python backend → direct "http://localhost:8000"
 *
 * TUNNEL (*.trycloudflare.com or any other remote host):
 *   - Node backend  → VITE_TUNNEL_BACKEND env var (set in .env.tunnel)
 *   - Python backend → VITE_TUNNEL_PYTHON  env var (set in .env.tunnel)
 *
 * After starting new tunnels, just update .env.tunnel and restart Vite.
 */

const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'

/** Node.js backend (Express, port 3333) — returns base like "http://…/api" */
export const API_URL: string = isLocal
  ? import.meta.env.VITE_API_URL || '/api'
  : import.meta.env.VITE_TUNNEL_BACKEND || '/api'

/** Python backend (FastAPI, port 8000) — returns base like "http://…" (no trailing slash) */
export const PYTHON_API: string = isLocal
  ? import.meta.env.VITE_PYTHON_API_URL || 'http://localhost:8000'
  : import.meta.env.VITE_TUNNEL_PYTHON || '/python-api'
