import { Router, Request, Response } from "express";
import { AuthService } from "../services/auth-service";
import { requireAuth, requireAdmin } from "../middleware/auth";

const router = Router();
const authService = new AuthService();

/**
 * POST /auth/login
 */
router.post("/auth/login", async (req: Request, res: Response) => {
  try {
    const { username, senha } = req.body;
    if (!username || !senha) {
      res.status(400).json({ error: "Usuário e senha são obrigatórios" });
      return;
    }

    const result = await authService.login(username, senha);
    if (!result) {
      res.status(401).json({ error: "Usuário ou senha incorretos" });
      return;
    }

    res.json({ success: true, token: result.token, user: result.user });
  } catch (error: any) {
    console.error("Erro no login:", error);
    if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      res.status(503).json({ error: "Banco de dados indisponível" });
    } else if (error.code === "28P01" || error.code === "28000") {
      res
        .status(503)
        .json({ error: "Erro de autenticação com o banco de dados" });
    } else {
      res.status(500).json({ error: "Erro interno no login" });
    }
  }
});

/**
 * GET /auth/me - retorna dados do usuário logado
 */
router.get("/auth/me", requireAuth, async (req: Request, res: Response) => {
  try {
    res.json({ success: true, user: req.user });
  } catch (error: any) {
    console.error("Erro no /me:", error);
    res.status(500).json({ error: "Erro interno" });
  }
});

/**
 * GET /auth/empresas - retorna empresas do usuário logado
 */
router.get(
  "/auth/empresas",
  requireAuth,
  async (req: Request, res: Response) => {
    try {
      const empresas = await authService.getEmpresasDoUsuario(req.user!.userId);
      res.json({ success: true, empresas });
    } catch (error: any) {
      console.error("Erro ao buscar empresas:", error);
      res.status(500).json({ error: "Erro ao buscar empresas" });
    }
  },
);

/**
 * POST /auth/usuarios - criar novo usuário (admin only)
 */
router.post(
  "/auth/usuarios",
  requireAuth,
  requireAdmin,
  async (req: Request, res: Response) => {
    try {
      const { username, nome, senha, role } = req.body;
      if (!username || !nome || !senha) {
        res
          .status(400)
          .json({ error: "Usuário, nome e senha são obrigatórios" });
        return;
      }

      const user = await authService.criarUsuario(
        username,
        nome,
        senha,
        role || "operador",
      );
      res.json({ success: true, user });
    } catch (error: any) {
      if (error.code === "23505") {
        res.status(409).json({ error: "Usuário já cadastrado" });
        return;
      }
      console.error("Erro ao criar usuário:", error);
      res.status(500).json({ error: "Erro ao criar usuário" });
    }
  },
);

/**
 * POST /auth/usuarios/:userId/empresas - linkar usuário a empresa (admin only)
 */
router.post(
  "/auth/usuarios/:userId/empresas",
  requireAuth,
  requireAdmin,
  async (req: Request, res: Response) => {
    try {
      const userId = parseInt(req.params.userId as string);
      const { empresaId, roleEmp } = req.body;
      if (!empresaId) {
        res.status(400).json({ error: "empresaId é obrigatório" });
        return;
      }
      await authService.linkarUsuarioEmpresa(
        userId,
        empresaId,
        roleEmp || "operador",
      );
      res.json({ success: true });
    } catch (error: any) {
      console.error("Erro ao linkar:", error);
      res.status(500).json({ error: "Erro ao linkar usuário à empresa" });
    }
  },
);

/**
 * GET /auth/admin/usuarios - lista todos os usuários (admin only)
 */
router.get(
  "/auth/admin/usuarios",
  requireAuth,
  requireAdmin,
  async (_req: Request, res: Response) => {
    try {
      const usuarios = await authService.listarUsuarios();
      res.json({ success: true, usuarios });
    } catch (error: any) {
      console.error("Erro ao listar:", error);
      res.status(500).json({ error: "Erro ao listar usuários" });
    }
  },
);

/**
 * GET /auth/admin/empresas - lista todas as empresas (admin only)
 */
router.get(
  "/auth/admin/empresas",
  requireAuth,
  requireAdmin,
  async (_req: Request, res: Response) => {
    try {
      const empresas = await authService.listarEmpresas();
      res.json({ success: true, empresas });
    } catch (error: any) {
      console.error("Erro ao listar:", error);
      res.status(500).json({ error: "Erro ao listar empresas" });
    }
  },
);

export default router;
