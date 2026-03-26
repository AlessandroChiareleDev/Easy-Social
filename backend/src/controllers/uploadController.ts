import { Request, Response } from "express";
import { DIRFParser } from "../services/dirf-parser";
import fs from "fs";
import pool from "../config/database";

export class UploadController {
  /**
   * POST /api/upload
   * Recebe arquivo DIRF.xlsx e inicia análise
   */
  async uploadDIRF(req: Request, res: Response) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "Nenhum arquivo enviado" });
      }

      const filePath = req.file.path;
      const originalFileName = req.file.originalname;

      // Verificar se já existe upload completo com mesmo nome de arquivo original
      const client = await pool.connect();
      try {
        const existing = await client.query(
          `SELECT id, file_name, analysis_data, created_at FROM uploads
           WHERE status = 'completed'
           ORDER BY created_at DESC LIMIT 1`,
        );

        if (existing.rows.length > 0) {
          // Já existe um processamento completo — remover arquivo enviado duplicado
          if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
          }

          return res.status(200).json({
            success: true,
            duplicate: true,
            message: `Este arquivo já foi processado anteriormente. Visualize os dados na seção de tabelas.`,
            data: {
              uploadId: existing.rows[0].id,
              fileName: existing.rows[0].file_name,
              processedAt: existing.rows[0].created_at,
            },
          });
        }

        const parser = new DIRFParser(filePath);
        const analysis = await parser.analyzeDIRF();

        const result = await client.query(
          `INSERT INTO uploads (file_name, file_size, analysis_data, status)
           VALUES ($1, $2, $3, $4) RETURNING id`,
          [
            analysis.fileName,
            analysis.fileSize,
            JSON.stringify(analysis),
            "analyzed",
          ],
        );
        const uploadId = result.rows[0].id;
        analysis.uploadId = uploadId;
        analysis.filePath = filePath;

        return res.status(200).json({
          success: true,
          duplicate: false,
          message: "Arquivo analisado com sucesso",
          data: analysis,
        });
      } finally {
        client.release();
      }
    } catch (error: any) {
      // Remover arquivo temporário em caso de erro
      if (req.file && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      return res.status(500).json({
        error: error.message,
      });
    }
  }

  /**
   * GET /api/upload/status/:uploadId
   * Retorna status do processamento
   */
  async getUploadStatus(req: Request, res: Response) {
    try {
      const { uploadId } = req.params;

      const client = await pool.connect();
      try {
        const result = await client.query(
          `SELECT id, file_name, status, analysis_data, created_at FROM uploads WHERE id = $1`,
          [uploadId],
        );

        if (result.rows.length === 0) {
          return res.status(404).json({ error: "Upload não encontrado" });
        }

        return res.status(200).json(result.rows[0]);
      } finally {
        client.release();
      }
    } catch (error: any) {
      return res.status(500).json({ error: error.message });
    }
  }
}
