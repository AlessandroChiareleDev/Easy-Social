<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { PYTHON_API } from '@/lib/api'

const router = useRouter()

interface Celula {
  per_apur: string
  lote_num: number
  total: number
  ok: number
  erro: number
  enviando: number
  pendente: number
  na: number
  tem_xlsx: boolean
  estado:
    | 'sem_dados'
    | 'processando'
    | 'pronto_para_processar'
    | 'concluido_com_erros'
    | 'concluido'
    | 'aguardando_mapeamento'
}

interface MesLinha {
  per_apur: string
  lotes: Celula[]
}

interface OverviewAnual {
  ano: number
  meses: MesLinha[]
}

const ano = ref(2025)
const loading = ref(true)
const erro = ref('')
const overview = ref<OverviewAnual | null>(null)

const mesesLabel: Record<string, string> = {
  '2025-02': 'Fev/2025',
  '2025-03': 'Mar/2025',
  '2025-04': 'Abr/2025',
  '2025-05': 'Mai/2025',
  '2025-06': 'Jun/2025',
  '2025-07': 'Jul/2025',
  '2025-08': 'Ago/2025',
  '2025-09': 'Set/2025',
  '2025-10': 'Out/2025',
  '2025-11': 'Nov/2025',
  '2025-12': 'Dez/2025',
}

const resumo = computed(() => {
  if (!overview.value) {
    return { total: 0, ok: 0, erro: 0, pendente: 0, processando: 0, na: 0, mesesAtivos: 0 }
  }

  let total = 0
  let ok = 0
  let erro = 0
  let pendente = 0
  let processando = 0
  let na = 0
  let mesesAtivos = 0

  for (const mes of overview.value.meses) {
    const mesTemDados = mes.lotes.some(
      (c) => c.total > 0 || c.ok > 0 || c.erro > 0 || c.pendente > 0 || c.enviando > 0 || (c.na ?? 0) > 0,
    )
    if (mesTemDados) mesesAtivos += 1
    for (const c of mes.lotes) {
      total += c.total
      ok += c.ok
      erro += c.erro
      pendente += c.pendente
      processando += c.enviando
      na += c.na ?? 0
    }
  }

  return { total, ok, erro, pendente, processando, na, mesesAtivos }
})

function classeEstado(estado: Celula['estado']) {
  if (estado === 'concluido') return 'st st-ok'
  if (estado === 'concluido_com_erros') return 'st st-err'
  if (estado === 'processando') return 'st st-run'
  if (estado === 'pronto_para_processar') return 'st st-pend'
  if (estado === 'aguardando_mapeamento') return 'st st-map'
  return 'st st-empty'
}

function labelEstado(estado: Celula['estado']) {
  if (estado === 'concluido') return 'Concluído'
  if (estado === 'concluido_com_erros') return 'Concluído c/ erro'
  if (estado === 'processando') return 'Processando'
  if (estado === 'pronto_para_processar') return 'Pronto'
  if (estado === 'aguardando_mapeamento') return 'Aguardando mapeamento CPF'
  return 'Sem dados'
}

function abrirDetalhe(c: Celula) {
  if (c.estado === 'sem_dados') return
  router.push({
    name: 'repositorio-s1210-compartimento',
    params: { lote: String(c.lote_num), mes: c.per_apur },
  })
}

function voltarRepositorio() {
  router.push('/repositorio-s1210')
}

async function carregar() {
  loading.value = true
  erro.value = ''
  try {
    const resp = await axios.get<OverviewAnual>(`${PYTHON_API}/api/s1210-repo/anual/overview`, {
      params: { ano: ano.value },
    })
    overview.value = resp.data
  } catch (e: unknown) {
    const err = e as { message?: string }
    erro.value = err.message ?? 'Falha ao carregar S-1210 anual'
  } finally {
    loading.value = false
  }
}

onMounted(carregar)
</script>

<template>
  <div class="page">
    <header class="head">
      <button class="btn-back" @click="voltarRepositorio">← Repositório S-1210</button>
      <h1>S-1210 ANUAL</h1>
      <p class="sub">
        Visão unificada de 11 meses (fev a dez) com 4 lotes. Dados atuais já populados para 2025-02,
        2025-03 e 2025-04.
      </p>
    </header>

    <section class="cards" v-if="!loading && !erro">
      <article class="kpi">
        <span class="k">Meses ativos</span>
        <strong>{{ resumo.mesesAtivos }}</strong>
      </article>
      <article class="kpi">
        <span class="k">Total escopo</span>
        <strong>{{ resumo.total.toLocaleString('pt-BR') }}</strong>
      </article>
      <article class="kpi">
        <span class="k">OK</span>
        <strong class="ok">{{ resumo.ok.toLocaleString('pt-BR') }} <span v-if="resumo.na > 0" class="na-inline" title="N/A (Não aplica)">({{ resumo.na.toLocaleString('pt-BR') }})</span></strong>
      </article>
      <article class="kpi">
        <span class="k">Erro</span>
        <strong class="err">{{ resumo.erro.toLocaleString('pt-BR') }}</strong>
      </article>
      <article class="kpi">
        <span class="k">Pendente</span>
        <strong class="pend">{{ resumo.pendente.toLocaleString('pt-BR') }}</strong>
      </article>
      <article class="kpi">
        <span class="k">Processando</span>
        <strong class="run">{{ resumo.processando.toLocaleString('pt-BR') }}</strong>
      </article>
    </section>

    <div v-if="loading" class="state">Carregando visão anual...</div>
    <div v-else-if="erro" class="state state-err">{{ erro }}</div>

    <section v-else-if="overview" class="grid-wrap">
      <div class="grid-head">
        <div class="col col-mes">Mês</div>
        <div class="col">Lote 1</div>
        <div class="col">Lote 2</div>
        <div class="col">Lote 3</div>
        <div class="col">Lote 4</div>
      </div>

      <div v-for="mes in overview.meses" :key="mes.per_apur" class="grid-row">
        <div class="col col-mes">
          <div class="mes-label">{{ mesesLabel[mes.per_apur] ?? mes.per_apur }}</div>
          <div class="mes-sub">{{ mes.per_apur }}</div>
        </div>

        <button
          v-for="celula in mes.lotes"
          :key="`${celula.per_apur}-${celula.lote_num}`"
          class="col cell"
          :class="{ 'cell-disabled': celula.estado === 'sem_dados' }"
          :disabled="celula.estado === 'sem_dados'"
          @click="abrirDetalhe(celula)"
        >
          <div :class="classeEstado(celula.estado)">{{ labelEstado(celula.estado) }}</div>
          <div class="nums">
            <span>{{ celula.total }} escopo</span>
            <span class="ok">{{ celula.ok }} ok</span>
            <span class="err">{{ celula.erro }} erro</span>
            <span class="pend">{{ celula.pendente + celula.enviando }} pend</span>
            <span v-if="(celula.na ?? 0) > 0" class="na">{{ celula.na }} N/A</span>
          </div>
          <div v-if="celula.estado === 'aguardando_mapeamento'" class="hint">
            Clique para ver lista com identificador temporário
          </div>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page {
  --neon-a: #4f8ef5;
  --neon-b: #2d7dff;
  --neon-soft: rgba(79, 142, 245, 0.22);
  --card-bg: rgba(6, 18, 34, 0.72);
  max-width: 1360px;
  margin: 0 auto;
  padding: 24px 26px 34px;
  background:
    radial-gradient(circle at 90% -10%, rgba(79, 142, 245, 0.28), transparent 34%),
    radial-gradient(circle at -10% 0%, rgba(45, 125, 255, 0.28), transparent 36%);
}
.head h1 {
  margin: 0;
  color: #fff;
  letter-spacing: 0.4px;
  text-shadow: 0 0 20px rgba(79, 142, 245, 0.25);
}
.sub {
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.74);
}
.btn-back {
  margin-bottom: 12px;
  background: rgba(79, 142, 245, 0.06);
  border: 1px solid rgba(79, 142, 245, 0.4);
  color: rgba(255, 255, 255, 0.9);
  border-radius: 999px;
  padding: 7px 14px;
  cursor: pointer;
  transition: all 0.18s ease;
}
.btn-back:hover {
  color: #fff;
  background: rgba(79, 142, 245, 0.16);
  transform: translateY(-1px);
  box-shadow: 0 0 14px rgba(79, 142, 245, 0.28);
}

.cards {
  margin: 20px 0 18px;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}
.kpi {
  border: 1px solid rgba(79, 142, 245, 0.24);
  background: linear-gradient(180deg, rgba(4, 21, 40, 0.85), rgba(6, 20, 38, 0.55));
  border-radius: 14px;
  padding: 12px 13px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 0 20px rgba(79, 142, 245, 0.08);
}
.kpi .k {
  display: block;
  color: rgba(255, 255, 255, 0.64);
  font-size: 12px;
}
.kpi strong {
  color: #fff;
  font-size: 24px;
  line-height: 1.1;
}
.kpi .ok {
  color: #55e39c;
}
.kpi .err {
  color: #ff6b6b;
}
.kpi .pend {
  color: #ffd166;
}
.kpi .na {
  color: #b3a8ff;
}
.kpi .na-inline {
  color: #b3a8ff;
  font-size: 0.7em;
  font-weight: 600;
  margin-left: 4px;
}
.kpi .run {
  color: #66d9ff;
}

.state {
  text-align: center;
  padding: 30px;
  color: rgba(255, 255, 255, 0.72);
}
.state-err {
  color: #ff6b6b;
}

.grid-wrap {
  border: 1px solid rgba(79, 142, 245, 0.24);
  border-radius: 16px;
  overflow: hidden;
  background: rgba(4, 16, 34, 0.62);
  box-shadow:
    0 10px 26px rgba(0, 0, 0, 0.22),
    0 0 24px rgba(79, 142, 245, 0.12);
}
.grid-head,
.grid-row {
  display: grid;
  grid-template-columns: 180px repeat(4, minmax(0, 1fr));
}
.grid-head {
  background: linear-gradient(90deg, rgba(28, 56, 140, 0.46), rgba(79, 142, 245, 0.24));
  font-weight: 700;
}
.grid-row:nth-child(even) {
  background: rgba(255, 255, 255, 0.018);
}
.col {
  padding: 12px 13px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #fff;
}
.col:last-child {
  border-right: 0;
}
.col-mes {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.mes-label {
  font-weight: 700;
}
.mes-sub {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

.cell {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.015), rgba(255, 255, 255, 0));
  text-align: left;
  cursor: pointer;
  transition:
    background 0.14s ease,
    transform 0.14s ease;
}
.cell:hover {
  background: rgba(79, 142, 245, 0.1);
  transform: translateY(-1px);
  box-shadow: inset 0 0 0 1px rgba(79, 142, 245, 0.2);
}
.cell-disabled {
  cursor: default;
  opacity: 0.55;
}
.cell-disabled:hover {
  background: transparent;
  transform: none;
}

.st {
  display: inline-block;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  border: 1px solid transparent;
  margin-bottom: 8px;
}
.st-ok {
  color: #8ff0be;
  border-color: rgba(143, 240, 190, 0.45);
  background: rgba(143, 240, 190, 0.1);
}
.st-err {
  color: #ff9b9b;
  border-color: rgba(255, 155, 155, 0.45);
  background: rgba(255, 155, 155, 0.1);
}
.st-run {
  color: #9ce8ff;
  border-color: rgba(156, 232, 255, 0.45);
  background: rgba(156, 232, 255, 0.1);
}
.st-pend {
  color: #ffe39a;
  border-color: rgba(255, 227, 154, 0.45);
  background: rgba(255, 227, 154, 0.1);
}
.st-empty {
  color: rgba(255, 255, 255, 0.55);
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.06);
}
.st-map {
  color: #67d8ff;
  border-color: rgba(79, 142, 245, 0.45);
  background: rgba(79, 142, 245, 0.14);
}

.nums {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 10px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
}
.nums .ok {
  color: #70e6ad;
}
.nums .err {
  color: #ff8f8f;
}
.nums .pend {
  color: #ffd77a;
}
.nums .na {
  color: #b3a8ff;
}

.hint {
  margin-top: 8px;
  color: rgba(103, 216, 255, 0.96);
  font-size: 11px;
  font-weight: 600;
  text-shadow: 0 0 12px rgba(79, 142, 245, 0.35);
}

@media (max-width: 1200px) {
  .cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .grid-wrap {
    overflow-x: auto;
  }
  .grid-head,
  .grid-row {
    min-width: 920px;
  }
}
</style>
