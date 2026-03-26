import { Request, Response, NextFunction } from "express";
import { AuthService, UserPayload } from "../services/auth-service";

const authService = new AuthService();

/**
 * Extende Request para incluir dados do usuário autenticado
 */
declare global {
  namespace Express {
    interface Request {
      user?: UserPayload;
      empresaDbName?: string;
    }
  }
}

/**
 * Middleware: requer autenticação via Bearer token
 */
export function requireAuth(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith("Bearer ")) {
    res.status(401).json({ error: "Token não fornecido" });
    return;
  }

  const token = authHeader.substring(7);
  const user = authService.verifyToken(token);
  if (!user) {
    res.status(401).json({ error: "Token inválido ou expirado" });
    return;
  }

  req.user = user;
  next();
}

/**
 * Middleware: requer role admin
 */
export function requireAdmin(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  if (req.user?.role !== "admin") {
    res.status(403).json({ error: "Acesso negado: apenas administradores" });
    return;
  }
  next();
}

/**
 * Middleware: requer header X-Empresa-Id e verifica acesso
 */
export async function requireEmpresa(
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> {
  const empresaId = parseInt(req.headers["x-empresa-id"] as string);
  if (!empresaId || isNaN(empresaId)) {
    res.status(400).json({ error: "Header X-Empresa-Id obrigatório" });
    return;
  }

  const acesso = await authService.verificarAcessoEmpresa(
    req.user!.userId,
    empresaId,
  );
  if (!acesso) {
    res.status(403).json({ error: "Sem acesso a esta empresa" });
    return;
  }

  req.empresaDbName = acesso.dbName;
  next();
}
