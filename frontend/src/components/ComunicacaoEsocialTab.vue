<template>
  <div class="comunicacao-tab">
    <h1 class="title">Comunicação eSocial — Envios e Retornos</h1>
    <p class="subtitle">
      Rastreamento completo de todas as comunicações com o governo — envios, consultas, downloads e
      provas de bloqueio
    </p>

    <!-- Cota Banner -->
    <div
      v-if="cotaInfo"
      class="cota-banner"
      :class="cotaInfo.esgotada ? 'cota-esgotada' : 'cota-ok'"
    >
      <div class="cota-header">
        <span class="cota-icon">{{ cotaInfo.esgotada ? '🚫' : '📡' }}</span>
        <span class="cota-titulo"> Cota Diária de Download Cirúrgico (Governo) </span>
        <span class="cota-counter" :class="cotaInfo.esgotada ? 'counter-esgotada' : ''">
          {{ cotaInfo.usadas }}/10 requests usadas hoje
        </span>
      </div>
      <div class="cota-bar-wrap">
        <div
          class="cota-bar"
          :style="{ width: Math.min(cotaInfo.usadas * 10, 100) + '%' }"
          :class="cotaInfo.esgotada ? 'bar-esgotada' : 'bar-ok'"
        ></div>
      </div>
      <p v-if="cotaInfo.esgotada" class="cota-msg">
        Limite imposto pelo eSocial (governo). Máximo 10 requests HTTP por dia no webservice de
        download cirúrgico. Cada execução do script de consulta/download consome múltiplas requests.
        Reseta à meia-noite.
      </p>
    </div>

    <!-- Resumo Cards Compacto -->
    <div v-if="resumo" class="cards-grid">
      <div class="stat-card">
        <div class="stat-value">{{ resumo.total }}</div>
        <div class="stat-label">Total</div>
      </div>
      <div
        v-for="item in resumo.por_status"
        :key="item.status"
        class="stat-card"
        :class="statusCardClass(item.status)"
      >
        <div class="stat-value">{{ item.total }}</div>
        <div class="stat-label">{{ statusLabelCurto(item.status) }}</div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="filtros-bar">
      <select v-model="filtroTipo" class="filtro-select" @change="resetAndLoad">
        <option value="">Todos os Eventos</option>
        <option v-for="t in tiposDisponiveis" :key="t" :value="t">{{ t }}</option>
      </select>
      <select v-model="filtroStatus" class="filtro-select" @change="resetAndLoad">
        <option value="">Todos os Status</option>
        <option value="sucesso">Sucesso</option>
        <option value="processado">Processado</option>
        <option value="erro">Erro</option>
        <option value="enviado">Pendente/Enviado</option>
        <option value="bloqueado">Bloqueado (dias 1-7)</option>
        <option value="limite_esgotado">Limite Esgotado (405)</option>
      </select>
      <select v-model="filtroAmbiente" class="filtro-select" @change="resetAndLoad">
        <option value="">Todos os Ambientes</option>
        <option value="1">Produção</option>
        <option value="2">Produção Restrita</option>
      </select>
      <select v-model="filtroCpf" class="filtro-select" @change="filtrarLocal">
        <option value="">Todos os CPFs</option>
        <option v-for="cpf in cpfsDisponiveis" :key="cpf" :value="cpf">{{ formatCpf(cpf) }}</option>
      </select>
      <button class="btn btn-refresh" @click="carregarTudo">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          class="btn-icon"
        >
          <polyline points="23 4 23 10 17 10" />
          <polyline points="1 20 1 14 7 14" />
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
        </svg>
        Atualizar
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <span>Carregando comunicações...</span>
    </div>

    <!-- Erro -->
    <div v-if="erro" class="erro-box">{{ erro }}</div>

    <!-- Tabela de Envios — Limpa -->
    <div v-if="!loading && enviosFiltrados.length > 0" class="envios-table-wrap">
      <table class="envios-table">
        <thead>
          <tr>
            <th class="th-data">Data/Hora</th>
            <th>Evento</th>
            <th>CPF</th>
            <th>Período</th>
            <th>Status</th>
            <th>Resultado</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="envio in enviosFiltrados" :key="envio.id">
            <tr
              :class="[rowClass(envio), { 'row-selected': envioSelecionado?.id === envio.id }]"
              @click="selecionarEnvio(envio)"
            >
              <td class="mono td-data">
                <span class="expand-icon">{{ envioSelecionado?.id === envio.id ? '▼' : '▶' }}</span>
                {{ formatDate(envio.created_at) }}
              </td>
              <td>
                <span class="badge badge-tipo">{{ tipoEventoLabel(envio.tipo_evento) }}</span>
              </td>
              <td class="mono">{{ formatCpf(extrairCpf(envio)) }}</td>
              <td class="mono">{{ extrairPeriodo(envio) }}</td>
              <td>
                <span :class="['badge', statusBadgeClass(statusEfetivo(envio))]">
                  {{ statusLabelCurto(statusEfetivo(envio)) }}
                </span>
              </td>
              <td class="desc-cell" :title="envio.descricao_resposta">
                {{ descricaoResumida(envio) }}
              </td>
            </tr>
            <!-- Linha expandida inline -->
            <tr v-if="envioSelecionado?.id === envio.id" class="row-expand">
              <td colspan="6" class="expand-cell">
                <div class="expand-body">
                  <!-- Status Badge + Código -->
                  <div class="detalhe-status-row">
                    <span :class="['badge badge-lg', statusBadgeClass(statusEfetivo(envio))]">
                      {{ statusLabel(statusEfetivo(envio)) }}
                    </span>
                    <span v-if="envio.codigo_resposta" class="detalhe-cod">
                      Código {{ envio.codigo_resposta }}
                    </span>
                  </div>

                  <!-- Grid de Dados -->
                  <div class="detalhe-grid">
                    <div class="detalhe-item">
                      <span class="detalhe-label">Evento</span>
                      <span class="detalhe-value">{{ envio.tipo_evento }}</span>
                    </div>
                    <div class="detalhe-item">
                      <span class="detalhe-label">Modo</span>
                      <span class="detalhe-value">{{ modoLabel(envio.modo) }}</span>
                    </div>
                    <div class="detalhe-item">
                      <span class="detalhe-label">CPF</span>
                      <span class="detalhe-value mono">{{ formatCpf(extrairCpf(envio)) }}</span>
                    </div>
                    <div class="detalhe-item">
                      <span class="detalhe-label">Período</span>
                      <span class="detalhe-value mono">{{ extrairPeriodo(envio) }}</span>
                    </div>
                    <div class="detalhe-item">
                      <span class="detalhe-label">Ambiente</span>
                      <span class="detalhe-value">
                        {{
                          envio.ambiente === '1' || envio.ambiente === 1
                            ? '🟢 Produção'
                            : '🟡 Prod. Restrita'
                        }}
                      </span>
                    </div>
                    <div class="detalhe-item">
                      <span class="detalhe-label">Total Eventos</span>
                      <span class="detalhe-value">{{ envio.total_eventos || '0' }}</span>
                    </div>
                    <div class="detalhe-item" v-if="envio.protocolo_envio">
                      <span class="detalhe-label">Protocolo</span>
                      <span class="detalhe-value mono">{{ envio.protocolo_envio }}</span>
                    </div>
                    <div class="detalhe-item" v-if="envio.nr_recibo">
                      <span class="detalhe-label">Nº Recibo</span>
                      <span class="detalhe-value mono">{{ envio.nr_recibo }}</span>
                    </div>
                    <div class="detalhe-item" v-if="envio.ini_valid">
                      <span class="detalhe-label">Ini. Validade</span>
                      <span class="detalhe-value mono">{{ envio.ini_valid }}</span>
                    </div>
                    <div class="detalhe-item" v-if="envio.rubrica_ids?.length">
                      <span class="detalhe-label">Rubricas</span>
                      <span class="detalhe-value mono">{{ envio.rubrica_ids.join(', ') }}</span>
                    </div>
                    <div class="detalhe-item">
                      <span class="detalhe-label">Criado em</span>
                      <span class="detalhe-value mono">{{ formatDateFull(envio.created_at) }}</span>
                    </div>
                    <div class="detalhe-item" v-if="envio.updated_at !== envio.created_at">
                      <span class="detalhe-label">Atualizado em</span>
                      <span class="detalhe-value mono">{{ formatDateFull(envio.updated_at) }}</span>
                    </div>
                  </div>

                  <!-- Resposta do Governo -->
                  <div v-if="envio.descricao_resposta" class="detalhe-section">
                    <h4>Resposta do Governo</h4>
                    <div class="code-block">{{ envio.descricao_resposta }}</div>
                  </div>

                  <!-- Ocorrências -->
                  <div v-if="temOcorrencias(envio)" class="detalhe-section">
                    <h4>Ocorrências / Contexto</h4>
                    <div class="ocorrencias-list">
                      <div
                        v-for="(oc, i) in parseOcorrencias(envio)"
                        :key="i"
                        class="ocorrencia-item"
                        :class="ocClass(oc)"
                      >
                        <div class="oc-row">
                          <span v-if="oc.cpf" class="oc-tag">CPF {{ formatCpf(oc.cpf) }}</span>
                          <span v-if="oc.periodo" class="oc-tag">Período {{ oc.periodo }}</span>
                          <span v-if="oc.tipo" class="oc-tag">{{ oc.tipo }}</span>
                          <span v-if="oc.codigo" class="oc-tag oc-codigo"
                            >Cód. {{ oc.codigo }}</span
                          >
                        </div>
                        <div class="oc-msg">
                          {{ oc.mensagem || oc.descricao || JSON.stringify(oc) }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Detalhes das Rubricas (S-1010) -->
                  <div v-if="envio.rubrica_detalhes?.length" class="detalhe-section">
                    <h4>Detalhes das Rubricas Enviadas</h4>
                    <div class="rubrica-cards">
                      <div v-for="(rub, i) in parseRubricas(envio)" :key="i" class="rubrica-card">
                        <div class="rubrica-header">
                          <span class="rubrica-cod">Rubrica {{ rub.cod_rubrica }}</span>
                          <span class="rubrica-desc">{{ rub.descricao }}</span>
                        </div>
                        <div class="rubrica-grid">
                          <div v-if="rub.nat_rubr" class="rubrica-field">
                            <span class="rf-label">Natureza</span>
                            <span class="rf-value"
                              >{{ rub.nat_rubr }}
                              {{ rub.cod_natureza ? '— ' + rub.cod_natureza : '' }}</span
                            >
                          </div>
                          <div class="rubrica-field">
                            <span class="rf-label">INSS</span>
                            <span class="rf-value">{{
                              rub.codIncCP ?? rub.incid_inss ?? '-'
                            }}</span>
                          </div>
                          <div class="rubrica-field">
                            <span class="rf-label">IRRF</span>
                            <span class="rf-value">{{
                              rub.codIncIRRF ?? rub.incid_irrf ?? '-'
                            }}</span>
                          </div>
                          <div class="rubrica-field">
                            <span class="rf-label">FGTS</span>
                            <span class="rf-value">{{
                              rub.codIncFGTS ?? rub.incid_fgts ?? '-'
                            }}</span>
                          </div>
                          <div v-if="rub.nr_recibo" class="rubrica-field rubrica-field-wide">
                            <span class="rf-label">Recibo</span>
                            <span class="rf-value mono">{{ rub.nr_recibo }}</span>
                          </div>
                          <div v-if="rub.analise" class="rubrica-field rubrica-field-wide">
                            <span class="rf-label">Análise</span>
                            <span class="rf-value rf-analise">{{ rub.analise }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Vazio -->
    <div v-if="!loading && !erro && enviosFiltrados.length === 0 && carregou" class="empty-state">
      <p>Nenhuma comunicação encontrada com os filtros selecionados.</p>
    </div>

    <!-- Paginação -->
    <div v-if="total > limit" class="paginacao">
      <button :disabled="offset === 0" @click="paginaAnterior" class="btn btn-page">
        ← Anterior
      </button>
      <span class="page-info">{{ paginaAtual }} / {{ totalPaginas }}</span>
      <button :disabled="offset + limit >= total" @click="proximaPagina" class="btn btn-page">
        Próxima →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const API = '/api'

const loading = ref(false)
const carregou = ref(false)
const erro = ref('')
const envios = ref<any[]>([])
const total = ref(0)
const limit = ref(50)
const offset = ref(0)
const resumo = ref<any>(null)
const envioSelecionado = ref<any>(null)

const filtroTipo = ref('')
const filtroStatus = ref('')
const filtroAmbiente = ref('')
const filtroCpf = ref('')

const tiposDisponiveis = computed(() => {
  if (!resumo.value?.por_tipo) return []
  return resumo.value.por_tipo.map((t: any) => t.tipo_evento)
})

// Extrair CPFs únicos das ocorrencias dos envios carregados
const cpfsDisponiveis = computed(() => {
  const cpfs = new Set<string>()
  for (const e of envios.value) {
    const cpf = extrairCpf(e)
    if (cpf && cpf !== '-') cpfs.add(cpf)
  }
  return Array.from(cpfs).sort()
})

// Filtro local por CPF (não vai ao backend)
const enviosFiltrados = computed(() => {
  if (!filtroCpf.value) return envios.value
  return envios.value.filter((e) => extrairCpf(e) === filtroCpf.value)
})

// Cota de download cirúrgico — calcula a partir dos envios de hoje
const cotaInfo = computed(() => {
  const hoje = new Date().toISOString().slice(0, 10)
  let usadas = 0
  for (const e of envios.value) {
    if (!e.created_at) continue
    const dia = e.created_at.slice(0, 10)
    if (dia !== hoje) continue
    const tipo = e.tipo_evento || ''
    if (tipo.startsWith('CONSULTA') || tipo.startsWith('DOWNLOAD')) {
      usadas++
    }
  }
  return { usadas, esgotada: usadas >= 10 }
})

const paginaAtual = computed(() => Math.floor(offset.value / limit.value) + 1)
const totalPaginas = computed(() => Math.ceil(total.value / limit.value))

function proximaPagina() {
  offset.value += limit.value
  carregarEnvios()
}
function paginaAnterior() {
  offset.value = Math.max(0, offset.value - limit.value)
  carregarEnvios()
}

function resetAndLoad() {
  offset.value = 0
  carregarEnvios()
}

function filtrarLocal() {
  // CPF filter is purely client-side via computed
}

async function carregarResumo() {
  try {
    const res = await fetch(`${API}/envios/resumo`)
    const data = await res.json()
    if (data.success) resumo.value = data.resumo
  } catch (e: any) {
    console.error('Erro ao carregar resumo:', e)
  }
}

async function carregarEnvios() {
  loading.value = true
  erro.value = ''
  try {
    const params = new URLSearchParams()
    params.set('limit', String(limit.value))
    params.set('offset', String(offset.value))
    if (filtroTipo.value) params.set('tipo_evento', filtroTipo.value)
    if (filtroStatus.value) params.set('status', filtroStatus.value)
    if (filtroAmbiente.value) params.set('ambiente', filtroAmbiente.value)

    const res = await fetch(`${API}/envios?${params}`)
    const data = await res.json()
    if (data.success) {
      envios.value = data.envios
      total.value = data.total
    } else {
      erro.value = data.error || 'Erro desconhecido'
    }
  } catch (e: any) {
    erro.value = `Erro ao carregar: ${e.message}`
  } finally {
    loading.value = false
    carregou.value = true
  }
}

async function carregarTudo() {
  offset.value = 0
  await Promise.all([carregarResumo(), carregarEnvios()])
}

function selecionarEnvio(envio: any) {
  envioSelecionado.value = envioSelecionado.value?.id === envio.id ? null : envio
}

// === Formatters ===

function formatDate(d: string) {
  if (!d) return '-'
  const dt = new Date(d)
  return (
    dt.toLocaleDateString('pt-BR') +
    ' ' +
    dt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  )
}

function formatDateFull(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleString('pt-BR')
}

function formatCpf(cpf: string) {
  if (!cpf || cpf === '-') return '-'
  if (cpf.length === 11) {
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
  }
  return cpf
}

function tipoEventoLabel(tipo: string) {
  const map: Record<string, string> = {
    'CONSULTA-IDENT': 'Consulta',
    'DOWNLOAD-S5002': 'Download S-5002',
    'DOWNLOAD-S-5002': 'Download S-5002',
    'DOWNLOAD-S-5001': 'Download S-5001',
    'S-1010': 'S-1010',
  }
  return map[tipo] || tipo
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    sucesso: 'Aceito',
    processado: 'Processado',
    erro: 'Rejeitado/Erro',
    pendente: 'Pendente',
    enviado: 'Enviado',
    bloqueado: '⛔ Bloqueado (dias 1-7)',
    limite_esgotado: '🚫 Limite Esgotado (405)',
  }
  return map[s] || s
}

function statusLabelCurto(s: string) {
  const map: Record<string, string> = {
    sucesso: 'Aceitos',
    processado: 'Processados',
    erro: 'Erro',
    pendente: 'Pendentes',
    enviado: 'Enviados',
    bloqueado: '⛔ Bloqueado',
    limite_esgotado: '🚫 Limite',
  }
  return map[s] || s
}

function modoLabel(m: string) {
  const map: Record<string, string> = {
    consulta: 'Consulta/Download',
    alteracao: 'Alteração',
    inclusao: 'Inclusão',
    exclusao: 'Exclusão',
  }
  return map[m] || m || '-'
}

// === Data extractors ===

function extrairCpf(envio: any): string {
  const ocs = parseOcorrencias(envio)
  for (const oc of ocs) {
    if (oc.cpf) return oc.cpf
  }
  return '-'
}

function extrairPeriodo(envio: any): string {
  // First from ocorrencias
  const ocs = parseOcorrencias(envio)
  for (const oc of ocs) {
    if (oc.periodo) return oc.periodo
  }
  // Fallback to ini_valid
  return envio.ini_valid || '-'
}

function statusEfetivo(envio: any): string {
  if (envio.codigo_resposta === '405' || envio.codigo_resposta === 405) {
    return 'limite_esgotado'
  }
  if (
    envio.descricao_resposta?.includes?.('500 Server Error') ||
    envio.descricao_resposta?.includes?.('ServiceActivationException')
  ) {
    return 'erro'
  }
  return envio.status
}

function descricaoResumida(envio: any): string {
  const d = envio.descricao_resposta || '-'
  if (d.includes('10 solicitações por dia')) return '🚫 Cota esgotada — limite governo'
  if (d.includes('ServiceActivationException')) return '💥 Servidor gov. fora do ar (500)'
  if (d.includes('Quantidade total de eventos encontrados')) {
    const m = d.match(/(\d+)/)
    return m ? `✅ ${m[1]} eventos encontrados` : d
  }
  if (d.includes('Lote processado com sucesso')) return '✅ Processado com sucesso'
  if (d.includes('Lote Recebido com Sucesso')) return '✅ Recebido com sucesso'
  return d.length > 50 ? d.substring(0, 50) + '…' : d
}

// === Status styling ===

function statusCardClass(s: string) {
  if (s === 'sucesso' || s === 'processado') return 'card-ok'
  if (s === 'erro') return 'card-erro'
  if (s === 'bloqueado') return 'card-bloqueado'
  if (s === 'limite_esgotado') return 'card-limite'
  return 'card-pendente'
}

function statusBadgeClass(s: string) {
  if (s === 'sucesso' || s === 'processado') return 'badge-ok'
  if (s === 'erro') return 'badge-erro'
  if (s === 'bloqueado') return 'badge-bloqueado'
  if (s === 'limite_esgotado') return 'badge-limite'
  return 'badge-pendente'
}

function rowClass(envio: any) {
  const st = statusEfetivo(envio)
  if (st === 'limite_esgotado') return 'row-limite'
  if (st === 'erro') return 'row-erro'
  if (st === 'bloqueado') return 'row-bloqueado'
  if (st === 'sucesso' || st === 'processado') return 'row-ok'
  return ''
}

function ocClass(oc: any) {
  if (oc.tipo === 1) return 'oc-erro'
  if (oc.mensagem?.includes?.('limite') || oc.mensagem?.includes?.('405')) return 'oc-limite'
  if (oc.mensagem?.includes?.('500') || oc.mensagem?.includes?.('Error')) return 'oc-erro'
  return 'oc-info'
}

// === Parsers ===

function temOcorrencias(envio: any) {
  if (!envio.ocorrencias) return false
  if (typeof envio.ocorrencias === 'string') {
    try {
      return JSON.parse(envio.ocorrencias)?.length > 0
    } catch {
      return false
    }
  }
  return Array.isArray(envio.ocorrencias) && envio.ocorrencias.length > 0
}

function contarOcorrencias(envio: any) {
  return parseOcorrencias(envio).length
}

function parseOcorrencias(envio: any): any[] {
  if (!envio.ocorrencias) return []
  if (typeof envio.ocorrencias === 'string') {
    try {
      return JSON.parse(envio.ocorrencias)
    } catch {
      return []
    }
  }
  return Array.isArray(envio.ocorrencias) ? envio.ocorrencias : []
}

function parseRubricas(envio: any): any[] {
  if (!envio.rubrica_detalhes) return []
  if (typeof envio.rubrica_detalhes === 'string') {
    try {
      return JSON.parse(envio.rubrica_detalhes)
    } catch {
      return []
    }
  }
  return Array.isArray(envio.rubrica_detalhes) ? envio.rubrica_detalhes : []
}

function formatJson(val: any) {
  if (!val) return '-'
  if (typeof val === 'string') {
    try {
      return JSON.stringify(JSON.parse(val), null, 2)
    } catch {
      return val
    }
  }
  return JSON.stringify(val, null, 2)
}

onMounted(() => {
  carregarTudo()
})
</script>

<style scoped>
.comunicacao-tab {
  position: relative;
  z-index: 1;
  padding-top: 20px;
}

.title {
  font-size: 22px;
  font-weight: 700;
  color: white;
  margin: 0 0 6px 0;
}

.subtitle {
  font-size: 14px;
  color: rgba(224, 230, 237, 0.5);
  margin: 0 0 20px 0;
}

/* Cota Banner */
.cota-banner {
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.cota-esgotada {
  background: rgba(168, 85, 247, 0.08);
  border: 1px solid rgba(168, 85, 247, 0.4);
}
.cota-ok {
  background: rgba(34, 197, 94, 0.06);
  border: 1px solid rgba(34, 197, 94, 0.25);
}
.cota-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.cota-icon {
  font-size: 18px;
}
.cota-titulo {
  font-size: 13px;
  font-weight: 600;
  color: rgba(224, 230, 237, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.cota-counter {
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  color: #22c55e;
}
.counter-esgotada {
  color: #a855f7;
}
.cota-bar-wrap {
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
}
.cota-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}
.bar-ok {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}
.bar-esgotada {
  background: linear-gradient(90deg, #a855f7, #ef4444);
}
.cota-msg {
  margin: 10px 0 0 0;
  font-size: 12px;
  color: rgba(168, 85, 247, 0.8);
  line-height: 1.5;
}

/* Cards */
.cards-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.stat-card {
  background: rgba(13, 21, 48, 0.7);
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 10px;
  padding: 12px 16px;
  min-width: 80px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: white;
}

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(224, 230, 237, 0.5);
  margin-top: 2px;
}

.card-ok {
  border-color: rgba(34, 197, 94, 0.4);
}
.card-ok .stat-value {
  color: #22c55e;
}
.card-erro {
  border-color: rgba(239, 68, 68, 0.4);
}
.card-erro .stat-value {
  color: #ef4444;
}
.card-pendente {
  border-color: rgba(250, 204, 21, 0.4);
}
.card-pendente .stat-value {
  color: #facc15;
}
.card-bloqueado {
  border-color: rgba(249, 115, 22, 0.5);
  background: rgba(249, 115, 22, 0.08);
}
.card-bloqueado .stat-value {
  color: #f97316;
}
.card-limite {
  border-color: rgba(168, 85, 247, 0.5);
  background: rgba(168, 85, 247, 0.08);
}
.card-limite .stat-value {
  color: #a855f7;
}

/* Filtros */
.filtros-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.filtro-select {
  background: rgba(13, 21, 48, 0.8);
  border: 1px solid rgba(0, 102, 255, 0.2);
  border-radius: 8px;
  padding: 7px 10px;
  color: #e0e6ed;
  font-size: 12px;
  cursor: pointer;
}
.filtro-select:focus {
  outline: none;
  border-color: #0066ff;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}
.btn-refresh {
  background: rgba(0, 102, 255, 0.15);
  color: #60a5fa;
}
.btn-refresh:hover {
  background: rgba(0, 102, 255, 0.3);
}
.btn-icon {
  width: 14px;
  height: 14px;
}
.btn-page {
  background: rgba(0, 102, 255, 0.1);
  color: #60a5fa;
}
.btn-page:hover {
  background: rgba(0, 102, 255, 0.2);
}
.btn-page:disabled {
  opacity: 0.3;
  cursor: default;
}

/* Loading / Error */
.loading-spinner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 32px;
  color: rgba(224, 230, 237, 0.6);
}
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(0, 102, 255, 0.2);
  border-top-color: #0066ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.erro-box {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
  color: #fca5a5;
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: rgba(224, 230, 237, 0.4);
  font-size: 14px;
}

/* Table — Clean 6-column layout */
.envios-table-wrap {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid rgba(0, 102, 255, 0.12);
  background: rgba(13, 21, 48, 0.5);
}

.envios-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}

.envios-table th {
  background: rgba(0, 102, 255, 0.08);
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(224, 230, 237, 0.6);
  border-bottom: 1px solid rgba(0, 102, 255, 0.15);
  white-space: nowrap;
}

.envios-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 102, 255, 0.06);
  color: #c4cdd8;
}

.envios-table tbody tr {
  cursor: pointer;
  transition: background 0.15s;
}
.envios-table tbody tr:hover {
  background: rgba(0, 102, 255, 0.06);
}

.row-ok {
  border-left: 3px solid #22c55e;
}
.row-erro {
  border-left: 3px solid #ef4444;
}
.row-bloqueado {
  border-left: 3px solid #f97316;
  background: rgba(249, 115, 22, 0.04);
}
.row-limite {
  border-left: 3px solid #a855f7;
  background: rgba(168, 85, 247, 0.04);
}
.row-selected {
  background: rgba(0, 102, 255, 0.1) !important;
}

.mono {
  font-family: 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 11.5px;
}

.td-data {
  white-space: nowrap;
}
.desc-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Badges */
.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}
.badge-lg {
  padding: 6px 14px;
  font-size: 13px;
}
.badge-tipo {
  background: rgba(0, 102, 255, 0.15);
  color: #60a5fa;
}
.badge-ok {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}
.badge-erro {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.badge-pendente {
  background: rgba(250, 204, 21, 0.15);
  color: #facc15;
}
.badge-bloqueado {
  background: rgba(249, 115, 22, 0.2);
  color: #f97316;
  font-weight: 700;
}
.badge-limite {
  background: rgba(168, 85, 247, 0.2);
  color: #a855f7;
  font-weight: 700;
}

/* Paginação */
.paginacao {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px;
}
.page-info {
  font-size: 13px;
  color: rgba(224, 230, 237, 0.6);
}

/* Expand icon */
.expand-icon {
  display: inline-block;
  width: 12px;
  font-size: 9px;
  color: rgba(224, 230, 237, 0.35);
  margin-right: 4px;
  transition: transform 0.15s;
}

/* Inline expand row */
.row-expand {
  background: rgba(13, 21, 48, 0.85);
}
.row-expand:hover {
  background: rgba(13, 21, 48, 0.85) !important;
}
.expand-cell {
  padding: 0 !important;
  border-bottom: 2px solid rgba(0, 102, 255, 0.2) !important;
}
.expand-body {
  padding: 18px 24px 20px;
  border-left: 3px solid #0066ff;
  animation: expandIn 0.15s ease;
}
@keyframes expandIn {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 2000px;
  }
}

.detalhe-status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.detalhe-cod {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: rgba(224, 230, 237, 0.5);
}

.detalhe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.detalhe-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.detalhe-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(224, 230, 237, 0.4);
}
.detalhe-value {
  font-size: 13px;
  color: #e0e6ed;
}

.detalhe-section {
  margin-top: 16px;
}
.detalhe-section h4 {
  margin: 0 0 10px 0;
  font-size: 12px;
  color: rgba(224, 230, 237, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.code-block {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 102, 255, 0.1);
  border-radius: 8px;
  padding: 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: #a3b8d0;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

/* Ocorrências */
.ocorrencias-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ocorrencia-item {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 12px;
}
.oc-erro {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
}
.oc-limite {
  background: rgba(168, 85, 247, 0.08);
  border: 1px solid rgba(168, 85, 247, 0.2);
}
.oc-info {
  background: rgba(0, 102, 255, 0.06);
  border: 1px solid rgba(0, 102, 255, 0.15);
}

.oc-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.oc-tag {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(224, 230, 237, 0.7);
}
.oc-codigo {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}
.oc-msg {
  color: #c4cdd8;
  line-height: 1.4;
}

/* Rubrica Cards */
.rubrica-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rubrica-card {
  background: rgba(0, 102, 255, 0.04);
  border: 1px solid rgba(0, 102, 255, 0.12);
  border-radius: 10px;
  overflow: hidden;
}

.rubrica-header {
  padding: 10px 14px;
  background: rgba(0, 102, 255, 0.06);
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(0, 102, 255, 0.08);
}
.rubrica-cod {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: #60a5fa;
}
.rubrica-desc {
  font-size: 12px;
  color: rgba(224, 230, 237, 0.7);
}

.rubrica-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  padding: 12px 14px;
}

.rubrica-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rubrica-field-wide {
  grid-column: 1 / -1;
}
.rf-label {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(224, 230, 237, 0.35);
}
.rf-value {
  font-size: 12px;
  color: #c4cdd8;
}
.rf-analise {
  color: #facc15;
  font-weight: 600;
  font-size: 11px;
}
</style>
