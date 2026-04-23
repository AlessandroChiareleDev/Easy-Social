<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { PYTHON_API } from '@/lib/api'

const router = useRouter()

interface LoteInfo {
  per_apur: string
  lote_num: number
  total: number
  ok: number
  erro: number
  enviando: number
  pendente: number
  tem_xlsx: boolean
}

interface Overview {
  empresa_id: number
  meses: string[]
  por_lote: Record<string, LoteInfo[]>
}

const loading = ref(true)
const erro = ref('')
const overview = ref<Overview | null>(null)
const showInfoLotes = ref(false)

const mesLabels: Record<string, string> = {
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

async function carregar() {
  loading.value = true
  erro.value = ''
  try {
    const resp = await axios.get<Overview>(`${PYTHON_API}/api/s1210-repo/overview`)
    overview.value = resp.data
  } catch (e: unknown) {
    const err = e as { message?: string }
    erro.value = err.message ?? 'erro'
  } finally {
    loading.value = false
  }
}

function pct(ok: number, total: number): number {
  if (!total) return 0
  return Math.round((ok / total) * 100)
}

function irParaCompartimento(lote: number, mes: string) {
  router.push({
    name: 'repositorio-s1210-compartimento',
    params: { lote: String(lote), mes },
  })
}

function voltarPorta() {
  router.push('/repositorio-s1210')
}

onMounted(carregar)
</script>

<template>
  <div class="page">
    <header class="page-header">
      <button class="voltar" @click="voltarPorta">← Repositório S-1210</button>
      <h1>Vertente A — Por Lote</h1>
      <p class="sub">
        4 grandes lotes × 3 meses. Clique numa caixa para abrir a lista de CPFs daquele
        compartimento.
      </p>

      <div class="info-box">
        <button class="info-toggle" @click="showInfoLotes = !showInfoLotes">
          <span>ℹ Entenda os lotes</span>
          <span class="info-caret">{{ showInfoLotes ? '−' : '+' }}</span>
        </button>
        <div v-if="showInfoLotes" class="info-body">
          <div class="info-item">
            <strong>Lote 1 — Sem plano de saúde</strong>
            <p>
              CPFs sem nenhuma operadora identificada na aba "Operadoras" do XLSX. S-1210 retif é
              enviado <em>sem</em> bloco <code>&lt;planSaude&gt;</code>
              (apenas ajustes de IR/detPgtos conforme o original).
            </p>
          </div>
          <div class="info-item">
            <strong>Lote 2 — Plano de saúde (grupo A)</strong>
            <p>
              CPFs com titular + operadora identificados cujas rubricas de plano de saúde (516, 605,
              607, 619, 631, 638, 774, 775) já estão configuradas corretamente no eSocial para gerar
              <code>&lt;planSaude&gt;</code> no S-1210. O envio agrega todos os valores por CNPJ de
              operadora.
            </p>
          </div>
          <div class="info-item">
            <strong>Lote 3 — Plano de saúde (grupo B)</strong>
            <p>
              Estruturalmente <em>idêntico</em> ao Lote 2. A diferença é que hoje as rubricas 774,
              775 e 522 ainda não estão com a natureza correta no eSocial (774 → 9219, 775 → outros
              descontos, 522 → plano coletivo empresarial). Enquanto a APPA não reclassificar, este
              lote fica bloqueado.
            </p>
          </div>
          <div class="info-item">
            <strong>Lote 4 — Casos manuais</strong>
            <p>
              Situações especiais que precisam de tratamento individual (divergências de base, CPFs
              em blocklist etc.).
            </p>
          </div>
          <div class="info-note">
            Os contadores <strong>OK / erro / pend</strong> são alimentados pela view
            <code>v_s1210_contadores</code> a partir da tabela <code>s1210_cpf_envios</code>
            (histórico de envios da missão atual).
          </div>
        </div>
      </div>
    </header>

    <div v-if="loading" class="state">Carregando…</div>
    <div v-else-if="erro" class="state state--err">{{ erro }}</div>

    <template v-else-if="overview">
      <div v-for="lote in [1, 2, 3, 4]" :key="lote" class="lote-block">
        <header class="lote-head">
          <div class="lote-title">
            <span class="lote-num">Lote {{ lote }}</span>
            <span class="lote-desc">{{ descricaoLote[lote] }}</span>
          </div>
        </header>
        <div class="meses">
          <button
            v-for="item in overview.por_lote[String(lote)]"
            :key="item.per_apur"
            class="comp"
            :class="{
              'comp--empty': !item.tem_xlsx || item.total === 0,
              'comp--done': item.total > 0 && item.ok === item.total,
            }"
            :disabled="!item.tem_xlsx"
            @click="irParaCompartimento(lote, item.per_apur)"
          >
            <div class="comp-head">
              <span class="comp-mes">{{ mesLabels[item.per_apur] ?? item.per_apur }}</span>
              <span v-if="!item.tem_xlsx" class="comp-tag">sem XLSX</span>
              <span v-else-if="item.total === 0" class="comp-tag">vazio</span>
            </div>
            <div class="comp-total">
              <span class="big">{{ item.total.toLocaleString('pt-BR') }}</span>
              <span class="small">CPFs</span>
            </div>
            <div class="comp-bar">
              <div class="bar-ok" :style="{ width: pct(item.ok, item.total) + '%' }"></div>
              <div class="bar-err" :style="{ width: pct(item.erro, item.total) + '%' }"></div>
            </div>
            <div class="comp-stats">
              <span class="stat stat--ok">{{ item.ok }} OK</span>
              <span class="stat stat--err">{{ item.erro }} erro</span>
              <span class="stat stat--pend">{{ item.pendente + item.enviando }} pend</span>
            </div>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page {
  padding: 24px 32px;
  max-width: 1200px;
  margin: 0 auto;
}
.info-box {
  margin: 6px 0 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
}
.info-toggle {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: transparent;
  border: 0;
  color: rgba(255, 255, 255, 0.8);
  padding: 10px 14px;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
}
.info-toggle:hover {
  background: rgba(255, 255, 255, 0.04);
}
.info-caret {
  color: rgba(255, 255, 255, 0.5);
  font-size: 16px;
}
.info-body {
  padding: 4px 16px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
}
.info-item {
  margin-top: 10px;
}
.info-item strong {
  color: #fff;
  display: block;
  margin-bottom: 2px;
}
.info-item p {
  margin: 0;
  line-height: 1.5;
}
.info-item code {
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 12px;
}
.info-note {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.55);
  font-size: 12px;
}
.info-note code {
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 3px;
}
.voltar {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  margin-bottom: 10px;
}
.voltar:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}
.page-header h1 {
  margin: 0 0 6px;
  color: #fff;
}
.sub {
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 24px;
}
.state {
  padding: 40px;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
}
.state--err {
  color: #ff6b6b;
}

.lote-block {
  margin-bottom: 24px;
}
.lote-head {
  display: flex;
  align-items: baseline;
  padding: 6px 2px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 12px;
}
.lote-num {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  margin-right: 12px;
}
.lote-desc {
  color: rgba(255, 255, 255, 0.55);
  font-size: 13px;
}

.meses {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.comp {
  text-align: left;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 14px 16px;
  color: #fff;
  cursor: pointer;
  transition:
    transform 0.1s,
    border-color 0.1s,
    background 0.1s;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 130px;
}
.comp:hover:not(:disabled) {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.6);
  background: rgba(99, 102, 241, 0.08);
}
.comp:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}
.comp--empty .big {
  color: rgba(255, 255, 255, 0.35);
}
.comp--done {
  border-color: rgba(74, 222, 128, 0.5);
  background: rgba(74, 222, 128, 0.06);
}

.comp-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.comp-mes {
  font-weight: 600;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}
.comp-tag {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
}

.comp-total {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.comp-total .big {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}
.comp-total .small {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.comp-bar {
  position: relative;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
  display: flex;
}
.bar-ok {
  background: #4ade80;
  height: 100%;
}
.bar-err {
  background: #ff6b6b;
  height: 100%;
}

.comp-stats {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
}
.stat--ok {
  color: #4ade80;
}
.stat--err {
  color: #ff6b6b;
}
.stat--pend {
  color: #fbbf24;
}
</style>
