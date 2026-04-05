<template>
  <div class="audit-view">
    <!-- Glass shapes -->
    <div class="glass-shapes">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
    </div>

    <h1 class="title">Pipeline Audit — Comprovação</h1>
    <p class="subtitle">Snapshots pré/pós pipeline para verificação de alterações no eSocial</p>

    <!-- ═══════ PAINEL DE EXECUÇÃO ═══════ -->
    <div class="exec-panel">
      <div class="exec-header" @click="execOpen = !execOpen">
        <h2 class="exec-title">Execução Pipeline Recovery</h2>
        <span class="exec-toggle">{{ execOpen ? '▼' : '►' }}</span>
      </div>
      <div v-if="execOpen" class="exec-body">
        <!-- Linha de ações rápidas -->
        <div class="exec-actions">
          <button
            class="btn btn-execute-all"
            @click="executarTudo"
            :disabled="execLoading || !formReady"
          >
            <svg
              class="btn-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Executar Tudo (PRÉ → Recovery → PÓS)
          </button>
        </div>
        <div class="exec-actions exec-actions-secondary">
          <button
            class="btn btn-snapshot"
            @click="capturarSnapshot('pre_pipeline')"
            :disabled="execLoading"
          >
            <svg
              class="btn-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"
              />
              <circle cx="12" cy="13" r="4" />
            </svg>
            Capturar PRÉ
          </button>
          <button
            class="btn btn-execute"
            @click="executarRecovery"
            :disabled="execLoading || !formReady"
          >
            <svg
              class="btn-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Só Recovery
          </button>
          <button
            class="btn btn-snapshot"
            @click="capturarSnapshot('pos_pipeline')"
            :disabled="execLoading"
          >
            <svg
              class="btn-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"
              />
              <circle cx="12" cy="13" r="4" />
            </svg>
            Capturar PÓS
          </button>
          <button class="btn btn-compare" @click="loadComparacao" :disabled="execLoading">
            <svg
              class="btn-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Comparar
          </button>
        </div>

        <!-- Fase atual do executar-tudo -->
        <div v-if="faseAtual" class="fase-tracker">
          <div class="fase-item" :class="{ active: faseAtual === 'pre', done: fasesDone.pre }">
            <span class="fase-num">1</span> Snapshot PRÉ
          </div>
          <div class="fase-arrow">→</div>
          <div
            class="fase-item"
            :class="{ active: faseAtual === 'recovery', done: fasesDone.recovery }"
          >
            <span class="fase-num">2</span> Recovery (8 steps)
          </div>
          <div class="fase-arrow">→</div>
          <div class="fase-item" :class="{ active: faseAtual === 'pos', done: fasesDone.pos }">
            <span class="fase-num">3</span> Snapshot PÓS
          </div>
          <div class="fase-arrow">→</div>
          <div
            class="fase-item"
            :class="{ active: faseAtual === 'comparacao', done: fasesDone.comparacao }"
          >
            <span class="fase-num">4</span> Comparação
          </div>
        </div>

        <!-- Log de Execução em tempo real -->
        <div v-if="eventLog.length > 0" class="event-log" ref="eventLogRef">
          <div class="log-header">
            <h3 class="log-title">Log de Execução</h3>
            <span class="log-count">{{ eventLog.length }} eventos</span>
          </div>
          <div class="log-entries">
            <div v-for="(ev, i) in eventLog" :key="i" class="log-entry" :class="ev.level">
              <span class="log-time">{{ ev.time }}</span>
              <span class="log-icon">{{ ev.icon }}</span>
              <span class="log-msg">{{ ev.msg }}</span>
            </div>
          </div>
        </div>

        <!-- Status do snapshot -->
        <div v-if="snapMsg" class="snap-msg" :class="snapMsgType">{{ snapMsg }}</div>

        <!-- Form de dados -->
        <div class="exec-form">
          <div class="form-row">
            <label>CPF</label>
            <input v-model="execForm.cpf" class="input mono" placeholder="08132588983" />
          </div>
          <div class="form-row">
            <label>Ambiente</label>
            <select v-model="execForm.ambiente" class="input">
              <option value="1">PRODUÇÃO</option>
              <option value="2">Homologação</option>
            </select>
          </div>
          <div class="form-row">
            <label>Per. Alvo (bloqueado)</label>
            <input v-model="execForm.per_apur_alvo" class="input mono" placeholder="2024-12" />
          </div>
          <div class="form-row">
            <label>Per. Bloqueador</label>
            <input
              v-model="execForm.per_apur_bloqueador"
              class="input mono"
              placeholder="2025-01"
            />
          </div>
          <div class="form-row">
            <label>nrRecibo S-1200 alvo</label>
            <input v-model="execForm.s1200_nr_recibo" class="input mono" placeholder="1.1.000..." />
          </div>
          <div class="form-row">
            <label>nrRecibo S-1210 alvo</label>
            <input
              v-model="execForm.s1210_alvo_nr_recibo"
              class="input mono"
              placeholder="1.1.000..."
            />
          </div>
          <div class="form-row">
            <label>nrRecibo S-1210 bloq.</label>
            <input
              v-model="execForm.s1210_bloq_nr_recibo"
              class="input mono"
              placeholder="1.1.000..."
            />
          </div>
          <!-- Payloads JSON -->
          <div class="form-row full">
            <label>Payload S-1200 dm_devs (JSON)</label>
            <textarea
              v-model="execForm.s1200_dm_devs_json"
              class="input textarea mono"
              rows="4"
              placeholder='[{"ideDmDev":"10711955",...}]'
            ></textarea>
          </div>
          <div class="form-row full">
            <label>Payload S-1210 alvo info_pgtos (JSON)</label>
            <textarea
              v-model="execForm.s1210_alvo_info_pgtos_json"
              class="input textarea mono"
              rows="3"
              placeholder='[{"dtPgto":"2024-12-06",...}]'
            ></textarea>
          </div>
          <div class="form-row full">
            <label>Payload S-1210 bloqueador info_pgtos (JSON)</label>
            <textarea
              v-model="execForm.s1210_bloq_info_pgtos_json"
              class="input textarea mono"
              rows="3"
              placeholder='[{"dtPgto":"2025-01-07",...}]'
            ></textarea>
          </div>
          <div class="form-row full">
            <label>info_ir_complem S-1210 alvo (JSON, opcional)</label>
            <textarea
              v-model="execForm.s1210_alvo_info_ir_complem_json"
              class="input textarea mono"
              rows="3"
              placeholder='{"infoIRCR":[...]}'
            ></textarea>
          </div>
        </div>

        <!-- Progress tracker -->
        <div v-if="recoverySteps.length > 0" class="recovery-progress">
          <h3 class="progress-title">Progresso da Recuperação</h3>
          <div v-for="s in recoverySteps" :key="s.step" class="progress-step" :class="s.status">
            <div class="step-num">{{ s.step }}</div>
            <div class="step-info">
              <div class="step-name">{{ s.evento }} — {{ s.per_apur }}</div>
              <div class="step-detail mono" v-if="s.nr_recibo">✓ {{ s.nr_recibo }}</div>
              <div class="step-detail step-error" v-if="s.status === 'erro'">
                {{ s.descricao }}
              </div>
            </div>
            <div class="step-badge" :class="s.status">{{ s.status }}</div>
          </div>
        </div>

        <!-- Resultado final -->
        <div v-if="recoveryResult" class="recovery-result" :class="recoveryResult.status">
          <strong>{{
            recoveryResult.status === 'completo' ? '✓ PIPELINE COMPLETO' : '✗ PIPELINE COM ERRO'
          }}</strong>
          <span>{{ recoveryResult.steps_ok }}/{{ recoveryResult.total_steps }} steps OK</span>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">Carregando snapshots...</div>

    <!-- Lista de Snapshots -->
    <div v-if="!loading && snapshots.length > 0" class="snapshots-list">
      <div
        v-for="snap in snapshots"
        :key="snap.id"
        class="snapshot-card"
        :class="{ active: selectedId === snap.id }"
        @click="selectSnapshot(snap.id)"
      >
        <div class="snap-header">
          <span class="snap-tipo" :class="snap.tipo">{{
            snap.tipo === 'pre_pipeline' ? 'PRÉ' : 'PÓS'
          }}</span>
          <span class="snap-id">#{{ snap.id }}</span>
        </div>
        <div class="snap-info">
          <span>CPF: {{ formatCpf(snap.cpf) }}</span>
          <span>Período: {{ snap.per_apur }}</span>
        </div>
        <div class="snap-date">{{ formatDate(snap.created_at) }}</div>
        <div v-if="snap.descricao" class="snap-desc">{{ snap.descricao }}</div>
      </div>
    </div>

    <!-- Sem dados -->
    <div v-if="!loading && snapshots.length === 0" class="empty">
      Nenhum snapshot registrado ainda.
    </div>

    <!-- Detalhe do snapshot selecionado -->
    <div v-if="detail" class="detail-panel">
      <h2 class="detail-title">
        Snapshot #{{ detail.id }} —
        <span :class="detail.tipo">{{
          detail.tipo === 'pre_pipeline' ? 'PRÉ-Pipeline' : 'PÓS-Pipeline'
        }}</span>
      </h2>
      <div class="detail-meta">
        <span>CPF: {{ formatCpf(detail.cpf) }}</span>
        <span>Período: {{ detail.per_apur }}</span>
        <span>Capturado em: {{ formatDate(detail.created_at) }}</span>
      </div>

      <!-- Rubricas -->
      <section class="detail-section">
        <h3>Rubricas (cruzamento_eb)</h3>
        <table class="data-table" v-if="detail.dados?.cruzamento_eb?.length">
          <thead>
            <tr>
              <th>Código</th>
              <th>Descrição</th>
              <th>INSS</th>
              <th>IRRF</th>
              <th>FGTS</th>
              <th>Corrigido</th>
              <th>Status Envio</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in detail.dados.cruzamento_eb" :key="r.cod_rubrica">
              <td class="mono">{{ r.cod_rubrica }}</td>
              <td>{{ r.descricao }}</td>
              <td class="mono">{{ r.incid_inss }}</td>
              <td class="mono" :class="{ 'val-wrong': isWrong(r) }">{{ r.incid_irrf }}</td>
              <td class="mono">{{ r.incid_fgts }}</td>
              <td>
                <span :class="r.corrigido ? 'badge-ok' : 'badge-pending'">
                  {{ r.corrigido ? 'Sim' : 'Não' }}
                </span>
              </td>
              <td>
                <span class="badge-status" :class="r.envio_status">{{ r.envio_status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- S-5002 Totalizadores -->
      <section class="detail-section">
        <h3>S-5002 Totalizadores (IRRF)</h3>
        <table class="data-table" v-if="detail.dados?.s5002_vigente?.totalizadores?.length">
          <thead>
            <tr>
              <th>tpInfoIR</th>
              <th>Descrição</th>
              <th>Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(t, i) in detail.dados.s5002_vigente.totalizadores" :key="i">
              <td class="mono">{{ t.tpInfoIR }}</td>
              <td>{{ t.descricao }}</td>
              <td class="mono">R$ {{ t.valor }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Recibos -->
      <section class="detail-section">
        <h3>Recibos Vigentes</h3>
        <div class="recibos-grid" v-if="detail.dados?.recibos_vigentes">
          <div
            v-for="(rec, evento) in detail.dados.recibos_vigentes"
            :key="evento"
            class="recibo-card"
          >
            <div class="recibo-evento">{{ evento }}</div>
            <div class="recibo-nr mono">{{ rec.nrRecibo }}</div>
            <div class="recibo-tipo">{{ rec.tipo }}</div>
            <div class="recibo-nota" v-if="rec.nota">{{ rec.nota }}</div>
          </div>
        </div>
      </section>

      <!-- S-1010 Correções -->
      <section class="detail-section" v-if="detail.dados?.s1010_correcoes">
        <h3>S-1010 Correções Enviadas</h3>
        <div class="recibos-grid">
          <div v-for="(cor, key) in detail.dados.s1010_correcoes" :key="key" class="recibo-card">
            <div class="recibo-evento">{{ key }}</div>
            <div class="recibo-nr mono">{{ cor.nrRecibo }}</div>
            <div class="recibo-tipo">{{ cor.alteracao }}</div>
            <div class="recibo-nota">Data: {{ cor.data }}</div>
          </div>
        </div>
      </section>

      <!-- Envios Histórico -->
      <section class="detail-section">
        <h3>Histórico de Envios (últimos 10)</h3>
        <table class="data-table" v-if="detail.dados?.esocial_envios?.length">
          <thead>
            <tr>
              <th>ID</th>
              <th>Evento</th>
              <th>Status</th>
              <th>Rubricas</th>
              <th>Ambiente</th>
              <th>Data</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in detail.dados.esocial_envios" :key="e.id">
              <td class="mono">{{ e.id }}</td>
              <td>{{ e.tipo_evento }}</td>
              <td>
                <span class="badge-status" :class="e.status">{{ e.status }}</span>
              </td>
              <td class="mono">
                {{ Array.isArray(e.rubrica_ids) ? e.rubrica_ids.join(', ') : e.rubrica_ids }}
              </td>
              <td>{{ e.ambiente === '1' ? 'PROD' : 'HOM' }}</td>
              <td class="mono">{{ formatDate(e.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <!-- Comparação PRÉ vs PÓS -->
    <div v-if="comparacao" class="comparacao-panel">
      <div class="comp-header">
        <h2 class="detail-title">Comparação PRÉ vs PÓS Pipeline</h2>
        <div class="comp-legend">
          <span class="legend-item"><span class="dot dot-red"></span> Antes (errado)</span>
          <span class="legend-item"><span class="dot dot-green"></span> Depois (corrigido)</span>
        </div>
      </div>

      <!-- Resumo rápido -->
      <div class="comp-summary" v-if="comparacao.rubricas?.length">
        <div class="summary-icon">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <div>
          <strong>{{ comparacao.rubricas.length }} rubrica(s) alterada(s)</strong>
          <span class="summary-detail" v-for="r in comparacao.rubricas" :key="r.cod_rubrica">
            {{ r.cod_rubrica }} ({{ r.descricao }})
          </span>
        </div>
      </div>

      <!-- Tabela de mudanças nas Rubricas -->
      <section class="detail-section" v-if="comparacao.rubricas?.length">
        <h3>Mudanças nas Rubricas</h3>
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
            <template v-for="r in comparacao.rubricas" :key="r.cod_rubrica">
              <tr v-for="(change, campo, idx) in r.mudancas" :key="r.cod_rubrica + '-' + campo">
                <td v-if="idx === 0" :rowspan="Object.keys(r.mudancas).length" class="rubrica-cell">
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
      </section>

      <!-- S-5002 Lado a Lado -->
      <section class="detail-section" v-if="comparacao.s5002">
        <h3>S-5002 Totalizadores IRRF — Antes vs Depois</h3>
        <div class="s5002-side-by-side">
          <div class="s5002-col s5002-antes">
            <div class="s5002-col-header"><span class="dot dot-red"></span> PRÉ-Pipeline</div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>tpInfoIR</th>
                  <th>Descrição</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(t, i) in comparacao.s5002.antes"
                  :key="'a' + i"
                  :class="{ 'row-changed': s5002Changed(t, comparacao.s5002.depois) }"
                >
                  <td class="mono">{{ t.tpInfoIR }}</td>
                  <td>{{ t.descricao }}</td>
                  <td class="mono">R$ {{ t.valor }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="s5002-col s5002-depois">
            <div class="s5002-col-header"><span class="dot dot-green"></span> PÓS-Pipeline</div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>tpInfoIR</th>
                  <th>Descrição</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(t, i) in comparacao.s5002.depois"
                  :key="'d' + i"
                  :class="{ 'row-changed': s5002Changed(t, comparacao.s5002.antes) }"
                >
                  <td class="mono">{{ t.tpInfoIR }}</td>
                  <td>{{ t.descricao }}</td>
                  <td class="mono">R$ {{ t.valor }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Recibos Antes vs Depois -->
      <section class="detail-section" v-if="comparacao.recibos">
        <h3>Recibos — Antes vs Depois</h3>
        <div class="recibos-compare">
          <div class="recibo-col">
            <div class="s5002-col-header"><span class="dot dot-red"></span> PRÉ</div>
            <div
              v-for="(rec, ev) in comparacao.recibos.antes"
              :key="'ra-' + ev"
              class="recibo-card"
            >
              <div class="recibo-evento">{{ ev }}</div>
              <div class="recibo-nr mono">{{ rec.nrRecibo }}</div>
            </div>
          </div>
          <div class="recibo-col">
            <div class="s5002-col-header"><span class="dot dot-green"></span> PÓS</div>
            <div
              v-for="(rec, ev) in comparacao.recibos.depois"
              :key="'rd-' + ev"
              class="recibo-card"
            >
              <div class="recibo-evento">{{ ev }}</div>
              <div class="recibo-nr mono">{{ typeof rec === 'string' ? rec : rec.nrRecibo }}</div>
            </div>
            <div
              v-if="
                !comparacao.recibos.depois || Object.keys(comparacao.recibos.depois).length === 0
              "
              class="empty-small"
            >
              Aguardando execução do pipeline...
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { PYTHON_API } from '../lib/api'

interface Snapshot {
  id: number
  cpf: string
  per_apur: string
  tipo: string
  descricao?: string
  created_at: string
  dados?: any
}

interface RecoveryStep {
  step: number
  evento: string
  per_apur: string
  status: string
  protocolo?: string
  nr_recibo?: string
  codigo_resposta?: string
  descricao?: string
}

const loading = ref(true)
const snapshots = ref<Snapshot[]>([])
const selectedId = ref<number | null>(null)
const detail = ref<Snapshot | null>(null)
const comparacao = ref<any>(null)

// ── Exec panel ─────────────────────────────────────────────────
const execOpen = ref(true)
const execLoading = ref(false)
const snapMsg = ref('')
const snapMsgType = ref<'success' | 'error'>('success')
const recoverySteps = ref<RecoveryStep[]>([])
const recoveryResult = ref<any>(null)

const faseAtual = ref<string | null>(null)
const fasesDone = ref<Record<string, boolean>>({
  pre: false,
  recovery: false,
  pos: false,
  comparacao: false,
})
const eventLog = ref<{ time: string; icon: string; msg: string; level: string }[]>([])
const eventLogRef = ref<HTMLElement | null>(null)

const execForm = ref({
  cpf: '08132588983',
  ambiente: '1',
  per_apur_alvo: '2024-12',
  per_apur_bloqueador: '2025-01',
  s1200_nr_recibo: '1.1.0000000030324738244',
  s1210_alvo_nr_recibo: '1.1.0000000039598280881',
  s1210_bloq_nr_recibo: '1.1.0000000039598924749',
  s1200_dm_devs_json: JSON.stringify(
    [
      {
        ideDmDev: '20241129.1.01512563',
        codCateg: '101',
        infoPerApur: {
          ideEstabLot: [
            {
              tpInsc: '1',
              nrInsc: '05969071000110',
              codLotacao: 'E00278-001-05A',
              remunPerApur: [
                {
                  matricula: '001-001-056502',
                  itensRemun: [
                    { codRubr: '9276', ideTabRubr: '1', vrRubr: '231.00', indApurIR: '0' },
                  ],
                  infoAgNocivo: { grauExp: '1' },
                },
              ],
            },
          ],
        },
      },
      {
        ideDmDev: '20241129.1.01512566',
        codCateg: '101',
        infoPerApur: {
          ideEstabLot: [
            {
              tpInsc: '1',
              nrInsc: '05969071000110',
              codLotacao: 'E00278-001-05A',
              remunPerApur: [
                {
                  matricula: '001-001-056502',
                  itensRemun: [
                    { codRubr: '9284', ideTabRubr: '1', vrRubr: '667.80', indApurIR: '0' },
                  ],
                  infoAgNocivo: { grauExp: '1' },
                },
              ],
            },
          ],
        },
      },
      {
        ideDmDev: '10711955',
        codCateg: '101',
        infoPerApur: {
          ideEstabLot: [
            {
              tpInsc: '1',
              nrInsc: '05969071000110',
              codLotacao: 'E00278-001-05A',
              remunPerApur: [
                {
                  matricula: '001-001-056502',
                  itensRemun: [
                    {
                      codRubr: '2',
                      ideTabRubr: '1',
                      qtdRubr: '30.00',
                      vrRubr: '2501.20',
                      indApurIR: '0',
                    },
                    { codRubr: '10', ideTabRubr: 'EA001', vrRubr: '125.06', indApurIR: '0' },
                    {
                      codRubr: '105',
                      ideTabRubr: 'EA001',
                      qtdRubr: '34.34',
                      vrRubr: '585.62',
                      indApurIR: '0',
                    },
                    { codRubr: '160', ideTabRubr: 'EA001', vrRubr: '140.55', indApurIR: '0' },
                    { codRubr: '273', ideTabRubr: '1', vrRubr: '0.70', indApurIR: '0' },
                    { codRubr: '541', ideTabRubr: '1', vrRubr: '1.20', indApurIR: '0' },
                    {
                      codRubr: '566',
                      ideTabRubr: '1',
                      qtdRubr: '12.00',
                      vrRubr: '301.11',
                      indApurIR: '0',
                    },
                    {
                      codRubr: '570',
                      ideTabRubr: '1',
                      qtdRubr: '7.50',
                      vrRubr: '39.63',
                      indApurIR: '0',
                    },
                    { codRubr: '672', ideTabRubr: '1', vrRubr: '150.07', indApurIR: '0' },
                    { codRubr: '776', ideTabRubr: '1', vrRubr: '108.12', indApurIR: '0' },
                  ],
                  infoAgNocivo: { grauExp: '1' },
                },
              ],
            },
          ],
        },
      },
      {
        ideDmDev: '10711965',
        codCateg: '101',
        infoPerApur: {
          ideEstabLot: [
            {
              tpInsc: '1',
              nrInsc: '05969071000110',
              codLotacao: 'E00278-001-05A',
              remunPerApur: [
                {
                  matricula: '001-001-056502',
                  itensRemun: [
                    { codRubr: '273', ideTabRubr: '1', vrRubr: '0.44', indApurIR: '0' },
                    { codRubr: '480', ideTabRubr: 'EA001', vrRubr: '70.94', indApurIR: '0' },
                    {
                      codRubr: '596',
                      ideTabRubr: '1',
                      qtdRubr: '9.00',
                      vrRubr: '6.38',
                      indApurIR: '0',
                    },
                  ],
                  infoAgNocivo: { grauExp: '1' },
                },
              ],
            },
          ],
        },
      },
    ],
    null,
    2,
  ),
  s1210_alvo_info_pgtos_json: JSON.stringify(
    [
      { dtPgto: '2024-12-06', tpPgto: '1', perRef: '2024-11', ideDmDev: '10711884', vrLiq: '2883' },
      { dtPgto: '2024-12-20', tpPgto: '1', perRef: '2024', ideDmDev: '10711933', vrLiq: '1273' },
    ],
    null,
    2,
  ),
  s1210_bloq_info_pgtos_json: JSON.stringify(
    [
      { dtPgto: '2025-01-07', tpPgto: '1', perRef: '2024-12', ideDmDev: '10711965', vrLiq: '65' },
      { dtPgto: '2025-01-07', tpPgto: '1', perRef: '2024-12', ideDmDev: '10711955', vrLiq: '2753' },
    ],
    null,
    2,
  ),
  s1210_alvo_info_ir_complem_json: JSON.stringify(
    {
      infoIRCR: [
        {
          tpCR: '056107',
          dedDepen: [
            { tpRend: '12', cpfDep: '14020816930', vlrDedDep: '189.59' },
            { tpRend: '11', cpfDep: '14020816930', vlrDedDep: '189.59' },
          ],
        },
      ],
    },
    null,
    2,
  ),
})

const formReady = computed(() => {
  return (
    execForm.value.cpf.length === 11 &&
    execForm.value.s1200_nr_recibo &&
    execForm.value.s1210_alvo_nr_recibo &&
    execForm.value.s1210_bloq_nr_recibo &&
    execForm.value.s1210_bloq_info_pgtos_json.trim().length > 2
  )
})

async function capturarSnapshot(tipo: 'pre_pipeline' | 'pos_pipeline') {
  execLoading.value = true
  snapMsg.value = ''
  try {
    const res = await fetch(`${PYTHON_API}/api/pipeline-audit/capturar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cpf: execForm.value.cpf,
        per_apur: execForm.value.per_apur_alvo,
        tipo,
        descricao:
          tipo === 'pre_pipeline'
            ? 'Snapshot PRÉ recuperação S-1200 (capturado pelo frontend)'
            : 'Snapshot PÓS recuperação S-1200 (capturado pelo frontend)',
        rubrica_ids: ['566', '596'],
      }),
    })
    const data = await res.json()
    if (data.sucesso) {
      snapMsg.value = `✓ Snapshot ${tipo === 'pre_pipeline' ? 'PRÉ' : 'PÓS'} capturado (ID #${data.snapshot_id})`
      snapMsgType.value = 'success'
      await loadSnapshots()
    } else {
      snapMsg.value = `✗ Erro: ${data.detail || JSON.stringify(data)}`
      snapMsgType.value = 'error'
    }
  } catch (e: any) {
    snapMsg.value = `✗ Erro: ${e.message}`
    snapMsgType.value = 'error'
  } finally {
    execLoading.value = false
  }
}

async function executarRecovery() {
  if (
    !confirm(
      '⚠ ATENÇÃO: Isso vai executar operações em PRODUÇÃO no eSocial.\n\n' +
        'Passos:\n' +
        '1. S-1298 reabrir Jan/2025\n' +
        '2. S-1298 reabrir Dez/2024\n' +
        '3. S-3000 excluir S-1210 Jan/2025 (remove dmDevs)\n' +
        '4. S-1200 retif Dez/2024 (desbloqueado!)\n' +
        '5. S-1210 retif Dez/2024 (recalcular S-5002)\n' +
        '6. S-1210 incluir Jan/2025 (re-incluir evento)\n' +
        '7. S-1299 fechar Dez/2024\n' +
        '8. S-1299 fechar Jan/2025\n\n' +
        'Confirma?',
    )
  )
    return

  execLoading.value = true
  recoverySteps.value = []
  recoveryResult.value = null

  try {
    const body = buildRecoveryBody()
    const res = await fetch(`${PYTHON_API}/api/pipeline/recuperar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    const data = await res.json()
    recoverySteps.value = data.steps || []
    recoveryResult.value = {
      status: data.status,
      total_steps: data.total_steps,
      steps_ok: data.steps_ok,
    }
  } catch (e: any) {
    snapMsg.value = `✗ Erro na recuperação: ${e.message}`
    snapMsgType.value = 'error'
  } finally {
    execLoading.value = false
  }
}

function buildRecoveryBody() {
  const body: any = {
    cpf: execForm.value.cpf,
    ambiente: execForm.value.ambiente,
    per_apur_alvo: execForm.value.per_apur_alvo,
    per_apur_bloqueador: execForm.value.per_apur_bloqueador,
    s1200_nr_recibo: execForm.value.s1200_nr_recibo,
    s1200_dm_devs: JSON.parse(execForm.value.s1200_dm_devs_json),
    s1210_alvo_nr_recibo: execForm.value.s1210_alvo_nr_recibo,
    s1210_alvo_info_pgtos: JSON.parse(execForm.value.s1210_alvo_info_pgtos_json),
    s1210_bloq_nr_recibo: execForm.value.s1210_bloq_nr_recibo,
    s1210_bloq_info_pgtos: JSON.parse(execForm.value.s1210_bloq_info_pgtos_json),
  }

  const irComplem = execForm.value.s1210_alvo_info_ir_complem_json.trim()
  if (irComplem) {
    body.s1210_alvo_info_ir_complem = JSON.parse(irComplem)
  }
  return body
}

function addLogEntry(icon: string, msg: string, level = 'info') {
  const now = new Date()
  const time = now.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  eventLog.value.push({ time, icon, msg, level })
  nextTick(() => {
    if (eventLogRef.value) {
      const entries = eventLogRef.value.querySelector('.log-entries')
      if (entries) entries.scrollTop = entries.scrollHeight
    }
  })
}

function handleStreamEvent(event: any) {
  switch (event.tipo) {
    case 'inicio':
      addLogEntry('●', event.msg)
      break
    case 'fase':
      faseAtual.value = event.fase
      addLogEntry('●', event.msg, 'fase')
      break
    case 'fase_ok':
      fasesDone.value[event.fase] = true
      addLogEntry('✓', event.msg, 'success')
      if (event.comparacao) {
        comparacao.value = event.comparacao
      }
      break
    case 'fase_erro':
      addLogEntry('✗', event.msg, 'error')
      break
    case 'step_inicio':
      addLogEntry('▸', `Step ${event.step}: ${event.evento} — ${event.per_apur}`, 'step')
      break
    case 'step_enviando':
      addLogEntry(
        '↗',
        `Step ${event.step}: Enviando lote (tentativa ${event.tentativa})...`,
        'detail',
      )
      break
    case 'step_retry':
      addLogEntry(
        '⟳',
        `Step ${event.step}: Retry ${event.tentativa}/${event.max} — ${event.erro}`,
        'warn',
      )
      break
    case 'step_protocolo':
      addLogEntry('◎', `Step ${event.step}: Protocolo ${event.protocolo}`, 'detail')
      break
    case 'step_polling':
      addLogEntry(
        '⟳',
        `Step ${event.step}: Consultando resultado (${event.tentativa}/${event.max})...`,
        'detail',
      )
      break
    case 'step_poll_erro':
      addLogEntry(
        '⚠',
        `Step ${event.step}: Erro ao consultar (${event.tentativa}) — ${event.erro}`,
        'warn',
      )
      break
    case 'step_override': {
      addLogEntry('↪', event.msg, 'warn')
      const lastStep = recoverySteps.value[recoverySteps.value.length - 1]
      if (lastStep) lastStep.status = 'ok'
      break
    }
    case 'step_fim': {
      const stepData: RecoveryStep = {
        step: event.step,
        evento: event.evento || '',
        per_apur: event.per_apur || '',
        status: event.status === 'ok' ? 'ok' : 'erro',
        nr_recibo: event.resultado?.nr_recibo,
        protocolo: event.resultado?.protocolo,
        codigo_resposta: event.resultado?.codigo_resposta,
        descricao: event.resultado?.descricao,
      }
      recoverySteps.value.push(stepData)
      if (event.status === 'ok') {
        addLogEntry(
          '✓',
          `Step ${event.step}: ${event.evento} — OK${
            event.resultado?.nr_recibo ? ' — ' + event.resultado.nr_recibo : ''
          }`,
          'success',
        )
      } else {
        addLogEntry(
          '✗',
          `Step ${event.step}: ${event.evento} — ERRO: ${event.resultado?.descricao || ''}`,
          'error',
        )
      }
      break
    }
    case 'recovery_erro':
      addLogEntry('✗', event.msg, 'error')
      break
    case 'completo':
      if (event.recovery_ok) {
        snapMsg.value = `✓ ${event.msg}`
        snapMsgType.value = 'success'
        recoveryResult.value = { status: 'completo', steps_ok: event.steps_ok, total_steps: 7 }
      } else {
        snapMsg.value = `✗ ${event.msg}`
        snapMsgType.value = 'error'
        recoveryResult.value = { status: 'erro', steps_ok: event.steps_ok, total_steps: 7 }
      }
      addLogEntry('●', event.msg, event.recovery_ok ? 'success' : 'error')
      break
    case 'erro':
      snapMsg.value = `✗ ${event.msg}`
      snapMsgType.value = 'error'
      addLogEntry('✗', event.msg, 'error')
      break
  }
}

async function executarTudo() {
  if (
    !confirm(
      '⚠ EXECUÇÃO COMPLETA — PRODUÇÃO\n\n' +
        'Vai executar em sequência:\n' +
        '1. Capturar snapshot PRÉ-pipeline\n' +
        '2. Recovery (8 steps com retry)\n' +
        '3. Capturar snapshot PÓS-pipeline\n' +
        '4. Gerar comparação automática\n\n' +
        'Acompanhe o progresso em tempo real no log. Confirma?',
    )
  )
    return

  execLoading.value = true
  recoverySteps.value = []
  recoveryResult.value = null
  comparacao.value = null
  snapMsg.value = ''
  eventLog.value = []
  faseAtual.value = null
  fasesDone.value = { pre: false, recovery: false, pos: false, comparacao: false }

  try {
    const body = buildRecoveryBody()
    const res = await fetch(`${PYTHON_API}/api/pipeline/executar-completo-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      const errText = await res.text()
      snapMsg.value = `✗ Erro HTTP ${res.status}: ${errText}`
      snapMsgType.value = 'error'
      addLogEntry('✗', `Erro HTTP ${res.status}`, 'error')
      return
    }

    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop()!

      for (const part of parts) {
        const trimmed = part.trim()
        if (!trimmed.startsWith('data: ')) continue
        try {
          const event = JSON.parse(trimmed.slice(6))
          handleStreamEvent(event)
        } catch (e) {
          console.warn('SSE parse error:', trimmed, e)
        }
      }
    }

    // Process remaining buffer
    if (buffer.trim().startsWith('data: ')) {
      try {
        const event = JSON.parse(buffer.trim().slice(6))
        handleStreamEvent(event)
      } catch {}
    }

    await loadSnapshots()
  } catch (e: any) {
    snapMsg.value = `✗ Erro: ${e.message}`
    snapMsgType.value = 'error'
    addLogEntry('✗', `Erro de conexão: ${e.message}`, 'error')
  } finally {
    execLoading.value = false
  }
}

async function loadComparacao() {
  try {
    const res = await fetch(`${PYTHON_API}/api/pipeline-audit/comparar/${execForm.value.cpf}`)
    const data = await res.json()
    comparacao.value = data.comparacao || null
    if (!comparacao.value) {
      snapMsg.value = '⚠ Sem snapshots PRÉ e PÓS para comparar ainda'
      snapMsgType.value = 'error'
    }
  } catch {
    comparacao.value = null
  }
}

async function loadSnapshots() {
  loading.value = true
  try {
    const res = await fetch(`${PYTHON_API}/api/pipeline-audit/snapshots`)
    const data = await res.json()
    snapshots.value = data.snapshots || []
    if (snapshots.value.length > 0 && snapshots.value[0]) {
      await selectSnapshot(snapshots.value[0].id)
    }
  } catch (e) {
    console.error('Erro ao carregar snapshots:', e)
  } finally {
    loading.value = false
  }
}

async function selectSnapshot(id: number) {
  selectedId.value = id
  try {
    const res = await fetch(`${PYTHON_API}/api/pipeline-audit/snapshots/${id}`)
    const data = await res.json()
    detail.value = data.snapshot || null
  } catch (e) {
    console.error('Erro ao carregar snapshot:', e)
  }

  // Tentar carregar comparação
  const snap = snapshots.value.find((s) => s.id === id)
  if (snap) {
    try {
      const res = await fetch(`${PYTHON_API}/api/pipeline-audit/comparar/${snap.cpf}`)
      const data = await res.json()
      comparacao.value = data.comparacao || null
    } catch {
      comparacao.value = null
    }
  }
}

function formatCpf(cpf: string) {
  if (!cpf || cpf.length !== 11) return cpf
  return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9)}`
}

function formatDate(iso: string) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'medium' })
}

function isWrong(r: any) {
  return (
    (r.cod_rubrica === '566' && r.incid_irrf === '11') ||
    (r.cod_rubrica === '596' && r.incid_irrf === '12')
  )
}

function formatCampo(campo: string) {
  const map: Record<string, string> = {
    incid_irrf: 'Cód. IRRF',
    incid_inss: 'Cód. INSS',
    incid_fgts: 'Cód. FGTS',
    corrigido: 'Corrigido',
    envio_status: 'Status Envio',
  }
  return map[campo] || campo
}

function s5002Changed(item: any, otherList: any[]) {
  if (!otherList) return false
  const match = otherList.find(
    (o: any) => o.tpInfoIR === item.tpInfoIR && o.descricao === item.descricao,
  )
  return !match || String(match.valor) !== String(item.valor)
}

onMounted(loadSnapshots)
</script>

<style scoped>
.audit-view {
  position: relative;
  overflow: hidden;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  color: #e2e8f0;
}

.title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}

.subtitle {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 24px;
}

.loading,
.empty {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
}

/* Snapshot cards */
.snapshots-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.snapshot-card {
  background: rgba(17, 27, 56, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 10px;
  padding: 14px 18px;
  cursor: pointer;
  min-width: 220px;
  transition: all 0.2s;
}

.snapshot-card:hover {
  border-color: rgba(0, 102, 255, 0.4);
}

.snapshot-card.active {
  border-color: #0066ff;
  box-shadow: 0 0 12px rgba(0, 102, 255, 0.2);
}

.snap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.snap-tipo {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}

.snap-tipo.pre_pipeline {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.snap-tipo.pos_pipeline {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}

.snap-id {
  font-size: 0.75rem;
  color: #64748b;
}

.snap-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 0.8rem;
  color: #cbd5e1;
}

.snap-date {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 6px;
}

.snap-desc {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-top: 4px;
  font-style: italic;
}

/* Detail panel */
.detail-panel,
.comparacao-panel {
  background: rgba(17, 27, 56, 0.7);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 0 20px rgba(0, 102, 255, 0.04), 0 8px 32px rgba(0, 0, 0, 0.3);
}

.detail-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 12px;
}

.detail-meta {
  display: flex;
  gap: 20px;
  font-size: 0.8rem;
  color: #94a3b8;
  margin-bottom: 20px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h3 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #60a5fa;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(0, 102, 255, 0.1);
}

/* Tables */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.data-table th {
  text-align: left;
  font-weight: 600;
  color: #94a3b8;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(0, 102, 255, 0.1);
  font-size: 0.75rem;
  text-transform: uppercase;
}

.data-table td {
  padding: 7px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #cbd5e1;
}

.mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
}

.val-wrong {
  color: #f87171 !important;
  font-weight: 700;
}

/* Badges */
.badge-ok {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.badge-pending {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.badge-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.badge-status.processado,
.badge-status.enviado {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}

.badge-status.erro {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

.badge-status.pendente {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

/* Recibos */
.recibos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px;
}

.recibo-card {
  background: rgba(0, 102, 255, 0.05);
  border: 1px solid rgba(0, 102, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
}

.recibo-evento {
  font-weight: 700;
  color: #60a5fa;
  margin-bottom: 4px;
}

.recibo-nr {
  font-size: 0.8rem;
  color: #e2e8f0;
  margin-bottom: 4px;
}

.recibo-tipo {
  font-size: 0.75rem;
  color: #94a3b8;
}

.recibo-nota {
  font-size: 0.7rem;
  color: #64748b;
  margin-top: 4px;
  font-style: italic;
}

/* Diff / Comparação melhorada */
.comp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.comp-legend {
  display: flex;
  gap: 16px;
  font-size: 0.75rem;
  color: #94a3b8;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.dot-red {
  background: #f87171;
}

.dot-green {
  background: #34d399;
}

.comp-summary {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(52, 211, 153, 0.08);
  border: 1px solid rgba(52, 211, 153, 0.2);
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 0.85rem;
  color: #e2e8f0;
}

.summary-icon {
  width: 24px;
  height: 24px;
  min-width: 24px;
  color: #34d399;
}

.summary-icon svg {
  width: 100%;
  height: 100%;
}

.summary-detail {
  display: block;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 2px;
}

/* Tabela de comparação */
.comp-table .col-antes {
  color: #f87171;
}

.comp-table .col-depois {
  color: #34d399;
}

.rubrica-cell {
  vertical-align: top;
  border-right: 2px solid rgba(0, 102, 255, 0.1);
}

.rubrica-cell small {
  font-size: 0.7rem;
  color: #94a3b8;
}

.campo-name {
  font-size: 0.78rem;
  color: #94a3b8;
  font-weight: 500;
}

.val-antes {
  color: #f87171 !important;
  font-weight: 700;
  background: rgba(248, 113, 113, 0.08);
  text-align: center;
}

.val-depois {
  color: #34d399 !important;
  font-weight: 700;
  background: rgba(52, 211, 153, 0.08);
  text-align: center;
}

.arrow-cell {
  text-align: center;
  color: #64748b;
  font-size: 1rem;
  padding: 0 4px;
}

/* S-5002 lado a lado */
.s5002-side-by-side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.s5002-col {
  border-radius: 8px;
  overflow: hidden;
}

.s5002-antes {
  border: 1px solid rgba(248, 113, 113, 0.15);
}

.s5002-depois {
  border: 1px solid rgba(52, 211, 153, 0.15);
}

.s5002-col-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #94a3b8;
}

.s5002-antes .s5002-col-header {
  background: rgba(248, 113, 113, 0.06);
}

.s5002-depois .s5002-col-header {
  background: rgba(52, 211, 153, 0.06);
}

.row-changed td {
  background: rgba(251, 191, 36, 0.1) !important;
  font-weight: 600;
}

/* Recibos compare */
.recibos-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.recibo-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-small {
  font-size: 0.78rem;
  color: #64748b;
  font-style: italic;
  padding: 10px;
}

/* ═══ Execution Panel ═══ */
.exec-panel {
  background: rgba(13, 21, 41, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(251, 191, 36, 0.25);
  border-radius: 12px;
  margin-bottom: 24px;
  overflow: hidden;
}

.exec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
  background: rgba(251, 191, 36, 0.06);
}

.exec-header:hover {
  background: rgba(251, 191, 36, 0.1);
}

.exec-title {
  font-size: 1rem;
  font-weight: 700;
  color: #fbbf24;
  margin: 0;
}

.exec-toggle {
  color: #fbbf24;
  font-size: 0.8rem;
}

.exec-body {
  padding: 20px;
}

.exec-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-snapshot {
  background: rgba(96, 165, 250, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(96, 165, 250, 0.3);
}

.btn-snapshot:hover:not(:disabled) {
  background: rgba(96, 165, 250, 0.25);
}

.btn-execute {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.btn-execute:hover:not(:disabled) {
  background: rgba(251, 191, 36, 0.25);
}

.btn-compare {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.btn-compare:hover:not(:disabled) {
  background: rgba(52, 211, 153, 0.25);
}

.snap-msg {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  margin-bottom: 14px;
}

.snap-msg.success {
  background: rgba(52, 211, 153, 0.1);
  color: #34d399;
  border: 1px solid rgba(52, 211, 153, 0.2);
}

.snap-msg.error {
  background: rgba(248, 113, 113, 0.1);
  color: #f87171;
  border: 1px solid rgba(248, 113, 113, 0.2);
}

/* Form */
.exec-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 16px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-row.full {
  grid-column: 1 / -1;
}

.form-row label {
  font-size: 0.7rem;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
}

.input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 7px 10px;
  color: #e2e8f0;
  font-size: 0.8rem;
}

.input:focus {
  outline: none;
  border-color: rgba(96, 165, 250, 0.5);
}

.textarea {
  resize: vertical;
  min-height: 60px;
  font-size: 0.72rem;
  line-height: 1.4;
}

/* Recovery Progress */
.recovery-progress {
  margin-top: 16px;
}

.progress-title {
  font-size: 0.85rem;
  color: #60a5fa;
  margin-bottom: 10px;
}

.progress-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 6px;
  background: rgba(0, 0, 0, 0.2);
}

.progress-step.ok {
  border-left: 3px solid #34d399;
}

.progress-step.erro {
  border-left: 3px solid #f87171;
}

.progress-step.timeout {
  border-left: 3px solid #fbbf24;
}

.step-num {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(96, 165, 250, 0.15);
  color: #60a5fa;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.step-info {
  flex: 1;
}

.step-name {
  font-size: 0.8rem;
  color: #e2e8f0;
  font-weight: 600;
}

.step-detail {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-top: 2px;
}

.step-error {
  color: #f87171 !important;
}

.step-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.step-badge.ok {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}

.step-badge.erro {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

.step-badge.timeout {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

/* Recovery result */
.recovery-result {
  margin-top: 12px;
  padding: 12px 18px;
  border-radius: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.recovery-result.completo {
  background: rgba(52, 211, 153, 0.1);
  border: 1px solid rgba(52, 211, 153, 0.3);
  color: #34d399;
}

.recovery-result.erro {
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.3);
  color: #f87171;
}

/* Executar Tudo - botão principal */
.btn-execute-all {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.25), rgba(52, 211, 153, 0.25));
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.4);
  font-size: 0.9rem;
  padding: 10px 24px;
}

.btn-execute-all:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.35), rgba(52, 211, 153, 0.35));
  box-shadow: 0 0 16px rgba(251, 191, 36, 0.2);
}

.exec-actions-secondary {
  margin-top: 0;
  margin-bottom: 16px;
}

.exec-actions-secondary .btn {
  font-size: 0.72rem;
  padding: 5px 12px;
  opacity: 0.7;
}

.exec-actions-secondary .btn:hover:not(:disabled) {
  opacity: 1;
}

/* Fase tracker */
.fase-tracker {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.fase-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.78rem;
  color: #64748b;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s;
}

.fase-item.active {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.1);
  border-color: rgba(251, 191, 36, 0.3);
  animation: pulse-fase 1.5s infinite;
}

.fase-item.done {
  color: #34d399;
  background: rgba(52, 211, 153, 0.1);
  border-color: rgba(52, 211, 153, 0.3);
}

.fase-num {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 0.65rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.1);
}

.fase-item.active .fase-num {
  background: rgba(251, 191, 36, 0.3);
}

.fase-item.done .fase-num {
  background: rgba(52, 211, 153, 0.3);
}

.fase-arrow {
  color: #475569;
  font-size: 0.75rem;
}

@keyframes pulse-fase {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* Event Log */
.event-log {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(96, 165, 250, 0.15);
  border-radius: 10px;
  margin-bottom: 16px;
  overflow: hidden;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.log-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: #60a5fa;
  margin: 0;
}

.log-count {
  font-size: 0.7rem;
  color: #64748b;
}

.log-entries {
  max-height: 360px;
  overflow-y: auto;
  padding: 8px 0;
}

.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 3px 16px;
  font-size: 0.75rem;
  line-height: 1.5;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.log-entry.info {
  color: #cbd5e1;
}
.log-entry.fase {
  color: #fbbf24;
  font-weight: 600;
}
.log-entry.step {
  color: #e2e8f0;
  font-weight: 600;
}
.log-entry.detail {
  color: #94a3b8;
}
.log-entry.success {
  color: #34d399;
}
.log-entry.error {
  color: #f87171;
}
.log-entry.warn {
  color: #fbbf24;
}

.log-time {
  color: #475569;
  flex-shrink: 0;
  min-width: 70px;
}

.log-icon {
  flex-shrink: 0;
  width: 16px;
  text-align: center;
}

.log-msg {
  word-break: break-word;
}

.log-entries::-webkit-scrollbar {
  width: 6px;
}

.log-entries::-webkit-scrollbar-track {
  background: transparent;
}

.log-entries::-webkit-scrollbar-thumb {
  background: rgba(96, 165, 250, 0.2);
  border-radius: 3px;
}

/* ── Glass Shapes ── */
.glass-shapes { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.glass-shape {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(0, 102, 255, 0.15);
  background: rgba(0, 102, 255, 0.04);
  box-shadow: 0 0 15px rgba(0, 102, 255, 0.2), 0 0 40px rgba(0, 102, 255, 0.1);
}
.shape-1 { width: 280px; height: 280px; top: -60px; right: -60px; filter: blur(2px); animation: drift1 26s ease-in-out infinite; }
.shape-2 { width: 200px; height: 200px; bottom: 10%; left: -40px; border-radius: 36px; filter: blur(1.5px); animation: drift2 30s ease-in-out infinite; }
.shape-3 { width: 150px; height: 150px; top: 40%; left: 55%; filter: blur(3px); animation: drift3 22s ease-in-out infinite; animation-delay: -8s; }
@keyframes drift1 { 0%,100% { transform: translate(-10%,-15%) rotate(0deg); } 50% { transform: translate(30%,50%) rotate(25deg); } }
@keyframes drift2 { 0%,100% { transform: translate(10%,-20%) rotate(45deg); } 50% { transform: translate(-40%,60%) rotate(90deg); } }
@keyframes drift3 { 0%,100% { transform: translate(0,-20%) rotate(0deg); } 50% { transform: translate(-25%,70%) rotate(-20deg); } }
</style>
