"""
Easy e-Social — Robô eSocial (PyAutoGUI)
Developed By Xandao

Bot automático para correção de rubricas no eSocial.
Opera via PyAutoGUI (mouse/teclado reais) — indetectável pelo eSocial.

Pré-requisitos:
  1. Certificado digital instalado no Windows
  2. Usuário loga manualmente no eSocial 
  3. Navega até: Empregador > Tabelas > Tabela de Rubricas
  4. Inicia o bot via API ou terminal
"""
import psycopg2
import pyautogui
import time
import json
import os
import sys
import keyboard
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from enum import Enum
from PIL import Image

# Segurança: PyAutoGUI FAILSAFE — mova o mouse pro canto superior esquerdo pra abortar
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3  # Pausa de 300ms entre cada ação

# ============================================================
# CONFIGURAÇÃO
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "easy_social_user"),
    "password": os.getenv("DB_PASSWORD", "sua_senha_segura"),
    "database": os.getenv("DB_NAME", "easy_social_db"),
}

# Diretório para salvar screenshots de referência e debug
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Diretório para imagens de referência dos elementos do eSocial
REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "referencias")
os.makedirs(REFERENCE_DIR, exist_ok=True)

# Arquivo de calibração com coordenadas dos elementos
CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), "calibration.json")

# Delays entre ações (em segundos) — ajustar conforme velocidade da internet
DELAYS = {
    "after_click": 0.5,
    "after_type": 0.3,
    "page_load": 3.0,
    "after_search": 3.0,
    "after_save": 3.0,
    "between_rubricas": 2.0,
}

# ============================================================
# DATA CLASSES
# ============================================================

class BotStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class Divergencia:
    id: int
    tabela_eb_id: int
    cod_rubrica: str
    descricao: str
    inss_antes: str
    irrf_antes: str
    fgts_antes: str
    inss_correto: str
    irrf_correto: str
    fgts_correto: str
    status: str


@dataclass
class BotState:
    status: BotStatus = BotStatus.IDLE
    current_rubrica: Optional[Divergencia] = None
    current_step: str = ""
    total_pendentes: int = 0
    total_corrigidas: int = 0
    total_erros: int = 0
    log: list = None
    started_at: Optional[str] = None

    def __post_init__(self):
        if self.log is None:
            self.log = []

    def add_log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        self.log.append(entry)
        print(entry)
        # Manter só os últimos 200 logs em memória
        if len(self.log) > 200:
            self.log = self.log[-200:]


# Estado global do bot
bot_state = BotState()

# ============================================================
# BANCO DE DADOS
# ============================================================

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_pendentes() -> list[Divergencia]:
    """Retorna todas as divergências pendentes"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, tabela_eb_id, cod_rubrica, descricao,
                   inss_antes, irrf_antes, fgts_antes,
                   inss_correto, irrf_correto, fgts_correto, status
            FROM rubrica_corrections
            WHERE status = 'pendente'
            ORDER BY cod_rubrica::int, id
        """)
        rows = cur.fetchall()
        return [Divergencia(*row) for row in rows]
    finally:
        conn.close()


def marcar_corrigido(correction_id: int, observacao: str = ""):
    """Marca uma correção como realizada no banco"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE rubrica_corrections
            SET status = 'corrigido', corrigido_em = NOW(), observacao = %s
            WHERE id = %s
        """, (observacao, correction_id))
        conn.commit()
    finally:
        conn.close()


def marcar_erro(correction_id: int, erro: str):
    """Marca uma correção com erro"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE rubrica_corrections
            SET status = 'erro', observacao = %s
            WHERE id = %s
        """, (erro, correction_id))
        conn.commit()
    finally:
        conn.close()


def get_resumo() -> dict:
    """Retorna contagem por status"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'pendente') as pendentes,
                COUNT(*) FILTER (WHERE status = 'corrigido') as corrigidas,
                COUNT(*) FILTER (WHERE status = 'erro') as erros
            FROM rubrica_corrections
        """)
        row = cur.fetchone()
        return {
            "total": row[0],
            "pendentes": row[1],
            "corrigidas": row[2],
            "erros": row[3],
        }
    finally:
        conn.close()


# ============================================================
# FUNÇÕES DE SCREENSHOT / REFERÊNCIA
# ============================================================

def take_screenshot(name: str = "debug") -> str:
    """Tira screenshot e salva na pasta screenshots/"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    pyautogui.screenshot(filepath)
    bot_state.add_log(f"📸 Screenshot salvo: {filename}")
    return filepath


def find_on_screen(image_name: str, confidence: float = 0.8, timeout: int = 10):
    """
    Procura uma imagem de referência na tela.
    Retorna (x, y) do centro se encontrar, None se não.
    """
    image_path = os.path.join(REFERENCE_DIR, image_name)
    if not os.path.exists(image_path):
        bot_state.add_log(f"⚠️ Imagem de referência não encontrada: {image_name}")
        return None

    start = time.time()
    while time.time() - start < timeout:
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                return center
        except pyautogui.ImageNotFoundException:
            pass
        time.sleep(0.5)

    bot_state.add_log(f"❌ Elemento não encontrado na tela: {image_name}")
    return None


# ============================================================
# CALIBRAÇÃO — Coordenadas dos elementos na tela
# ============================================================

def load_calibration():
    """Carrega coordenadas salvas"""
    if not os.path.exists(CALIBRATION_FILE):
        return None
    with open(CALIBRATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_calibration(data: dict):
    """Salva coordenadas no arquivo JSON"""
    with open(CALIBRATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def wait_for_f2() -> list:
    """Espera F2 e retorna [x, y] do mouse"""
    keyboard.wait("f2")
    pos = pyautogui.position()
    time.sleep(0.3)  # debounce
    return [pos.x, pos.y]


def crop_reference(x: int, y: int, name: str, w: int = 150, h: int = 40) -> str:
    """Recorta região ao redor do ponto e salva como imagem de referência"""
    screenshot = pyautogui.screenshot()
    left = max(0, x - w // 2)
    top = max(0, y - h // 2)
    right = min(screenshot.width, x + w // 2)
    bottom = min(screenshot.height, y + h // 2)
    cropped = screenshot.crop((left, top, right, bottom))
    path = os.path.join(REFERENCE_DIR, f"{name}.png")
    cropped.save(path)
    return path


def calibrate_mode():
    """
    Modo interativo de calibração.
    O usuário posiciona o mouse sobre cada elemento e pressiona F2.
    Funciona em qualquer resolução de tela.
    """
    print("=" * 60)
    print("  CALIBRAÇÃO DO BOT eSocial")
    print("=" * 60)
    print()
    print("Você vai posicionar o mouse sobre cada elemento e pressionar F2.")
    print("⚠️  NÃO clique nos elementos — apenas posicione o mouse e F2.")
    print()
    print("Pré-requisitos:")
    print("  ✓ Chrome aberto com eSocial logado")
    print("  ✓ Na página: Tabela de Rubricas")
    print("  ✓ Uma rubrica já pesquisada (com resultado visível)")
    print()

    cal = {}

    # 1 — Campo de código
    print("[1/7] Campo 'Código da rubrica'")
    print("  Posicione o mouse sobre o campo de texto e pressione F2...")
    cal["campo_codigo"] = wait_for_f2()
    print(f"  ✅ Capturado: ({cal['campo_codigo'][0]}, {cal['campo_codigo'][1]})")

    # 2 — Botão Alterar (resultado)
    print("\n[2/7] Botão 'Alterar' (no resultado da pesquisa)")
    print("  Posicione o mouse sobre o botão Alterar e pressione F2...")
    cal["btn_alterar"] = wait_for_f2()
    crop_reference(cal["btn_alterar"][0], cal["btn_alterar"][1], "btn_alterar")
    print(f"  ✅ Capturado + referência salva")

    # Transição: usuário clica em Alterar pra abrir edição
    print("\n  ★ AGORA: Clique no 'Alterar' para abrir a tela de edição.")
    print("    Quando a tela de edição carregar, pressione F2...")
    keyboard.wait("f2")
    time.sleep(0.5)
    take_screenshot("calibracao_tela_edicao")
    print("  ✅ Tela de edição detectada")

    # 3 — Dropdown INSS
    print("\n[3/7] Dropdown 'Incidência Tributária - Previdência Social' (INSS)")
    print("  Posicione o mouse sobre o dropdown e pressione F2...")
    cal["dropdown_inss"] = wait_for_f2()
    print(f"  ✅ Capturado: ({cal['dropdown_inss'][0]}, {cal['dropdown_inss'][1]})")

    # 4 — Dropdown IRRF
    print("\n[4/7] Dropdown 'Incidência Tributária – IRRF'")
    print("  Posicione o mouse sobre o dropdown e pressione F2...")
    cal["dropdown_irrf"] = wait_for_f2()
    print(f"  ✅ Capturado: ({cal['dropdown_irrf'][0]}, {cal['dropdown_irrf'][1]})")

    # 5 — Dropdown FGTS
    print("\n[5/7] Dropdown 'Incidência Tributária - FGTS'")
    print("  Posicione o mouse sobre o dropdown e pressione F2...")
    cal["dropdown_fgts"] = wait_for_f2()
    print(f"  ✅ Capturado: ({cal['dropdown_fgts'][0]}, {cal['dropdown_fgts'][1]})")

    # 6 — Botão Salvar (Alterar na edição)
    print("\n[6/7] Botão 'Alterar' (salvar, na parte de cima da edição)")
    print("  Posicione o mouse sobre o botão e pressione F2...")
    cal["btn_salvar"] = wait_for_f2()
    crop_reference(cal["btn_salvar"][0], cal["btn_salvar"][1], "btn_salvar", w=120, h=35)
    print(f"  ✅ Capturado: ({cal['btn_salvar'][0]}, {cal['btn_salvar'][1]})")

    # 7 — Link voltar (breadcrumb)
    print("\n[7/7] Link 'Tabela de Rubricas' (no breadcrumb para voltar)")
    print("  Posicione o mouse sobre o link no caminho de navegação e pressione F2...")
    cal["link_voltar"] = wait_for_f2()
    print(f"  ✅ Capturado: ({cal['link_voltar'][0]}, {cal['link_voltar'][1]})")

    # Metadados
    cal["screen_resolution"] = list(pyautogui.size())
    cal["calibrated_at"] = datetime.now().isoformat()

    save_calibration(cal)
    take_screenshot("calibracao_final")

    print("\n" + "=" * 60)
    print("  ★ CALIBRAÇÃO CONCLUÍDA! ★")
    print("=" * 60)
    print(f"\n  Salvo em: {CALIBRATION_FILE}")
    print(f"  Referências em: {REFERENCE_DIR}")
    print(f"\n  Para iniciar o bot:")
    print(f"    python bot_esocial.py --run")


# Compatibilidade com código antigo
def capture_reference_mode():
    calibrate_mode()


# ============================================================
# MOTOR DO BOT — AÇÕES NO eSocial
# ============================================================

def check_abort():
    """Verifica se o usuário quer parar (tecla ESC ou mouse no canto)"""
    if bot_state.status == BotStatus.STOPPED:
        raise KeyboardInterrupt("Bot parado pelo usuário")
    if keyboard.is_pressed('esc'):
        bot_state.add_log("🛑 ESC pressionado — parando bot")
        bot_state.status = BotStatus.STOPPED
        raise KeyboardInterrupt("ESC pressionado")


def wait(seconds: float, reason: str = ""):
    """Espera com checagem de abort"""
    if reason:
        bot_state.add_log(f"⏳ Aguardando {seconds}s — {reason}")
    end_time = time.time() + seconds
    while time.time() < end_time:
        check_abort()
        time.sleep(0.1)


def safe_click(x: int, y: int, description: str = ""):
    """Clica com log e delay"""
    check_abort()
    bot_state.add_log(f"🖱️ Click ({x}, {y}) — {description}")
    pyautogui.click(x, y)
    time.sleep(DELAYS["after_click"])


def safe_type(text: str, description: str = ""):
    """Digita texto com log e delay"""
    check_abort()
    bot_state.add_log(f"⌨️ Digitando: '{text}' — {description}")
    pyautogui.typewrite(str(text), interval=0.05)
    time.sleep(DELAYS["after_type"])


def safe_hotkey(*keys, description: str = ""):
    """Pressiona combinação de teclas"""
    check_abort()
    bot_state.add_log(f"⌨️ Hotkey: {'+'.join(keys)} — {description}")
    pyautogui.hotkey(*keys)
    time.sleep(DELAYS["after_click"])


# ============================================================
# FLUXO PRINCIPAL DO BOT — Baseado no eSocial real
# ============================================================

def select_dropdown_value(x: int, y: int, code: str, label: str = ""):
    """
    Seleciona valor em dropdown <select> do eSocial pelo código numérico.
    Funciona via type-ahead do Chrome: clica, digita o código, Enter.
    """
    check_abort()
    code_str = str(code).zfill(2)
    bot_state.add_log(f"🔽 Dropdown {label}: selecionando {code_str}")

    # Clicar no dropdown para abrir
    pyautogui.click(x, y)
    time.sleep(0.6)

    # Digitar código para type-ahead match do Chrome
    for digit in code_str:
        pyautogui.press(digit)
        time.sleep(0.05)

    time.sleep(0.4)
    pyautogui.press('enter')
    time.sleep(0.3)


def click_first_alterar(cal: dict) -> bool:
    """
    Encontra e clica no primeiro botão 'Alterar' nos resultados.
    Tenta image matching primeiro, fallback para coordenadas calibradas.
    """
    # Image matching (mais confiável entre buscas diferentes)
    ref = os.path.join(REFERENCE_DIR, "btn_alterar.png")
    if os.path.exists(ref):
        try:
            locations = list(pyautogui.locateAllOnScreen(ref, confidence=0.75))
            if locations:
                # Primeiro match = resultado mais acima na tela
                first = min(locations, key=lambda loc: loc.top)
                center = pyautogui.center(first)
                safe_click(center.x, center.y, "Alterar (imagem)")
                return True
        except Exception:
            pass

    # Fallback: coordenadas calibradas
    coords = cal.get("btn_alterar")
    if coords:
        safe_click(coords[0], coords[1], "Alterar (coords)")
        return True

    bot_state.add_log("❌ Botão Alterar não encontrado")
    return False


def processar_rubrica(div: Divergencia, cal: dict) -> bool:
    """
    Processa uma rubrica divergente no eSocial.
    Fluxo: buscar → Alterar → mudar dropdowns INSS/IRRF/FGTS → salvar → voltar.
    """
    bot_state.current_rubrica = div
    bot_state.add_log(f"{'='*50}")
    bot_state.add_log(f"📋 Rubrica {div.cod_rubrica} — {div.descricao}")

    changes = []
    if div.inss_antes != div.inss_correto:
        changes.append(f"INSS: {div.inss_antes}→{div.inss_correto}")
    if div.irrf_antes != div.irrf_correto:
        changes.append(f"IRRF: {div.irrf_antes}→{div.irrf_correto}")
    if div.fgts_antes != div.fgts_correto:
        changes.append(f"FGTS: {div.fgts_antes}→{div.fgts_correto}")
    bot_state.add_log(f"  Correções: {', '.join(changes)}")

    try:
        # ETAPA 1: Buscar rubrica
        bot_state.current_step = "Buscando rubrica"
        bot_state.add_log("🔍 Etapa 1: Buscar rubrica")
        safe_click(cal["campo_codigo"][0], cal["campo_codigo"][1], "Campo código")
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.typewrite(str(div.cod_rubrica), interval=0.05)
        pyautogui.press('enter')
        wait(DELAYS["after_search"], "Resultados")

        # ETAPA 2: Clicar em Alterar (primeiro resultado)
        bot_state.current_step = "Abrindo edição"
        bot_state.add_log("✏️ Etapa 2: Clicar em Alterar")
        if not click_first_alterar(cal):
            take_screenshot(f"erro_alterar_{div.cod_rubrica}")
            return False
        wait(DELAYS["page_load"], "Tela de edição")

        # ETAPA 3: Alterar dropdowns
        bot_state.current_step = "Aplicando correções"
        bot_state.add_log("🔧 Etapa 3: Alterar dropdowns")

        if div.inss_antes != div.inss_correto:
            select_dropdown_value(
                cal["dropdown_inss"][0], cal["dropdown_inss"][1],
                div.inss_correto, "INSS"
            )

        if div.irrf_antes != div.irrf_correto:
            select_dropdown_value(
                cal["dropdown_irrf"][0], cal["dropdown_irrf"][1],
                div.irrf_correto, "IRRF"
            )

        if div.fgts_antes != div.fgts_correto:
            select_dropdown_value(
                cal["dropdown_fgts"][0], cal["dropdown_fgts"][1],
                div.fgts_correto, "FGTS"
            )

        # ETAPA 4: Salvar (botão Alterar da edição)
        bot_state.current_step = "Salvando"
        bot_state.add_log("💾 Etapa 4: Salvar")
        safe_click(cal["btn_salvar"][0], cal["btn_salvar"][1], "Salvar (Alterar)")
        wait(DELAYS["after_save"], "Salvamento")
        take_screenshot(f"salvo_{div.cod_rubrica}")

        # ETAPA 5: Voltar para busca (breadcrumb)
        bot_state.current_step = "Voltando"
        bot_state.add_log("↩️ Etapa 5: Voltar para busca")
        safe_click(cal["link_voltar"][0], cal["link_voltar"][1], "Voltar (breadcrumb)")
        wait(DELAYS["page_load"], "Página de busca")

        bot_state.add_log(f"✅ Rubrica {div.cod_rubrica} corrigida!")
        return True

    except KeyboardInterrupt:
        raise
    except Exception as e:
        bot_state.add_log(f"❌ ERRO rubrica {div.cod_rubrica}: {str(e)}")
        take_screenshot(f"erro_{div.cod_rubrica}")
        # Tentar voltar para a busca
        try:
            safe_click(cal["link_voltar"][0], cal["link_voltar"][1], "Voltando após erro")
            wait(DELAYS["page_load"])
        except Exception:
            pass
        return False


def run_bot():
    """Loop principal do bot — corrige todas as rubricas pendentes"""
    # Carregar calibração
    cal = load_calibration()
    if not cal:
        bot_state.add_log("❌ Calibração não encontrada! Execute: python bot_esocial.py --calibrate")
        bot_state.status = BotStatus.ERROR
        return

    # Verificar resolução
    current_res = list(pyautogui.size())
    if cal.get("screen_resolution") != current_res:
        bot_state.add_log(
            f"⚠️ Resolução mudou: {cal.get('screen_resolution')} → {current_res}"
        )
        bot_state.add_log("⚠️ Recomenda-se recalibrar (--calibrate)")

    bot_state.status = BotStatus.RUNNING
    bot_state.started_at = datetime.now().isoformat()
    bot_state.total_erros = 0

    pendentes = get_pendentes()
    bot_state.total_pendentes = len(pendentes)
    bot_state.total_corrigidas = 0

    bot_state.add_log(f"🚀 BOT INICIADO — {len(pendentes)} rubricas pendentes")
    bot_state.add_log(f"⚠️ FAILSAFE: mouse no canto superior esquerdo = ABORTAR")
    bot_state.add_log(f"⚠️ ESC = PARAR")
    bot_state.add_log(f"📐 Calibração de {cal.get('calibrated_at', '?')}")

    # Countdown
    for i in range(5, 0, -1):
        bot_state.add_log(f"⏳ Iniciando em {i}...")
        time.sleep(1)
        check_abort()

    for i, div in enumerate(pendentes):
        check_abort()

        if i > 0:
            wait(DELAYS["between_rubricas"], "Pausa entre rubricas")

        success = processar_rubrica(div, cal)

        if success:
            marcar_corrigido(div.id, f"Bot {datetime.now().isoformat()}")
            bot_state.total_corrigidas += 1
        else:
            marcar_erro(div.id, f"Bot erro {datetime.now().isoformat()}")
            bot_state.total_erros += 1

        bot_state.add_log(
            f"📊 Progresso: {bot_state.total_corrigidas}/{bot_state.total_pendentes} "
            f"(erros: {bot_state.total_erros})"
        )

    bot_state.status = BotStatus.IDLE
    bot_state.add_log(
        f"🏁 FINALIZADO — {bot_state.total_corrigidas} corrigidas, "
        f"{bot_state.total_erros} erros"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    if "--calibrate" in sys.argv or "--capture" in sys.argv:
        calibrate_mode()
    elif "--status" in sys.argv:
        resumo = get_resumo()
        cal = load_calibration()
        print(f"\n📊 Status das Correções:")
        print(f"   Total:      {resumo['total']}")
        print(f"   Pendentes:  {resumo['pendentes']}")
        print(f"   Corrigidas: {resumo['corrigidas']}")
        print(f"   Erros:      {resumo['erros']}")
        print(f"\n📐 Calibração: {'✅ ' + cal['calibrated_at'] if cal else '❌ Não calibrado'}")
    elif "--run" in sys.argv:
        try:
            run_bot()
        except KeyboardInterrupt:
            bot_state.add_log("🛑 Bot interrompido pelo usuário")
            bot_state.status = BotStatus.STOPPED
    else:
        print("Easy e-Social — Bot eSocial")
        print()
        print("Comandos:")
        print("  python bot_esocial.py --calibrate  Calibrar (marcar posições dos elementos)")
        print("  python bot_esocial.py --status     Ver status das correções no banco")
        print("  python bot_esocial.py --run        Iniciar o bot")
        print()
        print("FLUXO:")
        print("  1. Logue no eSocial com certificado digital")
        print("  2. Navegue até: Empregador > Tabelas > Tabela de Rubricas")
        print("  3. Pesquise qualquer rubrica (pra ter resultado na tela)")
        print("  4. Rode: python bot_esocial.py --calibrate")
        print("  5. Rode: python bot_esocial.py --run")
        print("  4. Recorte as imagens de referência")
        print("  5. Aí sim: python bot_esocial.py --run")
