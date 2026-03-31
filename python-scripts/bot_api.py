"""
Easy e-Social — API de controle do Bot eSocial
Developed By Xandao

Roda em porta 8000. O frontend Vue se comunica com esta API
para iniciar, parar e monitorar o robô.
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import os
import glob
import uvicorn

from bot_esocial import (
    bot_state,
    BotStatus,
    run_bot,
    get_resumo,
    get_pendentes,
    calibrate_mode,
    capture_reference_mode,
    take_screenshot,
    load_calibration,
)

app = FastAPI(
    title="Easy e-Social — Bot Control API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https://.*\.trycloudflare\.com$",
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3333",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas eSocial (certificados A1)
from esocial.certificate_routes import router as cert_router
app.include_router(cert_router)

# Rotas eSocial (orquestração S-1010)
from esocial.esocial_routes import router as esocial_router
app.include_router(esocial_router)

# Rotas De-Para (mapeamento de campos S-1010)
from esocial.depara_routes import router as depara_router
app.include_router(depara_router)

# Rotas Cruzamento EB Skills
from esocial.cruzamento_eb_routes import router as cruzamento_eb_router
app.include_router(cruzamento_eb_router)

# Thread do bot
bot_thread: threading.Thread | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "system": "Easy e-Social Bot API", "version": "2.0.0"}


@app.get("/bot/status")
async def get_bot_status():
    """Retorna estado atual do bot + resumo do banco"""
    resumo = get_resumo()
    cal = load_calibration()
    current = None
    if bot_state.current_rubrica:
        current = {
            "cod_rubrica": bot_state.current_rubrica.cod_rubrica,
            "descricao": bot_state.current_rubrica.descricao,
            "inss_antes": bot_state.current_rubrica.inss_antes,
            "irrf_antes": bot_state.current_rubrica.irrf_antes,
            "fgts_antes": bot_state.current_rubrica.fgts_antes,
            "inss_correto": bot_state.current_rubrica.inss_correto,
            "irrf_correto": bot_state.current_rubrica.irrf_correto,
            "fgts_correto": bot_state.current_rubrica.fgts_correto,
        }

    return {
        "bot_status": bot_state.status.value,
        "current_step": bot_state.current_step,
        "current_rubrica": current,
        "total_pendentes": resumo["pendentes"],
        "total_corrigidas": resumo["corrigidas"],
        "total_erros": resumo["erros"],
        "total": resumo["total"],
        "started_at": bot_state.started_at,
        "calibrated": cal is not None,
        "calibrated_at": cal.get("calibrated_at") if cal else None,
        "log": bot_state.log[-50:],
    }


@app.post("/bot/start")
async def start_bot():
    """Inicia o bot em background"""
    global bot_thread

    if bot_state.status == BotStatus.RUNNING:
        return {"error": "Bot já está rodando"}

    def _run():
        try:
            run_bot()
        except KeyboardInterrupt:
            bot_state.add_log("🛑 Bot interrompido")
            bot_state.status = BotStatus.STOPPED
        except Exception as e:
            bot_state.add_log(f"❌ Erro fatal: {str(e)}")
            bot_state.status = BotStatus.ERROR

    bot_thread = threading.Thread(target=_run, daemon=True)
    bot_thread.start()

    return {"success": True, "message": "Bot iniciado"}


@app.post("/bot/stop")
async def stop_bot():
    """Para o bot"""
    bot_state.status = BotStatus.STOPPED
    bot_state.add_log("🛑 Parada solicitada pelo usuário")
    return {"success": True, "message": "Bot será parado na próxima iteração"}


@app.post("/bot/screenshot")
async def do_screenshot():
    """Tira um screenshot da tela atual"""
    filepath = take_screenshot("manual")
    return {"success": True, "path": filepath}


@app.get("/bot/screenshot/view")
async def view_screenshot():
    """Retorna a imagem do screenshot mais recente"""
    screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    if not os.path.isdir(screenshots_dir):
        return {"error": "Nenhum screenshot encontrado"}
    files = sorted(glob.glob(os.path.join(screenshots_dir, "*.png")), key=os.path.getmtime, reverse=True)
    if not files:
        return {"error": "Nenhum screenshot encontrado"}
    return FileResponse(files[0], media_type="image/png")


@app.get("/bot/divergencias")
async def list_divergencias():
    """Lista resumida de divergências para o frontend"""
    resumo = get_resumo()
    return resumo


if __name__ == "__main__":
    print("=" * 50)
    print("  Easy e-Social — Bot Control API")
    print("  http://localhost:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
