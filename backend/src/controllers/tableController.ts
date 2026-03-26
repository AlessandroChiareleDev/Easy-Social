import { Request, Response } from "express";
import { DatabaseService } from "../services/database-service";

const databaseService = new DatabaseService();

export class TableController {
  async listTables(_req: Request, res: Response) {
    // Implementado diretamente em tableRoutes.ts para simplificar
    res.status(501).json({ message: "Not Implemented - see tableRoutes.ts" });
  }

  async getTableData(_req: Request, res: Response) {
    // Implementado diretamente em tableRoutes.ts para simplificar
    res.status(501).json({ message: "Not Implemented - see tableRoutes.ts" });
  }

  async getTableColumns(_req: Request, res: Response) {
    // Implementado diretamente em tableRoutes.ts para simplificar
    res.status(501).json({ message: "Not Implemented - see tableRoutes.ts" });
  }

  async processAndNormalize(_req: Request, res: Response) {
    // Implementado diretamente em tableRoutes.ts para simplificar
    res.status(501).json({ message: "Not Implemented - see tableRoutes.ts" });
  }
}
