<template>
  <div class="explorador-view">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-3">
          <svg
            class="w-7 h-7 text-[#5ac8f5]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
            <line x1="11" y1="8" x2="11" y2="14" />
            <line x1="8" y1="11" x2="14" y2="11" />
          </svg>
          Explorador de Eventos
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Buscar e analisar eventos eSocial por CPF, rubrica, período e mais
        </p>
      </div>
      <button @click="showImport = true" class="import-btn">
        <svg
          class="w-4 h-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        Importar Período
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-icon stat-icon--blue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
        </div>
        <div>
          <p class="stat-value">{{ stats.total_eventos.toLocaleString('pt-BR') }}</p>
          <p class="stat-label">Eventos Importados</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--cyan">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4-4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 00-3-3.87" />
            <path d="M16 3.13a4 4 0 010 7.75" />
          </svg>
        </div>
        <div>
          <p class="stat-value">{{ stats.total_cpfs.toLocaleString('pt-BR') }}</p>
          <p class="stat-label">CPFs Únicos</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--green">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
        </div>
        <div>
          <p class="stat-value">{{ stats.periodos.length }}</p>
          <p class="stat-label">Períodos Importados</p>
        </div>
      </div>
      <div class="stat-card" :class="{ 'stat-card--alert': stats.cpfs_irrf_11 > 0 }">
        <div
          class="stat-icon"
          :class="stats.cpfs_irrf_11 > 0 ? 'stat-icon--red' : 'stat-icon--green'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path
              d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
            />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <div>
          <p class="stat-value">{{ stats.cpfs_irrf_11.toLocaleString('pt-BR') }}</p>
          <p class="stat-label">CPFs com IRRF=11</p>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-card">
      <div class="filter-grid">
        <!-- Período -->
        <div class="filter-group">
          <label class="filter-label">Período</label>
          <select v-model="filters.per_apur" class="filter-select" @change="buscar(1)">
            <option value="">Todos</option>
            <option v-for="p in stats?.periodos ?? []" :key="p" :value="p">
              {{ formatPeriodo(p) }}
            </option>
          </select>
        </div>

        <!-- CPF -->
        <div class="filter-group filter-group--wide">
          <label class="filter-label">CPF</label>
          <div class="cpf-search-container">
            <input
              v-model="cpfSearch"
              type="text"
              placeholder="Digite o CPF..."
              class="filter-input"
              @input="onCpfInput"
              @keydown.enter="applyCpf"
              @keydown.escape="cpfSuggestions = []"
              @focus="cpfFocused = true"
              @blur="onCpfBlur"
            />
            <button v-if="filters.cpf" @click="clearCpf" class="cpf-clear-btn" title="Limpar CPF">
              <svg
                class="w-3.5 h-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
            <!-- Autocomplete dropdown -->
            <div v-if="cpfSuggestions.length > 0 && cpfFocused" class="cpf-dropdown">
              <button
                v-for="s in cpfSuggestions"
                :key="s.cpf"
                class="cpf-suggestion"
                @mousedown.prevent="selectCpf(s.cpf)"
              >
                <span class="font-mono">{{ formatCpf(s.cpf) }}</span>
                <span class="text-slate-500 text-xs">{{ s.total_eventos }} eventos</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Tipo de Evento -->
        <div class="filter-group">
          <label class="filter-label">Tipo de Evento</label>
          <select v-model="filters.tipo_evento" class="filter-select" @change="buscar(1)">
            <option value="">Todos</option>
            <option v-for="t in eventTypes" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>

        <!-- Rubrica -->
        <div class="filter-group">
          <label class="filter-label">Rubrica</label>
          <input
            v-model="filters.cod_rubr"
            type="text"
            placeholder="Ex: 566"
            class="filter-input"
            @keydown.enter="buscar(1)"
          />
        </div>

        <!-- codIncIRRF -->
        <div class="filter-group">
          <label class="filter-label">Cód. Inc. IRRF</label>
          <input
            v-model="filters.cod_inc_irrf"
            type="text"
            placeholder="Ex: 11 ou 41"
            class="filter-input"
            @keydown.enter="buscar(1)"
          />
        </div>

        <!-- Nr Recibo -->
        <div class="filter-group filter-group--wide">
          <label class="filter-label">Nº Recibo</label>
          <input
            v-model="filters.nr_recibo"
            type="text"
            placeholder="Ex: 1.1.0000000038890968113"
            class="filter-input font-mono text-xs"
            @keydown.enter="buscar(1)"
          />
        </div>
      </div>

      <div class="filter-actions">
        <button @click="buscar(1)" class="btn-search">
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          Buscar
        </button>
        <button @click="limparFiltros" class="btn-clear">Limpar Filtros</button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="text-slate-400 mt-3">Buscando eventos...</p>
    </div>

    <div v-else-if="result" class="results-section">
      <!-- Results header -->
      <div class="results-header">
        <p class="text-sm text-slate-400">
          <span class="text-white font-semibold">{{ result.total.toLocaleString('pt-BR') }}</span>
          evento{{ result.total !== 1 ? 's' : '' }} encontrado{{ result.total !== 1 ? 's' : '' }}
          <span v-if="result.pages > 1" class="text-slate-500">
            &mdash; Página {{ result.page }} de {{ result.pages }}</span
          >
        </p>
      </div>

      <!-- Results table -->
      <div class="results-table-wrapper" v-if="result.eventos.length > 0">
        <table class="results-table">
          <thead>
            <tr>
              <th class="w-24">Evento</th>
              <th class="w-32">CPF</th>
              <th class="w-24">Período</th>
              <th>Detalhes</th>
              <th class="w-20 text-center">Rubricas</th>
              <th class="w-36">Processado</th>
              <th class="w-16 text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="evt in result.eventos"
              :key="evt.id"
              class="result-row"
              :class="{ 'result-row--expanded': expandedId === evt.id }"
              @click="toggleExpand(evt.id)"
            >
              <td>
                <span class="event-badge" :class="eventBadgeClass(evt.tipo_evento)">{{
                  evt.tipo_evento
                }}</span>
              </td>
              <td class="font-mono text-xs text-slate-300">
                {{ evt.cpf ? formatCpf(evt.cpf) : '—' }}
              </td>
              <td class="text-slate-300 text-sm">{{ evt.per_apur ?? '—' }}</td>
              <td class="text-xs text-slate-400 max-w-[300px] truncate">{{ eventSummary(evt) }}</td>
              <td class="text-center">
                <span v-if="evt.rubricas?.length > 0" class="rubrica-count">{{
                  evt.rubricas.length
                }}</span>
                <span v-else class="text-slate-600">—</span>
              </td>
              <td class="text-xs text-slate-500">{{ formatDateTime(evt.dt_processamento) }}</td>
              <td class="text-center">
                <span
                  v-if="evt.cd_resposta === '201'"
                  class="status-dot status-dot--ok"
                  title="Sucesso"
                ></span>
                <span
                  v-else-if="evt.cd_resposta"
                  class="status-dot status-dot--err"
                  :title="'Código: ' + evt.cd_resposta"
                ></span>
                <span v-else class="status-dot status-dot--none" title="Sem recibo"></span>
              </td>
            </tr>

            <!-- Expanded detail row -->
            <tr
              v-for="evt in result.eventos"
              :key="'detail-' + evt.id"
              v-show="expandedId === evt.id"
              class="detail-row"
            >
              <td colspan="7">
                <div class="detail-content">
                  <!-- Event metadata -->
                  <div class="detail-meta">
                    <div class="meta-item">
                      <span class="meta-label">ID Evento</span>
                      <span class="meta-value font-mono text-xs">{{ evt.id_evento ?? '—' }}</span>
                    </div>
                    <div class="meta-item">
                      <span class="meta-label">Nº Recibo</span>
                      <span class="meta-value font-mono text-xs">{{ evt.nr_recibo ?? '—' }}</span>
                    </div>
                    <div class="meta-item">
                      <span class="meta-label">Arquivo</span>
                      <span class="meta-value font-mono text-xs">{{ evt.arquivo_origem }}</span>
                    </div>
                    <div
                      v-if="evt.dados_json"
                      v-for="(val, key) in flatDadosJson(evt.dados_json)"
                      :key="key"
                      class="meta-item"
                    >
                      <span class="meta-label">{{ key }}</span>
                      <span class="meta-value text-xs">{{ val }}</span>
                    </div>
                  </div>

                  <!-- Rubricas table -->
                  <div v-if="evt.rubricas?.length > 0" class="rubricas-detail">
                    <h4 class="text-xs font-semibold text-[#5ac8f5] mb-2 uppercase tracking-wider">
                      Rubricas ({{ evt.rubricas.length }})
                    </h4>
                    <table class="rubricas-table">
                      <thead>
                        <tr>
                          <th>Código</th>
                          <th>Tab</th>
                          <th>Natureza</th>
                          <th>Tipo</th>
                          <th>Inc. CP</th>
                          <th>Inc. IRRF</th>
                          <th>Inc. FGTS</th>
                          <th>Valor</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(rub, ri) in evt.rubricas" :key="ri">
                          <td class="font-mono font-semibold text-white">{{ rub.cod_rubr }}</td>
                          <td class="text-slate-400">{{ rub.ide_tab_rubr ?? '—' }}</td>
                          <td class="text-slate-300">{{ rub.nat_rubr ?? '—' }}</td>
                          <td class="text-slate-400">{{ rub.tp_rubr ?? '—' }}</td>
                          <td class="text-slate-300">{{ rub.cod_inc_cp ?? '—' }}</td>
                          <td
                            :class="
                              rub.cod_inc_irrf === '11'
                                ? 'text-red-400 font-bold'
                                : 'text-slate-300'
                            "
                          >
                            {{ rub.cod_inc_irrf ?? '—' }}
                          </td>
                          <td class="text-slate-300">{{ rub.cod_inc_fgts ?? '—' }}</td>
                          <td class="font-mono text-emerald-400">
                            {{
                              rub.vr_rubr
                                ? Number(rub.vr_rubr).toLocaleString('pt-BR', {
                                    minimumFractionDigits: 2,
                                  })
                                : '—'
                            }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty state -->
      <div v-else class="empty-state">
        <svg
          class="w-16 h-16 text-slate-600 mx-auto mb-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <p class="text-slate-400">Nenhum evento encontrado com os filtros selecionados</p>
      </div>

      <!-- Pagination -->
      <div v-if="result.pages > 1" class="pagination">
        <button :disabled="result.page <= 1" @click="buscar(result.page - 1)" class="page-btn">
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <template v-for="p in visiblePages" :key="p">
          <button v-if="p === '...'" class="page-btn page-ellipsis" disabled>...</button>
          <button
            v-else
            @click="buscar(p as number)"
            :class="{ active: p === result.page }"
            class="page-btn"
          >
            {{ p }}
          </button>
        </template>
        <button
          :disabled="result.page >= result.pages"
          @click="buscar(result.page + 1)"
          class="page-btn"
        >
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Import modal -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showImport" class="modal-overlay" @click.self="showImport = false">
          <div class="modal-content">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-bold text-white">Importar Período</h2>
              <button
                @click="showImport = false"
                class="text-slate-400 hover:text-white transition-colors"
              >
                <svg
                  class="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div v-if="!importing && !importResult">
              <div class="mb-4">
                <label class="filter-label">Caminho da Pasta</label>
                <input
                  v-model="importPasta"
                  type="text"
                  placeholder="C:\Users\xandao\Downloads\28947360"
                  class="filter-input w-full"
                />
                <p class="text-xs text-slate-500 mt-1">
                  Cole o caminho completo da pasta com os XMLs baixados
                </p>
              </div>
              <div class="mb-6">
                <label class="filter-label">Período (opcional)</label>
                <input
                  v-model="importPeriodo"
                  type="text"
                  placeholder="2026-02"
                  class="filter-input w-full"
                  maxlength="7"
                />
                <p class="text-xs text-slate-500 mt-1">
                  Formato: AAAA-MM. Se não informar, será detectado dos XMLs
                </p>
              </div>
              <button
                @click="iniciarImport"
                :disabled="!importPasta.trim()"
                class="btn-search w-full justify-center"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                Iniciar Importação
              </button>
            </div>

            <!-- Importing progress -->
            <div v-if="importing" class="text-center py-8">
              <div class="loading-spinner mx-auto"></div>
              <p class="text-white mt-4 font-medium">Importando XMLs...</p>
              <div class="progress-bar-container mt-4">
                <div class="progress-bar" :style="{ width: importProgressPct + '%' }"></div>
              </div>
              <p class="text-2xl font-bold text-[var(--brain-blue)] mt-3">
                {{ importProgressPct }}%
              </p>
              <p class="text-sm text-slate-300 mt-1">{{ importProgressText }}</p>
              <div class="grid grid-cols-3 gap-3 mt-4 text-xs">
                <div>
                  <div class="text-slate-500">Importados</div>
                  <div class="text-emerald-400 font-mono font-bold">
                    {{ importProgressImported.toLocaleString('pt-BR') }}
                  </div>
                </div>
                <div>
                  <div class="text-slate-500">Erros</div>
                  <div class="text-red-400 font-mono font-bold">
                    {{ importProgressErrors.toLocaleString('pt-BR') }}
                  </div>
                </div>
                <div>
                  <div class="text-slate-500">Velocidade</div>
                  <div class="text-white font-mono font-bold">{{ importProgressRate }} arq/s</div>
                </div>
              </div>
              <p v-if="importProgressEta" class="text-xs text-slate-500 mt-2">
                Estimativa: {{ importProgressEta }}
              </p>
              <p
                v-if="importProgressLastError"
                class="text-xs text-red-400/70 mt-2 truncate max-w-md mx-auto"
                :title="importProgressLastError"
              >
                {{ importProgressLastError }}
              </p>
            </div>

            <!-- Import result -->
            <div v-if="importResult">
              <div
                class="import-result"
                :class="importResult.erros > 0 ? 'import-result--warn' : 'import-result--ok'"
              >
                <svg
                  v-if="importResult.erros === 0"
                  class="w-12 h-12 text-emerald-400 mx-auto mb-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
                <svg
                  v-else
                  class="w-12 h-12 text-amber-400 mx-auto mb-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                  />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <h3 class="text-lg font-bold text-white mb-2">Importação Concluída</h3>
                <div class="grid grid-cols-2 gap-3 text-sm mt-4">
                  <div class="text-slate-400">Arquivos processados</div>
                  <div class="text-white font-mono">
                    {{ importResult.total_arquivos.toLocaleString('pt-BR') }}
                  </div>
                  <div class="text-slate-400">Importados com sucesso</div>
                  <div class="text-emerald-400 font-mono">
                    {{ importResult.importados.toLocaleString('pt-BR') }}
                  </div>
                  <div class="text-slate-400">Erros</div>
                  <div
                    :class="importResult.erros > 0 ? 'text-red-400' : 'text-slate-500'"
                    class="font-mono"
                  >
                    {{ importResult.erros }}
                  </div>
                  <div class="text-slate-400">Tempo</div>
                  <div class="text-white font-mono">{{ importResult.tempo_seg }}s</div>
                </div>
              </div>
              <button @click="fecharImport" class="btn-search w-full justify-center mt-4">
                Fechar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Import History (bottom section) -->
    <div v-if="importacoes.length > 0" class="imports-section">
      <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
        Importações Realizadas
      </h3>
      <div class="imports-list">
        <div v-for="imp in importacoes" :key="imp.id" class="import-item">
          <div class="flex items-center gap-3 flex-1">
            <svg
              class="w-4 h-4 text-[#5ac8f5] shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
            </svg>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-white truncate">
                {{ imp.periodo ?? 'Sem período' }} &mdash;
                {{ imp.total_arquivos.toLocaleString('pt-BR') }} arquivos
              </p>
              <p class="text-xs text-slate-500 truncate">{{ imp.pasta }}</p>
            </div>
            <div class="text-right shrink-0">
              <p class="text-xs text-slate-400">
                {{ imp.total_eventos?.toLocaleString('pt-BR') }} eventos &bull;
                {{ imp.cpfs_unicos?.toLocaleString('pt-BR') }} CPFs
              </p>
              <p class="text-xs text-slate-500">{{ formatDateTime(imp.importado_em) }}</p>
            </div>
          </div>
          <button
            @click.stop="deletarImport(imp.id)"
            class="delete-import-btn"
            title="Remover importação"
          >
            <svg
              class="w-3.5 h-3.5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const API = 'http://localhost:8000/api/explorador'

// ── State ──
const stats = ref<any>(null)
const result = ref<any>(null)
const loading = ref(false)
const expandedId = ref<number | null>(null)
const importacoes = ref<any[]>([])

// Filters
const filters = ref({
  cpf: '',
  tipo_evento: '',
  per_apur: '',
  cod_rubr: '',
  cod_inc_irrf: '',
  nr_recibo: '',
})
const cpfSearch = ref('')
const cpfSuggestions = ref<any[]>([])
const cpfFocused = ref(false)
let cpfTimer: ReturnType<typeof setTimeout> | null = null

// Import
const showImport = ref(false)
const importing = ref(false)
const importResult = ref<any>(null)
const importPasta = ref('')
const importPeriodo = ref('')
const importProgressPct = ref(0)
const importProgressText = ref('')
const importProgressImported = ref(0)
const importProgressErrors = ref(0)
const importProgressRate = ref(0)
const importProgressEta = ref('')
const importProgressLastError = ref('')
let progressInterval: ReturnType<typeof setInterval> | null = null

const eventTypes = [
  'S-1010',
  'S-1020',
  'S-1200',
  'S-1210',
  'S-1298',
  'S-1299',
  'S-2200',
  'S-2205',
  'S-2206',
  'S-2210',
  'S-2220',
  'S-2230',
  'S-2240',
  'S-2299',
  'S-3000',
  'S-5001',
  'S-5002',
  'S-5003',
  'S-5011',
  'S-5012',
  'S-5013',
]

// ── Computed ──
const visiblePages = computed(() => {
  if (!result.value) return []
  const total = result.value.pages
  const current = result.value.page
  const pages: (number | string)[] = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
      pages.push(i)
    }
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }
  return pages
})

// ── Lifecycle ──
onMounted(async () => {
  await Promise.all([loadStats(), loadImportacoes()])
})

// ── API calls ──
async function loadStats() {
  try {
    const res = await fetch(`${API}/estatisticas`)
    if (res.ok) stats.value = await res.json()
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

async function loadImportacoes() {
  try {
    const res = await fetch(`${API}/importacoes`)
    if (res.ok) importacoes.value = await res.json()
  } catch (e) {
    console.error('Failed to load importacoes:', e)
  }
}

async function buscar(page: number = 1) {
  loading.value = true
  expandedId.value = null
  try {
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('page_size', '50')
    if (filters.value.cpf) params.set('cpf', filters.value.cpf)
    if (filters.value.tipo_evento) params.set('tipo_evento', filters.value.tipo_evento)
    if (filters.value.per_apur) params.set('per_apur', filters.value.per_apur)
    if (filters.value.cod_rubr) params.set('cod_rubr', filters.value.cod_rubr)
    if (filters.value.cod_inc_irrf) params.set('cod_inc_irrf', filters.value.cod_inc_irrf)
    if (filters.value.nr_recibo) params.set('nr_recibo', filters.value.nr_recibo)

    const res = await fetch(`${API}/eventos?${params}`)
    if (res.ok) result.value = await res.json()
  } catch (e) {
    console.error('Search error:', e)
  } finally {
    loading.value = false
  }
}

async function onCpfInput() {
  if (cpfTimer) clearTimeout(cpfTimer)
  const q = cpfSearch.value.replace(/\D/g, '')
  if (q.length < 3) {
    cpfSuggestions.value = []
    return
  }
  cpfTimer = setTimeout(async () => {
    try {
      const params = new URLSearchParams({ q, limit: '10' })
      if (filters.value.per_apur) params.set('per_apur', filters.value.per_apur)
      const res = await fetch(`${API}/cpfs?${params}`)
      if (res.ok) cpfSuggestions.value = await res.json()
    } catch (e) {
      cpfSuggestions.value = []
    }
  }, 300)
}

function selectCpf(cpf: string) {
  filters.value.cpf = cpf
  cpfSearch.value = formatCpf(cpf)
  cpfSuggestions.value = []
  buscar(1)
}

function applyCpf() {
  const clean = cpfSearch.value.replace(/\D/g, '')
  if (clean.length >= 3) {
    filters.value.cpf = clean
    cpfSuggestions.value = []
    buscar(1)
  }
}

function clearCpf() {
  filters.value.cpf = ''
  cpfSearch.value = ''
  cpfSuggestions.value = []
  buscar(1)
}

function onCpfBlur() {
  setTimeout(() => {
    cpfFocused.value = false
  }, 200)
}

function limparFiltros() {
  filters.value = {
    cpf: '',
    tipo_evento: '',
    per_apur: '',
    cod_rubr: '',
    cod_inc_irrf: '',
    nr_recibo: '',
  }
  cpfSearch.value = ''
  result.value = null
}

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

// Import
async function iniciarImport() {
  importing.value = true
  importResult.value = null
  importProgressPct.value = 0
  importProgressText.value = 'Iniciando...'
  importProgressImported.value = 0
  importProgressErrors.value = 0
  importProgressRate.value = 0
  importProgressEta.value = ''
  importProgressLastError.value = ''

  // Poll progress — also detects when import finishes
  progressInterval = setInterval(async () => {
    try {
      const res = await fetch(`${API}/progresso`)
      if (res.ok) {
        const prog = await res.json()
        if (prog.total > 0) {
          const pct = Math.round((prog.processed / prog.total) * 100)
          importProgressPct.value = pct
          importProgressText.value = `${prog.processed.toLocaleString('pt-BR')} / ${prog.total.toLocaleString('pt-BR')} arquivos`
          importProgressImported.value = prog.imported || 0
          importProgressErrors.value = prog.errors || 0
          importProgressRate.value = prog.rate || 0
          importProgressLastError.value = prog.last_error || ''
          // ETA
          if (prog.rate > 0) {
            const remaining = prog.total - prog.processed
            const etaSec = Math.round(remaining / prog.rate)
            if (etaSec < 60) {
              importProgressEta.value = `~${etaSec}s restantes`
            } else {
              importProgressEta.value = `~${Math.round(etaSec / 60)}min restantes`
            }
          }
        }
        // Check if background import finished
        if (prog.finished && !prog.running) {
          if (progressInterval) clearInterval(progressInterval)
          importing.value = false
          importProgressPct.value = 100
          if (prog.result) {
            importResult.value = prog.result
          } else {
            importResult.value = {
              total_arquivos: prog.total,
              importados: prog.imported || 0,
              erros: prog.errors || 0,
              tempo_seg: prog.elapsed || 0,
            }
          }
        }
      }
    } catch {
      /* ignore */
    }
  }, 800)

  try {
    const res = await fetch(`${API}/importar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pasta: importPasta.value, periodo: importPeriodo.value || null }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }))
      alert(err.detail || 'Erro na importação')
      importing.value = false
      if (progressInterval) clearInterval(progressInterval)
    }
    // If ok, the background thread is running — polling will detect completion
  } catch (e) {
    alert('Erro de conexão com o servidor')
    importing.value = false
    if (progressInterval) clearInterval(progressInterval)
  }
}

function fecharImport() {
  showImport.value = false
  importing.value = false
  importResult.value = null
  importPasta.value = ''
  importPeriodo.value = ''
  loadStats()
  loadImportacoes()
}

async function deletarImport(id: number) {
  if (!confirm('Remover esta importação e todos os seus eventos?')) return
  try {
    const res = await fetch(`${API}/importacoes/${id}`, { method: 'DELETE' })
    if (res.ok) {
      await Promise.all([loadStats(), loadImportacoes()])
      result.value = null
    }
  } catch (e) {
    alert('Erro ao remover')
  }
}

// ── Formatting helpers ──
function formatCpf(cpf: string): string {
  if (!cpf || cpf.length !== 11) return cpf ?? ''
  return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9)}`
}

function formatPeriodo(p: string): string {
  if (!p) return ''
  const parts = p.split('-')
  const year = parts[0] ?? p
  const month = parts[1] ?? ''
  const months = [
    '',
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
  ]
  return `${months[parseInt(month)] || month}/${year}`
}

function formatDateTime(dt: string | null): string {
  if (!dt) return '—'
  try {
    const d = new Date(dt)
    return (
      d.toLocaleDateString('pt-BR') +
      ' ' +
      d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
    )
  } catch {
    return dt
  }
}

function eventBadgeClass(tipo: string): string {
  const map: Record<string, string> = {
    'S-1010': 'badge--purple',
    'S-1200': 'badge--blue',
    'S-1210': 'badge--cyan',
    'S-5001': 'badge--green',
    'S-5002': 'badge--amber',
    'S-5003': 'badge--teal',
    'S-2299': 'badge--red',
    'S-3000': 'badge--red',
  }
  return map[tipo] ?? 'badge--slate'
}

function eventSummary(evt: any): string {
  const d = evt.dados_json
  if (!d) return evt.arquivo_origem ?? ''
  const parts: string[] = []
  if (d.operacao) parts.push(d.operacao)
  if (d.dscRubr) parts.push(d.dscRubr)
  if (d.matricula) parts.push(`Mat: ${d.matricula}`)
  if (d.codCateg) parts.push(`Cat: ${d.codCateg}`)
  if (d.dtPgto) parts.push(`Pgto: ${d.dtPgto}`)
  if (d.vrLiq)
    parts.push(`Líq: R$ ${Number(d.vrLiq).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`)
  if (d.cdResposta) parts.push(d.descResposta ?? `Resp: ${d.cdResposta}`)
  return parts.join(' \u2022 ') || (evt.arquivo_origem ?? '')
}

function flatDadosJson(dados: any): Record<string, string> {
  if (!dados) return {}
  const flat: Record<string, string> = {}
  for (const [key, val] of Object.entries(dados)) {
    if (typeof val === 'string' || typeof val === 'number') {
      flat[key] = String(val)
    }
  }
  return flat
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════
   Explorador de Eventos — Neural Glassmorphism Design
   ═══════════════════════════════════════════════════ */

.explorador-view {
  --brain-blue: #5ac8f5;
  --brain-glow: rgba(90, 200, 245, 0.55);
  --brain-dim: rgba(90, 200, 245, 0.25);
  --brain-faint: rgba(90, 200, 245, 0.08);
  --glass-bg: rgba(8, 14, 36, 0.75);
  --glass-border: rgba(90, 200, 245, 0.12);
  --surface-dark: #0a1024;
  max-width: 1200px;
}

/* ── Import Button ───────────────────────────────── */
.import-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--brain-blue);
  border: 1px solid rgba(90, 200, 245, 0.25);
  border-radius: 10px;
  background: rgba(90, 200, 245, 0.08);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: all 0.25s ease;
}

.import-btn:hover {
  background: rgba(90, 200, 245, 0.15);
  border-color: rgba(90, 200, 245, 0.4);
  box-shadow: 0 0 16px rgba(90, 200, 245, 0.15);
}

/* ── Stats Cards ─────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 14px;
  border: 1px solid var(--glass-border);
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-color: rgba(90, 200, 245, 0.22);
  box-shadow: 0 0 20px rgba(90, 200, 245, 0.06);
}

.stat-card--alert {
  border-color: rgba(239, 68, 68, 0.25) !important;
}

.stat-card--alert:hover {
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.1);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 22px;
  height: 22px;
}

.stat-icon--blue {
  background: rgba(0, 102, 255, 0.12);
  color: #4d9fff;
}
.stat-icon--cyan {
  background: rgba(90, 200, 245, 0.1);
  color: #5ac8f5;
}
.stat-icon--green {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
}
.stat-icon--red {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 2px;
}

/* ── Filter Card ─────────────────────────────────── */
.filter-card {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 20px 24px;
  border: 1px solid var(--glass-border);
  margin-bottom: 24px;
  box-shadow:
    0 0 20px rgba(90, 200, 245, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.3);
}

.filter-grid {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-group--wide {
  grid-column: span 1;
}

.filter-label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: rgba(90, 200, 245, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.filter-input,
.filter-select {
  width: 100%;
  padding: 8px 12px;
  background: var(--surface-dark);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  color: #fff;
  font-size: 0.8125rem;
  outline: none;
  transition:
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.filter-input:focus,
.filter-select:focus {
  border-color: var(--brain-blue);
  box-shadow: 0 0 12px rgba(90, 200, 245, 0.15);
}

.filter-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}

.filter-select option {
  background: #0a1024;
  color: #fff;
}

.filter-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 14px;
  border-top: 1px solid rgba(90, 200, 245, 0.08);
}

.btn-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 22px;
  background: rgba(90, 200, 245, 0.15);
  border: 1px solid rgba(90, 200, 245, 0.3);
  border-radius: 10px;
  color: var(--brain-blue);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}

.btn-search:hover {
  background: rgba(90, 200, 245, 0.25);
  box-shadow: 0 0 18px rgba(90, 200, 245, 0.2);
}

.btn-search:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-clear {
  padding: 8px 18px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #64748b;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.25s ease;
}

.btn-clear:hover {
  color: #94a3b8;
  border-color: rgba(255, 255, 255, 0.2);
}

/* ── CPF Autocomplete ────────────────────────────── */
.cpf-search-container {
  position: relative;
}

.cpf-clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  padding: 4px;
  color: #64748b;
  cursor: pointer;
  border: none;
  background: none;
  transition: color 0.2s;
}

.cpf-clear-btn:hover {
  color: #f87171;
}

.cpf-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: #111b3a;
  border: 1px solid rgba(90, 200, 245, 0.2);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  z-index: 50;
  max-height: 240px;
  overflow-y: auto;
}

.cpf-suggestion {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: none;
  color: #e2e8f0;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: background 0.15s;
  text-align: left;
}

.cpf-suggestion:hover {
  background: rgba(90, 200, 245, 0.08);
}

.cpf-suggestion:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

/* ── Results ─────────────────────────────────────── */
.loading-container {
  text-align: center;
  padding: 48px 0;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(90, 200, 245, 0.15);
  border-top-color: var(--brain-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.results-section {
  margin-bottom: 32px;
}

.results-header {
  margin-bottom: 12px;
}

.results-table-wrapper {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 14px;
  border: 1px solid var(--glass-border);
  overflow: hidden;
  box-shadow:
    0 0 20px rgba(90, 200, 245, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.3);
}

.results-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.results-table thead tr {
  border-bottom: 1px solid rgba(90, 200, 245, 0.1);
}

.results-table th {
  padding: 12px 14px;
  text-align: left;
  font-size: 0.6875rem;
  font-weight: 600;
  color: rgba(90, 200, 245, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(90, 200, 245, 0.1);
}

.results-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.result-row {
  cursor: pointer;
  transition: background 0.2s ease;
}

.result-row:hover {
  background: rgba(90, 200, 245, 0.03);
}

.result-row--expanded {
  background: rgba(90, 200, 245, 0.05) !important;
}

/* ── Event badges ────────────────────────────────── */
.event-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.6875rem;
  font-weight: 700;
  font-family: monospace;
  letter-spacing: 0.02em;
}

.badge--purple {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.25);
}
.badge--blue {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.25);
}
.badge--cyan {
  background: rgba(90, 200, 245, 0.12);
  color: #5ac8f5;
  border: 1px solid rgba(90, 200, 245, 0.2);
}
.badge--green {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.2);
}
.badge--amber {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.2);
}
.badge--teal {
  background: rgba(20, 184, 166, 0.12);
  color: #2dd4bf;
  border: 1px solid rgba(20, 184, 166, 0.2);
}
.badge--red {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
}
.badge--slate {
  background: rgba(100, 116, 139, 0.12);
  color: #94a3b8;
  border: 1px solid rgba(100, 116, 139, 0.2);
}

.rubrica-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 22px;
  padding: 0 6px;
  border-radius: 6px;
  font-size: 0.6875rem;
  font-weight: 700;
  background: rgba(90, 200, 245, 0.1);
  color: var(--brain-blue);
  border: 1px solid rgba(90, 200, 245, 0.15);
}

.status-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot--ok {
  background: #34d399;
  box-shadow: 0 0 6px rgba(52, 211, 153, 0.5);
}
.status-dot--err {
  background: #f87171;
  box-shadow: 0 0 6px rgba(248, 113, 113, 0.5);
}
.status-dot--none {
  background: #475569;
}

/* ── Detail row ──────────────────────────────────── */
.detail-row td {
  padding: 0 !important;
  border-bottom: 1px solid rgba(90, 200, 245, 0.08) !important;
}

.detail-content {
  padding: 16px 20px;
  background: rgba(90, 200, 245, 0.02);
}

.detail-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-size: 0.625rem;
  font-weight: 600;
  color: rgba(90, 200, 245, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.meta-value {
  color: #cbd5e1;
  word-break: break-all;
}

.rubricas-detail {
  border-top: 1px solid rgba(90, 200, 245, 0.08);
  padding-top: 14px;
}

.rubricas-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.rubricas-table th {
  padding: 6px 10px;
  font-size: 0.625rem;
  font-weight: 600;
  color: rgba(90, 200, 245, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: left;
  border-bottom: 1px solid rgba(90, 200, 245, 0.08);
}

.rubricas-table td {
  padding: 6px 10px;
  font-size: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

/* ── Empty state ─────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 48px 0;
}

/* ── Pagination ──────────────────────────────────── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 16px;
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  color: #fff;
  border-color: rgba(90, 200, 245, 0.2);
  background: rgba(90, 200, 245, 0.08);
}

.page-btn.active {
  color: var(--brain-blue);
  border-color: rgba(90, 200, 245, 0.3);
  background: rgba(90, 200, 245, 0.12);
  box-shadow: 0 0 10px rgba(90, 200, 245, 0.12);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-ellipsis {
  border: none !important;
  cursor: default !important;
}

/* ── Modal ───────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #0d1530;
  border: 1px solid rgba(90, 200, 245, 0.15);
  border-radius: 20px;
  padding: 28px;
  width: 100%;
  max-width: 520px;
  box-shadow:
    0 0 40px rgba(90, 200, 245, 0.08),
    0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-fade-enter-active {
  transition: all 0.25s ease;
}
.modal-fade-leave-active {
  transition: all 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* ── Progress bar ────────────────────────────────── */
.progress-bar-container {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: rgba(90, 200, 245, 0.1);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--brain-blue), #3b82f6);
  transition: width 0.5s ease;
  box-shadow: 0 0 8px rgba(90, 200, 245, 0.4);
}

/* ── Import Result ───────────────────────────────── */
.import-result {
  text-align: center;
  padding: 20px;
  border-radius: 14px;
  border: 1px solid;
}

.import-result--ok {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
}

.import-result--warn {
  background: rgba(245, 158, 11, 0.05);
  border-color: rgba(245, 158, 11, 0.2);
}

/* ── Imports History ─────────────────────────────── */
.imports-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(90, 200, 245, 0.08);
}

.imports-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.import-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.import-item:hover {
  border-color: rgba(90, 200, 245, 0.2);
}

.delete-import-btn {
  padding: 6px;
  color: #64748b;
  border: 1px solid transparent;
  border-radius: 6px;
  background: none;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.delete-import-btn:hover {
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.2);
}
</style>
