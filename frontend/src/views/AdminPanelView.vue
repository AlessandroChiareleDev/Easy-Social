<template>
  <div class="min-h-screen relative overflow-hidden admin-bg">
    <!-- Background shapes -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
    </div>

    <!-- Top bar -->
    <div class="relative z-10 flex items-center justify-between px-8 pt-6">
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/')"
          class="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Voltar
        </button>
      </div>
      <h1 class="text-white/90 font-semibold text-lg">
        Painel <span class="text-[#0066FF]">Admin</span>
      </h1>
      <div class="text-white/40 text-xs">{{ authStore.user?.username }}</div>
    </div>

    <!-- Content -->
    <div class="relative z-10 px-8 mt-6 pb-16 max-w-7xl mx-auto">
      <!-- Filters bar -->
      <div class="glass-card p-4 mb-6 flex flex-wrap items-center gap-4">
        <label class="text-white/60 text-sm">Período:</label>
        <select v-model="periodoSelecionado" @change="loadData" class="glass-input text-sm">
          <option value="hoje">Hoje</option>
          <option value="7d">Últimos 7 dias</option>
          <option value="30d">Últimos 30 dias</option>
          <option value="90d">Últimos 90 dias</option>
          <option value="todos">Todos (retroativo)</option>
        </select>

        <label class="text-white/60 text-sm ml-4">Usuário:</label>
        <select v-model="filtroUsuarioId" @change="onFiltroUsuarioChange" class="glass-input text-sm">
          <option :value="null">Todos</option>
          <option v-for="op in resumoOperadores" :key="op.usuario_id" :value="op.usuario_id">
            {{ op.username }}
          </option>
        </select>

        <button @click="loadData" class="btn-primary text-sm">Atualizar</button>
        <div v-if="loading" class="text-[#0066FF] text-sm animate-pulse">Carregando...</div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 mb-6">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id; loadTabData()"
          :class="[
            'px-5 py-2.5 rounded-t-lg text-sm font-medium transition-all',
            activeTab === tab.id
              ? 'bg-white/10 text-white border-b-2 border-[#0066FF]'
              : 'text-white/40 hover:text-white/70 hover:bg-white/5',
          ]"
        >
          {{ tab.label }}
          <span v-if="tab.count !== undefined" class="ml-1.5 text-xs bg-white/10 px-1.5 py-0.5 rounded-full">
            {{ tab.count }}
          </span>
        </button>
      </div>

      <!-- Summary cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="glass-card p-5 text-center">
          <div class="text-3xl font-bold text-white">{{ totalAcoes }}</div>
          <div class="text-white/50 text-sm mt-1">Total de Ações</div>
        </div>
        <div class="glass-card p-5 text-center">
          <div class="text-3xl font-bold text-[#0066FF]">{{ totalUsuarios }}</div>
          <div class="text-white/50 text-sm mt-1">Operadores Ativos</div>
        </div>
        <div class="glass-card p-5 text-center">
          <div class="text-3xl font-bold text-green-400">{{ totalEnvios }}</div>
          <div class="text-white/50 text-sm mt-1">Envios eSocial</div>
        </div>
        <div class="glass-card p-5 text-center">
          <div class="text-3xl font-bold text-amber-400">{{ totalPipelines }}</div>
          <div class="text-white/50 text-sm mt-1">Pipelines Correção</div>
        </div>
      </div>

      <!-- ═══════════ TAB: ATIVIDADES ═══════════ -->
      <template v-if="activeTab === 'atividades'">
        <!-- Operator summary table -->
        <div class="glass-card p-5 mb-6">
          <h2 class="text-white/90 font-semibold mb-4 flex items-center gap-2">
            <svg class="w-5 h-5 text-[#0066FF]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            Atividade por Operador
          </h2>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-white/50 border-b border-white/10">
                  <th class="text-left py-2 px-3">Operador</th>
                  <th class="text-right py-2 px-3">Total</th>
                  <th class="text-right py-2 px-3">GETs</th>
                  <th class="text-right py-2 px-3">POSTs</th>
                  <th class="text-right py-2 px-3">Erros</th>
                  <th class="text-right py-2 px-3">Tempo Médio</th>
                  <th class="text-right py-2 px-3">Dias Ativos</th>
                  <th class="text-left py-2 px-3">Último Acesso</th>
                  <th class="text-left py-2 px-3">IPs</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="op in resumoOperadores"
                  :key="op.usuario_id"
                  class="text-white/80 border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                  :class="{ 'bg-[#0066FF]/10': filtroUsuarioId === op.usuario_id }"
                  @click="filtrarPorUsuario(op.usuario_id)"
                >
                  <td class="py-2 px-3 font-medium">{{ op.username }}</td>
                  <td class="py-2 px-3 text-right">{{ op.total_acoes }}</td>
                  <td class="py-2 px-3 text-right text-blue-300">{{ op.gets }}</td>
                  <td class="py-2 px-3 text-right text-green-300">{{ op.posts }}</td>
                  <td class="py-2 px-3 text-right" :class="op.erros > 0 ? 'text-red-400' : 'text-white/40'">
                    {{ op.erros }}
                  </td>
                  <td class="py-2 px-3 text-right">{{ op.duracao_media_ms }}ms</td>
                  <td class="py-2 px-3 text-right">{{ op.dias_ativos }}</td>
                  <td class="py-2 px-3 text-white/50">{{ formatDate(op.ultimo_acesso) }}</td>
                  <td class="py-2 px-3 text-white/40 text-xs">{{ (op.ips || []).join(', ') }}</td>
                </tr>
                <tr v-if="resumoOperadores.length === 0">
                  <td colspan="9" class="text-center py-8 text-white/30">Nenhuma atividade registrada</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Popular routes -->
        <div class="glass-card p-5 mb-6">
          <h2 class="text-white/90 font-semibold mb-4 flex items-center gap-2">
            <svg class="w-5 h-5 text-[#0066FF]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
            Rotas Mais Acessadas
          </h2>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-white/50 border-b border-white/10">
                  <th class="text-left py-2 px-3">Método</th>
                  <th class="text-left py-2 px-3">Rota</th>
                  <th class="text-right py-2 px-3">Total</th>
                  <th class="text-right py-2 px-3">Tempo Médio</th>
                  <th class="text-right py-2 px-3">Erros</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, i) in rotasPopulares" :key="i" class="text-white/80 border-b border-white/5">
                  <td class="py-2 px-3">
                    <span :class="methodClass(r.metodo)" class="px-2 py-0.5 rounded text-xs font-mono">{{ r.metodo }}</span>
                  </td>
                  <td class="py-2 px-3 font-mono text-xs">{{ r.rota }}</td>
                  <td class="py-2 px-3 text-right">{{ r.total }}</td>
                  <td class="py-2 px-3 text-right">{{ r.duracao_media_ms }}ms</td>
                  <td class="py-2 px-3 text-right" :class="r.erros > 0 ? 'text-red-400' : 'text-white/40'">{{ r.erros }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Activity log -->
        <div class="glass-card p-5">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-white/90 font-semibold flex items-center gap-2">
              <svg class="w-5 h-5 text-[#0066FF]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              Log de Atividades
              <span v-if="filtroUsuarioId" class="text-xs bg-[#0066FF]/20 text-[#0066FF] px-2 py-0.5 rounded-full">
                {{ filtroUsuarioNome }}
                <button @click="limparFiltroUsuario" class="ml-1 hover:text-white">✕</button>
              </span>
            </h2>
            <div class="text-white/40 text-xs">{{ totalAtividades }} registros</div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-white/50 border-b border-white/10">
                  <th class="text-left py-2 px-3">Quando</th>
                  <th class="text-left py-2 px-3">Operador</th>
                  <th class="text-left py-2 px-3">Método</th>
                  <th class="text-left py-2 px-3">Rota</th>
                  <th class="text-right py-2 px-3">Status</th>
                  <th class="text-right py-2 px-3">Tempo</th>
                  <th class="text-left py-2 px-3">IP</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="a in atividades"
                  :key="a.id"
                  class="text-white/70 border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td class="py-2 px-3 text-xs text-white/50">{{ formatDateTime(a.criado_em) }}</td>
                  <td class="py-2 px-3 font-medium text-white/80">{{ a.username }}</td>
                  <td class="py-2 px-3">
                    <span :class="methodClass(a.metodo)" class="px-2 py-0.5 rounded text-xs font-mono">{{ a.metodo }}</span>
                  </td>
                  <td class="py-2 px-3 font-mono text-xs max-w-xs truncate">{{ a.rota }}</td>
                  <td class="py-2 px-3 text-right" :class="statusClass(a.status_code)">{{ a.status_code }}</td>
                  <td class="py-2 px-3 text-right">{{ a.duracao_ms }}ms</td>
                  <td class="py-2 px-3 text-white/40 text-xs">{{ a.ip }}</td>
                </tr>
                <tr v-if="atividades.length === 0">
                  <td colspan="7" class="text-center py-8 text-white/30">Nenhuma atividade encontrada</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div v-if="totalAtividades > pageSize" class="flex items-center justify-center gap-4 mt-4">
            <button @click="paginaAnterior" :disabled="currentPage === 0" class="btn-secondary text-sm" :class="{ 'opacity-30 cursor-not-allowed': currentPage === 0 }">← Anterior</button>
            <span class="text-white/50 text-sm">Página {{ currentPage + 1 }} de {{ totalPages }}</span>
            <button @click="proximaPagina" :disabled="currentPage >= totalPages - 1" class="btn-secondary text-sm" :class="{ 'opacity-30 cursor-not-allowed': currentPage >= totalPages - 1 }">Próxima →</button>
          </div>
        </div>
      </template>

      <!-- ═══════════ TAB: ENVIOS ESOCIAL ═══════════ -->
      <template v-if="activeTab === 'envios'">
        <!-- Envios summary cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6" v-if="enviosResumo">
          <div class="glass-card p-4 text-center" v-for="s in enviosResumo.por_status" :key="s.status">
            <div class="text-2xl font-bold" :class="envioStatusColor(s.status)">{{ s.total }}</div>
            <div class="text-white/50 text-xs mt-1">{{ s.status || 'sem status' }}</div>
          </div>
        </div>

        <!-- Envios filters -->
        <div class="glass-card p-4 mb-6 flex flex-wrap items-center gap-4">
          <label class="text-white/60 text-sm">Tipo:</label>
          <select v-model="envioFiltroTipo" @change="loadEnvios" class="glass-input text-sm">
            <option value="">Todos</option>
            <option value="S-1010">S-1010</option>
            <option value="S-1200">S-1200</option>
            <option value="S-1210">S-1210</option>
            <option value="S-1298">S-1298</option>
            <option value="S-1299">S-1299</option>
          </select>
          <label class="text-white/60 text-sm">Ambiente:</label>
          <select v-model="envioFiltroAmbiente" @change="loadEnvios" class="glass-input text-sm">
            <option value="">Todos</option>
            <option value="1">Produção</option>
            <option value="2">Homologação</option>
          </select>
          <label class="text-white/60 text-sm">Status:</label>
          <select v-model="envioFiltroStatus" @change="loadEnvios" class="glass-input text-sm">
            <option value="">Todos</option>
            <option value="enviado">Enviado</option>
            <option value="processado">Processado</option>
            <option value="erro">Erro</option>
          </select>
        </div>

        <!-- Envios table -->
        <div class="glass-card p-5">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-white/90 font-semibold flex items-center gap-2">
              <svg class="w-5 h-5 text-[#0066FF]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
              Envios ao eSocial
            </h2>
            <div class="text-white/40 text-xs">{{ totalEnviosPage }} registros</div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-white/50 border-b border-white/10">
                  <th class="text-left py-2 px-3">Data</th>
                  <th class="text-left py-2 px-3">Tipo</th>
                  <th class="text-left py-2 px-3">Modo</th>
                  <th class="text-center py-2 px-3">Amb.</th>
                  <th class="text-left py-2 px-3">Status</th>
                  <th class="text-left py-2 px-3">iniValid</th>
                  <th class="text-right py-2 px-3">Qtd</th>
                  <th class="text-left py-2 px-3">Protocolo</th>
                  <th class="text-left py-2 px-3">nrRecibo</th>
                  <th class="text-left py-2 px-3">Resposta</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="e in envios"
                  :key="e.id"
                  class="text-white/70 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
                  @click="envioExpandido === e.id ? envioExpandido = null : envioExpandido = e.id"
                >
                  <td class="py-2 px-3 text-xs text-white/50">{{ formatDateTime(e.created_at) }}</td>
                  <td class="py-2 px-3 font-mono font-medium text-[#0066FF]">{{ e.tipo_evento }}</td>
                  <td class="py-2 px-3">
                    <span :class="e.modo === 'inclusao' ? 'text-green-400' : 'text-amber-400'" class="text-xs">
                      {{ e.modo }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span :class="e.ambiente === '1' ? 'bg-red-500/20 text-red-300' : 'bg-blue-500/20 text-blue-300'" class="px-2 py-0.5 rounded text-xs font-mono">
                      {{ e.ambiente === '1' ? 'PROD' : 'HOM' }}
                    </span>
                  </td>
                  <td class="py-2 px-3">
                    <span :class="envioStatusClass(e.status)" class="px-2 py-0.5 rounded text-xs">
                      {{ e.status }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-xs font-mono">{{ e.ini_valid || '-' }}</td>
                  <td class="py-2 px-3 text-right">{{ e.total_eventos || '-' }}</td>
                  <td class="py-2 px-3 font-mono text-xs text-white/40 max-w-[120px] truncate">{{ e.protocolo_envio || '-' }}</td>
                  <td class="py-2 px-3 font-mono text-xs max-w-[120px] truncate" :class="e.nr_recibo ? 'text-green-400' : 'text-white/30'">
                    {{ e.nr_recibo || 'pendente' }}
                  </td>
                  <td class="py-2 px-3 text-xs max-w-[200px] truncate" :class="e.codigo_resposta === '201' ? 'text-green-400' : e.codigo_resposta ? 'text-amber-400' : 'text-white/40'">
                    {{ e.codigo_resposta ? `[${e.codigo_resposta}] ` : '' }}{{ e.descricao_resposta || '-' }}
                  </td>
                </tr>
                <tr v-if="envios.length === 0">
                  <td colspan="10" class="text-center py-8 text-white/30">Nenhum envio encontrado</td>
                </tr>
              </tbody>
            </table>

            <!-- Expanded envio details -->
            <div v-if="envioExpandido" class="mt-4 p-4 bg-white/5 rounded-lg border border-white/10">
              <div v-for="e in envios.filter(x => x.id === envioExpandido)" :key="'detail-' + e.id">
                <h3 class="text-white/80 font-semibold mb-3">Detalhes do Envio #{{ e.id }}</h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                  <div><span class="text-white/40">Protocolo:</span> <span class="text-white/80 font-mono">{{ e.protocolo_envio || '-' }}</span></div>
                  <div><span class="text-white/40">nrRecibo:</span> <span class="text-green-400 font-mono">{{ e.nr_recibo || '-' }}</span></div>
                  <div><span class="text-white/40">Código Resp:</span> <span class="text-white/80">{{ e.codigo_resposta || '-' }}</span></div>
                  <div class="col-span-2 md:col-span-3"><span class="text-white/40">Descrição:</span> <span class="text-white/70">{{ e.descricao_resposta || '-' }}</span></div>
                  <div><span class="text-white/40">Criado:</span> <span class="text-white/70">{{ formatDateTimeFull(e.created_at) }}</span></div>
                  <div><span class="text-white/40">Atualizado:</span> <span class="text-white/70">{{ formatDateTimeFull(e.updated_at) }}</span></div>
                </div>
                <div v-if="e.rubrica_detalhes && e.rubrica_detalhes.length > 0" class="mt-3">
                  <h4 class="text-white/60 text-xs mb-2">Rubricas enviadas ({{ e.rubrica_detalhes.length }}):</h4>
                  <div class="flex flex-wrap gap-1">
                    <span v-for="(rb, ri) in e.rubrica_detalhes.slice(0, 20)" :key="ri" class="bg-white/10 px-2 py-0.5 rounded text-xs text-white/70 font-mono">
                      {{ rb.cod_rubrica || rb.codRubr || rb }}
                    </span>
                    <span v-if="e.rubrica_detalhes.length > 20" class="text-white/40 text-xs">+{{ e.rubrica_detalhes.length - 20 }} mais</span>
                  </div>
                </div>
                <div v-if="e.ocorrencias && (Array.isArray(e.ocorrencias) ? e.ocorrencias.length > 0 : true)" class="mt-3">
                  <h4 class="text-amber-400 text-xs mb-2">Ocorrências:</h4>
                  <pre class="text-xs text-white/60 bg-black/30 p-2 rounded overflow-x-auto max-h-40">{{ JSON.stringify(e.ocorrencias, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>

          <!-- Pagination envios -->
          <div v-if="totalEnviosPage > pageSize" class="flex items-center justify-center gap-4 mt-4">
            <button @click="envioPage > 0 && (envioPage--, loadEnvios())" :disabled="envioPage === 0" class="btn-secondary text-sm" :class="{ 'opacity-30 cursor-not-allowed': envioPage === 0 }">← Anterior</button>
            <span class="text-white/50 text-sm">Página {{ envioPage + 1 }} de {{ envioTotalPages }}</span>
            <button @click="envioPage < envioTotalPages - 1 && (envioPage++, loadEnvios())" :disabled="envioPage >= envioTotalPages - 1" class="btn-secondary text-sm" :class="{ 'opacity-30 cursor-not-allowed': envioPage >= envioTotalPages - 1 }">Próxima →</button>
          </div>
        </div>
      </template>

      <!-- ═══════════ TAB: PIPELINE CORREÇÃO ═══════════ -->
      <template v-if="activeTab === 'pipeline'">
        <!-- Pipeline filters -->
        <div class="glass-card p-4 mb-6 flex flex-wrap items-center gap-4">
          <label class="text-white/60 text-sm">CPF:</label>
          <input v-model="pipelineFiltoCpf" @change="loadPipelines" class="glass-input text-sm w-36" placeholder="CPF..." />
          <label class="text-white/60 text-sm">Status:</label>
          <select v-model="pipelineFiltroStatus" @change="loadPipelines" class="glass-input text-sm">
            <option value="">Todos</option>
            <option value="completo">Completo</option>
            <option value="em_andamento">Em andamento</option>
            <option value="erro">Erro</option>
            <option value="parcial">Parcial</option>
          </select>
          <label class="text-white/60 text-sm">Ambiente:</label>
          <select v-model="pipelineFiltroAmbiente" @change="loadPipelines" class="glass-input text-sm">
            <option value="">Todos</option>
            <option value="1">Produção</option>
            <option value="2">Homologação</option>
          </select>
        </div>

        <!-- Pipeline table -->
        <div class="glass-card p-5">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-white/90 font-semibold flex items-center gap-2">
              <svg class="w-5 h-5 text-[#0066FF]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="16 3 21 3 21 8" /><line x1="4" y1="20" x2="21" y2="3" />
                <polyline points="21 16 21 21 16 21" /><line x1="15" y1="15" x2="21" y2="21" />
                <line x1="4" y1="4" x2="9" y2="9" />
              </svg>
              Pipeline de Correção
            </h2>
            <div class="text-white/40 text-xs">{{ totalPipelinesPage }} registros</div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-white/50 border-b border-white/10">
                  <th class="text-left py-2 px-3">Data</th>
                  <th class="text-left py-2 px-3">CPF</th>
                  <th class="text-left py-2 px-3">Período</th>
                  <th class="text-center py-2 px-3">Amb.</th>
                  <th class="text-left py-2 px-3">Status</th>
                  <th class="text-center py-2 px-3">Step</th>
                  <th class="text-center py-2 px-3">S-1010</th>
                  <th class="text-center py-2 px-3">S-1298</th>
                  <th class="text-center py-2 px-3">S-1200</th>
                  <th class="text-center py-2 px-3">S-1210</th>
                  <th class="text-center py-2 px-3">S-1299</th>
                  <th class="text-left py-2 px-3">Erro</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="p in pipelines"
                  :key="p.id"
                  class="text-white/70 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
                  @click="pipelineExpandido === p.id ? pipelineExpandido = null : pipelineExpandido = p.id"
                >
                  <td class="py-2 px-3 text-xs text-white/50">{{ formatDateTime(p.created_at) }}</td>
                  <td class="py-2 px-3 font-mono text-white/80">{{ formatCpf(p.cpf) }}</td>
                  <td class="py-2 px-3 font-mono text-xs">{{ p.per_apur }}</td>
                  <td class="py-2 px-3 text-center">
                    <span :class="p.ambiente === '1' ? 'bg-red-500/20 text-red-300' : 'bg-blue-500/20 text-blue-300'" class="px-2 py-0.5 rounded text-xs font-mono">
                      {{ p.ambiente === '1' ? 'PROD' : 'HOM' }}
                    </span>
                  </td>
                  <td class="py-2 px-3">
                    <span :class="pipelineStatusClass(p.status)" class="px-2 py-0.5 rounded text-xs">{{ p.status }}</span>
                  </td>
                  <td class="py-2 px-3 text-center font-mono">{{ p.step_atual }}/5</td>
                  <td class="py-2 px-3 text-center">
                    <span :class="p.s1010_nr_recibo ? 'text-green-400' : 'text-white/20'" class="text-xs">{{ p.s1010_nr_recibo ? '✓' : '·' }}</span>
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span :class="p.s1298_nr_recibo ? 'text-green-400' : 'text-white/20'" class="text-xs">{{ p.s1298_nr_recibo ? '✓' : '·' }}</span>
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span :class="p.s1200_nr_recibo ? 'text-green-400' : 'text-white/20'" class="text-xs">{{ p.s1200_nr_recibo ? '✓' : '·' }}</span>
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span :class="p.s1210_nr_recibo ? 'text-green-400' : 'text-white/20'" class="text-xs">{{ p.s1210_nr_recibo ? '✓' : '·' }}</span>
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span :class="p.s1299_nr_recibo ? 'text-green-400' : 'text-white/20'" class="text-xs">{{ p.s1299_nr_recibo ? '✓' : '·' }}</span>
                  </td>
                  <td class="py-2 px-3 text-xs text-red-400 max-w-[200px] truncate">{{ p.erro || '' }}</td>
                </tr>
                <tr v-if="pipelines.length === 0">
                  <td colspan="12" class="text-center py-8 text-white/30">Nenhum pipeline encontrado</td>
                </tr>
              </tbody>
            </table>

            <!-- Expanded pipeline details -->
            <div v-if="pipelineExpandido" class="mt-4 p-4 bg-white/5 rounded-lg border border-white/10">
              <div v-for="p in pipelines.filter(x => x.id === pipelineExpandido)" :key="'pdetail-' + p.id">
                <h3 class="text-white/80 font-semibold mb-3">Pipeline #{{ p.id }} — {{ formatCpf(p.cpf) }} — {{ p.per_apur }}</h3>
                <div class="grid grid-cols-1 md:grid-cols-5 gap-3 mb-3">
                  <div v-for="step in ['s1010','s1298','s1200','s1210','s1299']" :key="step" class="bg-white/5 rounded-lg p-3">
                    <div class="text-xs text-white/40 mb-1">{{ step.toUpperCase().replace('S', 'S-') }}</div>
                    <div class="text-xs">
                      <div class="text-white/60">Prot: <span class="font-mono text-white/80">{{ p[step + '_protocolo'] || '-' }}</span></div>
                      <div :class="p[step + '_nr_recibo'] ? 'text-green-400' : 'text-white/30'">
                        Recibo: <span class="font-mono">{{ p[step + '_nr_recibo'] || 'pendente' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-if="p.steps_log && p.steps_log.length > 0">
                  <h4 class="text-white/60 text-xs mb-2">Steps Log:</h4>
                  <pre class="text-xs text-white/60 bg-black/30 p-2 rounded overflow-x-auto max-h-60">{{ JSON.stringify(p.steps_log, null, 2) }}</pre>
                </div>
                <div v-if="p.erro" class="mt-2">
                  <h4 class="text-red-400 text-xs mb-1">Erro:</h4>
                  <pre class="text-xs text-red-300 bg-red-900/20 p-2 rounded overflow-x-auto">{{ p.erro }}</pre>
                </div>
                <div class="text-xs text-white/40 mt-2">
                  Criado: {{ formatDateTimeFull(p.created_at) }} | Atualizado: {{ formatDateTimeFull(p.updated_at) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Pagination pipelines -->
          <div v-if="totalPipelinesPage > pageSize" class="flex items-center justify-center gap-4 mt-4">
            <button @click="pipelinePage > 0 && (pipelinePage--, loadPipelines())" :disabled="pipelinePage === 0" class="btn-secondary text-sm" :class="{ 'opacity-30 cursor-not-allowed': pipelinePage === 0 }">← Anterior</button>
            <span class="text-white/50 text-sm">Página {{ pipelinePage + 1 }} de {{ pipelineTotalPages }}</span>
            <button @click="pipelinePage < pipelineTotalPages - 1 && (pipelinePage++, loadPipelines())" :disabled="pipelinePage >= pipelineTotalPages - 1" class="btn-secondary text-sm" :class="{ 'opacity-30 cursor-not-allowed': pipelinePage >= pipelineTotalPages - 1 }">Próxima →</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import { API_URL } from '@/lib/api'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const periodoSelecionado = ref('todos')
const activeTab = ref('atividades')

// ── Tabs ─────────────────────────────────────────
const tabs = computed(() => [
  { id: 'atividades', label: 'Atividades', count: totalAcoes.value },
  { id: 'envios', label: 'Envios eSocial', count: totalEnvios.value },
  { id: 'pipeline', label: 'Pipeline Correção', count: totalPipelines.value },
])

// ── Atividades data ──────────────────────────────
const resumoOperadores = ref<any[]>([])
const rotasPopulares = ref<any[]>([])
const atividades = ref<any[]>([])
const totalAtividades = ref(0)
const filtroUsuarioId = ref<number | null>(null)
const filtroUsuarioNome = ref('')
const currentPage = ref(0)
const pageSize = 50

// ── Envios data ──────────────────────────────────
const envios = ref<any[]>([])
const enviosResumo = ref<any>(null)
const totalEnviosPage = ref(0)
const envioPage = ref(0)
const envioExpandido = ref<number | null>(null)
const envioFiltroTipo = ref('')
const envioFiltroAmbiente = ref('')
const envioFiltroStatus = ref('')

// ── Pipeline data ────────────────────────────────
const pipelines = ref<any[]>([])
const totalPipelinesPage = ref(0)
const pipelinePage = ref(0)
const pipelineExpandido = ref<number | null>(null)
const pipelineFiltoCpf = ref('')
const pipelineFiltroStatus = ref('')
const pipelineFiltroAmbiente = ref('')

// ── Computed ─────────────────────────────────────
const totalAcoes = computed(() =>
  resumoOperadores.value.reduce((sum, op) => sum + parseInt(op.total_acoes || 0), 0),
)
const totalUsuarios = computed(() => resumoOperadores.value.length)
const totalEnvios = computed(() => enviosResumo.value?.total || 0)
const totalPipelines = computed(() => totalPipelinesPage.value)
const totalPages = computed(() => Math.ceil(totalAtividades.value / pageSize))
const envioTotalPages = computed(() => Math.ceil(totalEnviosPage.value / pageSize))
const pipelineTotalPages = computed(() => Math.ceil(totalPipelinesPage.value / pageSize))

// ── Period helper ────────────────────────────────
function getPeriodDates() {
  const now = new Date()
  let desde: string | undefined
  switch (periodoSelecionado.value) {
    case 'hoje':
      desde = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString()
      break
    case '7d':
      desde = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString()
      break
    case '30d':
      desde = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString()
      break
    case '90d':
      desde = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString()
      break
    default:
      desde = undefined
  }
  return { desde }
}

// ── Load all data ────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const { desde } = getPeriodDates()
    const params: any = {}
    if (desde) params.desde = desde

    const [resumoRes, rotasRes, enviosResumoRes] = await Promise.all([
      axios.get(`${API_URL}/admin/atividades/resumo`, { params }),
      axios.get(`${API_URL}/admin/atividades/rotas-populares`, { params }),
      axios.get(`${API_URL}/admin/envios/resumo`).catch(() => ({ data: { resumo: { total: 0 } } })),
    ])

    resumoOperadores.value = resumoRes.data.resumo || []
    rotasPopulares.value = rotasRes.data.rotas || []
    enviosResumo.value = enviosResumoRes.data.resumo || { total: 0 }

    await loadTabData()
  } catch (err: any) {
    console.error('Erro ao carregar dados admin:', err)
  } finally {
    loading.value = false
  }
}

async function loadTabData() {
  if (activeTab.value === 'atividades') await loadAtividades()
  else if (activeTab.value === 'envios') await loadEnvios()
  else if (activeTab.value === 'pipeline') await loadPipelines()
}

// ── Atividades ───────────────────────────────────
async function loadAtividades() {
  const { desde } = getPeriodDates()
  const params: any = { limit: pageSize, offset: currentPage.value * pageSize }
  if (desde) params.desde = desde
  if (filtroUsuarioId.value) params.usuario_id = filtroUsuarioId.value

  const res = await axios.get(`${API_URL}/admin/atividades`, { params })
  atividades.value = res.data.atividades || []
  totalAtividades.value = res.data.total || 0
}

// ── Envios eSocial ───────────────────────────────
async function loadEnvios() {
  const { desde } = getPeriodDates()
  const params: any = { limit: pageSize, offset: envioPage.value * pageSize }
  if (desde) params.desde = desde
  if (envioFiltroTipo.value) params.tipo_evento = envioFiltroTipo.value
  if (envioFiltroAmbiente.value) params.ambiente = envioFiltroAmbiente.value
  if (envioFiltroStatus.value) params.status = envioFiltroStatus.value

  try {
    const res = await axios.get(`${API_URL}/admin/envios`, { params })
    envios.value = res.data.envios || []
    totalEnviosPage.value = res.data.total || 0
  } catch {
    envios.value = []
    totalEnviosPage.value = 0
  }
}

// ── Pipelines ────────────────────────────────────
async function loadPipelines() {
  const { desde } = getPeriodDates()
  const params: any = { limit: pageSize, offset: pipelinePage.value * pageSize }
  if (desde) params.desde = desde
  if (pipelineFiltoCpf.value) params.cpf = pipelineFiltoCpf.value.replace(/\D/g, '')
  if (pipelineFiltroStatus.value) params.status = pipelineFiltroStatus.value
  if (pipelineFiltroAmbiente.value) params.ambiente = pipelineFiltroAmbiente.value

  try {
    const res = await axios.get(`${API_URL}/admin/pipelines`, { params })
    pipelines.value = res.data.pipelines || []
    totalPipelinesPage.value = res.data.total || 0
  } catch {
    pipelines.value = []
    totalPipelinesPage.value = 0
  }
}

// ── User filter ──────────────────────────────────
function filtrarPorUsuario(id: number) {
  const op = resumoOperadores.value.find((o) => o.usuario_id === id)
  filtroUsuarioId.value = id
  filtroUsuarioNome.value = op?.username || `#${id}`
  currentPage.value = 0
  loadAtividades()
}

function onFiltroUsuarioChange() {
  const op = resumoOperadores.value.find((o) => o.usuario_id === filtroUsuarioId.value)
  filtroUsuarioNome.value = op?.username || ''
  currentPage.value = 0
  loadAtividades()
}

function limparFiltroUsuario() {
  filtroUsuarioId.value = null
  filtroUsuarioNome.value = ''
  currentPage.value = 0
  loadAtividades()
}

function paginaAnterior() {
  if (currentPage.value > 0) { currentPage.value--; loadAtividades() }
}
function proximaPagina() {
  if (currentPage.value < totalPages.value - 1) { currentPage.value++; loadAtividades() }
}

// ── Helpers ──────────────────────────────────────
function methodClass(method: string) {
  switch (method) {
    case 'GET': return 'bg-blue-500/20 text-blue-300'
    case 'POST': return 'bg-green-500/20 text-green-300'
    case 'PUT': return 'bg-amber-500/20 text-amber-300'
    case 'DELETE': return 'bg-red-500/20 text-red-300'
    default: return 'bg-white/10 text-white/60'
  }
}

function statusClass(code: number) {
  if (code >= 500) return 'text-red-400 font-bold'
  if (code >= 400) return 'text-amber-400'
  if (code >= 200 && code < 300) return 'text-green-400'
  return 'text-white/60'
}

function envioStatusClass(status: string) {
  switch (status) {
    case 'processado': return 'bg-green-500/20 text-green-300'
    case 'enviado': return 'bg-blue-500/20 text-blue-300'
    case 'erro': return 'bg-red-500/20 text-red-300'
    default: return 'bg-white/10 text-white/60'
  }
}

function envioStatusColor(status: string) {
  switch (status) {
    case 'processado': return 'text-green-400'
    case 'enviado': return 'text-blue-400'
    case 'erro': return 'text-red-400'
    default: return 'text-white'
  }
}

function pipelineStatusClass(status: string) {
  switch (status) {
    case 'completo': return 'bg-green-500/20 text-green-300'
    case 'em_andamento': return 'bg-blue-500/20 text-blue-300'
    case 'erro': return 'bg-red-500/20 text-red-300'
    case 'parcial': return 'bg-amber-500/20 text-amber-300'
    default: return 'bg-white/10 text-white/60'
  }
}

function formatCpf(cpf: string) {
  if (!cpf || cpf.length !== 11) return cpf
  return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9)}`
}

function formatDate(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatDateTime(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatDateTimeFull(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

onMounted(() => {
  if (!authStore.isAdmin) { router.push('/'); return }
  loadData()
})
</script>

<style scoped>
.admin-bg {
  background: linear-gradient(135deg, #0a1024 0%, #0d1530 40%, #111b3d 100%);
  min-height: 100vh;
}

.glass-card {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.glass-input {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: white;
  padding: 6px 12px;
  outline: none;
}
.glass-input:focus {
  border-color: #0066ff;
}
.glass-input option {
  background: #1a2340;
  color: white;
}

.btn-primary {
  background: #0066ff;
  color: white;
  padding: 6px 16px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
}
.btn-primary:hover {
  background: #0055dd;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: white;
  padding: 6px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}
.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.glass-shape {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 102, 255, 0.08) 0%, transparent 70%);
  animation: float 20s ease-in-out infinite;
}
.shape-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}
.shape-2 {
  width: 300px;
  height: 300px;
  bottom: 10%;
  left: -50px;
  animation-delay: -7s;
}
.shape-3 {
  width: 250px;
  height: 250px;
  top: 50%;
  right: 20%;
  animation-delay: -14s;
}

@keyframes float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -20px) scale(1.05);
  }
  66% {
    transform: translate(-20px, 15px) scale(0.95);
  }
}
</style>
