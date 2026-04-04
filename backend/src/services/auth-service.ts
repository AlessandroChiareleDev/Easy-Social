import { masterPool } from "../config/masterDatabase";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";

const JWT_SECRET =
  process.env.JWT_SECRET || "mude_esta_chave_secreta_para_producao";
const JWT_EXPIRES_IN = "24h";

export interface UserPayload {
  userId: number;
  username: string;
  nome: string;
  role: string;
}

export interface Empresa {
  id: number;
  nome: string;
  cnpj: string | null;
  db_name: string;
  role_emp: string;
}

export class AuthService {
  /**
   * Autentica usuário e retorna JWT
   */
  async login(
    username: string,
    senha: string,
  ): Promise<{ token: string; user: UserPayload } | null> {
    const result = await masterPool.query(
      "SELECT id, username, nome, senha_hash, role, ativo FROM master_perfis WHERE username = $1",
      [username],
    );

    if (result.rows.length === 0) return null;

    const user = result.rows[0];
    if (!user.ativo) return null;

    const senhaValida = await bcrypt.compare(senha, user.senha_hash);
    if (!senhaValida) return null;

    const payload: UserPayload = {
      userId: user.id,
      username: user.username,
      nome: user.nome,
      role: user.role,
    };

    const token = jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });

    // Update last access
    await masterPool.query(
      "UPDATE master_perfis SET atualizado_em = CURRENT_TIMESTAMP WHERE id = $1",
      [user.id],
    );

    return { token, user: payload };
  }

  /**
   * Verifica e decodifica JWT
   */
  verifyToken(token: string): UserPayload | null {
    try {
      return jwt.verify(token, JWT_SECRET) as UserPayload;
    } catch {
      return null;
    }
  }

  /**
   * Retorna empresas acessíveis pelo usuário
   */
  async getEmpresasDoUsuario(userId: number): Promise<Empresa[]> {
    const userResult = await masterPool.query(
      "SELECT role FROM master_perfis WHERE id = $1",
      [userId],
    );
    const isAdmin = userResult.rows[0]?.role === "admin";

    if (isAdmin) {
      const result = await masterPool.query(
        `SELECT e.id, e.nome, e.cnpj, e.db_name, 'admin' as role_emp
         FROM master_empresas e
         WHERE e.ativo = true
         ORDER BY e.nome`,
      );
      return result.rows;
    }

    const result = await masterPool.query(
      `SELECT e.id, e.nome, e.cnpj, e.db_name, ue.role_emp
       FROM master_empresas e
       JOIN master_usuario_empresa ue ON ue.empresa_id = e.id
       WHERE ue.usuario_id = $1 AND e.ativo = true
       ORDER BY e.nome`,
      [userId],
    );
    return result.rows;
  }

  /**
   * Verifica se o usuário tem acesso a uma empresa
   */
  async verificarAcessoEmpresa(
    userId: number,
    empresaId: number,
  ): Promise<{ dbName: string; roleEmp: string } | null> {
    const userResult = await masterPool.query(
      "SELECT role FROM master_perfis WHERE id = $1",
      [userId],
    );
    const isAdmin = userResult.rows[0]?.role === "admin";

    if (isAdmin) {
      const result = await masterPool.query(
        `SELECT e.db_name FROM master_empresas e WHERE e.id = $1 AND e.ativo = true`,
        [empresaId],
      );
      if (result.rows.length === 0) return null;
      return { dbName: result.rows[0].db_name, roleEmp: "admin" };
    }

    const result = await masterPool.query(
      `SELECT e.db_name, ue.role_emp
       FROM master_empresas e
       JOIN master_usuario_empresa ue ON ue.empresa_id = e.id
       WHERE ue.usuario_id = $1 AND e.id = $2 AND e.ativo = true`,
      [userId, empresaId],
    );
    if (result.rows.length === 0) return null;
    return { dbName: result.rows[0].db_name, roleEmp: result.rows[0].role_emp };
  }

  /**
   * Cria novo usuário (admin only)
   */
  async criarUsuario(
    username: string,
    nome: string,
    senha: string,
    role: string = "operador",
  ): Promise<{ id: number; username: string; nome: string; role: string }> {
    const senhaHash = await bcrypt.hash(senha, 12);
    const result = await masterPool.query(
      `INSERT INTO master_perfis (username, nome, senha_hash, role) 
       VALUES ($1, $2, $3, $4) 
       RETURNING id, username, nome, role`,
      [username, nome, senhaHash, role],
    );
    return result.rows[0];
  }

  /**
   * Linka usuário a empresa
   */
  async linkarUsuarioEmpresa(
    userId: number,
    empresaId: number,
    roleEmp: string = "operador",
  ): Promise<void> {
    await masterPool.query(
      `INSERT INTO master_usuario_empresa (usuario_id, empresa_id, role_emp) 
       VALUES ($1, $2, $3) ON CONFLICT (usuario_id, empresa_id) DO UPDATE SET role_emp = $3`,
      [userId, empresaId, roleEmp],
    );
  }

  /**
   * Lista todos os usuários (admin only)
   */
  async listarUsuarios(): Promise<any[]> {
    const result = await masterPool.query(
      `SELECT u.id, u.username, u.nome, u.role, u.ativo, u.criado_em,
              array_agg(json_build_object('id', e.id, 'nome', e.nome)) FILTER (WHERE e.id IS NOT NULL) as empresas
       FROM master_perfis u
       LEFT JOIN master_usuario_empresa ue ON ue.usuario_id = u.id
       LEFT JOIN master_empresas e ON e.id = ue.empresa_id
       GROUP BY u.id
       ORDER BY u.nome`,
    );
    return result.rows;
  }

  /**
   * Lista todas as empresas (admin only)
   */
  async listarEmpresas(): Promise<any[]> {
    const result = await masterPool.query(
      "SELECT id, nome, cnpj, db_name, ativo, criado_em FROM master_empresas ORDER BY nome",
    );
    return result.rows;
  }
}
