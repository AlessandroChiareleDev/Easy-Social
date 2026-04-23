<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

const totalCPFsEscopo = ref(0)
const totalOk = ref(0)
const totalErro = ref(0)
const totalPend = ref(0)
const mesesComXlsx = ref<Set<string>>(new Set())

async function carregar() {
  loading.value = true
  erro.value = ''
  try {
    const resp = await axios.get<Overview>(`${PYTHON_API}/api/s1210-repo/overview`)
    overview.value = resp.data

    let tot = 0
    let ok = 0
    let err = 0
    let pend = 0
    const meses = new Set<string>()
    for (const lote of Object.values(resp.data.por_lote)) {
      for (const r of lote) {
        tot += r.total
        ok += r.ok
        err += r.erro
        pend += r.pendente + r.enviando
        if (r.tem_xlsx) meses.add(r.per_apur)
      }
    }
    totalCPFsEscopo.value = tot
    totalOk.value = ok
    totalErro.value = err
    totalPend.value = pend
    mesesComXlsx.value = meses
  } catch (e: unknown) {
    const err = e as { message?: string }
    erro.value = err.message ?? 'erro'
  } finally {
    loading.value = false
  }
}

function abrirPorLote() {
  router.push('/repositorio-s1210/por-lote')
}

onMounted(carregar)
</script>

<template>
  <div class="page">
    <header class="page-header">
      <h1>Repositório S-1210 — APPA</h1>
      <p class="sub">
        Tela única da missão: 3 meses (Fev/Mar/Abr 2025) × 4 lotes a partir das XLSX oficiais da
        Ana.
      </p>
    </header>

    <div v-if="loading" class="state">Carregando…</div>
    <div v-else-if="erro" class="state state--err">{{ erro }}</div>

    <template v-else>
      <!-- Resumo geral -->
      <section class="resumo">
        <div class="kpi">
          <span class="kpi-n">{{ totalCPFsEscopo.toLocaleString('pt-BR') }}</span>
          <span class="kpi-lbl">CPFs no escopo</span>
        </div>
        <div class="kpi kpi--ok">
          <span class="kpi-n">{{ totalOk.toLocaleString('pt-BR') }}</span>
          <span class="kpi-lbl">Enviados OK</span>
        </div>
        <div class="kpi kpi--err">
          <span class="kpi-n">{{ totalErro.toLocaleString('pt-BR') }}</span>
          <span class="kpi-lbl">Com erro</span>
        </div>
        <div class="kpi kpi--pend">
          <span class="kpi-n">{{ totalPend.toLocaleString('pt-BR') }}</span>
          <span class="kpi-lbl">Pendentes</span>
        </div>
        <div class="kpi">
          <span class="kpi-n">{{ mesesComXlsx.size }}/3</span>
          <span class="kpi-lbl">XLSX ingeridas</span>
        </div>
      </section>

      <!-- Duas vertentes -->
      <section class="vertentes">
        <button class="vcard vcard--a" @click="abrirPorLote">
          <div class="vcard-head">
            <span class="vcard-badge">Vertente A</span>
            <h2>Por Lote</h2>
          </div>
          <p class="vcard-desc">
            Visão operacional: 4 grandes lotes (1, 2, 3, 4) × 3 meses. Para cada combinação: quantos
            CPFs estão no escopo, quantos já foram enviados, quantos deram erro, quantos faltam.
            Drill-down até a lista de CPFs.
          </p>
          <div class="vcard-foot">
            <span>4 × 3 compartimentos</span>
            <span class="arrow">→</span>
          </div>
        </button>

        <button class="vcard vcard--b" disabled>
          <div class="vcard-head">
            <span class="vcard-badge">Vertente B</span>
            <h2>Mensal</h2>
          </div>
          <p class="vcard-desc">
            Visão por competência: Fev / Mar / Abr 2025. Cada mês reúne os 4 lotes num único painel,
            com timeline dos envios.
          </p>
          <div class="vcard-foot">
            <span>Em breve</span>
            <span class="arrow">—</span>
          </div>
        </button>
      </section>

      <!-- Regra de ouro (lembrete) -->
      <section class="nota">
        <strong>⚠️ Regras inegociáveis:</strong>
        <ul>
          <li>As 3 XLSX ficam persistidas no sistema. Não é preciso reupar a cada sessão.</li>
          <li>
            Os ZIPs do eSocial continuam em <code>Downloads</code> — o backend lê em streaming (nada
            sobe ao banco).
          </li>
          <li>Todo envio S-1210 é em <strong>produção</strong> e exige confirmação explícita.</li>
          <li>Nada toca em S-1200, S-1298 ou pipeline antigo.</li>
        </ul>
      </section>
    </template>
  </div>
</template>

<style scoped>
.page {
  padding: 24px 32px;
  max-width: 1200px;
  margin: 0 auto;
}
.page-header h1 {
  margin: 0 0 6px;
  color: #fff;
}
.sub {
  color: rgba(255, 255, 255, 0.65);
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

.resumo {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 32px;
}
.kpi {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.kpi-n {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}
.kpi-lbl {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.kpi--ok .kpi-n {
  color: #4ade80;
}
.kpi--err .kpi-n {
  color: #ff6b6b;
}
.kpi--pend .kpi-n {
  color: #fbbf24;
}

.vertentes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 32px;
}
.vcard {
  text-align: left;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(99, 102, 241, 0.05));
  border: 1px solid rgba(99, 102, 241, 0.35);
  border-radius: 14px;
  padding: 20px 22px;
  color: #fff;
  cursor: pointer;
  transition:
    transform 0.12s,
    border-color 0.12s,
    background 0.12s;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}
.vcard:hover:not(:disabled) {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.8);
}
.vcard:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.vcard--b {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(168, 85, 247, 0.05));
  border-color: rgba(168, 85, 247, 0.35);
}
.vcard-head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.vcard-badge {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.6px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.3);
  color: #c7d2fe;
}
.vcard--b .vcard-badge {
  background: rgba(168, 85, 247, 0.3);
  color: #e9d5ff;
}
.vcard h2 {
  margin: 0;
  font-size: 20px;
}
.vcard-desc {
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
  line-height: 1.55;
  margin: 0;
}
.vcard-foot {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  color: rgba(255, 255, 255, 0.55);
  font-size: 12px;
}
.vcard-foot .arrow {
  font-size: 18px;
}

.nota {
  background: rgba(250, 204, 21, 0.08);
  border: 1px solid rgba(250, 204, 21, 0.25);
  border-radius: 10px;
  padding: 14px 18px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 13px;
  line-height: 1.7;
}
.nota ul {
  margin: 8px 0 0;
  padding-left: 20px;
}
.nota code {
  background: rgba(0, 0, 0, 0.4);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
