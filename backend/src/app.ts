import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import path from "path";
import { initializeDatabase } from "./config/database";
import uploadRoutes from "./routes/uploadRoutes";
import tableRoutes from "./routes/tableRoutes";
import validationRoutes from "./routes/validationRoutes";
import naturezaRoutes from "./routes/naturezaRoutes";
import authRoutes from "./routes/authRoutes";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3333;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Servir arquivos estáticos (uploads)
app.use("/uploads", express.static(path.join(__dirname, "../uploads")));

// Inicializar banco de dados
initializeDatabase().catch((err) => {
  console.error("Erro ao inicializar banco:", err);
  process.exit(1);
});

// Rotas
app.use("/api", authRoutes);
app.use("/api", uploadRoutes);
app.use("/api", tableRoutes);
app.use("/api", validationRoutes);
app.use("/api", naturezaRoutes);

// Health check
app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    system: "Easy Social",
    version: "1.0.0",
    author: "Xandao",
  });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`✅ Servidor rodando em http://localhost:${PORT}`);
});

export default app;
