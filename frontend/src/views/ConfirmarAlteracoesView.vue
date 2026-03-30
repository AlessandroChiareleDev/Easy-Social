<template>
  <div class="confirmar-view">
    <!-- Header -->
    <div class="header">
      <h1>Confirmar Alterações</h1>
      <div class="header-actions">
        <div class="stats" v-if="!loading">
          <span class="stat">{{ correcoes.length }} correções no staging</span>
          <span class="stat pendente" v-if="pendentes > 0">{{ pendentes }} pendentes</span>
          <span class="stat aplicada" v-if="aplicadas > 0">{{ aplicadas }} já aplicadas</span>
        </div>
        <button
          class="btn-aplicar"
          @click="aplicarTodas"
          :disabled="pendentes === 0 || aplicando"
          v-if="pendentes > 0"
        >
          {{ aplicando ? 'Aplicando...' : `Aplicar ${pendentes} correções` }}
        </button>
      </div>
    </div>

    <!-- Filtros -->
    <div class="filtros">
      <button
        :class="['filtro-btn', { active: filtro === 'pendente' }]"
        @click="filtro = 'pendente'"
      >
        Pendentes ({{ pendentes }})
      </button>
      <button :class="['filtro-btn', { active: filtro === 'todas' }]" @click="filtro = 'todas'">
        Todas ({{ correcoes.length }})
      </button>
      <button
        :class="['filtro-btn', { active: filtro === 'aplicada' }]"
        @click="filtro = 'aplicada'"
      >
        Aplicadas ({{ aplicadas }})
      </button>
      <input v-model="busca" class="busca-input" placeholder="Buscar por código ou nome..." />
    </div>

    <div v-if="loading" class="loading">Carregando correções...</div>

    <!-- Tabela de correções -->
    <div v-else-if="correcoesFiltradas.length > 0" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th class="col-num">#</th>
            <th class="col-cod">Cód. Evento</th>
            <th class="col-nome">Nome do Evento</th>
            <th class="col-nat-ant">Natureza Anterior</th>
            <th class="col-nat-nova">Natureza Nova</th>
            <th class="col-usuario">Usuário</th>
            <th class="col-data">Data</th>
            <th class="col-status">Status</th>
            <th class="col-acoes">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(c, i) in correcoesFiltradas"
            :key="c.id"
            :class="{
              'row-aplicada': c.status === 'aplicada',
              'row-editando': editandoId === c.id,
            }"
          >
            <td class="col-num">{{ i + 1 }}</td>
            <td class="col-cod mono">{{ c.codigoevento }}</td>
            <td class="col-nome">{{ c.nome_evento }}</td>
            <td class="col-nat-ant">
              <span class="nat-antiga">{{ c.natureza_anterior || '—' }}</span>
            </td>
            <td class="col-nat-nova">
              <template v-if="editandoId === c.id">
                <div class="edit-inline">
                  <input
                    v-model="editCodigo"
                    class="edit-input codigo"
                    placeholder="Código"
                    @keyup.enter="salvarEdicao(c)"
                    @keyup.escape="cancelarEdicao"
                    ref="editCodigoRef"
                  />
                  <input
                    v-model="editNome"
                    class="edit-input nome"
                    :placeholder="buscandoNome ? 'Buscando...' : 'Nome'"
                    readonly
                    @keyup.enter="salvarEdicao(c)"
                    @keyup.escape="cancelarEdicao"
                  />
                </div>
              </template>
              <template v-else>
                <span class="nat-nova">{{ c.natureza_nova }}</span>
              </template>
            </td>
            <td class="col-usuario">{{ c.usuario_nome }}</td>
            <td class="col-data">{{ formatDate(c.data_correcao) }}</td>
            <td class="col-status">
              <span :class="['badge', c.status]">
                {{ c.status === 'pendente' ? 'Pendente' : 'Aplicada' }}
              </span>
            </td>
            <td class="col-acoes">
              <template v-if="c.status === 'pendente'">
                <template v-if="editandoId === c.id">
                  <button class="btn-icon salvar" @click="salvarEdicao(c)" title="Salvar">✓</button>
                  <button class="btn-icon cancelar" @click="cancelarEdicao" title="Cancelar">
                    ✕
                  </button>
                </template>
                <template v-else>
                  <button class="btn-icon editar" @click="iniciarEdicao(c)" title="Editar">
                    <svg
                      width="15"
                      height="15"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                  </button>
                  <button class="btn-icon remover" @click="removerCorrecao(c)" title="Remover">
                    <svg
                      width="15"
                      height="15"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <polyline points="3 6 5 6 21 6" />
                      <path
                        d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                      />
                    </svg>
                  </button>
                </template>
              </template>
              <span v-else class="text-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="empty">
      <p>Nenhuma correção encontrada.</p>
      <p class="sub">As correções feitas no Validador aparecerão aqui para revisão</p>
    </div>

    <!-- Feedback -->
    <Transition name="toast">
      <div v-if="toast" :class="['toast', toast.type]">{{ toast.msg }}</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333/api'

interface Correcao {
  id: number
  codigoevento: string
  nome_evento: string
  natureza_anterior: string
  natureza_nova: string
  usuario_nome: string
  data_correcao: string
  motivo: string
  status: string
}

const correcoes = ref<Correcao[]>([])
const loading = ref(true)
const filtro = ref<'pendente' | 'todas' | 'aplicada'>('pendente')
const busca = ref('')
const aplicando = ref(false)
const toast = ref<{ msg: string; type: 'ok' | 'err' } | null>(null)

// Edição inline
const editandoId = ref<number | null>(null)
const editCodigo = ref('')
const editNome = ref('')
const buscandoNome = ref(false)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(editCodigo, (novoCodigo) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  const cod = novoCodigo.trim()
  if (!cod || cod.length < 2) {
    editNome.value = ''
    return
  }
  debounceTimer = setTimeout(async () => {
    buscandoNome.value = true
    try {
      const res = await axios.get(`${API_URL}/naturezas/por-codigo/${cod}`)
      if (res.data.success && res.data.data) {
        editNome.value = res.data.data.nome
      } else {
        editNome.value = ''
      }
    } catch {
      editNome.value = ''
    } finally {
      buscandoNome.value = false
    }
  }, 400)
})

const pendentes = computed(() => correcoes.value.filter((c) => c.status === 'pendente').length)
const aplicadas = computed(() => correcoes.value.filter((c) => c.status === 'aplicada').length)

const correcoesFiltradas = computed(() => {
  let list = correcoes.value
  if (filtro.value === 'pendente') list = list.filter((c) => c.status === 'pendente')
  else if (filtro.value === 'aplicada') list = list.filter((c) => c.status === 'aplicada')

  if (busca.value.trim()) {
    const q = busca.value.toLowerCase()
    list = list.filter(
      (c) =>
        c.codigoevento?.toLowerCase().includes(q) ||
        c.nome_evento?.toLowerCase().includes(q) ||
        c.natureza_nova?.toLowerCase().includes(q),
    )
  }
  return list
})

async function carregarCorrecoes() {
  loading.value = true
  try {
    const res = await axios.get(`${API_URL}/rubricas/relatorio-final`)
    correcoes.value = res.data.data || []
  } catch {
    showToast('Erro ao carregar correções', 'err')
  } finally {
    loading.value = false
  }
}

function iniciarEdicao(c: Correcao) {
  editandoId.value = c.id
  // natureza_nova format: "1002-DSR - Descanso semanal remunerado"
  const dash = c.natureza_nova?.indexOf('-')
  if (dash !== undefined && dash > 0) {
    editCodigo.value = c.natureza_nova.substring(0, dash).trim()
    editNome.value = c.natureza_nova.substring(dash + 1).trim()
  } else {
    editCodigo.value = c.natureza_nova || ''
    editNome.value = ''
  }
}

function cancelarEdicao() {
  editandoId.value = null
  editCodigo.value = ''
  editNome.value = ''
}

async function salvarEdicao(c: Correcao) {
  if (!editCodigo.value.trim()) return
  try {
    await axios.put(`${API_URL}/rubricas/staging/${c.id}`, {
      naturezaCodigo: editCodigo.value.trim(),
      naturezaNome: editNome.value.trim(),
    })
    // Atualizar localmente
    c.natureza_nova = `${editCodigo.value.trim()}-${editNome.value.trim()}`
    cancelarEdicao()
    showToast('Correção atualizada', 'ok')
  } catch {
    showToast('Erro ao salvar edição', 'err')
  }
}

async function removerCorrecao(c: Correcao) {
  try {
    await axios.post(`${API_URL}/rubricas/desfazer/${c.id}`)
    correcoes.value = correcoes.value.filter((x) => x.id !== c.id)
    showToast('Correção removida', 'ok')
  } catch {
    showToast('Erro ao remover', 'err')
  }
}

async function aplicarTodas() {
  aplicando.value = true
  try {
    const res = await axios.post(`${API_URL}/rubricas/aplicar-correcoes`)
    showToast(res.data.message || 'Correções aplicadas!', 'ok')
    await carregarCorrecoes()
  } catch {
    showToast('Erro ao aplicar correções', 'err')
  } finally {
    aplicando.value = false
  }
}

function formatDate(d: string) {
  if (!d) return '—'
  const dt = new Date(d)
  return (
    dt.toLocaleDateString('pt-BR') +
    ' ' +
    dt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  )
}

function showToast(msg: string, type: 'ok' | 'err') {
  toast.value = { msg, type }
  setTimeout(() => (toast.value = null), 3000)
}

onMounted(carregarCorrecoes)
</script>

<style scoped>
.confirmar-view {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  color: #e2e8f0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.header h1 {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats {
  display: flex;
  gap: 12px;
}

.stat {
  font-size: 13px;
  color: #94a3b8;
  background: rgba(0, 102, 255, 0.06);
  padding: 4px 10px;
  border-radius: 6px;
}

.stat.pendente {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.1);
}
.stat.aplicada {
  color: #34d399;
  background: rgba(52, 211, 153, 0.1);
}

.btn-aplicar {
  background: #0066ff;
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}
.btn-aplicar:hover {
  background: #0055dd;
}
.btn-aplicar:disabled {
  background: #1e293b;
  color: #475569;
  cursor: not-allowed;
}

/* Filtros */
.filtros {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filtro-btn {
  padding: 6px 14px;
  border: 1px solid rgba(0, 102, 255, 0.15);
  background: transparent;
  color: #94a3b8;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.filtro-btn:hover {
  border-color: #0066ff;
  color: #e2e8f0;
}
.filtro-btn.active {
  background: rgba(0, 102, 255, 0.12);
  border-color: #0066ff;
  color: #0066ff;
  font-weight: 600;
}

.busca-input {
  margin-left: auto;
  padding: 6px 12px;
  border: 1px solid rgba(0, 102, 255, 0.15);
  border-radius: 6px;
  background: #0d1530;
  color: #e2e8f0;
  font-size: 13px;
  width: 250px;
}
.busca-input::placeholder {
  color: #475569;
}
.busca-input:focus {
  outline: none;
  border-color: #0066ff;
}

/* Tabela */
.table-wrapper {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid rgba(0, 102, 255, 0.1);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th {
  background: #111b3a;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.5px;
  padding: 10px 12px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid rgba(0, 102, 255, 0.12);
}

td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(0, 102, 255, 0.06);
  vertical-align: middle;
}

tr:hover {
  background: rgba(0, 102, 255, 0.04);
}
tr.row-aplicada {
  opacity: 0.5;
}
tr.row-editando {
  background: rgba(0, 102, 255, 0.08);
}

.mono {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

.col-num {
  width: 40px;
  text-align: center;
  color: #475569;
}
.col-cod {
  width: 90px;
}
.col-status {
  width: 90px;
}
.col-acoes {
  width: 80px;
  text-align: center;
}
.col-usuario {
  width: 90px;
}
.col-data {
  width: 130px;
  white-space: nowrap;
}

.nat-antiga {
  color: #f87171;
}
.nat-nova {
  color: #34d399;
  font-weight: 600;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.badge.pendente {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}
.badge.aplicada {
  background: rgba(52, 211, 153, 0.12);
  color: #34d399;
}

/* Edit inline */
.edit-inline {
  display: flex;
  gap: 4px;
}

.edit-input {
  padding: 4px 6px;
  border: 1px solid #0066ff;
  border-radius: 4px;
  background: #0a1024;
  color: #e2e8f0;
  font-size: 13px;
}
.edit-input.codigo {
  width: 70px;
}
.edit-input.nome {
  flex: 1;
  min-width: 120px;
}

/* Action buttons */
.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background 0.2s;
}
.btn-icon:hover {
  background: rgba(255, 255, 255, 0.08);
}
.btn-icon.salvar {
  color: #34d399;
  font-weight: bold;
  font-size: 18px;
}
.btn-icon.cancelar {
  color: #f87171;
  font-weight: bold;
  font-size: 18px;
}
.btn-icon.remover:hover {
  background: rgba(248, 113, 113, 0.12);
}

.text-muted {
  color: #334155;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #64748b;
}

.empty {
  text-align: center;
  padding: 60px 20px;
  color: #64748b;
}
.empty .sub {
  font-size: 13px;
  margin-top: 8px;
  color: #475569;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  z-index: 9999;
}
.toast.ok {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  border: 1px solid rgba(52, 211, 153, 0.3);
}
.toast.err {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
  border: 1px solid rgba(248, 113, 113, 0.3);
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
