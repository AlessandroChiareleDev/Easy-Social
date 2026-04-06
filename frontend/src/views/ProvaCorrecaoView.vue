<template>
  <div class="prova-view">
    <!-- Glass shapes -->
    <div class="glass-shapes">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
    </div>

    <h1 class="title">Prova de Correção — Comprovação Completa</h1>
    <p class="subtitle">
      Evidência integral do trabalho realizado no eSocial para o CPF piloto
    </p>

    <!-- Busca por CPF -->
    <div class="search-bar">
      <input
        v-model="cpfInput"
        class="input mono"
        placeholder="CPF (11 dígitos)"
        @keyup.enter="carregarProva"
      />
      <button class="btn btn-primary" @click="carregarProva" :disabled="loading">
        {{ loading ? 'Carregando...' : 'Carregar Prova' }}
      </button>
    </div>

    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <span>Buscando evidências no banco de dados...</span>
    </div>

    <div v-if="erro" class="erro-box">{{ erro }}</div>

    <template v-if="prova">
      <!-- ═══════ 1. RESUMO EXECUTIVO ═══════ -->
      <section class="section resumo-section">
        <h2 class="section-title">1. Resumo Executivo</h2>
        <div class="cards-grid">
          <div class="stat-card">
            <div class="stat-value">{{ prova.resumo.rubricas_corrigidas }}</div>
            <div class="stat-label">Rubricas Corrigidas (S-1010)</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ prova.resumo.total_envios }}</div>
            <div class="stat-label">Envios ao eSocial</div>
          </div>
          <div class="stat-card" :class="prova.resumo.envios_sucesso > 0 ? 'card-ok' : ''">
            <div class="stat-value">{{ prova.resumo.envios_sucesso }}</div>
            <div class="stat-label">Aceitos pelo Governo</div>
          </div>
          <div class="stat-card" :class="prova.resumo.envios_erro > 0 ? 'card-warn' : ''">
            <div class="stat-value">{{ prova.resumo.envios_erro }}</div>
            <div class="stat-label">Com Rejeição/Erro</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ prova.resumo.total_pipelines }}</div>
            <div class="stat-label">Pipelines Executados</div>
          </div>
          <div class="stat-card" :class="prova.resumo.tem_comparacao ? 'card-ok' : 'card-warn'">
            <div class="stat-value">{{ prova.resumo.tem_comparacao ? 'SIM' : 'NÃO' }}</div>
            <div class="stat-label">Comparação PRÉ/PÓS</div>
          </div>
        </div>
      </section>

      <!-- ═══════ 2. RUBRICAS CORRIGIDAS ═══════ -->
      <section class="section" v-if="prova.rubricas_corrigidas?.length">
        <h2 class="section-title">2. Rubricas Corrigidas (S-1010)</h2>
        <p class="section-desc">
          Cada rubrica abaixo teve seu cadastro corrigido no eSocial com envio de evento S-1010
          (alteração).
        </p>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Descrição</th>
                <th>Natureza</th>
                <th>INSS (codIncCP)</th>
                <th>IRRF (codIncIRRF)</th>
                <th>FGTS (codIncFGTS)</th>
                <th>Status Envio</th>
                <th>Data Correção</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in prova.rubricas_corrigidas" :key="r.cod_rubrica">
                <td class="mono">{{ r.cod_rubrica }}</td>
                <td>{{ r.descricao }}</td>
                <td class="mono">{{ r.cod_natureza }}</td>
                <td class="mono">{{ r.incid_inss }}</td>
                <td class="mono">{{ r.incid_irrf }}</td>
                <td class="mono">{{ r.incid_fgts }}</td>
                <td>
                  <span class="badge" :class="badgeClass(r.envio_status)">{{
                    r.envio_status
                  }}</span>
                </td>
                <td class="mono">{{ formatDate(r.corrigido_em) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ═══════ 3. ENVIOS AO ESOCIAL (Respostas do Governo) ═══════ -->
      <section class="section" v-if="prova.envios_esocial?.length">
        <h2 class="section-title">3. Envios ao eSocial — Respostas do Governo</h2>
        <p class="section-desc">
          Cada linha é um envio real ao webservice do eSocial (governo federal). O
          <strong>código de resposta</strong> e <strong>descrição</strong> são a resposta literal
          da API do governo, não do nosso sistema.
        </p>
        <div class="table-wrap">
          <table class="data-table envios-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Evento</th>
                <th>Modo</th>
                <th>Ambiente</th>
                <th>Status</th>
                <th>Protocolo</th>
                <th>nrRecibo</th>
                <th>Cód. Resposta</th>
                <th>Resposta do Governo</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="e in prova.envios_esocial"
                :key="e.id"
                :class="{ 'row-erro': e.status !== '201', 'row-ok': e.status === '201' }"
              >
                <td class="mono">{{ e.id }}</td>
                <td class="mono">{{ e.tipo_evento }}</td>
                <td>{{ e.modo }}</td>
                <td>{{ e.ambiente === '1' ? 'PROD' : 'HOM' }}</td>
                <td>
                  <span class="badge" :class="e.status === '201' ? 'badge-ok' : 'badge-erro'">
                    {{ e.status }}
                  </span>
                </td>
                <td class="mono small">{{ e.protocolo_envio || '—' }}</td>
                <td class="mono small">{{ e.nr_recibo || '—' }}</td>
                <td class="mono">{{ e.codigo_resposta || '—' }}</td>
                <td class="resposta-cell">
                  <span
                    v-if="e.descricao_resposta"
                    class="resposta-text"
                    :class="{ 'resposta-erro': e.status !== '201' }"
                  >
                    {{ e.descricao_resposta }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="mono small">{{ formatDate(e.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Ocorrências detalhadas -->
        <div v-if="enviosComOcorrencias.length" class="ocorrencias-section">
          <h3 class="sub-title">Detalhes de Ocorrências (respostas detalhadas do governo)</h3>
          <div v-for="e in enviosComOcorrencias" :key="'oc-' + e.id" class="ocorrencia-card">
            <div class="oc-header">
              Envio #{{ e.id }} — {{ e.tipo_evento }} ({{ formatDate(e.created_at) }})
            </div>
            <pre class="oc-body">{{ formatOcorrencias(e.ocorrencias) }}</pre>
          </div>
        </div>
      </section>

      <!-- ═══════ 4. PIPELINE DE RECUPERAÇÃO ═══════ -->
      <section class="section" v-if="prova.pipelines?.length">
        <h2 class="section-title">4. Pipeline de Recuperação Executado</h2>
        <p class="section-desc">
          Sequência completa de 8 passos executados em produção para corrigir o período
          {{ prova.per_apur }}.
        </p>
        <div v-for="p in prova.pipelines" :key="p.id" class="pipeline-card">
          <div class="pipeline-header">
            <span class="pipeline-id">Pipeline #{{ p.id }}</span>
            <span class="badge" :class="p.status === 'completo' ? 'badge-ok' : 'badge-erro'">
              {{ p.status }}
            </span>
            <span class="mono small">{{ formatDate(p.created_at) }}</span>
          </div>
          <div class="pipeline-steps">
            <div class="step-row" v-if="p.s1010_nr_recibo">
              <span class="step-label">S-1010 (Correção Rubrica)</span>
              <span class="mono">{{ p.s1010_nr_recibo }}</span>
            </div>
            <div class="step-row" v-if="p.s1298_nr_recibo">
              <span class="step-label">S-1298 (Reabertura)</span>
              <span class="mono">{{ p.s1298_nr_recibo }}</span>
            </div>
            <div class="step-row" v-if="p.s1200_nr_recibo">
              <span class="step-label">S-1200 (Retificação Remuneração)</span>
              <span class="mono">{{ p.s1200_nr_recibo }}</span>
            </div>
            <div class="step-row" v-if="p.s1210_nr_recibo">
              <span class="step-label">S-1210 (Retificação Pagamento)</span>
              <span class="mono">{{ p.s1210_nr_recibo }}</span>
            </div>
            <div class="step-row" v-if="p.s1299_nr_recibo">
              <span class="step-label">S-1299 (Fechamento)</span>
              <span class="mono">{{ p.s1299_nr_recibo }}</span>
            </div>
            <div v-if="p.erro" class="step-error">
              <strong>Erro:</strong> {{ p.erro }}
            </div>
          </div>

          <!-- Steps log detalhado -->
          <div v-if="p.steps_log" class="steps-log">
            <details>
              <summary class="log-summary">Ver log detalhado ({{ stepsLogCount(p.steps_log) }} eventos)</summary>
              <pre class="log-pre">{{ formatStepsLog(p.steps_log) }}</pre>
            </details>
          </div>
        </div>
      </section>

      <!-- ═══════ 5. COMPARAÇÃO PRÉ vs PÓS ═══════ -->
      <section class="section" v-if="prova.comparacao">
        <h2 class="section-title">5. Comparação PRÉ vs PÓS Pipeline</h2>

        <!-- Mudanças nas rubricas -->
        <div v-if="prova.comparacao.rubricas?.length" class="comp-block">
          <h3 class="sub-title">Campos Alterados nas Rubricas</h3>
          <div class="table-wrap">
            <table class="data-table comp-table">
              <thead>
                <tr>
                  <th>Rubrica</th>
                  <th>Campo</th>
                  <th class="col-antes">ANTES</th>
                  <th></th>
                  <th class="col-depois">DEPOIS</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="r in prova.comparacao.rubricas" :key="r.cod_rubrica">
                  <tr v-for="(change, campo, idx) in r.mudancas" :key="r.cod_rubrica + '-' + campo">
                    <td
                      v-if="idx === 0"
                      :rowspan="Object.keys(r.mudancas).length"
                      class="rubrica-cell"
                    >
                      <span class="mono">{{ r.cod_rubrica }}</span>
                      <br />
                      <small>{{ r.descricao }}</small>
                    </td>
                    <td class="campo-name">{{ formatCampo(campo as string) }}</td>
                    <td class="val-antes mono">{{ change.antes }}</td>
                    <td class="arrow-cell">→</td>
                    <td class="val-depois mono">{{ change.depois }}</td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>

        <!-- S-5002 lado a lado -->
        <div v-if="prova.comparacao.s5002" class="comp-block">
          <h3 class="sub-title">S-5002 Totalizadores IRRF — Antes vs Depois</h3>
          <div class="s5002-side">
            <div class="s5002-col">
              <div class="s5002-header antes">PRÉ-Pipeline</div>
              <table class="data-table" v-if="prova.comparacao.s5002.antes?.length">
                <thead>
                  <tr>
                    <th>tpInfoIR</th>
                    <th>Descrição</th>
                    <th>Valor</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(t, i) in prova.comparacao.s5002.antes" :key="'a' + i">
                    <td class="mono">{{ t.tpInfoIR }}</td>
                    <td>{{ t.descricao }}</td>
                    <td class="mono">R$ {{ t.valor }}</td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="empty-note">Nenhum totalizador capturado no PRÉ</p>
            </div>
            <div class="s5002-col">
              <div class="s5002-header depois">PÓS-Pipeline</div>
              <table class="data-table" v-if="prova.comparacao.s5002.depois?.length">
                <thead>
                  <tr>
                    <th>tpInfoIR</th>
                    <th>Descrição</th>
                    <th>Valor</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(t, i) in prova.comparacao.s5002.depois" :key="'d' + i">
                    <td class="mono">{{ t.tpInfoIR }}</td>
                    <td>{{ t.descricao }}</td>
                    <td class="mono">R$ {{ t.valor }}</td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="empty-note">
                S-5002 pós-correção indisponível — Bloqueio eSocial dias 1-7 do mês
              </p>
            </div>
          </div>
        </div>

        <!-- Recibos antes vs depois -->
        <div v-if="prova.comparacao.recibos" class="comp-block">
          <h3 class="sub-title">Recibos — Antes vs Depois</h3>
          <div class="recibos-compare">
            <div class="recibo-col">
              <div class="s5002-header antes">PRÉ</div>
              <div
                v-for="(rec, ev) in prova.comparacao.recibos.antes"
                :key="'ra-' + ev"
                class="recibo-card"
              >
                <div class="recibo-evento">{{ ev }}</div>
                <div class="recibo-nr mono">{{ rec.nrRecibo || rec }}</div>
              </div>
            </div>
            <div class="recibo-col">
              <div class="s5002-header depois">PÓS</div>
              <div
                v-for="(rec, ev) in prova.comparacao.recibos.depois"
                :key="'rd-' + ev"
                class="recibo-card"
              >
                <div class="recibo-evento">{{ ev }}</div>
                <div class="recibo-nr mono">{{ rec.nrRecibo || rec }}</div>
              </div>
              <div
                v-if="
                  !prova.comparacao.recibos.depois ||
                  Object.keys(prova.comparacao.recibos.depois).length === 0
                "
                class="empty-note"
              >
                Aguardando execução do pipeline
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══════ 6. NOTA SOBRE BLOQUEIO DOWNLOAD ═══════ -->
      <section class="section bloqueio-section">
        <h2 class="section-title">6. Nota Técnica — Bloqueio Download eSocial</h2>
        <div class="bloqueio-card">
          <div class="bloqueio-icon">⛔</div>
          <div class="bloqueio-content">
            <h3>Bloqueio de Download entre dias 1 e 7 do mês</h3>
            <p>
              A API do eSocial (webservice do governo federal, operado pelo SERPRO) retorna
              <strong>HTTP 403</strong> ao tentar fazer download de eventos/totalizadores entre os
              dias 1 e 7 de cada mês.
            </p>
            <div class="bloqueio-msg">
              <code
                >Erro 403: "Não é possível enviar solicitação de download entre os dias 1 e 7 do
                mês"</code
              >
            </div>
            <p class="bloqueio-detail">
              Esta mensagem é retornada diretamente pela
              <strong>API do governo</strong> (endpoint
              <code>consultar_identificadores_trabalhador</code> /
              <code>SolicitarDownloadEventosPorId</code>), não pelo nosso sistema. A restrição
              existe provavelmente para proteger a infraestrutura durante o pico de processamento de
              fechamento de folha no início do mês.
            </p>
            <p class="bloqueio-detail">
              <strong>Origem da evidência:</strong> Tentativa de download do S-5002 em 04/04/2026
              para o CPF 081.325.889-83 retornou este erro. O S-5002 novo (gerado pelo S-1299
              Dez/2024) existe no eSocial mas só pode ser baixado a partir do dia 8 do mês.
            </p>
          </div>
        </div>
      </section>

      <!-- ═══════ 7. SNAPSHOTS BRUTOS ═══════ -->
      <section class="section" v-if="prova.snapshot_pre || prova.snapshot_pos">
        <h2 class="section-title">7. Dados Brutos dos Snapshots</h2>
        <div class="snapshots-raw">
          <details v-if="prova.snapshot_pre">
            <summary class="log-summary">
              Snapshot PRÉ-Pipeline #{{ prova.snapshot_pre.id }} ({{
                formatDate(prova.snapshot_pre.created_at)
              }})
            </summary>
            <pre class="log-pre">{{ JSON.stringify(prova.snapshot_pre.dados, null, 2) }}</pre>
          </details>
          <details v-if="prova.snapshot_pos">
            <summary class="log-summary">
              Snapshot PÓS-Pipeline #{{ prova.snapshot_pos.id }} ({{
                formatDate(prova.snapshot_pos.created_at)
              }})
            </summary>
            <pre class="log-pre">{{ JSON.stringify(prova.snapshot_pos.dados, null, 2) }}</pre>
          </details>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { PYTHON_API } from '../lib/api'

const cpfInput = ref('08132588983')
const loading = ref(false)
const erro = ref('')
const prova = ref<any>(null)

const enviosComOcorrencias = computed(() => {
  if (!prova.value?.envios_esocial) return []
  return prova.value.envios_esocial.filter(
    (e: any) => e.ocorrencias && (Array.isArray(e.ocorrencias) ? e.ocorrencias.length > 0 : true),
  )
})

async function carregarProva() {
  const cpf = cpfInput.value.replace(/\D/g, '')
  if (cpf.length !== 11) {
    erro.value = 'CPF deve ter 11 dígitos'
    return
  }
  loading.value = true
  erro.value = ''
  prova.value = null

  try {
    const res = await fetch(`${PYTHON_API}/api/pipeline-audit/prova/${cpf}`)
    if (!res.ok) {
      const text = await res.text()
      erro.value = `Erro ${res.status}: ${text}`
      return
    }
    prova.value = await res.json()
  } catch (e: any) {
    erro.value = `Erro de conexão: ${e.message}`
  } finally {
    loading.value = false
  }
}

function formatDate(d: string | null) {
  if (!d) return '—'
  try {
    return new Date(d).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return d
  }
}

function formatCampo(campo: string) {
  const map: Record<string, string> = {
    incid_irrf: 'codIncIRRF',
    incid_inss: 'codIncCP',
    incid_fgts: 'codIncFGTS',
    corrigido: 'Corrigido?',
    envio_status: 'Status Envio',
  }
  return map[campo] || campo
}

function badgeClass(status: string) {
  if (!status) return ''
  if (status === '201' || status === 'enviado' || status === 'aceito') return 'badge-ok'
  if (status === 'erro' || status === 'rejeitado') return 'badge-erro'
  return 'badge-pending'
}

function formatOcorrencias(occ: any) {
  if (!occ) return ''
  if (typeof occ === 'string') return occ
  return JSON.stringify(occ, null, 2)
}

function stepsLogCount(log: any) {
  if (Array.isArray(log)) return log.length
  if (typeof log === 'object') return Object.keys(log).length
  return '?'
}

function formatStepsLog(log: any) {
  if (!log) return ''
  return JSON.stringify(log, null, 2)
}
</script>

<style scoped>
.prova-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
}

.glass-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.glass-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.1;
}
.shape-1 {
  width: 400px;
  height: 400px;
  background: #0066ff;
  top: -100px;
  right: -100px;
  animation: drift1 18s ease-in-out infinite;
}
.shape-2 {
  width: 300px;
  height: 300px;
  background: #00ccff;
  bottom: 200px;
  left: -80px;
  animation: drift2 22s ease-in-out infinite;
}
.shape-3 {
  width: 250px;
  height: 250px;
  background: #6600ff;
  top: 50%;
  right: 30%;
  animation: drift3 20s ease-in-out infinite;
}

@keyframes drift1 {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-40px, 30px);
  }
}
@keyframes drift2 {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(30px, -20px);
  }
}
@keyframes drift3 {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-20px, 40px);
  }
}

.title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #e2e8f0;
  margin-bottom: 0.25rem;
}
.subtitle {
  color: #94a3b8;
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
}

/* Search bar */
.search-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
}
.input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.6rem 1rem;
  color: #e2e8f0;
  font-size: 0.95rem;
  backdrop-filter: blur(8px);
}
.input:focus {
  outline: none;
  border-color: #0066ff;
  box-shadow: 0 0 0 2px rgba(0, 102, 255, 0.2);
}
.mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85rem;
}
.btn {
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary {
  background: linear-gradient(135deg, #0066ff, #0088ff);
  color: white;
}
.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0, 102, 255, 0.4);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Loading */
.loading-spinner {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #94a3b8;
  padding: 2rem;
  justify-content: center;
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
  padding: 1rem;
  color: #fca5a5;
  margin-bottom: 1.5rem;
}

/* Sections */
.section {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
.section-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #e2e8f0;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.section-desc {
  color: #94a3b8;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

/* Stats cards */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}
.stat-card {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 1.2rem;
  text-align: center;
}
.stat-card.card-ok {
  border-color: rgba(34, 197, 94, 0.3);
  box-shadow: 0 0 15px rgba(34, 197, 94, 0.1);
}
.stat-card.card-warn {
  border-color: rgba(234, 179, 8, 0.3);
  box-shadow: 0 0 15px rgba(234, 179, 8, 0.1);
}
.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: #e2e8f0;
  line-height: 1;
  margin-bottom: 0.5rem;
}
.stat-label {
  color: #94a3b8;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Tables */
.table-wrap {
  overflow-x: auto;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.data-table th {
  background: rgba(0, 102, 255, 0.1);
  color: #94a3b8;
  padding: 0.6rem 0.75rem;
  text-align: left;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.data-table td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #cbd5e1;
}
.data-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

/* Rows */
.row-ok {
  border-left: 3px solid #22c55e;
}
.row-erro {
  border-left: 3px solid #ef4444;
}

/* Badges */
.badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge-ok {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
}
.badge-erro {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.3);
}
.badge-pending {
  background: rgba(234, 179, 8, 0.15);
  color: #fde047;
  border: 1px solid rgba(234, 179, 8, 0.3);
}

.small {
  font-size: 0.75rem;
}
.text-muted {
  color: #475569;
}

/* Resposta cell */
.resposta-cell {
  max-width: 300px;
}
.resposta-text {
  display: block;
  word-break: break-word;
  line-height: 1.3;
}
.resposta-erro {
  color: #fca5a5;
  font-weight: 500;
}

/* Ocorrências */
.ocorrencias-section {
  margin-top: 1.5rem;
}
.sub-title {
  font-size: 1rem;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 0.75rem;
}
.ocorrencia-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  margin-bottom: 0.75rem;
  overflow: hidden;
}
.oc-header {
  background: rgba(255, 255, 255, 0.04);
  padding: 0.5rem 0.75rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #94a3b8;
}
.oc-body {
  padding: 0.75rem;
  font-size: 0.8rem;
  color: #cbd5e1;
  margin: 0;
  overflow-x: auto;
  font-family: 'JetBrains Mono', monospace;
  white-space: pre-wrap;
}

/* Pipeline cards */
.pipeline-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  margin-bottom: 1rem;
  overflow: hidden;
}
.pipeline-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.pipeline-id {
  font-weight: 700;
  color: #e2e8f0;
}
.pipeline-steps {
  padding: 0.75rem 1rem;
}
.step-row {
  display: flex;
  justify-content: space-between;
  padding: 0.35rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
.step-label {
  color: #94a3b8;
  font-size: 0.85rem;
}
.step-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  padding: 0.5rem;
  margin-top: 0.5rem;
  color: #fca5a5;
  font-size: 0.85rem;
}

/* Steps log */
.steps-log {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.log-summary {
  padding: 0.5rem 1rem;
  cursor: pointer;
  color: #64748b;
  font-size: 0.85rem;
  user-select: none;
}
.log-summary:hover {
  color: #94a3b8;
}
.log-pre {
  padding: 1rem;
  font-size: 0.75rem;
  color: #94a3b8;
  overflow-x: auto;
  margin: 0;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  background: rgba(0, 0, 0, 0.2);
}

/* Comparison tables */
.comp-block {
  margin-bottom: 1.5rem;
}
.comp-table .col-antes {
  color: #fca5a5;
}
.comp-table .col-depois {
  color: #4ade80;
}
.rubrica-cell {
  vertical-align: top;
  border-right: 2px solid rgba(255, 255, 255, 0.08);
}
.campo-name {
  color: #94a3b8;
  font-weight: 500;
}
.val-antes {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.05);
}
.val-depois {
  color: #4ade80;
  background: rgba(34, 197, 94, 0.05);
}
.arrow-cell {
  text-align: center;
  color: #475569;
  font-weight: bold;
}

/* S-5002 side by side */
.s5002-side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.s5002-header {
  padding: 0.5rem 0.75rem;
  font-weight: 700;
  border-radius: 6px 6px 0 0;
  text-align: center;
  font-size: 0.85rem;
}
.s5002-header.antes {
  background: rgba(239, 68, 68, 0.1);
  color: #fca5a5;
}
.s5002-header.depois {
  background: rgba(34, 197, 94, 0.1);
  color: #4ade80;
}

/* Recibos compare */
.recibos-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.recibo-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
}
.recibo-evento {
  font-weight: 700;
  color: #e2e8f0;
  font-size: 0.85rem;
  margin-bottom: 0.25rem;
}
.recibo-nr {
  color: #94a3b8;
  font-size: 0.8rem;
}
.empty-note {
  color: #64748b;
  font-style: italic;
  padding: 1rem;
  text-align: center;
  font-size: 0.85rem;
}

/* Bloqueio section */
.bloqueio-section {
  border-color: rgba(234, 179, 8, 0.2);
}
.bloqueio-card {
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
}
.bloqueio-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
}
.bloqueio-content h3 {
  color: #fde047;
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
}
.bloqueio-content p {
  color: #cbd5e1;
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 0.75rem;
}
.bloqueio-msg {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-left: 4px solid #ef4444;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin: 0.75rem 0;
}
.bloqueio-msg code {
  color: #fca5a5;
  font-size: 0.9rem;
  font-family: 'JetBrains Mono', monospace;
}
.bloqueio-detail {
  font-size: 0.85rem !important;
  color: #94a3b8 !important;
}

/* Snapshots raw */
.snapshots-raw details {
  margin-bottom: 0.75rem;
}

@media (max-width: 768px) {
  .prova-view {
    padding: 1rem;
  }
  .s5002-side,
  .recibos-compare {
    grid-template-columns: 1fr;
  }
  .cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .search-bar {
    flex-direction: column;
  }
  .envios-table {
    font-size: 0.75rem;
  }
}
</style>
