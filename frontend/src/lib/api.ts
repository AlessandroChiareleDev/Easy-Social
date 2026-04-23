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

const host = window.location.hostname
const isLoopback = host === 'localhost' || host === '127.0.0.1'
// LAN: 192.168.x.x, 10.x.x.x, 172.16-31.x.x (acesso por celular na mesma rede)
const isLan = /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(host)
const isLocal = isLoopback || isLan

/** Node.js backend (Express, port 3333) — returns base like "http://…/api" */
export const API_URL: string = isLocal
  ? import.meta.env.VITE_API_URL || '/api'
  : import.meta.env.VITE_TUNNEL_BACKEND || '/api'

/** Python backend (FastAPI, port 8000) — returns base like "http://…" (no trailing slash) */
export const PYTHON_API: string = isLoopback
  ? import.meta.env.VITE_PYTHON_API_URL || 'http://localhost:8000'
  : isLan
    ? `${window.location.protocol}//${host}:8000`
    : import.meta.env.VITE_TUNNEL_PYTHON || '/python-api'
