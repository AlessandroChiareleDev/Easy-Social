<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'
import { PYTHON_API } from '@/lib/api'

interface CPFRow {
  cpf: string
  nome: string | null
  matricula: string | null
  identificador?: string | null
  origem?: 'cpf_scope' | 'codfunc_scope' | string | null
  lote_num: number
  status: 'pendente' | 'ok' | 'erro' | 'enviando' | 'na'
  nr_recibo_novo: string | null
  nr_recibo_usado: string | null
  erro_descricao: string | null
  enviado_em: string | null
  nr_recibo_zip: string | null
  codigo_resposta: number | null
  descricao_resposta: string | null
}

// Extrai código/descrição da ocorrência do erro_descricao (formato:
//   "processamento_rejeitado | Código 401: ... | ... | ocorrencias=[{...}]")
function parseErroOcorrencia(s: string | null): { codigo: string; descricao: string } {
  if (!s) return { codigo: '', descricao: '' }
  const m = s.match(/ocorrencias=(\[.*\])/)
  if (m) {
    try {
      const arr = JSON.parse(m[1]) as { codigo?: string; descricao?: string }[]
      if (arr.length) {
        const primeira = arr[0]
        return {
          codigo: primeira.codigo ?? '',
          descricao: primeira.descricao ?? '',
        }
      }
    } catch {
      /* ignore */
    }
  }
  // fallback: "Código 401: descricao"
  const m2 = s.match(/Código\s+(\d+):\s*([^|]+)/i)
  if (m2) return { codigo: m2[1], descricao: m2[2].trim() }
  return { codigo: '', descricao: s.slice(0, 120) }
}

interface EnvioResultado {
  sucesso: boolean
  etapa?: string
  cpf?: string
  erro?: string
  descricao?: string
  codigo_resposta?: string | number
  nr_recibo_novo?: string
  nr_recibo_usado?: string
  ocorrencias?: Array<{ codigo?: string; descricao?: string; tipo?: string }>
  protocolo?: string
}

interface Pagamento {
  dt_pgto: string
  tp_pgto: string
  tp_pgto_label: string
  per_ref: string | null
  ide_dm_dev: string
  vr_liq: number | null
  vr_liq_raw: string
}
interface InfoIR {
  tp_cr: string
  tp_cr_label: string
  vr_cr: number | null
  vr_cr_raw: string
}
interface EnvioHist {
  status: string
  codigo_resposta: string | null
  descricao_resposta: string | null
  nr_recibo_usado: string | null
  nr_recibo_novo: string | null
  protocolo: string | null
  erro_descricao: string | null
  enviado_em: string | null
}
interface DetalheCpf {
  cpf: string
  nome: string | null
  matricula: string | null
  lote_num: number
  per_apur: string
  zip_encontrado: boolean
  zip_erro: string | null
  ind_retif_original: string | null
  dh_processamento: string | null
  nr_recibo_zip: string | null
  nr_recibo_ativo: string | null
  recibo_fonte: string | null
  cadeia_candidatos: number
  pagamentos: Pagamento[]
  total_vr_liq: number | null
  info_ir: InfoIR[]
  s5002_list: S5002Record[]
  s5002_ativo: S5002Record | null
  ir_efetivo_valor: number | null
  ir_efetivo_fonte: string | null
  status_atual: string
  ultimo_envio: EnvioHist | null
  historico_envios: EnvioHist[]
  qtd_envios: number
  empregador_cnpj_raiz: string
  tp_amb: string
  proc_emi: string
  ver_proc: string
}
interface S5002InfoIR {
  tp_info_ir: string
  tp_info_ir_label: string
  valor: number | null
}
interface S5002Record {
  nr_recibo: string
  id: string
  vazio: boolean
  cr_men: string | null
  vlr_rend_trib: number | null
  vlr_prev_oficial: number | null
  vlr_ir_retido: number | null
  info_ir: S5002InfoIR[]
}

const route = useRoute()
const router = useRouter()

const lote = computed(() => Number(route.params.lote))
const mes = computed(() => String(route.params.mes))

const mesLabels: Record<string, string> = {
  '2025-01': 'Jan/2025',
  '2025-02': 'Fev/2025',
  '2025-03': 'Mar/2025',
  '2025-04': 'Abr/2025',
}
const descricaoLote: Record<number, string> = {
  1: 'Sem plano de saúde — S-1210 sem planSaude',
  2: 'Plano de saúde com operadora — grupo A',
  3: 'Plano de saúde com operadora — grupo B',
  4: 'Casos manuais / especiais',
}

const loading = ref(true)
const erro = ref('')
const total = ref(0)
const rows = ref<CPFRow[]>([])
const totaisCompartimento = ref({ total: 0, ok: 0, erro: 0, enviando: 0, pendente: 0, na: 0 })
const filtro = ref('')
const statusFiltro = ref<'todos' | 'pendente' | 'ok' | 'erro' | 'na'>('todos')
const pagina = ref(0)
const pageSize = 200

// ── Filtro tipo Excel na coluna Código ──
// Chave = "<cdResposta>/<codOcorrencia>" (ex.: "401/1043", "201/", "erro/buscar_recibo")
// vazio = sem filtro (mostra tudo)
const codigosSelecionados = ref<Set<string>>(new Set())
const codigoFilterOpen = ref(false)
// Agregação vinda do backend — considera o compartimento INTEIRO
// (independente da página atual de rows). Preenchido em carregarCodigosAgregados().
interface CodigoBucket {
  chave: string
  descricao: string
  qtd: number
  tipo: 'ok' | 'err' | 'none'
}
const codigosAgregados = ref<CodigoBucket[]>([])
function codigoChave(r: CPFRow): string {
  if (r.status === 'ok') return `${r.codigo_resposta ?? '201'}/`
  if (r.status === 'erro') {
    const oc = parseErroOcorrencia(r.erro_descricao).codigo
    return `${r.codigo_resposta ?? 'erro'}/${oc}`
  }
  return ''
}
function codigoChaveLabel(chave: string): string {
  const [cd, oc] = chave.split('/')
  if (!oc) return cd || '—'
  return `${cd}/${oc}`
}
function codigoChaveDescricao(chave: string, r: CPFRow): string {
  if (chave.endsWith('/')) return r.descricao_resposta || 'Sucesso'
  const oc = parseErroOcorrencia(r.erro_descricao)
  return oc.descricao || r.descricao_resposta || '—'
}
const codigosDisponiveis = computed(() => {
  // Preferência: dados agregados do backend (compartimento inteiro).
  if (codigosAgregados.value.length > 0) return codigosAgregados.value
  // Fallback: agrega a partir das linhas da página atual (estado inicial).
  const map = new Map<
    string,
    { chave: string; descricao: string; qtd: number; tipo: 'ok' | 'err' | 'none' }
  >()
  for (const r of rows.value) {
    const chave = codigoChave(r)
    if (!chave) continue
    const existente = map.get(chave)
    if (existente) {
      existente.qtd++
    } else {
      map.set(chave, {
        chave,
        descricao: codigoChaveDescricao(chave, r),
        qtd: 1,
        tipo: r.status === 'ok' ? 'ok' : r.status === 'erro' ? 'err' : 'none',
      })
    }
  }
  return Array.from(map.values()).sort((a, b) => b.qtd - a.qtd)
})
function toggleCodigo(chave: string) {
  const s = new Set(codigosSelecionados.value)
  if (s.has(chave)) s.delete(chave)
  else s.add(chave)
  codigosSelecionados.value = s
}
function limparCodigoFiltro() {
  codigosSelecionados.value = new Set()
}
function selecionarTodosCodigos() {
  codigosSelecionados.value = new Set(codigosDisponiveis.value.map((c) => c.chave))
}
function fecharCodigoFilter(ev: MouseEvent) {
  const alvo = ev.target as HTMLElement
  if (alvo.closest('.cod-filter') || alvo.closest('.cod-filter-btn')) return
  codigoFilterOpen.value = false
}
watch(codigoFilterOpen, (aberto) => {
  if (aberto) {
    setTimeout(() => document.addEventListener('click', fecharCodigoFilter), 0)
  } else {
    document.removeEventListener('click', fecharCodigoFilter)
  }
})

// ── Miniterminal ──
type LogLevel = 'info' | 'ok' | 'err' | 'warn'
interface LogLine {
  id: number
  hora: string
  nivel: LogLevel
  texto: string
}
const logs = ref<LogLine[]>([])
let logSeq = 0
function log(nivel: LogLevel, texto: string) {
  const h = new Date().toLocaleTimeString('pt-BR', { hour12: false })
  logs.value.push({ id: ++logSeq, hora: h, nivel, texto })
  if (logs.value.length > 200) logs.value.shift()
  setTimeout(() => {
    const el = document.getElementById('mini-term-body')
    if (el) el.scrollTop = el.scrollHeight
  }, 10)
}
function limparLogs() {
  logs.value = []
}

async function carregar() {
  loading.value = true
  erro.value = ''
  try {
    const offset = pagina.value * pageSize
    const params: Record<string, unknown> = {
      limit: pageSize,
      offset,
      status: statusFiltro.value,
    }
    const q = filtro.value.trim()
    if (q) params.q = q
    const resp = await axios.get<{
      total: number
      totais: {
        total: number
        ok: number
        erro: number
        enviando: number
        pendente: number
        na?: number
      }
      cpfs: CPFRow[]
    }>(`${PYTHON_API}/api/s1210-repo/por-lote/${lote.value}/${mes.value}`, { params })
    total.value = resp.data.total
    rows.value = resp.data.cpfs
    totaisCompartimento.value = resp.data.totais
  } catch (e: unknown) {
    const err = e as { message?: string }
    erro.value = err.message ?? 'erro'
    log('err', `Falha ao carregar: ${erro.value}`)
  } finally {
    loading.value = false
  }
}

async function carregarCodigosAgregados() {
  try {
    const resp = await axios.get<{ codigos: CodigoBucket[]; total: number }>(
      `${PYTHON_API}/api/s1210-repo/codigos-agregados/${lote.value}/${mes.value}`,
    )
    codigosAgregados.value = resp.data.codigos || []
  } catch (e) {
    // silencioso: fallback usa linhas da página atual
    codigosAgregados.value = []
  }
}

const linhasFiltradas = computed(() => {
  const q = filtro.value.trim().toLowerCase()
  const qDigits = q.replace(/\D+/g, '') // "025.879.754-17" → "02587975417"
  const codSel = codigosSelecionados.value
  const temCodFiltro = codSel.size > 0
  return rows.value.filter((x) => {
    // filtro de código (multi-seleção estilo Excel)
    if (temCodFiltro && !codSel.has(codigoChave(x))) return false
    if (!q) return true
    // CPF: compara ignorando pontos/traço
    if (qDigits && qDigits.length >= 3 && x.cpf.includes(qDigits)) return true
    if (x.cpf.includes(q)) return true
    if ((x.identificador ?? '').toLowerCase().includes(q)) return true
    if ((x.nome ?? '').toLowerCase().includes(q)) return true
    if ((x.matricula ?? '').toLowerCase().includes(q)) return true
    // código de resposta do eSocial (ex.: 201, 401)
    if (x.codigo_resposta != null && String(x.codigo_resposta).includes(q)) return true
    // descrição de resposta (ex.: "Conteudo do evento inválido.")
    if ((x.descricao_resposta ?? '').toLowerCase().includes(q)) return true
    // código/descrição da ocorrência (ex.: 1043, 45, 1089)
    const oc = parseErroOcorrencia(x.erro_descricao)
    if (oc.codigo && oc.codigo.toLowerCase().includes(q)) return true
    if (oc.descricao && oc.descricao.toLowerCase().includes(q)) return true
    // texto bruto do erro (cobre mensagens de etapas pré-eSocial)
    if ((x.erro_descricao ?? '').toLowerCase().includes(q)) return true
    return false
  })
})

function setStatusFiltro(f: 'todos' | 'pendente' | 'ok' | 'erro' | 'na') {
  if (statusFiltro.value === f) return
  statusFiltro.value = f
  pagina.value = 0
  carregar()
}

// Busca server-side com debounce (CPF/nome/matrícula).
// Dispara recarregamento total do compartimento, não só da página atual.
let filtroDebounce: ReturnType<typeof setTimeout> | null = null
watch(filtro, () => {
  if (filtroDebounce) clearTimeout(filtroDebounce)
  filtroDebounce = setTimeout(() => {
    pagina.value = 0
    carregar()
  }, 350)
})

function voltar() {
  router.push('/repositorio-s1210/por-lote')
}
function proximaPagina() {
  if ((pagina.value + 1) * pageSize < total.value) {
    pagina.value++
    carregar()
  }
}
function paginaAnterior() {
  if (pagina.value > 0) {
    pagina.value--
    carregar()
  }
}
function formatCPF(cpf: string): string {
  if (!cpf) return '—'
  return cpf.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4')
}
function rowKey(r: CPFRow, idx: number): string {
  return `${r.cpf || r.identificador || r.matricula || 'sem-id'}-${pagina.value}-${idx}`
}
function identificadorLabel(r: CPFRow): string {
  return r.identificador || r.matricula || '—'
}
function formatDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

// ── Envio ──
const modalCpf = ref<CPFRow | null>(null)
const enviando = ref(false)
function abrirEnvio(row: CPFRow, ev?: Event) {
  ev?.stopPropagation()
  if (!row.cpf) return
  modalCpf.value = row
}
function fecharModal() {
  if (enviando.value) return
  modalCpf.value = null
}

// ── Detalhes do CPF ──
const detalhe = ref<DetalheCpf | null>(null)
const carregandoDetalhe = ref(false)
const erroDetalhe = ref('')

async function abrirDetalhe(row: CPFRow) {
  if (!row.cpf) return
  detalhe.value = null
  erroDetalhe.value = ''
  carregandoDetalhe.value = true
  try {
    const resp = await axios.get<DetalheCpf>(
      `${PYTHON_API}/api/s1210-repo/detalhe-cpf/${row.lote_num}/${mes.value}/${row.cpf}`,
    )
    detalhe.value = resp.data
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    erroDetalhe.value = err.response?.data?.detail ?? err.message ?? 'erro ao carregar detalhes'
  } finally {
    carregandoDetalhe.value = false
  }
}
function fecharDetalhe() {
  detalhe.value = null
  erroDetalhe.value = ''
}
function formatMoney(n: number | null): string {
  if (n == null) return '—'
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
function formatReciboShort(r: string | null): string {
  if (!r) return '—'
  return r.length > 16 ? `…${r.slice(-16)}` : r
}
function copiar(txt: string | null | undefined) {
  if (!txt) return
  navigator.clipboard?.writeText(txt).then(() => log('info', `copiado: ${txt.slice(0, 40)}…`))
}

// ── Envio individual (modal) ──
async function enviarUmCpf(row: CPFRow): Promise<EnvioResultado> {
  const resp = await axios.post<EnvioResultado>(
    `${PYTHON_API}/api/s1210-repo/enviar-cpf`,
    {
      cpf: row.cpf,
      per_apur: mes.value,
      lote_num: row.lote_num,
      confirmar_producao: true,
    },
    { timeout: 180000 },
  )
  return resp.data
}

// ── Envio em LOTE (usado pelo player) — até 50 CPFs por chamada ──
interface LoteResultadoItem {
  cpf: string
  sucesso?: boolean
  etapa?: string
  codigo_resposta?: string | number
  descricao?: string
  nr_recibo_novo?: string
  nr_recibo_usado?: string
  erro?: string
  ocorrencias?: Array<{ codigo?: string; descricao?: string; tipo?: string }>
  retry?: boolean
  idempotente?: boolean
}
interface LoteResposta {
  protocolo?: string
  resumo: {
    ok: number
    ok_idempotente: number
    erro: number
    erro_retry: number
    enviados: number
    total: number
  }
  resultados: LoteResultadoItem[]
  duracao_ms: number
}

async function enviarLoteCpfs(cpfs: string[]): Promise<LoteResposta> {
  const resp = await axios.post<LoteResposta>(
    `${PYTHON_API}/api/s1210-repo/enviar-lote-cpfs`,
    {
      cpfs,
      per_apur: mes.value,
      lote_num: lote.value,
      confirmar_producao: true,
    },
    { timeout: 300000 },
  )
  return resp.data
}

async function confirmarEnvio() {
  if (!modalCpf.value) return
  const row = modalCpf.value
  enviando.value = true
  log(
    'info',
    `▶ Enviando CPF ${formatCPF(row.cpf)} — Lote ${row.lote_num} · ${mesLabels[mes.value] ?? mes.value}`,
  )
  try {
    const r = await enviarUmCpf(row)
    if (r.sucesso) {
      log('ok', `✓ Aceito · recibo novo ${r.nr_recibo_novo} · código ${r.codigo_resposta ?? '—'}`)
      if (r.descricao) log('info', `  ${r.descricao}`)
    } else {
      log('err', `✗ Rejeitado em "${r.etapa}" · ${r.erro ?? r.descricao ?? 'sem detalhe'}`)
      if (r.codigo_resposta) log('err', `  código: ${r.codigo_resposta}`)
      if (r.ocorrencias?.length) {
        for (const o of r.ocorrencias) {
          log('err', `  ocorrência ${o.codigo ?? '?'}: ${o.descricao ?? ''}`)
        }
      }
    }
    fecharModal()
    await carregar()
    carregarCodigosAgregados()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    const msg = err.response?.data?.detail ?? err.message ?? 'erro desconhecido'
    log('err', `✗ Falha no envio: ${msg}`)
  } finally {
    enviando.value = false
  }
}

// ═══════════════════════════════════════════════════════════════════
// PAINEL DE COMANDO — Player automático
// ═══════════════════════════════════════════════════════════════════
type PlayerStatus = 'parado' | 'rodando' | 'pausando'
type TamanhoLote = 1 | 5 | 50
interface ErroItem {
  cpf: string
  nome: string | null
  erro: string
  codigo?: string | number
  etapa?: string
  quando: string
}

const playerStatus = ref<PlayerStatus>('parado')
const tamanhoLote = ref<TamanhoLote>(5)
const modoTodos = ref(false) // 🔒 cadeado: envia TODOS os pendentes em loop
const playerFeitos = ref(0)
const playerOk = ref(0)
const playerErro = ref(0)
const playerAlvo = ref(0) // total planejado para essa rodada (soma de todas as batches quando modoTodos)
const playerBatchAtual = ref(0) // número da batch atual no modo todos
const playerErros = ref<ErroItem[]>([])
const playerErrosExpandido = ref(false)
const confirmacaoPlay = ref(false) // modal de confirmação

// Sinalizadores para o loop
const _stopFlag = ref(false)

function cpfsPendentesNaListaAtual(): CPFRow[] {
  return rows.value.filter((r) => r.status === 'pendente' && !!r.cpf)
}

function pedirPlay() {
  if (playerStatus.value !== 'parado') return
  if (!rows.value.some((r) => !!r.cpf)) {
    log('warn', 'Este compartimento ainda está sem CPF mapeado. Aguarde a chave CPF para envio.')
    return
  }
  const disponiveis = modoTodos.value
    ? totaisCompartimento.value.pendente + totaisCompartimento.value.enviando
    : cpfsPendentesNaListaAtual().length
  if (disponiveis === 0) {
    log(
      'warn',
      modoTodos.value
        ? `Nenhum CPF pendente no Lote ${lote.value} · ${mesLabels[mes.value] ?? mes.value}.`
        : 'Nenhum CPF pendente na página atual.',
    )
    return
  }
  // Para 50 ou modo todos exige confirmação; para 1 e 5 avulsos dispara direto
  if (tamanhoLote.value === 50 || modoTodos.value) {
    confirmacaoPlay.value = true
  } else {
    iniciarPlayer()
  }
}

function confirmarPlay() {
  confirmacaoPlay.value = false
  iniciarPlayer()
}
function cancelarConfirmacao() {
  confirmacaoPlay.value = false
}

/**
 * Processa UMA batch (até 50 CPFs pendentes) em UMA ÚNICA chamada
 * ao backend, que monta um único <envioLoteEventos> no eSocial.
 * Isso elimina o 1089 (simultaneidade) e reduz overhead de polling.
 * Retorna quantos foram processados.
 */
async function _processarBatch(alvo: CPFRow[]): Promise<number> {
  if (!alvo.length) return 0
  const antes = playerFeitos.value
  const cpfs = alvo.map((r) => r.cpf)
  for (const r of alvo) log('info', `  → ${formatCPF(r.cpf)} enviando…`)

  try {
    const resp = await enviarLoteCpfs(cpfs)
    log(
      'info',
      `  ⏱ lote processado em ${(resp.duracao_ms / 1000).toFixed(1)}s · protocolo ${resp.protocolo ?? '—'}`,
    )
    for (const item of resp.resultados) {
      if (_stopFlag.value) break
      playerFeitos.value++
      if (item.sucesso) {
        playerOk.value++
        if (item.idempotente) {
          log('ok', `  ✓ ${formatCPF(item.cpf)} · idempotente (ocorrência 543 — já existia)`)
        } else {
          log(
            'ok',
            `  ✓ ${formatCPF(item.cpf)} · novo ${item.nr_recibo_novo ?? '—'} · cod ${item.codigo_resposta ?? '—'}`,
          )
        }
      } else {
        playerErro.value++
        const descr = item.erro ?? item.descricao ?? 'sem detalhe'
        playerErros.value.unshift({
          cpf: item.cpf,
          nome: alvo.find((a) => a.cpf === item.cpf)?.nome ?? null,
          erro: descr,
          codigo: item.codigo_resposta,
          etapa: item.etapa,
          quando: new Date().toLocaleTimeString('pt-BR', { hour12: false }),
        })
        const tag = item.retry ? '⟳ retry' : '✗'
        log('err', `  ${tag} ${formatCPF(item.cpf)} · ${item.etapa ?? '?'} · ${descr}`)
      }
    }
    log(
      'info',
      `  Σ lote: OK=${resp.resumo.ok} (idempotentes=${resp.resumo.ok_idempotente}) · ERRO=${resp.resumo.erro} (retry=${resp.resumo.erro_retry})`,
    )
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    const msg = err.response?.data?.detail ?? err.message ?? 'erro desconhecido'
    // Marca todos os CPFs do batch como erro de rede
    for (const r of alvo) {
      playerFeitos.value++
      playerErro.value++
      playerErros.value.unshift({
        cpf: r.cpf,
        nome: r.nome,
        erro: msg,
        quando: new Date().toLocaleTimeString('pt-BR', { hour12: false }),
      })
    }
    log('err', `  ✗ Falha de rede no lote: ${msg}`)
  }
  return playerFeitos.value - antes
}

async function iniciarPlayer() {
  const totalPendentes = modoTodos.value
    ? totaisCompartimento.value.pendente + totaisCompartimento.value.enviando
    : cpfsPendentesNaListaAtual().length
  if (totalPendentes === 0) {
    log('warn', 'Nenhum CPF pendente.')
    return
  }

  // Reset dos contadores
  playerFeitos.value = 0
  playerOk.value = 0
  playerErro.value = 0
  playerErros.value = []
  playerBatchAtual.value = 0
  _stopFlag.value = false
  playerStatus.value = 'rodando'

  if (modoTodos.value) {
    playerAlvo.value = totalPendentes
    log(
      'info',
      `▶ Player iniciado (🔒 TODOS do Lote ${lote.value} · ${mesLabels[mes.value] ?? mes.value}) — ${playerAlvo.value} CPF(s) · batches de ${tamanhoLote.value} · 1 lote eSocial por batch (sem concorrência)`,
    )
  } else {
    playerAlvo.value = Math.min(tamanhoLote.value, totalPendentes)
    log(
      'info',
      `▶ Player iniciado — ${playerAlvo.value} CPF(s) · 1 lote eSocial único (sem concorrência)`,
    )
  }

  // Loop de batches
  while (!_stopFlag.value) {
    let pendentes: CPFRow[]
    if (modoTodos.value) {
      // Busca pendentes DIRETO do backend (lote+mês atual), sem depender da página.
      try {
        const resp = await axios.get<{ cpfs: CPFRow[] }>(
          `${PYTHON_API}/api/s1210-repo/por-lote/${lote.value}/${mes.value}`,
          { params: { limit: tamanhoLote.value, offset: 0, status: 'pendente' } },
        )
        pendentes = resp.data.cpfs
      } catch (e: unknown) {
        const err = e as { message?: string }
        log('err', `Falha ao buscar pendentes: ${err.message ?? 'erro'}`)
        break
      }
    } else {
      pendentes = cpfsPendentesNaListaAtual()
    }

    if (pendentes.length === 0) {
      log(
        'info',
        `  (sem mais pendentes no Lote ${lote.value} · ${mesLabels[mes.value] ?? mes.value})`,
      )
      break
    }
    const alvo = pendentes.slice(0, tamanhoLote.value)
    playerBatchAtual.value++
    log('info', `━━ Batch #${playerBatchAtual.value} · ${alvo.length} CPF(s) ━━`)
    const processados = await _processarBatch(alvo)

    // Recarrega a lista para refletir status atualizados
    await carregar()
    carregarCodigosAgregados()

    if (!modoTodos.value) break // modo 1/5/50 sem cadeado → só uma batch
    if (_stopFlag.value) break
    if (processados === 0) break // nada foi feito (travou) — segurança

    // Pequena pausa entre batches para não martelar o servidor
    await new Promise((r) => setTimeout(r, 500))
  }

  playerStatus.value = 'parado'
  _stopFlag.value = false

  const foram = playerFeitos.value
  if (foram > 0) {
    log(
      foram === playerOk.value ? 'ok' : 'warn',
      `■ Player finalizado — ${foram} processado(s) · ${playerOk.value} OK · ${playerErro.value} erro · ${playerBatchAtual.value} batch(es)`,
    )
  }
}

function pedirPause() {
  if (playerStatus.value !== 'rodando') return
  playerStatus.value = 'pausando'
  _stopFlag.value = true
  log('warn', '⏸ Pause solicitado — aguardando envios em andamento finalizarem…')
}

onMounted(() => {
  log('info', `Repositório S-1210 — Lote ${lote.value} · ${mesLabels[mes.value] ?? mes.value}`)
  carregar()
  carregarCodigosAgregados()
})
watch([lote, mes], () => {
  pagina.value = 0
  logs.value = []
  log('info', `Trocou para Lote ${lote.value} · ${mesLabels[mes.value] ?? mes.value}`)
  carregar()
  carregarCodigosAgregados()
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <button class="voltar" @click="voltar"><span class="arrow">←</span> Por Lote</button>
      <div class="title-row">
        <div>
          <div class="kicker">Vertente A · Compartimento</div>
          <h1>Lote {{ lote }} <span class="sep">·</span> {{ mesLabels[mes] ?? mes }}</h1>
          <p class="sub">{{ descricaoLote[lote] }}</p>
        </div>
      </div>
    </header>

    <section class="mini-term" aria-label="Log de operações">
      <header class="mini-term-head">
        <span class="dot dot--r" />
        <span class="dot dot--y" />
        <span class="dot dot--g" />
        <span class="mini-term-title">logs · envios S-1210 em produção</span>
        <button class="limpar" @click="limparLogs">limpar</button>
      </header>
      <div id="mini-term-body" class="mini-term-body">
        <div v-if="logs.length === 0" class="mini-term-empty">aguardando eventos…</div>
        <div v-for="l in logs" :key="l.id" class="mini-term-line" :class="`lvl-${l.nivel}`">
          <span class="hora">{{ l.hora }}</span>
          <span class="txt">{{ l.texto }}</span>
        </div>
      </div>
    </section>

    <div v-if="loading" class="state">Carregando registros…</div>
    <div v-else-if="erro" class="state state--err">{{ erro }}</div>

    <template v-else>
      <div class="kpis">
        <div class="kpi">
          <span class="kpi-label">Total no escopo</span>
          <span class="kpi-val">{{ totaisCompartimento.total.toLocaleString('pt-BR') }}</span>
        </div>
        <div class="kpi kpi--sent">
          <span class="kpi-label">Enviados</span>
          <span class="kpi-val">
            {{ (totaisCompartimento.ok + totaisCompartimento.erro).toLocaleString('pt-BR') }}
          </span>
        </div>
        <div class="kpi kpi--ok">
          <span class="kpi-label">OK</span>
          <span class="kpi-val">{{ totaisCompartimento.ok.toLocaleString('pt-BR') }}</span>
        </div>
        <div class="kpi kpi--err">
          <span class="kpi-label">Erro</span>
          <span class="kpi-val">{{ totaisCompartimento.erro.toLocaleString('pt-BR') }}</span>
        </div>
        <div class="kpi kpi--pend">
          <span class="kpi-label">Pendentes</span>
          <span class="kpi-val">
            {{
              (totaisCompartimento.pendente + totaisCompartimento.enviando).toLocaleString('pt-BR')
            }}
          </span>
        </div>
        <div class="kpi kpi--na">
          <span class="kpi-label">N/A (não aplica)</span>
          <span class="kpi-val">{{ (totaisCompartimento.na ?? 0).toLocaleString('pt-BR') }}</span>
        </div>
      </div>

      <!-- ═══════ PAINEL DE COMANDO (player automático) ═══════ -->
      <section class="player">
        <div class="player-head">
          <div class="player-title">
            <span class="player-ico">▶</span>
            Painel de comando
          </div>
          <div class="player-sizer" role="group" aria-label="Tamanho do lote">
            <span class="sizer-lbl">Enviar</span>
            <button
              v-for="n in [1, 5, 50] as TamanhoLote[]"
              :key="n"
              class="sizer-btn"
              :class="{ 'sizer-btn--on': tamanhoLote === n }"
              :disabled="playerStatus !== 'parado'"
              @click="tamanhoLote = n"
            >
              {{ n }}
            </button>
            <span class="sizer-lbl">por batch</span>

            <label class="todos-toggle" :class="{ 'todos-toggle--on': modoTodos }">
              <input type="checkbox" v-model="modoTodos" :disabled="playerStatus !== 'parado'" />
              <span class="todos-ico">{{ modoTodos ? '🔒' : '🔓' }}</span>
              <span class="todos-lbl">Todos</span>
              <span v-if="modoTodos" class="todos-hint">repete batches até zerar pendentes</span>
            </label>
          </div>
          <div class="player-actions">
            <button v-if="playerStatus === 'parado'" class="btn-play" @click="pedirPlay">
              ▶ Play
            </button>
            <button v-else-if="playerStatus === 'rodando'" class="btn-pause" @click="pedirPause">
              ⏸ Pause
            </button>
            <button v-else class="btn-pausing" disabled>⏳ Parando…</button>
          </div>
        </div>

        <div class="player-stats">
          <div class="pstat">
            <span class="pstat-v"
              >{{ playerFeitos }}<span class="pstat-d">/{{ playerAlvo }}</span></span
            >
            <span class="pstat-l">Processados</span>
          </div>
          <div class="pstat pstat--ok">
            <span class="pstat-v">{{ playerOk }}</span>
            <span class="pstat-l">Sucessos</span>
          </div>
          <div class="pstat pstat--err">
            <span class="pstat-v">{{ playerErro }}</span>
            <span class="pstat-l">Erros</span>
          </div>
          <div v-if="modoTodos" class="pstat pstat--batch">
            <span class="pstat-v">#{{ playerBatchAtual }}</span>
            <span class="pstat-l">Batch atual</span>
          </div>
          <div class="pstat pstat--st" :class="`pstat--${playerStatus}`">
            <span class="pstat-v pstat-v--st">
              <span v-if="playerStatus === 'rodando'" class="live-dot" />
              {{
                playerStatus === 'rodando'
                  ? 'Rodando'
                  : playerStatus === 'pausando'
                    ? 'Parando…'
                    : 'Parado'
              }}
            </span>
            <span class="pstat-l">Estado</span>
          </div>
          <div class="pstat pstat--bar">
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: playerAlvo ? `${(playerFeitos / playerAlvo) * 100}%` : '0%' }"
              />
            </div>
            <span class="pstat-l">
              {{
                playerAlvo
                  ? `${Math.round((playerFeitos / playerAlvo) * 100)}% do lote`
                  : 'sem lote ativo'
              }}
            </span>
          </div>
        </div>

        <div v-if="playerErros.length" class="player-errs">
          <button class="errs-toggle" @click="playerErrosExpandido = !playerErrosExpandido">
            <span>
              {{ playerErrosExpandido ? '▾' : '▸' }}
              {{ playerErros.length }} erro(s) nesta rodada
            </span>
            <span class="errs-preview">
              último: {{ formatCPF(playerErros[0].cpf) }} — {{ playerErros[0].erro.slice(0, 60) }}
            </span>
          </button>
          <ul v-if="playerErrosExpandido" class="errs-list">
            <li v-for="(e, i) in playerErros" :key="i" class="err-item">
              <div class="err-head">
                <span class="err-hora">{{ e.quando }}</span>
                <span class="err-cpf mono">{{ formatCPF(e.cpf) }}</span>
                <span v-if="e.nome" class="err-nome">{{ e.nome }}</span>
                <span v-if="e.codigo" class="pill pill--cod">cod {{ e.codigo }}</span>
                <span v-if="e.etapa" class="pill">{{ e.etapa }}</span>
              </div>
              <div class="err-msg">{{ e.erro }}</div>
            </li>
          </ul>
        </div>
      </section>

      <div class="toolbar">
        <div class="busca-wrap">
          <svg
            class="lupa"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            v-model="filtro"
            type="text"
            placeholder="Buscar CPF, identificador, nome, matrícula, código (401, 1043…) ou motivo…"
            class="busca"
          />
        </div>
        <div class="tabs">
          <button
            v-for="f in ['todos', 'pendente', 'ok', 'erro', 'na'] as const"
            :key="f"
            class="tab"
            :class="{ 'tab--on': statusFiltro === f, [`tab--${f}`]: statusFiltro === f }"
            @click="setStatusFiltro(f)"
          >
            {{ f }}
          </button>
        </div>
        <div class="pag">
          <button class="pag-btn" :disabled="pagina === 0" @click="paginaAnterior">‹</button>
          <span class="pag-info">
            {{ pagina * pageSize + 1 }}–{{ Math.min((pagina + 1) * pageSize, total) }}
            <span class="dim">de</span>
            {{ total.toLocaleString('pt-BR') }}
          </span>
          <button
            class="pag-btn"
            :disabled="(pagina + 1) * pageSize >= total"
            @click="proximaPagina"
          >
            ›
          </button>
        </div>
      </div>

      <div class="tabela-wrap">
        <table class="tabela">
          <thead>
            <tr>
              <th class="th-num">#</th>
              <th>CPF</th>
              <th>Identificador</th>
              <th>Nome</th>
              <th>Matrícula</th>
              <th>Status</th>
              <th>Recibo</th>
              <th>Último envio</th>
              <th class="th-cod">
                <div class="th-cod-wrap">
                  <span>Código</span>
                  <button
                    class="cod-filter-btn"
                    :class="{ 'cod-filter-btn--on': codigosSelecionados.size > 0 }"
                    :title="
                      codigosSelecionados.size > 0
                        ? `${codigosSelecionados.size} selecionado(s)`
                        : 'Filtrar por código'
                    "
                    @click.stop="codigoFilterOpen = !codigoFilterOpen"
                  >
                    <svg
                      width="11"
                      height="11"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2.5"
                    >
                      <path d="M3 4h18l-7 9v6l-4 2v-8z" />
                    </svg>
                    <span v-if="codigosSelecionados.size > 0" class="cod-filter-badge">{{
                      codigosSelecionados.size
                    }}</span>
                  </button>
                  <div v-if="codigoFilterOpen" class="cod-filter" @click.stop>
                    <div class="cod-filter-head">
                      <strong>Filtrar por código</strong>
                      <div class="cod-filter-acts">
                        <button class="cod-filter-link" @click="selecionarTodosCodigos">
                          todos
                        </button>
                        <button class="cod-filter-link" @click="limparCodigoFiltro">limpar</button>
                      </div>
                    </div>
                    <div class="cod-filter-list">
                      <label
                        v-for="c in codigosDisponiveis"
                        :key="c.chave"
                        class="cod-filter-item"
                        :title="c.descricao"
                      >
                        <input
                          type="checkbox"
                          :checked="codigosSelecionados.has(c.chave)"
                          @change="toggleCodigo(c.chave)"
                        />
                        <span
                          class="cod-pill"
                          :class="c.tipo === 'ok' ? 'cod-pill--ok' : 'cod-pill--err'"
                        >
                          {{ codigoChaveLabel(c.chave) }}
                        </span>
                        <span class="cod-filter-desc">{{ c.descricao }}</span>
                        <span class="cod-filter-qtd">{{ c.qtd }}</span>
                      </label>
                      <div v-if="!codigosDisponiveis.length" class="cod-filter-vazio">
                        Sem dados na página atual
                      </div>
                    </div>
                    <div class="cod-filter-foot">
                      Dica: troque o status p/ <em>erro</em> e recarregue para ver só os erros
                    </div>
                  </div>
                </div>
              </th>
              <th>Motivo</th>
              <th class="th-ac"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(r, idx) in linhasFiltradas"
              :key="rowKey(r, idx)"
              :class="`row row-${r.status} ${r.cpf && (r.status === 'ok' || r.status === 'erro') ? 'row--clickable' : ''}`"
              @click="r.cpf && (r.status === 'ok' || r.status === 'erro') && abrirDetalhe(r)"
            >
              <td class="num">{{ pagina * pageSize + idx + 1 }}</td>
              <td class="cpf" :class="{ dim: !r.cpf }">{{ formatCPF(r.cpf) }}</td>
              <td class="mat mono">{{ identificadorLabel(r) }}</td>
              <td class="nome">{{ r.nome ?? '—' }}</td>
              <td class="mat">{{ r.matricula ?? '—' }}</td>
              <td>
                <span class="st" :class="`st--${r.status}`">
                  <span class="st-dot" />
                  {{ r.status === 'na' ? 'N/A' : r.status }}
                </span>
              </td>
              <td class="recibo">
                <span v-if="r.nr_recibo_novo" :title="r.nr_recibo_novo"
                  >…{{ r.nr_recibo_novo.slice(-12) }}</span
                >
                <span v-else-if="r.nr_recibo_zip" class="recibo-zip" :title="r.nr_recibo_zip">
                  …{{ r.nr_recibo_zip.slice(-12) }}<em>ZIP</em>
                </span>
                <span v-else class="dim">—</span>
              </td>
              <td class="data">{{ formatDate(r.enviado_em) }}</td>
              <td class="cod-resp">
                <span
                  v-if="r.status === 'erro'"
                  class="cod-pill cod-pill--err"
                  :title="`cdResposta ${r.codigo_resposta ?? '?'} · ocorrência ${parseErroOcorrencia(r.erro_descricao).codigo || '—'}`"
                >
                  {{ r.codigo_resposta ?? '—' }}/{{
                    parseErroOcorrencia(r.erro_descricao).codigo || '—'
                  }}
                </span>
                <span
                  v-else-if="r.status === 'ok'"
                  class="cod-pill cod-pill--ok"
                  title="cdResposta (201 = sucesso)"
                >
                  {{ r.codigo_resposta ?? '—' }}
                </span>
                <span v-else class="dim">—</span>
              </td>
              <td class="motivo">
                <span v-if="r.status === 'erro'" class="motivo-txt" :title="r.erro_descricao ?? ''">
                  {{
                    parseErroOcorrencia(r.erro_descricao).descricao || r.descricao_resposta || '—'
                  }}
                </span>
                <span v-else-if="r.status === 'ok'" class="motivo-ok">
                  {{ r.descricao_resposta || 'Sucesso' }}
                </span>
                <span
                  v-else-if="r.status === 'na'"
                  class="motivo-txt"
                  :title="r.erro_descricao ?? ''"
                >
                  {{ r.erro_descricao || 'Não aplica' }}
                </span>
                <span v-else class="dim">—</span>
              </td>
              <td class="ac">
                <button
                  class="enviar"
                  :class="{ 'enviar--re': r.status === 'ok' }"
                  :disabled="r.status === 'enviando' || r.status === 'na' || enviando || !r.cpf"
                  @click="abrirEnvio(r, $event)"
                >
                  {{
                    !r.cpf
                      ? 'Aguardando CPF'
                      : r.status === 'na'
                        ? 'N/A'
                        : r.status === 'ok'
                          ? 'Reenviar'
                          : 'Enviar'
                  }}
                </button>
              </td>
            </tr>
            <tr v-if="linhasFiltradas.length === 0">
              <td colspan="11" class="vazio">
                Nenhum registro nesta página com os filtros atuais.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="modalCpf" class="modal-bg" @click.self="fecharModal">
      <div class="modal">
        <header class="modal-head">
          <div>
            <div class="modal-kicker">Envio S-1210 · PRODUÇÃO</div>
            <h2>CPF {{ formatCPF(modalCpf.cpf) }}</h2>
          </div>
          <button class="fechar" :disabled="enviando" @click="fecharModal">×</button>
        </header>
        <div class="modal-body">
          <dl class="info-grid">
            <dt>Lote</dt>
            <dd>{{ modalCpf.lote_num }} — {{ descricaoLote[modalCpf.lote_num] }}</dd>
            <dt>Competência</dt>
            <dd>{{ mesLabels[mes] ?? mes }}</dd>
            <dt>Nome</dt>
            <dd>{{ modalCpf.nome ?? '—' }}</dd>
            <dt>Status atual</dt>
            <dd>
              <span class="st" :class="`st--${modalCpf.status}`">
                <span class="st-dot" /> {{ modalCpf.status }}
              </span>
            </dd>
            <template v-if="modalCpf.nr_recibo_zip">
              <dt>Recibo do ZIP</dt>
              <dd>
                <code>{{ modalCpf.nr_recibo_zip }}</code>
              </dd>
            </template>
          </dl>
          <div class="aviso">
            <strong>⚠ Atenção:</strong> este botão envia o evento S-1210
            <strong>em produção</strong>. O backend irá:
            <ol>
              <li>buscar o S-1210 original desse CPF no ZIP do mês;</li>
              <li>gerar XML de retificação sem plano de saúde (Lote 1);</li>
              <li>assinar com o certificado A1 ativo;</li>
              <li>enviar para o webservice do eSocial em produção;</li>
              <li>aguardar o recibo e gravar em <code>s1210_cpf_envios</code>.</li>
            </ol>
            Acompanhe o terminal no topo da tela.
          </div>
        </div>
        <footer class="modal-foot">
          <button class="btn-sec" :disabled="enviando" @click="fecharModal">Cancelar</button>
          <button class="btn-pri" :disabled="enviando" @click="confirmarEnvio">
            <span v-if="enviando" class="spin" />
            {{ enviando ? 'Enviando…' : 'Confirmar envio em produção' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- ═══════ MODAL DE DETALHES DO CPF ENVIADO ═══════ -->
    <div
      v-if="detalhe || carregandoDetalhe || erroDetalhe"
      class="modal-bg"
      @click.self="fecharDetalhe"
    >
      <div class="modal modal--lg">
        <header class="modal-head">
          <div>
            <div class="modal-kicker modal-kicker--det">Detalhes do envio · S-1210</div>
            <h2 v-if="detalhe">
              {{ formatCPF(detalhe.cpf) }}
              <span v-if="detalhe.nome" class="head-nome">· {{ detalhe.nome }}</span>
            </h2>
            <h2 v-else>Carregando…</h2>
          </div>
          <button class="fechar" @click="fecharDetalhe">×</button>
        </header>

        <div class="modal-body modal-body--det">
          <div v-if="carregandoDetalhe" class="det-state">Buscando informações do ZIP e banco…</div>
          <div v-else-if="erroDetalhe" class="det-state det-state--err">
            {{ erroDetalhe }}
          </div>

          <template v-else-if="detalhe">
            <!-- ▸ Linha de status + badges -->
            <div class="det-badges">
              <span class="st" :class="`st--${detalhe.status_atual}`">
                <span class="st-dot" /> {{ detalhe.status_atual }}
              </span>
              <span class="badge badge--prod">PRODUÇÃO</span>
              <span class="badge badge--ret">Retificação (indRetif=2)</span>
              <span class="badge">Lote {{ detalhe.lote_num }}</span>
              <span class="badge">{{ mesLabels[detalhe.per_apur] ?? detalhe.per_apur }}</span>
              <span v-if="detalhe.qtd_envios > 1" class="badge badge--hist">
                {{ detalhe.qtd_envios }} envios
              </span>
            </div>

            <!-- ▸ Cabeçalho: identificação -->
            <section class="det-sec">
              <h3 class="det-sec-t">👤 Identificação</h3>
              <dl class="det-kv">
                <dt>CPF</dt>
                <dd class="mono">{{ formatCPF(detalhe.cpf) }}</dd>
                <dt>Nome</dt>
                <dd>{{ detalhe.nome ?? '—' }}</dd>
                <dt>Matrícula</dt>
                <dd class="mono">{{ detalhe.matricula ?? '—' }}</dd>
                <dt>Competência</dt>
                <dd>{{ mesLabels[detalhe.per_apur] ?? detalhe.per_apur }}</dd>
                <dt>Lote / Grupo</dt>
                <dd>{{ detalhe.lote_num }} — {{ descricaoLote[detalhe.lote_num] }}</dd>
                <dt>Empregador</dt>
                <dd class="mono">APPA · CNPJ raiz {{ detalhe.empregador_cnpj_raiz }}</dd>
              </dl>
            </section>

            <!-- ▸ Linha de recibos (chain walk) -->
            <section class="det-sec">
              <h3 class="det-sec-t">🔗 Cadeia de recibos</h3>
              <div class="recibo-chain">
                <div class="chain-node">
                  <span class="chain-lbl">Recibo do ZIP</span>
                  <span class="chain-val mono" :title="detalhe.nr_recibo_zip ?? ''">
                    {{ formatReciboShort(detalhe.nr_recibo_zip) }}
                  </span>
                  <span class="chain-sub">estado em 10/04/2026</span>
                </div>
                <span class="chain-arr">→</span>
                <div class="chain-node chain-node--active">
                  <span class="chain-lbl">Recibo usado no envio</span>
                  <span
                    class="chain-val mono"
                    :title="detalhe.ultimo_envio?.nr_recibo_usado ?? detalhe.nr_recibo_ativo ?? ''"
                  >
                    {{
                      formatReciboShort(
                        detalhe.ultimo_envio?.nr_recibo_usado ?? detalhe.nr_recibo_ativo,
                      )
                    }}
                  </span>
                  <span class="chain-sub">
                    <template v-if="detalhe.recibo_fonte === 'cadeia'">
                      após {{ detalhe.cadeia_candidatos }} retific. anterior(es)
                    </template>
                    <template v-else>mesmo do ZIP</template>
                  </span>
                </div>
                <span class="chain-arr">→</span>
                <div
                  class="chain-node chain-node--new"
                  :class="{ 'chain-node--empty': !detalhe.ultimo_envio?.nr_recibo_novo }"
                >
                  <span class="chain-lbl">Recibo novo</span>
                  <span class="chain-val mono" :title="detalhe.ultimo_envio?.nr_recibo_novo ?? ''">
                    {{ formatReciboShort(detalhe.ultimo_envio?.nr_recibo_novo ?? null) }}
                  </span>
                  <span class="chain-sub">retorno eSocial</span>
                </div>
              </div>
            </section>

            <!-- ▸ Pagamentos (infoPgto[]) -->
            <section class="det-sec">
              <h3 class="det-sec-t">
                💰 Pagamentos declarados
                <span v-if="detalhe.pagamentos.length" class="det-sec-sub">
                  {{ detalhe.pagamentos.length }} pagamento(s) · total
                  <strong>{{ formatMoney(detalhe.total_vr_liq) }}</strong>
                </span>
              </h3>
              <div v-if="!detalhe.pagamentos.length" class="det-empty">
                Sem pagamentos encontrados no ZIP.
              </div>
              <table v-else class="det-table">
                <thead>
                  <tr>
                    <th>Data pgto</th>
                    <th>Tipo</th>
                    <th>Per. ref</th>
                    <th>ideDmDev</th>
                    <th class="rt">Valor líquido</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(p, i) in detalhe.pagamentos" :key="i">
                    <td>{{ p.dt_pgto }}</td>
                    <td>
                      <span class="pill pill--tp">{{ p.tp_pgto }}</span>
                      {{ p.tp_pgto_label }}
                    </td>
                    <td>{{ p.per_ref ?? '—' }}</td>
                    <td class="mono small">{{ p.ide_dm_dev }}</td>
                    <td class="rt bold">{{ formatMoney(p.vr_liq) }}</td>
                  </tr>
                </tbody>
              </table>
            </section>

            <!-- ▸ IR efetivo (prioriza S-5002 quando S-1210 não traz vrCR) -->
            <section class="det-sec">
              <h3 class="det-sec-t">
                💰 IRRF retido
                <span class="det-sec-sub"> fonte: {{ detalhe.ir_efetivo_fonte ?? '—' }} </span>
              </h3>
              <div class="ir-box">
                <div class="ir-main">
                  <span class="ir-lbl">Valor retido</span>
                  <span class="ir-val">{{ formatMoney(detalhe.ir_efetivo_valor) }}</span>
                </div>
                <div v-if="detalhe.s5002_ativo" class="ir-s5002">
                  <div class="ir-row">
                    <span class="ir-k">Rend. tributável</span>
                    <span class="ir-v">{{ formatMoney(detalhe.s5002_ativo.vlr_rend_trib) }}</span>
                  </div>
                  <div class="ir-row">
                    <span class="ir-k">Prev. oficial</span>
                    <span class="ir-v">{{
                      formatMoney(detalhe.s5002_ativo.vlr_prev_oficial)
                    }}</span>
                  </div>
                  <div class="ir-row">
                    <span class="ir-k">CRMen</span>
                    <span class="ir-v mono">{{ detalhe.s5002_ativo.cr_men ?? '—' }}</span>
                  </div>
                  <div class="ir-row">
                    <span class="ir-k">Recibo S-5002</span>
                    <span class="ir-v mono small">{{
                      formatReciboShort(detalhe.s5002_ativo.nr_recibo)
                    }}</span>
                  </div>
                </div>
                <div v-else-if="detalhe.zip_encontrado" class="ir-note">
                  Nenhum S-5002 encontrado para este CPF no ZIP do período.
                </div>
              </div>

              <!-- ▸ Detalhamento infoIR do S-5002 ativo -->
              <table
                v-if="detalhe.s5002_ativo && detalhe.s5002_ativo.info_ir.length"
                class="det-table"
                style="margin-top: 0.75rem"
              >
                <thead>
                  <tr>
                    <th>tpInfoIR</th>
                    <th>Descrição</th>
                    <th class="rt">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(it, i) in detalhe.s5002_ativo.info_ir" :key="i">
                    <td class="mono">{{ it.tp_info_ir }}</td>
                    <td>{{ it.tp_info_ir_label }}</td>
                    <td class="rt">{{ formatMoney(it.valor) }}</td>
                  </tr>
                </tbody>
              </table>
            </section>

            <!-- ▸ IR complementar do S-1210 (infoIRCR) — referência técnica -->
            <section v-if="detalhe.info_ir.length" class="det-sec">
              <h3 class="det-sec-t">
                🧾 infoIRCR (do S-1210)
                <span class="det-sec-sub">declaração complementar enviada pelo empregador</span>
              </h3>
              <table class="det-table">
                <thead>
                  <tr>
                    <th>Código (tpCR)</th>
                    <th>Descrição</th>
                    <th class="rt">vrCR</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(ir, i) in detalhe.info_ir" :key="i">
                    <td class="mono">{{ ir.tp_cr }}</td>
                    <td>{{ ir.tp_cr_label }}</td>
                    <td class="rt">
                      <span v-if="ir.vr_cr == null || ir.vr_cr === 0" class="muted">
                        não declarado
                      </span>
                      <span v-else class="bold">{{ formatMoney(ir.vr_cr) }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p class="det-hint">
                ℹ️ O S-1210 omite <code>&lt;vrCR&gt;</code> quando o IR já é calculado pelo eSocial
                a partir das rubricas do S-1200 — nesses casos o valor vem do S-5002 acima.
              </p>
            </section>

            <!-- ▸ Histórico de envios -->
            <section v-if="detalhe.historico_envios.length" class="det-sec">
              <h3 class="det-sec-t">
                🕒 Histórico de envios
                <span class="det-sec-sub">{{ detalhe.historico_envios.length }} registro(s)</span>
              </h3>
              <div class="timeline">
                <div
                  v-for="(h, i) in [...detalhe.historico_envios].reverse()"
                  :key="i"
                  class="tl-item"
                  :class="`tl-${h.status}`"
                >
                  <div class="tl-dot" />
                  <div class="tl-body">
                    <div class="tl-top">
                      <span class="st" :class="`st--${h.status}`">
                        <span class="st-dot" /> {{ h.status }}
                      </span>
                      <span class="tl-data">{{ formatDate(h.enviado_em) }}</span>
                      <span v-if="h.codigo_resposta" class="pill pill--cod">
                        código {{ h.codigo_resposta }}
                      </span>
                    </div>
                    <div v-if="h.descricao_resposta" class="tl-desc">
                      {{ h.descricao_resposta }}
                    </div>
                    <div v-if="h.erro_descricao" class="tl-erro">⚠ {{ h.erro_descricao }}</div>
                    <div class="tl-recibos">
                      <span v-if="h.nr_recibo_usado">
                        usado:
                        <code class="mono" @click="copiar(h.nr_recibo_usado)">
                          {{ formatReciboShort(h.nr_recibo_usado) }}
                        </code>
                      </span>
                      <span v-if="h.nr_recibo_novo">
                        novo:
                        <code class="mono" @click="copiar(h.nr_recibo_novo)">
                          {{ formatReciboShort(h.nr_recibo_novo) }}
                        </code>
                      </span>
                      <span v-if="h.protocolo">
                        protocolo:
                        <code class="mono small" @click="copiar(h.protocolo)">
                          {{ h.protocolo }}
                        </code>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- ▸ Técnico -->
            <section class="det-sec det-sec--tec">
              <h3 class="det-sec-t">⚙ Dados técnicos do evento</h3>
              <dl class="det-kv det-kv--small">
                <dt>tpAmb</dt>
                <dd>{{ detalhe.tp_amb }} (produção)</dd>
                <dt>indRetif</dt>
                <dd>{{ detalhe.ind_retif_original ?? '2' }} (retificação)</dd>
                <dt>procEmi / verProc</dt>
                <dd>{{ detalhe.proc_emi }} · {{ detalhe.ver_proc }}</dd>
                <dt>dhProcessamento ZIP</dt>
                <dd class="mono small">{{ detalhe.dh_processamento ?? '—' }}</dd>
                <dt v-if="detalhe.zip_erro">Aviso ZIP</dt>
                <dd v-if="detalhe.zip_erro" class="warn">{{ detalhe.zip_erro }}</dd>
              </dl>
            </section>
          </template>
        </div>

        <footer class="modal-foot">
          <button class="btn-sec" @click="fecharDetalhe">Fechar</button>
        </footer>
      </div>
    </div>

    <!-- Modal: confirmação do player (lote 50) -->
    <div v-if="confirmacaoPlay" class="modal-bg" @click.self="cancelarConfirmacao">
      <div class="modal">
        <header class="modal-head">
          <h3>Confirmar envio em lote</h3>
        </header>
        <div class="modal-body">
          <p class="warn-prod">
            <template v-if="modoTodos">
              🔒 Modo <strong>TODOS</strong> ativo — vou enviar
              <strong
                >{{ totaisCompartimento.pendente + totaisCompartimento.enviando }} CPF(s)
                pendentes</strong
              >
              em batches de <strong>{{ tamanhoLote }}</strong> até zerar, em
              <strong>PRODUÇÃO</strong>.
            </template>
            <template v-else>
              ⚠ Você está prestes a enviar
              <strong
                >{{ Math.min(tamanhoLote, cpfsPendentesNaListaAtual().length) }} CPF(s)</strong
              >
              em <strong>PRODUÇÃO</strong> no eSocial.
            </template>
          </p>
          <p class="small">
            <template v-if="modoTodos">
              Os pendentes da página atual serão processados em batches de {{ tamanhoLote }} (3
              simultâneos por batch). Ao terminar uma batch, a lista recarrega e a próxima começa
              automaticamente. Você pode pausar a qualquer momento — o batch atual termina antes de
              parar.
            </template>
            <template v-else>
              Serão processados os próximos pendentes da página atual, em paralelo (3 simultâneos).
              Você poderá pausar a qualquer momento — os envios em andamento terminam e o player
              para.
            </template>
          </p>
          <ul class="confirm-list">
            <li>
              Lote: <strong>{{ lote }}</strong>
            </li>
            <li>
              Competência: <strong>{{ mesLabels[mes] ?? mes }}</strong>
            </li>
            <li>
              Pendentes disponíveis:
              <strong>{{ cpfsPendentesNaListaAtual().length }}</strong>
            </li>
          </ul>
        </div>
        <footer class="modal-foot">
          <button class="btn-sec" @click="cancelarConfirmacao">Cancelar</button>
          <button class="btn-pri" @click="confirmarPlay">Confirmar e iniciar</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  --neon-a: #4f8ef5;
  --neon-b: #2855c8;
  --neon-soft: rgba(79, 142, 245, 0.22);
  padding: 28px 36px 60px;
  max-width: 1400px;
  margin: 0 auto;
  background:
    radial-gradient(circle at 88% -8%, rgba(79, 142, 245, 0.24), transparent 36%),
    radial-gradient(circle at -8% -10%, rgba(40, 85, 200, 0.22), transparent 36%);
}
.page-header {
  margin-bottom: 16px;
}
.voltar {
  background: rgba(79, 142, 245, 0.06);
  border: 1px solid rgba(79, 142, 245, 0.34);
  color: rgba(227, 247, 255, 0.92);
  padding: 5px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
  margin-bottom: 14px;
}
.voltar:hover {
  background: rgba(79, 142, 245, 0.14);
  color: #fff;
  border-color: rgba(79, 142, 245, 0.56);
  box-shadow: 0 0 14px rgba(79, 142, 245, 0.3);
}
.arrow {
  font-size: 14px;
}
.title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}
.kicker {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin-bottom: 4px;
}
.page-header h1 {
  margin: 0 0 6px;
  color: #fff;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.3px;
  text-shadow: 0 0 20px rgba(79, 142, 245, 0.24);
}
.sep {
  color: rgba(255, 255, 255, 0.3);
  margin: 0 6px;
  font-weight: 300;
}
.sub {
  color: rgba(255, 255, 255, 0.55);
  margin: 0;
  font-size: 13px;
}

.mini-term {
  background: linear-gradient(180deg, #0d0f1c 0%, #0a0c17 100%);
  border: 1px solid rgba(79, 142, 245, 0.28);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 20px;
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 0 18px rgba(79, 142, 245, 0.12);
}
.mini-term-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.dot--r {
  background: #ff5f57;
}
.dot--y {
  background: #febc2e;
}
.dot--g {
  background: #28c840;
}
.mini-term-title {
  margin-left: 10px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  font-family: 'SF Mono', Consolas, monospace;
  letter-spacing: 0.3px;
}
.limpar {
  margin-left: auto;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.4);
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 10px;
  cursor: pointer;
  font-family: 'SF Mono', Consolas, monospace;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.limpar:hover {
  color: rgba(255, 255, 255, 0.8);
  border-color: rgba(255, 255, 255, 0.3);
}
.mini-term-body {
  height: 168px;
  overflow-y: auto;
  padding: 8px 14px;
  font-family: 'SF Mono', Consolas, 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.8;
}
.mini-term-body::-webkit-scrollbar {
  width: 6px;
}
.mini-term-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
.mini-term-empty {
  color: rgba(255, 255, 255, 0.25);
  font-style: italic;
  padding-top: 2px;
}
.mini-term-line {
  white-space: pre-wrap;
  word-break: break-word;
}
.hora {
  color: rgba(255, 255, 255, 0.35);
  margin-right: 10px;
  user-select: none;
}
.lvl-info .txt {
  color: rgba(255, 255, 255, 0.78);
}
.lvl-ok .txt {
  color: #5dd39e;
}
.lvl-err .txt {
  color: #ff8585;
}
.lvl-warn .txt {
  color: #f3c969;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}
.kpi {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  overflow: hidden;
}
.kpi::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.1);
}
.kpi--ok::before {
  background: linear-gradient(90deg, #5dd39e, transparent);
}
.kpi--err::before {
  background: linear-gradient(90deg, #ff7a7a, transparent);
}
.kpi--pend::before {
  background: linear-gradient(90deg, #f3c969, transparent);
}
.kpi--sent::before {
  background: linear-gradient(90deg, #7cc4ff, transparent);
}
.kpi--na::before {
  background: linear-gradient(90deg, #b3a8ff, transparent);
}
.kpi-label {
  font-size: 10.5px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-weight: 500;
}
.kpi-val {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.5px;
}
.kpi--ok .kpi-val {
  color: #5dd39e;
}
.kpi--err .kpi-val {
  color: #ff8585;
}
.kpi--pend .kpi-val {
  color: #f3c969;
}
.kpi--sent .kpi-val {
  color: #7cc4ff;
}
.kpi--na .kpi-val {
  color: #b3a8ff;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.busca-wrap {
  position: relative;
  flex: 1 1 280px;
  display: flex;
  align-items: center;
}
.lupa {
  position: absolute;
  left: 11px;
  color: rgba(255, 255, 255, 0.4);
  pointer-events: none;
}
.busca {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  padding: 8px 12px 8px 33px;
  border-radius: 7px;
  font-size: 13px;
  transition: all 0.15s;
}
.busca:focus {
  outline: none;
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(99, 102, 241, 0.04);
}
.tabs {
  display: flex;
  gap: 2px;
  background: rgba(255, 255, 255, 0.03);
  padding: 3px;
  border-radius: 7px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.tab {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.55);
  padding: 5px 14px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  text-transform: capitalize;
  font-weight: 500;
  transition: all 0.12s;
}
.tab:hover {
  color: rgba(255, 255, 255, 0.8);
}
.tab--on {
  background: rgba(99, 102, 241, 0.2);
  color: #fff;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.08);
}
.tab--ok {
  background: rgba(93, 211, 158, 0.15);
  color: #5dd39e;
}
.tab--erro {
  background: rgba(255, 122, 122, 0.15);
  color: #ff8585;
}
.tab--pendente {
  background: rgba(243, 201, 105, 0.15);
  color: #f3c969;
}
.tab--na {
  background: rgba(179, 168, 255, 0.18);
  color: #b3a8ff;
}

.pag {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.pag .dim {
  color: rgba(255, 255, 255, 0.3);
  margin: 0 4px;
}
.pag-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  width: 28px;
  height: 28px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.12s;
}
.pag-btn:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.4);
}
.pag-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.pag-info {
  padding: 0 6px;
}

.tabela-wrap {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  overflow: hidden;
}
.tabela {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.tabela thead th {
  text-align: left;
  padding: 11px 14px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 10.5px;
  letter-spacing: 0.7px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}
.th-num {
  width: 46px;
  text-align: right !important;
}
.th-ac {
  width: 100px;
}
.tabela tbody td {
  padding: 10px 14px;
  color: rgba(255, 255, 255, 0.88);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-variant-numeric: tabular-nums;
}
.tabela tbody tr:last-child td {
  border-bottom: none;
}
.tabela tbody tr:hover {
  background: rgba(99, 102, 241, 0.04);
}
.row-ok {
  background: rgba(93, 211, 158, 0.03);
}
.row-erro {
  background: rgba(255, 122, 122, 0.03);
}
.row-enviando {
  background: rgba(243, 201, 105, 0.06);
}
.row-na {
  background: rgba(179, 168, 255, 0.05);
}

.num {
  text-align: right;
  color: rgba(255, 255, 255, 0.35);
  font-size: 11px;
}
.cpf {
  font-family: 'SF Mono', Consolas, monospace;
  color: #fff;
  font-weight: 500;
}
.nome {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mat {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}
.data {
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
}
.recibo {
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 11.5px;
}
.recibo-zip em {
  font-style: normal;
  font-size: 9px;
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 4px;
  border-radius: 3px;
  margin-left: 5px;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.dim {
  color: rgba(255, 255, 255, 0.25);
}

.th-cod {
  width: 90px;
  white-space: nowrap;
}
.th-cod-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.cod-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.55);
  padding: 2px 5px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s;
}
.cod-filter-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.9);
}
.cod-filter-btn--on {
  background: rgba(93, 211, 158, 0.14);
  border-color: rgba(93, 211, 158, 0.4);
  color: #5dd39e;
}
.cod-filter-badge {
  font-size: 9px;
  font-weight: 700;
  background: rgba(93, 211, 158, 0.25);
  padding: 0 4px;
  border-radius: 7px;
  line-height: 1.4;
}
.cod-filter {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 50;
  width: 360px;
  max-height: 420px;
  background: #1c1f24;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-weight: 400;
  text-transform: none;
  letter-spacing: normal;
}
.cod-filter-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12px;
}
.cod-filter-acts {
  display: flex;
  gap: 8px;
}
.cod-filter-link {
  background: none;
  border: none;
  color: #7ab8ff;
  font-size: 11px;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}
.cod-filter-link:hover {
  color: #a0cfff;
}
.cod-filter-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}
.cod-filter-item {
  display: grid;
  grid-template-columns: auto auto 1fr auto;
  gap: 8px;
  align-items: center;
  padding: 6px 8px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
}
.cod-filter-item:hover {
  background: rgba(255, 255, 255, 0.04);
}
.cod-filter-item input[type='checkbox'] {
  cursor: pointer;
  accent-color: #5dd39e;
}
.cod-filter-desc {
  color: rgba(255, 255, 255, 0.6);
  font-size: 11.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cod-filter-qtd {
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 10.5px;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.05);
  padding: 1px 7px;
  border-radius: 8px;
}
.cod-filter-vazio {
  padding: 16px;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}
.cod-filter-foot {
  padding: 6px 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 10.5px;
  color: rgba(255, 255, 255, 0.4);
}
.cod-filter-foot em {
  color: #ff8585;
  font-style: normal;
}
.cod-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 9px;
  font-size: 11px;
  font-family: 'SF Mono', Consolas, monospace;
  font-weight: 600;
  letter-spacing: 0.3px;
}
.cod-pill--ok {
  background: rgba(93, 211, 158, 0.12);
  color: #5dd39e;
}
.cod-pill--err {
  background: rgba(255, 122, 122, 0.14);
  color: #ff8585;
}
.motivo {
  max-width: 340px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.72);
}
.motivo-txt {
  display: inline-block;
  max-width: 340px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
.motivo-ok {
  color: rgba(93, 211, 158, 0.7);
  font-size: 11.5px;
}

.st {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 11px;
  font-size: 10.5px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.6px;
}
.st-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}
.st--ok {
  background: rgba(93, 211, 158, 0.12);
  color: #5dd39e;
  border: 1px solid rgba(93, 211, 158, 0.25);
}
.st--erro {
  background: rgba(255, 122, 122, 0.12);
  color: #ff8585;
  border: 1px solid rgba(255, 122, 122, 0.25);
}
.st--pendente {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.st--enviando {
  background: rgba(243, 201, 105, 0.12);
  color: #f3c969;
  border: 1px solid rgba(243, 201, 105, 0.3);
}
.st--na {
  background: rgba(179, 168, 255, 0.14);
  color: #b3a8ff;
  border: 1px solid rgba(179, 168, 255, 0.3);
}
.st--enviando .st-dot {
  animation: pulse 1.1s ease-in-out infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.25;
  }
}

.enviar {
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.28), rgba(99, 102, 241, 0.18));
  border: 1px solid rgba(99, 102, 241, 0.5);
  color: #fff;
  padding: 5px 14px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 11.5px;
  font-weight: 600;
  transition: all 0.12s;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06) inset;
}
.enviar:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.45), rgba(99, 102, 241, 0.3));
  transform: translateY(-1px);
}
.enviar--re {
  background: transparent;
  border-color: rgba(93, 211, 158, 0.4);
  color: #5dd39e;
}
.enviar--re:hover:not(:disabled) {
  background: rgba(93, 211, 158, 0.12);
}
.enviar:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.vazio {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  padding: 40px;
  font-style: italic;
}
.state {
  padding: 50px;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
}
.state--err {
  color: #ff7a7a;
}

.modal-bg {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadein 0.15s ease;
}
@keyframes fadein {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.modal {
  background: linear-gradient(180deg, #1c1e33, #151729);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  width: 560px;
  max-width: 92vw;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.65);
  overflow: hidden;
}
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 18px 22px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.modal-kicker {
  font-size: 10.5px;
  color: #f3c969;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-weight: 600;
  margin-bottom: 4px;
}
.modal-head h2 {
  margin: 0;
  font-size: 18px;
  color: #fff;
  font-family: 'SF Mono', Consolas, monospace;
}
.fechar {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.45);
  font-size: 26px;
  cursor: pointer;
  line-height: 1;
  padding: 0 6px;
  transition: color 0.12s;
}
.fechar:hover:not(:disabled) {
  color: #fff;
}
.fechar:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.modal-body {
  padding: 18px 22px;
  color: rgba(255, 255, 255, 0.88);
  font-size: 13px;
}
.info-grid {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 10px 14px;
  margin: 0 0 16px;
}
.info-grid dt {
  color: rgba(255, 255, 255, 0.45);
  font-size: 11.5px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-top: 2px;
}
.info-grid dd {
  margin: 0;
  color: rgba(255, 255, 255, 0.92);
}
.info-grid code {
  background: rgba(255, 255, 255, 0.06);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'SF Mono', Consolas, monospace;
}
.aviso {
  margin-top: 16px;
  padding: 12px 14px;
  background: rgba(243, 201, 105, 0.06);
  border: 1px solid rgba(243, 201, 105, 0.25);
  border-radius: 7px;
  color: rgba(255, 235, 180, 0.88);
  font-size: 12px;
  line-height: 1.6;
}
.aviso strong {
  color: #ffe6a6;
}
.aviso ol {
  margin: 8px 0 4px 18px;
  padding: 0;
}
.aviso li {
  margin: 2px 0;
}
.aviso code {
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
}
.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 22px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.2);
}
.btn-sec,
.btn-pri {
  padding: 8px 18px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s;
}
.btn-sec {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.8);
}
.btn-sec:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}
.btn-pri {
  background: linear-gradient(180deg, #6366f1, #4f52d9);
  border-color: rgba(99, 102, 241, 0.6);
  color: #fff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.35);
}
.btn-pri:hover:not(:disabled) {
  background: linear-gradient(180deg, #7477ff, #5a5de9);
  transform: translateY(-1px);
}
.btn-pri:disabled,
.btn-sec:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.spin {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ═══════ Linha clicável ═══════ */
.row--clickable {
  cursor: pointer;
}
.row--clickable:hover {
  background: rgba(99, 102, 241, 0.08) !important;
}

/* ═══════ Modal DETALHES (largo) ═══════ */
.modal--lg {
  width: 880px;
  max-width: 95vw;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
}
.modal--lg .modal-body--det {
  overflow-y: auto;
  flex: 1;
}
.modal--lg .modal-body--det::-webkit-scrollbar {
  width: 8px;
}
.modal--lg .modal-body--det::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
.modal-kicker--det {
  color: #8b8fff;
}
.head-nome {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
  font-size: 14px;
  font-family: system-ui, sans-serif;
  margin-left: 8px;
}

.det-state {
  padding: 40px;
  text-align: center;
  color: rgba(255, 255, 255, 0.55);
}
.det-state--err {
  color: #ff8585;
}

.det-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 11px;
  font-size: 10.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}
.badge--prod {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.35);
  color: #ff9e9e;
}
.badge--ret {
  background: rgba(139, 143, 255, 0.12);
  border-color: rgba(139, 143, 255, 0.35);
  color: #8b8fff;
}
.badge--hist {
  background: rgba(243, 201, 105, 0.12);
  border-color: rgba(243, 201, 105, 0.3);
  color: #f3c969;
}

.det-sec {
  margin-bottom: 22px;
}
.det-sec-t {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 12.5px;
  font-weight: 700;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin: 0 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.det-sec-sub {
  font-weight: 400;
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 0;
  text-transform: none;
}
.det-sec-sub strong {
  color: #5dd39e;
  font-weight: 600;
}

/* ── IR efetivo (S-5002) ─────────────────────────── */
.ir-box {
  background: linear-gradient(135deg, rgba(93, 211, 158, 0.08), rgba(93, 211, 158, 0.02));
  border: 1px solid rgba(93, 211, 158, 0.25);
  border-radius: 10px;
  padding: 14px 16px;
}
.ir-main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14px;
  padding-bottom: 10px;
  border-bottom: 1px dashed rgba(93, 211, 158, 0.2);
  margin-bottom: 10px;
}
.ir-lbl {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: rgba(255, 255, 255, 0.7);
}
.ir-val {
  font-size: 22px;
  font-weight: 700;
  color: #5dd39e;
  font-variant-numeric: tabular-nums;
}
.ir-s5002 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px 18px;
}
.ir-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12.5px;
}
.ir-k {
  color: rgba(255, 255, 255, 0.55);
}
.ir-v {
  color: rgba(255, 255, 255, 0.92);
  font-variant-numeric: tabular-nums;
}
.ir-v.small {
  font-size: 11px;
}
.ir-note {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  font-style: italic;
}
.det-hint {
  margin: 8px 2px 0;
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.5;
}
.det-hint code {
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
}
.muted {
  color: rgba(255, 255, 255, 0.4);
  font-style: italic;
}

.det-kv {
  display: grid;
  grid-template-columns: 170px 1fr;
  gap: 8px 16px;
  margin: 0;
}
.det-kv dt {
  color: rgba(255, 255, 255, 0.45);
  font-size: 11.5px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.det-kv dd {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
}
.det-kv--small dd,
.det-kv--small dt {
  font-size: 11.5px;
}
.det-kv .mono,
.mono {
  font-family: 'SF Mono', Consolas, monospace;
}
.det-kv .warn {
  color: #f3c969;
}

/* ═══════ Chain de recibos ═══════ */
.recibo-chain {
  display: flex;
  align-items: stretch;
  gap: 8px;
  padding: 8px 0;
}
.chain-node {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.chain-node--active {
  background: rgba(139, 143, 255, 0.08);
  border-color: rgba(139, 143, 255, 0.3);
}
.chain-node--new {
  background: rgba(93, 211, 158, 0.08);
  border-color: rgba(93, 211, 158, 0.35);
}
.chain-node--empty {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.06);
  opacity: 0.5;
}
.chain-lbl {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
}
.chain-val {
  font-size: 12.5px;
  color: #fff;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chain-node--new .chain-val {
  color: #5dd39e;
}
.chain-sub {
  font-size: 10.5px;
  color: rgba(255, 255, 255, 0.45);
}
.chain-arr {
  align-self: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 16px;
}

/* ═══════ Tabela interna ═══════ */
.det-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  overflow: hidden;
  font-size: 12px;
}
.det-table thead th {
  background: rgba(255, 255, 255, 0.03);
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.6px;
  text-align: left;
  padding: 8px 12px;
  font-weight: 700;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.det-table tbody td {
  padding: 8px 12px;
  color: rgba(255, 255, 255, 0.88);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-variant-numeric: tabular-nums;
}
.det-table tbody tr:last-child td {
  border-bottom: none;
}
.rt {
  text-align: right;
}
.bold {
  font-weight: 700;
  color: #fff;
}
.small {
  font-size: 10.5px;
}
.pill {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 9px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin-right: 6px;
  background: rgba(139, 143, 255, 0.15);
  color: #a5a8ff;
  font-family: 'SF Mono', Consolas, monospace;
}
.pill--cod {
  background: rgba(93, 211, 158, 0.15);
  color: #5dd39e;
}
.det-empty {
  padding: 16px;
  text-align: center;
  color: rgba(255, 255, 255, 0.35);
  font-style: italic;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 6px;
}

/* ═══════ Timeline ═══════ */
.timeline {
  position: relative;
  padding-left: 18px;
}
.timeline::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 6px;
  bottom: 6px;
  width: 1px;
  background: rgba(255, 255, 255, 0.1);
}
.tl-item {
  position: relative;
  margin-bottom: 14px;
}
.tl-item:last-child {
  margin-bottom: 0;
}
.tl-dot {
  position: absolute;
  left: -16px;
  top: 6px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #1c1e33;
  background: rgba(255, 255, 255, 0.3);
}
.tl-ok .tl-dot {
  background: #5dd39e;
}
.tl-erro .tl-dot {
  background: #ff7a7a;
}
.tl-enviando .tl-dot {
  background: #f3c969;
}
.tl-body {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 7px;
}
.tl-top {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.tl-data {
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.6);
}
.tl-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  margin: 3px 0;
}
.tl-erro {
  font-size: 11.5px;
  color: #ff8585;
  margin: 4px 0;
  padding: 5px 8px;
  background: rgba(255, 122, 122, 0.06);
  border-radius: 4px;
  border-left: 2px solid #ff7a7a;
}
.tl-recibos {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 5px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
}
.tl-recibos code {
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 6px;
  border-radius: 3px;
  color: #fff;
  cursor: pointer;
  transition: background 0.1s;
}
.tl-recibos code:hover {
  background: rgba(139, 143, 255, 0.2);
}

.det-sec--tec {
  opacity: 0.7;
  margin-top: 10px;
}

/* ═══════════ Painel de comando (player) ═══════════ */
.player {
  margin: 16px 0 18px;
  padding: 16px 18px 14px;
  background: linear-gradient(135deg, rgba(100, 110, 220, 0.08), rgba(80, 180, 200, 0.05));
  border: 1px solid rgba(150, 170, 255, 0.22);
  border-radius: 14px;
  backdrop-filter: blur(6px);
}
.player-head {
  display: flex;
  align-items: center;
  gap: 22px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.player-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #e8ebff;
}
.player-ico {
  display: inline-flex;
  width: 26px;
  height: 26px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(120, 140, 255, 0.22);
  color: #b9c6ff;
  font-size: 0.8rem;
}
.player-sizer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #a8adc7;
}
.sizer-lbl {
  font-size: 0.8rem;
}
.sizer-btn {
  min-width: 44px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #d5dafc;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.15s;
}
.sizer-btn:hover:not(:disabled) {
  background: rgba(120, 140, 255, 0.15);
  border-color: rgba(150, 170, 255, 0.4);
}
.sizer-btn--on {
  background: rgba(120, 140, 255, 0.28) !important;
  border-color: #8b9fff !important;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(139, 159, 255, 0.18);
}
.sizer-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.todos-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 10px;
  padding: 6px 10px 6px 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}
.todos-toggle:hover {
  background: rgba(255, 255, 255, 0.08);
}
.todos-toggle input {
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1.5px solid rgba(200, 210, 255, 0.4);
  background: transparent;
  cursor: pointer;
  position: relative;
}
.todos-toggle input:checked {
  background: #f2c94c;
  border-color: #f2c94c;
}
.todos-toggle input:checked::after {
  content: '✓';
  position: absolute;
  inset: 0;
  font-size: 11px;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
}
.todos-toggle input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.todos-ico {
  font-size: 0.95rem;
}
.todos-lbl {
  font-size: 0.85rem;
  font-weight: 600;
  color: #d5dafc;
  letter-spacing: 0.02em;
}
.todos-hint {
  font-size: 0.72rem;
  color: #f2c94c;
  opacity: 0.85;
  margin-left: 4px;
}
.todos-toggle--on {
  background: rgba(242, 201, 76, 0.12);
  border-color: rgba(242, 201, 76, 0.5);
  box-shadow: 0 0 0 2px rgba(242, 201, 76, 0.12);
}
.todos-toggle--on .todos-lbl {
  color: #ffe3a0;
}
.pstat--batch {
  background: rgba(242, 201, 76, 0.1);
  border-color: rgba(242, 201, 76, 0.3);
}
.pstat--batch .pstat-v {
  color: #f2c94c;
}
.player-actions {
  margin-left: auto;
  display: flex;
  gap: 10px;
}
.btn-play,
.btn-pause,
.btn-pausing {
  padding: 9px 22px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-play {
  background: linear-gradient(135deg, #2ec06a, #21a85c);
  color: #fff;
  box-shadow: 0 4px 14px rgba(46, 192, 106, 0.3);
}
.btn-play:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(46, 192, 106, 0.4);
}
.btn-pause {
  background: linear-gradient(135deg, #f2a53a, #e8821f);
  color: #fff;
  box-shadow: 0 4px 14px rgba(242, 165, 58, 0.3);
}
.btn-pause:hover {
  transform: translateY(-1px);
}
.btn-pausing {
  background: rgba(242, 165, 58, 0.25);
  color: #f2c98a;
  cursor: wait;
}

.player-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) 1.6fr;
  gap: 10px;
}
.pstat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
}
.pstat-v {
  font-size: 1.4rem;
  font-weight: 700;
  color: #f1f3ff;
  line-height: 1;
}
.pstat-d {
  font-size: 0.9rem;
  opacity: 0.5;
  font-weight: 500;
}
.pstat-l {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #888ea8;
}
.pstat--ok .pstat-v {
  color: #4ade80;
}
.pstat--err .pstat-v {
  color: #f87171;
}
.pstat--st.pstat--rodando {
  background: rgba(46, 192, 106, 0.1);
  border-color: rgba(46, 192, 106, 0.35);
}
.pstat--st.pstat--pausando {
  background: rgba(242, 165, 58, 0.1);
  border-color: rgba(242, 165, 58, 0.35);
}
.pstat-v--st {
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}
.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
  animation: live-pulse 1.4s infinite;
}
@keyframes live-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(74, 222, 128, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
  }
}
.pstat--bar {
  justify-content: center;
}
.bar-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 4px;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #5d7bff, #2ec06a);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.player-errs {
  margin-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 10px;
}
.errs-toggle {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.22);
  border-radius: 8px;
  color: #fca5a5;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.15s;
}
.errs-toggle:hover {
  background: rgba(248, 113, 113, 0.14);
}
.errs-preview {
  opacity: 0.75;
  font-size: 0.78rem;
  max-width: 55%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.errs-list {
  list-style: none;
  padding: 0;
  margin: 10px 0 0;
  max-height: 240px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.err-item {
  padding: 8px 10px;
  background: rgba(248, 113, 113, 0.05);
  border: 1px solid rgba(248, 113, 113, 0.18);
  border-radius: 8px;
}
.err-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 3px;
  font-size: 0.82rem;
}
.err-hora {
  opacity: 0.6;
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
}
.err-cpf {
  color: #fecaca;
  font-weight: 600;
}
.err-nome {
  color: #b8bfe0;
}
.pill--cod {
  background: rgba(248, 113, 113, 0.2);
  border-color: rgba(248, 113, 113, 0.4);
  color: #fecaca;
}
.err-msg {
  font-size: 0.82rem;
  color: #e8c7c7;
  line-height: 1.4;
}

.warn-prod {
  padding: 10px 12px;
  background: rgba(242, 165, 58, 0.1);
  border: 1px solid rgba(242, 165, 58, 0.35);
  border-radius: 8px;
  color: #f5cc87;
  margin: 0 0 10px;
  font-size: 0.92rem;
}
.confirm-list {
  margin: 10px 0 0;
  padding-left: 18px;
  font-size: 0.88rem;
  color: #c7ccea;
  line-height: 1.7;
}

@media (max-width: 900px) {
  .player-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .player-actions {
    margin-left: 0;
    width: 100%;
  }
}
</style>
