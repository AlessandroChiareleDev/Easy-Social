<template>
  <div class="esocial-view">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white">Envio eSocial S-1010</h1>
        <p class="text-sm text-slate-400 mt-1">Enviar alterações de rubricas ao eSocial</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- Ambiente Toggle -->
        <div
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border"
          :class="
            ambiente === '1'
              ? 'bg-red-500/10 text-red-400 border-red-500/30'
              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
          "
        >
          <button
            @click="ambiente = '2'"
            :class="
              ambiente === '2'
                ? 'bg-emerald-500/20 text-emerald-300 font-semibold'
                : 'text-slate-500 hover:text-slate-300'
            "
            class="px-2 py-0.5 rounded text-xs transition-colors"
          >
            Homologação
          </button>
          <button
            @click="ambiente = '1'"
            :class="
              ambiente === '1'
                ? 'bg-red-500/20 text-red-300 font-semibold'
                : 'text-slate-500 hover:text-slate-300'
            "
            class="px-2 py-0.5 rounded text-xs transition-colors"
          >
            Produção
          </button>
        </div>
        <div
          v-if="certStatus"
          @click="activeTab = 'certificado'"
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm cursor-pointer"
          :class="
            certStatus.ativo
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/15'
              : 'bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/15'
          "
        >
          <span v-if="certStatus.ativo"
            ><svg
              class="w-3.5 h-3.5 inline -mt-0.5 mr-1"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0110 0v4" /></svg
            >{{ certStatus.titular }}</span
          >
          <span v-else
            ><svg
              class="w-3.5 h-3.5 inline -mt-0.5 mr-1"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
              />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" /></svg
            >Clique para importar certificado</span
          >
        </div>
        <button @click="activeTab = 'historico'" class="header-btn">
          <svg
            class="w-3.5 h-3.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          Histórico
        </button>
        <!-- Botão Enviar (principal) -->
        <button
          @click="enviar"
          :disabled="selectedIds.length === 0 || enviando || !certStatus?.ativo"
          :class="
            selectedIds.length > 0 && !enviando && certStatus?.ativo
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
              : 'bg-slate-700 text-slate-400 cursor-not-allowed opacity-50'
          "
          class="px-5 py-1.5 font-medium rounded-lg transition-all duration-200 flex items-center gap-2 text-sm"
        >
          <svg v-if="enviando" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <span v-if="!enviando"
            ><svg
              class="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" /></svg
          ></span>
          {{
            enviando
              ? 'Enviando...'
              : selectedIds.length === 0
                ? 'Enviar'
                : `Enviar ${selectedIds.length} rubrica${selectedIds.length !== 1 ? 's' : ''}`
          }}
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="{ active: activeTab === tab.id }"
        class="tab-btn"
      >
        <!-- Tab icons -->
        <svg
          v-if="tab.id === 'certificado'"
          class="tab-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect x="3" y="11" width="18" height="11" rx="2" />
          <path d="M7 11V7a5 5 0 0110 0v4" />
        </svg>
        <svg
          v-else-if="tab.id === 'enviar'"
          class="tab-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
        <svg
          v-else-if="tab.id === 'naturezas_invalidas'"
          class="tab-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path
            d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
          />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <svg
          v-else-if="tab.id === 'historico'"
          class="tab-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <svg
          v-else-if="tab.id === 'repositorio'"
          class="tab-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
        </svg>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Certificado A1 -->
    <div v-if="activeTab === 'certificado'">
      <!-- Certificado ativo -->
      <div v-if="certStatus?.ativo" class="card mb-4">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-white">Certificado Ativo</h2>
          <span
            class="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
          >
            Válido
          </span>
        </div>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-slate-500">Titular</span>
            <p class="text-white mt-0.5">{{ certStatus.titular }}</p>
          </div>
          <div>
            <span class="text-slate-500">CNPJ</span>
            <p class="text-white mt-0.5 font-mono">{{ formatCnpj(certStatus.cnpj) }}</p>
          </div>
          <div>
            <span class="text-slate-500">Emissor</span>
            <p class="text-slate-300 mt-0.5">{{ certStatus.emissor }}</p>
          </div>
          <div>
            <span class="text-slate-500">Validade</span>
            <p class="text-slate-300 mt-0.5">{{ formatDate(certStatus.validade) }}</p>
          </div>
          <div>
            <span class="text-slate-500">Nº Série</span>
            <p class="text-slate-300 mt-0.5 font-mono text-xs break-all">
              {{ certStatus.numero_serie }}
            </p>
          </div>
          <div>
            <span class="text-slate-500">Importado em</span>
            <p class="text-slate-300 mt-0.5">{{ formatDate(certStatus.created_at) }}</p>
          </div>
        </div>
        <div
          class="mt-4 pt-4 flex justify-end"
          style="border-top: 1px solid rgba(255, 255, 255, 0.08)"
        >
          <button
            @click="removeCert"
            :disabled="certRemoving"
            class="px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors border border-red-500/20"
          >
            {{ certRemoving ? 'Removendo...' : 'Remover certificado' }}
          </button>
        </div>
      </div>

      <!-- Senha Salva -->
      <div class="card mb-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-white">Senha do Certificado</h2>
          <span
            v-if="senhaSalva?.saved"
            class="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
          >
            ✓ Salva
          </span>
          <span
            v-else
            class="px-2 py-0.5 rounded text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20"
          >
            Não salva
          </span>
        </div>

        <div v-if="senhaSalva?.saved" class="text-sm">
          <div
            class="flex items-center gap-3 p-3 rounded-lg"
            style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15)"
          >
            <svg
              class="w-6 h-6 text-emerald-400 shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"
              />
            </svg>
            <div class="flex-1">
              <p class="text-emerald-400 font-medium">Senha salva e ativa</p>
              <p class="text-slate-400 text-xs mt-0.5">
                Salva em {{ formatDate(senhaSalva.saved_at) }} — Expira em
                {{ formatDate(senhaSalva.expires_at) }}
              </p>
              <p class="text-slate-500 text-xs mt-0.5">
                Ao importar o certificado, a senha salva será usada automaticamente.
              </p>
            </div>
            <button
              @click="removerSenhaSalva"
              :disabled="removendoSenha"
              class="px-3 py-1.5 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors border border-red-500/20"
            >
              {{ removendoSenha ? 'Removendo...' : 'Remover' }}
            </button>
          </div>
        </div>

        <div v-else>
          <p class="text-sm text-slate-400 mb-3">
            Salve a senha do certificado para não precisar digitá-la toda vez que importar. A senha
            fica salva por 24 horas.
          </p>
          <div class="flex gap-3">
            <input
              v-model="senhaParaSalvar"
              type="password"
              placeholder="Digite a senha do certificado"
              class="input-field flex-1"
            />
            <button
              @click="salvarSenha"
              :disabled="!senhaParaSalvar || salvandoSenha"
              class="px-5 py-2 bg-[#0066FF] hover:bg-[#0055dd] disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors whitespace-nowrap"
            >
              {{ salvandoSenha ? 'Salvando...' : 'Salvar Senha' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Upload de certificado -->
      <div class="card">
        <h2 class="text-lg font-semibold text-white mb-1">
          {{ certStatus?.ativo ? 'Substituir Certificado' : 'Importar Certificado A1' }}
        </h2>
        <p class="text-sm text-slate-400 mb-4">
          Faça upload do arquivo <code class="text-[#0066FF]">.pfx / .p12</code> do certificado
          digital A1{{ senhaSalva?.saved ? '.' : ' e informe a senha.' }}
          <span v-if="senhaSalva?.saved" class="text-emerald-400"
            >A senha salva será usada automaticamente.</span
          >
        </p>

        <!-- Drag & drop area -->
        <div
          @dragover.prevent="certDragOver = true"
          @dragleave="certDragOver = false"
          @drop.prevent="onDropCert"
          @click="certInput?.click()"
          :class="
            certDragOver
              ? 'border-[#0066FF] bg-[#0066FF]/5'
              : 'border-white/10 hover:border-white/20'
          "
          class="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors"
        >
          <input
            ref="certInput"
            type="file"
            accept=".pfx,.p12"
            class="hidden"
            @change="onSelectCert"
          />
          <div v-if="certFile" class="flex items-center justify-center gap-3">
            <svg
              class="w-6 h-6 text-[#5ac8f5] shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <div class="text-left">
              <p class="text-white font-medium">{{ certFile.name }}</p>
              <p class="text-xs text-slate-400">{{ (certFile.size / 1024).toFixed(1) }} KB</p>
            </div>
            <button
              @click.stop="certFile = null"
              class="ml-2 text-slate-400 hover:text-red-400 text-lg"
            >
              ✕
            </button>
          </div>
          <div v-else>
            <svg
              class="w-8 h-8 text-[#5ac8f5] mx-auto mb-2"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0110 0v4" />
            </svg>
            <p class="text-slate-300">Arraste o arquivo <strong>.pfx / .p12</strong> aqui</p>
            <p class="text-xs text-slate-500 mt-1">ou clique para selecionar</p>
          </div>
        </div>

        <!-- Senha -->
        <div v-if="!senhaSalva?.saved" class="mt-4">
          <label class="text-sm text-slate-400">Senha do certificado</label>
          <input
            v-model="certSenha"
            type="password"
            placeholder="Digite a senha do certificado"
            class="input-field mt-1"
          />
        </div>
        <div v-else class="mt-4">
          <div
            class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
            style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.1)"
          >
            <svg
              class="w-4 h-4 text-emerald-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"
              />
            </svg>
            <span class="text-emerald-400/80">Senha salva será usada automaticamente</span>
          </div>
        </div>

        <!-- Botão Upload -->
        <div class="mt-4 flex justify-end">
          <button
            @click="uploadCert"
            :disabled="!certFile || (!certSenha && !senhaSalva?.saved) || certUploading"
            class="px-6 py-2.5 bg-[#0066FF] hover:bg-[#0055dd] disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <svg v-if="certUploading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            {{ certUploading ? 'Validando e enviando...' : 'Importar Certificado' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Tab: Enviar -->
    <div v-if="activeTab === 'enviar'">
      <!-- Seleção de período e modo -->
      <div class="card mb-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm text-slate-400">Período de vigência (iniValid)</label>
            <div class="flex items-center gap-2 mt-1">
              <button
                @click="iniValidAuto = true"
                :class="
                  iniValidAuto
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : 'text-slate-400 border-white/10 hover:text-white hover:bg-white/5'
                "
                class="px-3 py-2 rounded-lg text-xs font-medium border transition-colors"
              >
                <svg
                  class="w-3.5 h-3.5 inline -mt-0.5 mr-0.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polyline points="23 4 23 10 17 10" />
                  <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
                </svg>
                Auto
              </button>
              <button
                @click="iniValidAuto = false"
                :class="
                  !iniValidAuto
                    ? 'bg-[#0066FF]/15 text-[#0066FF] border-[#0066FF]/30'
                    : 'text-slate-400 border-white/10 hover:text-white hover:bg-white/5'
                "
                class="px-3 py-2 rounded-lg text-xs font-medium border transition-colors"
              >
                <svg
                  class="w-3.5 h-3.5 inline -mt-0.5 mr-0.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
                Manual
              </button>
            </div>
            <input v-if="!iniValidAuto" v-model="iniValid" type="month" class="input-field mt-2" />
            <div v-if="iniValidAuto" class="mt-2 space-y-1">
              <p class="text-xs text-emerald-400/80">
                iniValid automático: rubrica confirmada → empresa (S-1000) → Tabela 3
              </p>
              <div class="flex items-center gap-2">
                <span class="text-xs text-slate-400">Data empresa (S-1000):</span>
                <input
                  v-model="iniValidEmpresa"
                  type="month"
                  class="bg-white/5 border border-white/10 rounded px-2 py-0.5 text-xs text-white w-32"
                  @change="salvarIniValidEmpresa"
                />
                <span v-if="iniValidEmpresaSalvo" class="text-xs text-emerald-400">✓</span>
              </div>
            </div>
            <p
              v-if="!iniValidAuto && modoEnvio === 'alteracao'"
              class="text-xs text-amber-400/80 mt-1"
            >
              ⚠ Para alteração, informe o período em que a rubrica foi cadastrada no eSocial (ex:
              2019-01).
            </p>
          </div>
          <div>
            <label class="text-sm text-slate-400">Modo de envio</label>
            <div class="flex gap-2 mt-1">
              <button
                @click="modoEnvio = 'inclusao'"
                :class="
                  modoEnvio === 'inclusao'
                    ? 'bg-[#0066FF]/15 text-[#0066FF] border-[#0066FF]/30'
                    : 'text-slate-400 border-white/10 hover:text-white hover:bg-white/5'
                "
                class="flex-1 px-3 py-2 rounded-lg text-sm font-medium border transition-colors"
              >
                Inclusão
              </button>
              <button
                @click="modoEnvio = 'alteracao'"
                :class="
                  modoEnvio === 'alteracao'
                    ? 'bg-[#0066FF]/15 text-[#0066FF] border-[#0066FF]/30'
                    : 'text-slate-400 border-white/10 hover:text-white hover:bg-white/5'
                "
                class="flex-1 px-3 py-2 rounded-lg text-sm font-medium border transition-colors"
              >
                Alteração
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Rubricas pendentes -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <h2 class="text-lg font-semibold text-white">Rubricas</h2>
            <div class="flex rounded-lg overflow-hidden border border-white/10">
              <button
                @click="setFiltro('pendentes')"
                :class="
                  filtroRubricas === 'pendentes'
                    ? 'bg-[#0066FF]/15 text-[#0066FF]'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                "
                class="px-3 py-1 text-xs font-medium transition-colors"
              >
                Pendentes
              </button>
              <button
                @click="setFiltro('enviadas')"
                :class="
                  filtroRubricas === 'enviadas'
                    ? 'bg-purple-500/15 text-purple-400'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                "
                class="px-3 py-1 text-xs font-medium transition-colors border-l border-white/10"
              >
                Enviadas
              </button>
              <button
                @click="setFiltro('todas')"
                :class="
                  filtroRubricas === 'todas'
                    ? 'bg-[#0066FF]/15 text-[#0066FF]'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                "
                class="px-3 py-1 text-xs font-medium transition-colors border-l border-white/10"
              >
                Todas
              </button>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm text-slate-400"
              >{{ selectedIds.length }} selecionadas de {{ rubricas.length }}</span
            >
            <button
              v-if="rubricas.length > 0"
              @click="toggleSelectAll"
              class="text-sm text-[#0066FF] hover:text-[#3388ff] transition-colors"
            >
              {{ selectedIds.length === rubricas.length ? 'Desmarcar todas' : 'Selecionar todas' }}
            </button>
          </div>
        </div>

        <div v-if="loadingRubricas" class="text-center py-8 text-slate-400">
          Carregando rubricas...
        </div>

        <div v-else-if="rubricas.length === 0" class="text-center py-8">
          <p class="text-slate-400">Nenhuma rubrica pendente para envio.</p>
          <p class="text-sm text-slate-500 mt-1">
            Detecte divergências no Painel e corrija no Validador.
          </p>
        </div>

        <template v-else>
          <!-- Alerta naturezas expiradas -->
          <div
            v-if="naturezasExpiradas.length > 0"
            class="mb-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center gap-3"
          >
            <span class="text-red-400 text-lg"
              ><svg
                class="w-5 h-5 inline"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path
                  d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" /></svg
            ></span>
            <div>
              <p class="text-red-400 text-sm font-semibold">
                {{ naturezasExpiradas.length }} natureza{{
                  naturezasExpiradas.length > 1 ? 's' : ''
                }}
                inválida{{ naturezasExpiradas.length > 1 ? 's' : '' }}
              </p>
              <p class="text-red-400/70 text-xs mt-0.5">
                Corrija antes de enviar ao eSocial. Naturezas com validade encerrada na Tabela 3
                causarão erro no envio.
              </p>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-white/10">
                  <th class="py-2 px-3 text-left w-10">
                    <input
                      type="checkbox"
                      :checked="selectedIds.length === rubricas.length && rubricas.length > 0"
                      @change="toggleSelectAll"
                      class="accent-[#0066FF]"
                    />
                  </th>
                  <th class="py-2 px-3 text-left text-slate-400 font-medium">Código</th>
                  <th class="py-2 px-3 text-left text-slate-400 font-medium">Descrição</th>
                  <th
                    class="py-2 px-3 text-center font-medium"
                    :class="naturezasExpiradas.length > 0 ? 'text-red-400' : 'text-slate-400'"
                  >
                    Natureza
                    <span
                      v-if="naturezasExpiradas.length > 0"
                      class="ml-1 px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-400 text-[10px] font-bold"
                      >{{ naturezasExpiradas.length }}</span
                    >
                  </th>
                  <th class="py-2 px-3 text-center text-slate-400 font-medium">iniValid</th>
                  <th class="py-2 px-3 text-center text-slate-400 font-medium">
                    INSS Atual→Correto
                  </th>
                  <th class="py-2 px-3 text-center text-slate-400 font-medium">
                    IRRF Atual→Correto
                  </th>
                  <th class="py-2 px-3 text-center text-slate-400 font-medium">
                    FGTS Atual→Correto
                  </th>
                  <th class="py-2 px-3 text-center text-slate-400 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="rub in rubricasPaginadas"
                  :key="rub.cod_rubrica"
                  class="border-b border-white/5 hover:bg-white/[0.02] transition-colors cursor-pointer"
                  @click="toggleSelect(rub.cod_rubrica)"
                >
                  <td class="py-2 px-3">
                    <input
                      type="checkbox"
                      :checked="selectedIds.includes(rub.cod_rubrica)"
                      @click.stop
                      @change="toggleSelect(rub.cod_rubrica)"
                      class="accent-[#0066FF]"
                    />
                  </td>
                  <td class="py-2 px-3 text-white font-mono">{{ rub.cod_rubrica }}</td>
                  <td class="py-2 px-3 text-slate-300 max-w-[200px] truncate">
                    {{ rub.descricao }}
                  </td>
                  <td class="py-2 px-3 text-center" @click.stop>
                    <div
                      v-if="editingNatureza === rub.cod_rubrica"
                      class="flex items-center gap-1 justify-center"
                    >
                      <input
                        v-model="editNaturezaValue"
                        type="text"
                        class="w-16 px-1.5 py-0.5 text-xs text-white text-center rounded border border-[#0066FF]/50 bg-[#0a1024] outline-none focus:border-[#0066FF]"
                        @keyup.enter="salvarNatureza(rub)"
                        @keyup.escape="editingNatureza = null"
                        ref="naturezaInput"
                        maxlength="6"
                      />
                      <button
                        @click="salvarNatureza(rub)"
                        class="text-emerald-400 hover:text-emerald-300 text-xs"
                        :disabled="salvandoNatureza"
                      >
                        ✓
                      </button>
                      <button
                        @click="editingNatureza = null"
                        class="text-red-400 hover:text-red-300 text-xs"
                      >
                        ✕
                      </button>
                    </div>
                    <span
                      v-else
                      @click="iniciarEditNatureza(rub)"
                      class="text-xs cursor-pointer hover:underline transition-colors"
                      :class="
                        rub.nat_rubr_expirada
                          ? 'text-red-400 font-semibold hover:text-red-300'
                          : 'text-slate-300 hover:text-[#0066FF]'
                      "
                      :title="
                        rub.nat_rubr_expirada
                          ? `⚠ Natureza expirada em ${rub.nat_rubr_dt_fim} — clique para corrigir`
                          : 'Clique para editar a natureza'
                      "
                      >{{ rub.nat_rubr
                      }}<span v-if="rub.nat_rubr_expirada" class="ml-1 text-[10px]">⚠</span></span
                    >
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span
                      v-if="!iniValidAuto"
                      class="px-2 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-400"
                      >{{ iniValid }}</span
                    >
                    <span
                      v-else-if="rub.ini_valid_resolved"
                      class="px-2 py-0.5 rounded text-xs font-mono"
                      :class="{
                        'bg-emerald-500/10 text-emerald-400': rub.ini_valid_source === 'rubrica',
                        'bg-purple-500/10 text-purple-400': rub.ini_valid_source === 'empresa',
                        'bg-amber-500/10 text-amber-400': rub.ini_valid_source === 'tabela3',
                      }"
                      :title="
                        rub.ini_valid_source === 'rubrica'
                          ? 'Confirmado por envio anterior'
                          : rub.ini_valid_source === 'empresa'
                            ? 'Data da empresa (S-1000)'
                            : 'Tabela 3 eSocial'
                      "
                      >{{ rub.ini_valid_resolved }}</span
                    >
                    <span v-else class="px-2 py-0.5 rounded text-xs bg-red-500/10 text-red-400"
                      >?</span
                    >
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span v-if="rub.incid_inss !== rub.inss_correto" class="text-xs font-mono">
                      <span class="text-red-400">{{ rub.incid_inss }}</span>
                      <span class="text-slate-500">→</span>
                      <span class="text-emerald-400">{{ rub.inss_correto }}</span>
                    </span>
                    <span
                      v-else
                      class="px-2 py-0.5 rounded text-xs font-mono bg-emerald-500/10 text-emerald-400"
                      >{{ rub.inss_correto }}</span
                    >
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span v-if="rub.incid_irrf !== rub.irrf_correto" class="text-xs font-mono">
                      <span class="text-red-400">{{ rub.incid_irrf }}</span>
                      <span class="text-slate-500">→</span>
                      <span class="text-emerald-400">{{ rub.irrf_correto }}</span>
                    </span>
                    <span
                      v-else
                      class="px-2 py-0.5 rounded text-xs font-mono bg-emerald-500/10 text-emerald-400"
                      >{{ rub.irrf_correto }}</span
                    >
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span v-if="rub.incid_fgts !== rub.fgts_correto" class="text-xs font-mono">
                      <span class="text-red-400">{{ rub.incid_fgts }}</span>
                      <span class="text-slate-500">→</span>
                      <span class="text-emerald-400">{{ rub.fgts_correto }}</span>
                    </span>
                    <span
                      v-else
                      class="px-2 py-0.5 rounded text-xs font-mono bg-emerald-500/10 text-emerald-400"
                      >{{ rub.fgts_correto }}</span
                    >
                  </td>
                  <td class="py-2 px-3 text-center">
                    <span
                      v-if="rub.envio_status === 'feito' || rub.corrigido"
                      class="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400"
                      >✓ Feito</span
                    >
                    <span
                      v-else-if="rub.envio_status === 'enviado'"
                      class="px-2 py-0.5 rounded text-xs bg-purple-500/15 text-purple-400 inline-flex items-center gap-1"
                    >
                      <svg class="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle
                          class="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          stroke-width="4"
                        />
                        <path
                          class="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                      Enviado
                    </span>
                    <span v-else class="px-2 py-0.5 rounded text-xs bg-amber-500/10 text-amber-400"
                      >Pendente</span
                    >
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Paginação -->
            <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-4">
              <button
                @click="page--"
                :disabled="page <= 1"
                class="px-3 py-1 rounded text-sm text-slate-400 hover:text-white disabled:opacity-30"
              >
                ← Anterior
              </button>
              <span class="text-sm text-slate-400">{{ page }} / {{ totalPages }}</span>
              <button
                @click="page++"
                :disabled="page >= totalPages"
                class="px-3 py-1 rounded text-sm text-slate-400 hover:text-white disabled:opacity-30"
              >
                Próximo →
              </button>
            </div>
          </div>
        </template>

        <!-- Info rodapé -->
        <div
          v-if="rubricas.length > 0"
          class="mt-4 pt-3 text-sm text-slate-500"
          style="border-top: 1px solid rgba(255, 255, 255, 0.08)"
        >
          <strong class="text-slate-400">Ambiente:</strong>
          <span :class="ambiente === '1' ? 'text-red-400 font-semibold' : 'text-emerald-400'">
            {{ ambiente === '1' ? 'PRODUÇÃO (tpAmb=1)' : 'Homologação (tpAmb=2)' }}
          </span>
          <span class="ml-2 text-slate-600">|</span>
          <span class="ml-2 text-slate-400"
            >Modo: {{ modoEnvio === 'inclusao' ? 'Inclusão' : 'Alteração' }}</span
          >
          <span class="ml-2 text-slate-600">|</span>
          <span class="ml-2 text-slate-400">{{ selectedIds.length }} selecionada(s)</span>
        </div>
      </div>

      <!-- Resultado do Envio -->
      <div
        v-if="resultado"
        class="card mt-4"
        :class="resultado.sucesso ? 'border-emerald-500/30' : 'border-red-500/30'"
        style="border-width: 1px"
      >
        <div class="flex items-start gap-3">
          <span v-if="resultado.sucesso" class="text-emerald-400"
            ><svg
              class="w-6 h-6"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" /></svg
          ></span>
          <span v-else class="text-red-400"
            ><svg
              class="w-6 h-6"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" /></svg
          ></span>
          <div>
            <h3 class="text-white font-semibold">
              {{ resultado.sucesso ? 'Lote enviado com sucesso' : 'Erro no envio' }}
            </h3>
            <p class="text-sm text-slate-400 mt-1">{{ resultado.descricao }}</p>
            <div v-if="resultado.protocolo" class="mt-2 flex items-center gap-2">
              <span class="text-xs text-slate-500">Protocolo:</span>
              <code class="text-sm text-[#0066FF] font-mono bg-[#0066FF]/10 px-2 py-0.5 rounded">{{
                resultado.protocolo
              }}</code>
              <button
                @click="consultarProtocolo(resultado.protocolo)"
                class="text-xs text-[#0066FF] hover:underline"
              >
                Consultar
              </button>
            </div>
            <p v-if="resultado.eventos_enviados" class="text-xs text-slate-500 mt-1">
              {{ resultado.eventos_enviados }} evento(s) enviado(s) em {{ resultado.dh_recepcao }}
            </p>
            <div v-if="resultado.ocorrencias && resultado.ocorrencias.length > 0" class="mt-2">
              <p class="text-xs text-red-400" v-for="(oc, i) in resultado.ocorrencias" :key="i">
                {{ oc.codigo }}: {{ oc.descricao }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Naturezas Inválidas -->
    <div v-if="activeTab === 'naturezas_invalidas'">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-white">Naturezas Inválidas</h2>
            <p class="text-sm text-slate-400 mt-1">
              Naturezas com validade encerrada na Tabela 3 do eSocial. Corrija antes de enviar.
            </p>
          </div>
          <div
            v-if="naturezasExpiradas.length > 0"
            class="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30"
          >
            <span class="text-red-400 text-sm font-semibold"
              >{{ naturezasExpiradas.length }} inválida{{
                naturezasExpiradas.length !== 1 ? 's' : ''
              }}</span
            >
          </div>
        </div>

        <div v-if="loadingRubricas" class="text-center py-8 text-slate-400">Carregando...</div>

        <div v-else-if="naturezasExpiradas.length === 0" class="text-center py-12">
          <svg
            class="w-10 h-10 text-emerald-400 mx-auto"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          <p class="text-emerald-400 font-medium mt-3">Todas as naturezas estão válidas!</p>
          <p class="text-sm text-slate-500 mt-1">
            Nenhuma rubrica possui natureza expirada na Tabela 3.
          </p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-white/10">
                <th class="py-2 px-3 text-left text-slate-400 font-medium">Código</th>
                <th class="py-2 px-3 text-left text-slate-400 font-medium">Descrição</th>
                <th class="py-2 px-3 text-center text-red-400 font-medium">Natureza</th>
                <th class="py-2 px-3 text-center text-slate-400 font-medium">Início Validade</th>
                <th class="py-2 px-3 text-center text-slate-400 font-medium">Fim Validade</th>
                <th class="py-2 px-3 text-center text-slate-400 font-medium">Natureza Sugerida</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="rub in naturezasExpiradas"
                :key="rub.cod_rubrica"
                class="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
              >
                <td class="py-2.5 px-3 text-white font-mono">{{ rub.cod_rubrica }}</td>
                <td class="py-2.5 px-3 text-slate-300 max-w-[250px] truncate">
                  {{ rub.descricao }}
                </td>
                <td class="py-2.5 px-3 text-center">
                  <span
                    class="px-2 py-0.5 rounded text-xs font-mono bg-red-500/15 text-red-400 font-semibold"
                  >
                    {{ rub.nat_rubr }}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-center text-slate-300 text-xs font-mono">
                  {{ rub.ini_valid_auto || '—' }}
                </td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-xs font-mono bg-red-500/10 text-red-400">
                    {{ rub.nat_rubr_dt_fim }}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-center">
                  <span
                    v-if="sugestoesNatureza[rub.nat_rubr]?.tipo === 'codigo'"
                    class="px-2 py-0.5 rounded text-xs font-mono bg-emerald-500/15 text-emerald-400 font-semibold"
                  >
                    {{ sugestoesNatureza[rub.nat_rubr].valor }}
                  </span>
                  <span
                    v-else-if="sugestoesNatureza[rub.nat_rubr]?.tipo === 'nota'"
                    class="text-amber-400 text-xs"
                  >
                    {{ sugestoesNatureza[rub.nat_rubr].valor }}
                  </span>
                  <span v-else class="text-slate-500 text-xs">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Tab: Histórico -->
    <div v-if="activeTab === 'historico'">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-white">Histórico de Envios</h2>
          <button @click="fetchEnvios" class="text-sm text-[#0066FF] hover:text-[#3388ff]">
            ↻ Atualizar
          </button>
        </div>
        <div v-if="loadingEnvios" class="text-center py-8 text-slate-400">Carregando...</div>
        <div v-else-if="envios.length === 0" class="text-center py-8 text-slate-400">
          Nenhum envio realizado ainda.
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="env in envios"
            :key="env.id"
            class="rounded-lg border border-white/5 overflow-hidden"
            style="background: #0a1024"
          >
            <!-- Row principal -->
            <div
              class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/[0.02] transition-colors"
              @click="toggleEnvioExpand(env.id)"
            >
              <span class="text-xs text-slate-500 w-16">{{ formatDate(env.created_at) }}</span>
              <span class="text-white font-mono text-sm w-16">{{ env.tipo_evento }}</span>
              <span
                class="px-2 py-0.5 rounded text-xs w-20 text-center"
                :class="
                  env.modo === 'inclusao'
                    ? 'bg-blue-500/10 text-blue-400'
                    : 'bg-purple-500/10 text-purple-400'
                "
              >
                {{ env.modo === 'inclusao' ? 'Inclusão' : 'Alteração' }}
              </span>
              <span
                class="px-2 py-0.5 rounded text-xs w-24 text-center"
                :class="
                  env.ambiente === '1'
                    ? 'bg-red-500/10 text-red-400'
                    : 'bg-emerald-500/10 text-emerald-400'
                "
              >
                {{ env.ambiente === '1' ? 'Produção' : 'Homologação' }}
              </span>
              <span class="text-slate-400 text-sm">{{ env.total_eventos }} evento(s)</span>
              <span v-if="env.ini_valid" class="text-slate-500 text-xs font-mono">{{
                env.ini_valid
              }}</span>
              <span
                :class="{
                  'bg-emerald-500/10 text-emerald-400': env.status === 'processado',
                  'bg-blue-500/10 text-blue-400': env.status === 'enviado',
                  'bg-red-500/10 text-red-400': env.status === 'erro',
                }"
                class="px-2 py-0.5 rounded text-xs ml-auto"
                >{{ env.status }}</span
              >
              <span class="text-slate-600 text-xs">{{
                expandedEnvioId === env.id ? '▲' : '▼'
              }}</span>
            </div>

            <!-- Detalhes expandidos -->
            <div
              v-if="expandedEnvioId === env.id"
              class="px-4 py-3"
              style="border-top: 1px solid rgba(255, 255, 255, 0.05)"
            >
              <div class="grid grid-cols-3 gap-4 mb-3 text-xs">
                <div>
                  <span class="text-slate-500">Protocolo</span>
                  <p class="text-[#0066FF] font-mono mt-0.5">{{ env.protocolo_envio || '—' }}</p>
                </div>
                <div>
                  <span class="text-slate-500">Código Resposta</span>
                  <p
                    :class="env.codigo_resposta === '201' ? 'text-emerald-400' : 'text-red-400'"
                    class="font-mono mt-0.5"
                  >
                    {{ env.codigo_resposta || '—' }}
                  </p>
                </div>
                <div>
                  <span class="text-slate-500">Descrição</span>
                  <p class="text-slate-300 mt-0.5">{{ env.descricao_resposta || '—' }}</p>
                </div>
              </div>

              <!-- Rubricas enviadas -->
              <div v-if="env.rubrica_detalhes && env.rubrica_detalhes.length > 0" class="mb-3">
                <h4 class="text-xs text-slate-500 mb-2">Rubricas enviadas</h4>
                <div class="overflow-x-auto">
                  <table class="w-full text-xs">
                    <thead>
                      <tr class="border-b border-white/10">
                        <th class="py-1 px-2 text-left text-slate-500">Código</th>
                        <th class="py-1 px-2 text-left text-slate-500">Descrição</th>
                        <th class="py-1 px-2 text-center text-slate-500">Natureza</th>
                        <th class="py-1 px-2 text-center text-slate-500">INSS→</th>
                        <th class="py-1 px-2 text-center text-slate-500">IRRF→</th>
                        <th class="py-1 px-2 text-center text-slate-500">FGTS→</th>
                        <th v-if="env.recibo_consulta" class="py-1 px-2 text-center text-slate-500">
                          Recibo
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="(rub, ri) in env.rubrica_detalhes"
                        :key="ri"
                        class="border-b border-white/5"
                      >
                        <td class="py-1 px-2 text-white font-mono">{{ rub.cod_rubrica }}</td>
                        <td class="py-1 px-2 text-slate-300 max-w-[150px] truncate">
                          {{ rub.descricao }}
                        </td>
                        <td class="py-1 px-2 text-center text-slate-400">{{ rub.nat_rubr }}</td>
                        <td class="py-1 px-2 text-center text-emerald-400 font-mono">
                          {{ rub.inss_correto }}
                        </td>
                        <td class="py-1 px-2 text-center text-emerald-400 font-mono">
                          {{ rub.irrf_correto }}
                        </td>
                        <td class="py-1 px-2 text-center text-emerald-400 font-mono">
                          {{ rub.fgts_correto }}
                        </td>
                        <td
                          v-if="env.recibo_consulta"
                          class="py-1 px-2 text-center text-emerald-400 font-mono text-[10px]"
                        >
                          {{ getReciboForIndex(env, ri) }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              <!-- Rubricas simples (sem detalhes) -->
              <div v-else-if="env.rubrica_ids && env.rubrica_ids.length > 0" class="mb-3">
                <span class="text-xs text-slate-500">Rubricas: </span>
                <span class="text-xs text-white font-mono">{{ env.rubrica_ids.join(', ') }}</span>
              </div>

              <!-- Consulta/Recibos do lote -->
              <div v-if="env.recibo_consulta && env.recibo_consulta.eventos" class="mb-3">
                <h4 class="text-xs text-slate-500 mb-1">Resultado da consulta</h4>
                <div class="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span class="text-slate-500">Status lote:</span>
                    <span
                      :class="env.recibo_consulta.sucesso ? 'text-emerald-400' : 'text-red-400'"
                      class="ml-1"
                    >
                      {{ env.recibo_consulta.sucesso ? 'Sucesso' : 'Erro' }}
                    </span>
                  </div>
                  <div>
                    <span class="text-slate-500">Consultado em:</span>
                    <span class="text-slate-300 ml-1">{{ formatDate(env.updated_at) }}</span>
                  </div>
                </div>
              </div>

              <!-- Ações -->
              <div class="flex gap-2 mt-2">
                <button
                  v-if="env.protocolo_envio"
                  @click.stop="consultarProtocolo(env.protocolo_envio)"
                  class="px-3 py-1.5 text-xs bg-[#0066FF]/10 text-[#0066FF] hover:bg-[#0066FF]/20 rounded-lg transition-colors"
                >
                  Consultar Resultado
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Repositório de Recibos -->
    <div v-if="activeTab === 'repositorio'">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-white">Repositório de Recibos S-1010</h2>
            <p class="text-xs text-slate-500 mt-0.5">
              Registro detalhado de todos os envios — dados para auditoria e integração
            </p>
          </div>
          <div class="flex items-center gap-2">
            <!-- Filtro Ambiente -->
            <select
              v-model="repoFiltroAmbiente"
              class="px-2 py-1 text-xs rounded-lg border border-white/10 text-slate-300"
              style="background: #0a1024"
            >
              <option value="todos">Todos ambientes</option>
              <option value="2">Homologação</option>
              <option value="1">Produção</option>
            </select>
            <!-- Filtro Status -->
            <select
              v-model="repoFiltroStatus"
              class="px-2 py-1 text-xs rounded-lg border border-white/10 text-slate-300"
              style="background: #0a1024"
            >
              <option value="todos">Todos status</option>
              <option value="processado">Processado</option>
              <option value="enviado">Enviado</option>
              <option value="erro">Erro</option>
            </select>
            <button
              @click="fetchRepositorio"
              class="text-sm text-[#0066FF] hover:text-[#3388ff] ml-2"
            >
              ↻ Atualizar
            </button>
          </div>
        </div>

        <div v-if="loadingRepositorio" class="text-center py-8 text-slate-400">Carregando...</div>
        <div v-else-if="repositorioFiltrado.length === 0" class="text-center py-8 text-slate-400">
          Nenhum envio encontrado.
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="env in repositorioFiltrado"
            :key="env.id"
            class="rounded-lg border overflow-hidden"
            :class="{
              'border-emerald-500/20': env.status === 'processado',
              'border-blue-500/20': env.status === 'enviado',
              'border-red-500/20': env.status === 'erro',
            }"
            style="background: #0a1024"
          >
            <!-- Header do envio -->
            <div
              class="px-4 py-3 cursor-pointer hover:bg-white/[0.02] transition-colors"
              @click="toggleRepoExpand(env.id)"
            >
              <div class="flex items-center gap-3">
                <span class="text-slate-600 text-xs">{{
                  expandedRepoId === env.id ? '▲' : '▼'
                }}</span>
                <span
                  :class="{
                    'bg-emerald-500/10 text-emerald-400': env.status === 'processado',
                    'bg-blue-500/10 text-blue-400': env.status === 'enviado',
                    'bg-red-500/10 text-red-400': env.status === 'erro',
                  }"
                  class="px-2 py-0.5 rounded text-xs font-medium w-24 text-center"
                >
                  {{
                    env.status === 'processado'
                      ? 'Processado'
                      : env.status === 'enviado'
                        ? 'Enviado'
                        : 'Erro'
                  }}
                </span>
                <span
                  class="px-2 py-0.5 rounded text-xs w-24 text-center"
                  :class="
                    env.ambiente === '1'
                      ? 'bg-red-500/10 text-red-400'
                      : 'bg-emerald-500/10 text-emerald-400'
                  "
                >
                  {{ env.ambiente === '1' ? 'PRODUÇÃO' : 'Homologação' }}
                </span>
                <span
                  class="px-2 py-0.5 rounded text-xs"
                  :class="
                    env.modo === 'inclusao'
                      ? 'bg-blue-500/10 text-blue-400'
                      : 'bg-purple-500/10 text-purple-400'
                  "
                >
                  {{ env.modo === 'inclusao' ? 'Inclusão' : 'Alteração' }}
                </span>
                <span class="text-sm text-white font-mono">{{ env.total_eventos }} rubrica(s)</span>
                <span class="text-xs text-slate-500 ml-auto">{{ formatDate(env.created_at) }}</span>
              </div>
              <!-- Resumo rápido das rubricas -->
              <div
                v-if="env.rubrica_detalhes && env.rubrica_detalhes.length > 0"
                class="mt-1.5 flex gap-1.5 flex-wrap"
              >
                <span
                  v-for="rub in env.rubrica_detalhes.slice(0, 10)"
                  :key="rub.cod_rubrica"
                  class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-white/5 text-slate-400"
                >
                  #{{ rub.cod_rubrica }}
                </span>
                <span v-if="env.rubrica_detalhes.length > 10" class="text-[10px] text-slate-600">
                  +{{ env.rubrica_detalhes.length - 10 }} mais
                </span>
              </div>
            </div>

            <!-- Detalhes expandidos -->
            <div
              v-if="expandedRepoId === env.id"
              class="px-4 pb-4"
              style="border-top: 1px solid rgba(255, 255, 255, 0.05)"
            >
              <!-- Grid de informações do envio -->
              <div
                class="grid grid-cols-2 md:grid-cols-4 gap-3 py-3 mb-3"
                style="border-bottom: 1px solid rgba(255, 255, 255, 0.05)"
              >
                <div>
                  <span class="text-[10px] text-slate-600 uppercase tracking-wide">Protocolo</span>
                  <p class="text-sm text-[#0066FF] font-mono mt-0.5 break-all">
                    {{ env.protocolo_envio || '—' }}
                  </p>
                </div>
                <div>
                  <span class="text-[10px] text-slate-600 uppercase tracking-wide">Vigência</span>
                  <p class="text-sm text-white font-mono mt-0.5">{{ env.ini_valid || '—' }}</p>
                </div>
                <div>
                  <span class="text-[10px] text-slate-600 uppercase tracking-wide">Data Envio</span>
                  <p class="text-sm text-slate-300 mt-0.5">{{ formatDate(env.created_at) }}</p>
                </div>
                <div>
                  <span class="text-[10px] text-slate-600 uppercase tracking-wide"
                    >Cód. Resposta</span
                  >
                  <p
                    :class="env.codigo_resposta === '201' ? 'text-emerald-400' : 'text-red-400'"
                    class="text-sm font-mono mt-0.5"
                  >
                    {{ env.codigo_resposta || '—' }}
                    {{ env.descricao_resposta ? '— ' + env.descricao_resposta : '' }}
                  </p>
                </div>
              </div>

              <!-- Tabela detalhada de rubricas -->
              <div v-if="env.rubrica_detalhes && env.rubrica_detalhes.length > 0">
                <h4 class="text-xs text-slate-500 font-medium mb-2">
                  Detalhamento por Rubrica ({{ env.rubrica_detalhes.length }})
                </h4>
                <div class="overflow-x-auto">
                  <table class="w-full text-xs">
                    <thead>
                      <tr class="border-b border-white/10">
                        <th class="py-1.5 px-2 text-left text-slate-500 font-medium">#</th>
                        <th class="py-1.5 px-2 text-left text-slate-500 font-medium">Código</th>
                        <th class="py-1.5 px-2 text-left text-slate-500 font-medium">Descrição</th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">Natureza</th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">
                          INSS Antes
                        </th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">
                          INSS Novo
                        </th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">
                          IRRF Antes
                        </th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">
                          IRRF Novo
                        </th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">
                          FGTS Antes
                        </th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">
                          FGTS Novo
                        </th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">Recibo</th>
                        <th class="py-1.5 px-2 text-center text-slate-500 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="(rub, ri) in env.rubrica_detalhes"
                        :key="ri"
                        class="border-b border-white/5 hover:bg-white/[0.02]"
                      >
                        <td class="py-1.5 px-2 text-slate-600">{{ ri + 1 }}</td>
                        <td class="py-1.5 px-2 text-white font-mono font-medium">
                          {{ rub.cod_rubrica }}
                        </td>
                        <td
                          class="py-1.5 px-2 text-slate-300 max-w-[180px] truncate"
                          :title="rub.descricao"
                        >
                          {{ rub.descricao }}
                        </td>
                        <td class="py-1.5 px-2 text-center text-slate-400 font-mono">
                          {{ rub.nat_rubr }}
                        </td>
                        <!-- INSS antes/novo -->
                        <td class="py-1.5 px-2 text-center">
                          <span
                            v-if="rub.incid_inss && rub.incid_inss !== rub.inss_correto"
                            class="text-red-400 font-mono"
                            >{{ rub.incid_inss }}</span
                          >
                          <span v-else class="text-slate-600 font-mono">{{
                            rub.incid_inss || '—'
                          }}</span>
                        </td>
                        <td class="py-1.5 px-2 text-center text-emerald-400 font-mono font-medium">
                          {{ rub.inss_correto }}
                        </td>
                        <!-- IRRF antes/novo -->
                        <td class="py-1.5 px-2 text-center">
                          <span
                            v-if="rub.incid_irrf && rub.incid_irrf !== rub.irrf_correto"
                            class="text-red-400 font-mono"
                            >{{ rub.incid_irrf }}</span
                          >
                          <span v-else class="text-slate-600 font-mono">{{
                            rub.incid_irrf || '—'
                          }}</span>
                        </td>
                        <td class="py-1.5 px-2 text-center text-emerald-400 font-mono font-medium">
                          {{ rub.irrf_correto }}
                        </td>
                        <!-- FGTS antes/novo -->
                        <td class="py-1.5 px-2 text-center">
                          <span
                            v-if="rub.incid_fgts && rub.incid_fgts !== rub.fgts_correto"
                            class="text-red-400 font-mono"
                            >{{ rub.incid_fgts }}</span
                          >
                          <span v-else class="text-slate-600 font-mono">{{
                            rub.incid_fgts || '—'
                          }}</span>
                        </td>
                        <td class="py-1.5 px-2 text-center text-emerald-400 font-mono font-medium">
                          {{ rub.fgts_correto }}
                        </td>
                        <!-- Recibo -->
                        <td class="py-1.5 px-2 text-center">
                          <code
                            v-if="getReciboForIndex(env, ri) !== '—'"
                            class="text-emerald-400 font-mono text-[10px] bg-emerald-500/10 px-1.5 py-0.5 rounded"
                          >
                            {{ getReciboForIndex(env, ri) }}
                          </code>
                          <span v-else class="text-slate-600">—</span>
                        </td>
                        <!-- Status do evento -->
                        <td class="py-1.5 px-2 text-center">
                          <span v-if="getEventoStatus(env, ri) === '201'" class="text-emerald-400"
                            >✓</span
                          >
                          <span v-else-if="getEventoStatus(env, ri)" class="text-red-400">✕</span>
                          <span v-else class="text-slate-600">—</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <!-- Totais / Sumário -->
                <div
                  class="mt-3 pt-2 grid grid-cols-3 gap-4 text-xs"
                  style="border-top: 1px solid rgba(255, 255, 255, 0.05)"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-slate-500">Total rubricas:</span>
                    <span class="text-white font-medium">{{ env.rubrica_detalhes.length }}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-slate-500">Com recibo:</span>
                    <span class="text-emerald-400 font-medium">{{ countRecibos(env) }}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-slate-500">Alterações de incidência:</span>
                    <span class="text-amber-400 font-medium">{{ countAlteracoes(env) }}</span>
                  </div>
                </div>

                <!-- Fundamentação Jurídica por rubrica -->
                <div
                  v-if="
                    env.rubrica_detalhes.some(
                      (r: any) => r.base_legal_inss || r.base_legal_irrf || r.base_legal_fgts,
                    )
                  "
                  class="mt-3 pt-3"
                  style="border-top: 1px solid rgba(255, 255, 255, 0.05)"
                >
                  <h4 class="text-xs text-slate-500 font-medium mb-2">
                    Fundamentação Jurídica das Alterações
                  </h4>
                  <div class="space-y-3">
                    <div
                      v-for="(rub, ri) in env.rubrica_detalhes"
                      :key="'legal-' + ri"
                      class="p-3 rounded-lg"
                      style="background: rgba(255, 255, 255, 0.02)"
                    >
                      <div class="flex items-center gap-2 mb-2">
                        <span class="text-white font-mono font-medium text-xs"
                          >#{{ rub.cod_rubrica }}</span
                        >
                        <span class="text-slate-400 text-xs">{{ rub.descricao }}</span>
                        <span v-if="rub.analise" class="ml-auto text-xs text-amber-400/80 italic">{{
                          rub.analise
                        }}</span>
                      </div>
                      <div class="grid grid-cols-1 gap-1.5 text-xs">
                        <div v-if="rub.base_legal_inss" class="flex items-start gap-2">
                          <span class="text-slate-600 shrink-0 w-10">INSS:</span>
                          <span class="text-slate-300">{{ rub.base_legal_inss }}</span>
                        </div>
                        <div v-if="rub.base_legal_irrf" class="flex items-start gap-2">
                          <span class="text-slate-600 shrink-0 w-10">IRRF:</span>
                          <span class="text-slate-300">{{ rub.base_legal_irrf }}</span>
                        </div>
                        <div v-if="rub.base_legal_fgts" class="flex items-start gap-2">
                          <span class="text-slate-600 shrink-0 w-10">FGTS:</span>
                          <span class="text-slate-300">{{ rub.base_legal_fgts }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Dados da Consulta -->
              <div
                v-if="env.recibo_consulta"
                class="mt-3 pt-3"
                style="border-top: 1px solid rgba(255, 255, 255, 0.05)"
              >
                <h4 class="text-xs text-slate-500 font-medium mb-2">
                  Resultado da Consulta ao eSocial
                </h4>
                <div class="grid grid-cols-3 gap-3 text-xs">
                  <div>
                    <span class="text-slate-600">Status Lote</span>
                    <p
                      :class="env.recibo_consulta.sucesso ? 'text-emerald-400' : 'text-red-400'"
                      class="font-medium mt-0.5"
                    >
                      {{
                        env.recibo_consulta.sucesso
                          ? 'Processado com sucesso'
                          : 'Erro no processamento'
                      }}
                    </p>
                  </div>
                  <div>
                    <span class="text-slate-600">Código</span>
                    <p class="text-slate-300 font-mono mt-0.5">
                      {{
                        env.recibo_consulta.codigo_resposta ||
                        env.recibo_consulta.codigo_resposta_lote ||
                        '—'
                      }}
                    </p>
                  </div>
                  <div>
                    <span class="text-slate-600">Consultado em</span>
                    <p class="text-slate-300 mt-0.5">{{ formatDate(env.updated_at) }}</p>
                  </div>
                </div>
                <!-- Ocorrências da consulta -->
                <div v-if="env.recibo_consulta.eventos" class="mt-2 space-y-1">
                  <div
                    v-for="(evt, ei) in env.recibo_consulta.eventos"
                    :key="ei"
                    class="flex items-center gap-2 text-xs"
                  >
                    <span v-if="evt.codigo_resposta === '201'" class="text-emerald-400">✓</span>
                    <span v-else class="text-red-400">✕</span>
                    <span class="text-slate-400">Evento {{ ei + 1 }}:</span>
                    <span class="text-slate-300">{{ evt.descricao }}</span>
                    <span v-if="evt.nr_recibo" class="text-emerald-400 font-mono ml-auto">{{
                      evt.nr_recibo
                    }}</span>
                    <div v-if="evt.ocorrencias && evt.ocorrencias.length > 0">
                      <span v-for="(oc, oi) in evt.ocorrencias" :key="oi" class="text-red-400 ml-2">
                        {{ oc.codigo }}: {{ oc.descricao }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Ações -->
              <div
                class="flex gap-2 mt-3 pt-3"
                style="border-top: 1px solid rgba(255, 255, 255, 0.05)"
              >
                <button
                  v-if="env.protocolo_envio && !env.recibo_consulta"
                  @click.stop="consultarProtocolo(env.protocolo_envio)"
                  class="px-3 py-1.5 text-xs bg-[#0066FF]/10 text-[#0066FF] hover:bg-[#0066FF]/20 rounded-lg transition-colors"
                >
                  Consultar Resultado
                </button>
                <button
                  @click.stop="exportarEnvioJSON(env)"
                  class="px-3 py-1.5 text-xs bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                  Exportar JSON
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" :class="['toast', toast.type]">{{ toast.msg }}</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import axios from 'axios'

const ESOCIAL_API =
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://celebrities-packing-trackbacks-between.trycloudflare.com'

// ── State ────────────────────────────────────────────────────────

const tabs = [
  { id: 'certificado', label: 'Certificado A1' },
  { id: 'enviar', label: 'Enviar S-1010' },
  { id: 'naturezas_invalidas', label: 'Naturezas Inválidas' },
  { id: 'historico', label: 'Histórico' },
  { id: 'repositorio', label: 'Repositório' },
]
const activeTab = ref('certificado')

// Certificado
const certStatus = ref<any>(null)
const certFile = ref<File | null>(null)
const certSenha = ref('')
const certUploading = ref(false)
const certRemoving = ref(false)
const certDragOver = ref(false)
const certInput = ref<HTMLInputElement | null>(null)
const senhaSalva = ref<any>(null)
const salvandoSenha = ref(false)
const senhaParaSalvar = ref('')
const removendoSenha = ref(false)

// Rubricas
const rubricas = ref<any[]>([])
const loadingRubricas = ref(true)
const selectedIds = ref<string[]>([])
const filtroRubricas = ref('pendentes')
const page = ref(1)
const perPage = 50
const editingNatureza = ref<string | null>(null)
const editNaturezaValue = ref('')
const salvandoNatureza = ref(false)
const naturezaInput = ref<HTMLInputElement | null>(null)

// Envio
const iniValid = ref(localStorage.getItem('esocial_iniValid') || getCurrentMonth())
const iniValidAuto = ref(localStorage.getItem('esocial_iniValidAuto') !== 'false') // persiste escolha
const iniValidEmpresa = ref('')
const iniValidEmpresaSalvo = ref(false)
const modoEnvio = ref(localStorage.getItem('esocial_modoEnvio') || 'inclusao')
const ambiente = ref(localStorage.getItem('esocial_ambiente') || '2') // '1' = produção, '2' = homologação
const enviando = ref(false)
const resultado = ref<any>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

// Persistir configurações de envio no localStorage
watch(iniValid, (v) => localStorage.setItem('esocial_iniValid', v))
watch(iniValidAuto, (v) => localStorage.setItem('esocial_iniValidAuto', String(v)))
watch(modoEnvio, (v) => localStorage.setItem('esocial_modoEnvio', v))
watch(ambiente, (v) => localStorage.setItem('esocial_ambiente', v))

// Consulta
const protocoloConsulta = ref('')
const consultando = ref(false)
const resultadoConsulta = ref<any>(null)

// Histórico
const envios = ref<any[]>([])
const loadingEnvios = ref(false)
const expandedEnvioId = ref<number | null>(null)

// Repositório
const repositorioEnvios = ref<any[]>([])
const loadingRepositorio = ref(false)
const expandedRepoId = ref<number | null>(null)
const repoFiltroAmbiente = ref('todos') // 'todos', '1', '2'
const repoFiltroStatus = ref('todos') // 'todos', 'processado', 'enviado', 'erro'

// Toast
const toast = ref<{ msg: string; type: 'ok' | 'err' } | null>(null)

// ── Computed ─────────────────────────────────────────────────────

const totalPages = computed(() => Math.ceil(rubricas.value.length / perPage))
const rubricasPaginadas = computed(() => {
  const start = (page.value - 1) * perPage
  return rubricas.value.slice(start, start + perPage)
})
const repositorioFiltrado = computed(() => {
  return repositorioEnvios.value.filter((env: any) => {
    if (repoFiltroAmbiente.value !== 'todos' && env.ambiente !== repoFiltroAmbiente.value)
      return false
    if (repoFiltroStatus.value !== 'todos' && env.status !== repoFiltroStatus.value) return false
    return true
  })
})
const naturezasExpiradas = computed(() => rubricas.value.filter((r: any) => r.nat_rubr_expirada))

// Mapa de sugestões manuais para naturezas expiradas (nat_rubr → sugestão)
const sugestoesNatureza: Record<string, { tipo: 'codigo' | 'nota'; valor: string }> = {
  '2920': { tipo: 'nota', valor: 'Consultar RH APPA' },
  '1801': { tipo: 'codigo', valor: '1299' },
}

// ── Helpers ──────────────────────────────────────────────────────

function getCurrentMonth(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
  } catch {
    return dateStr
  }
}

function showToast(msg: string, type: 'ok' | 'err' = 'ok') {
  toast.value = { msg, type }
  setTimeout(() => {
    toast.value = null
  }, 4000)
}

// ── Selection ────────────────────────────────────────────────────

function toggleSelect(codRubrica: string) {
  const idx = selectedIds.value.indexOf(codRubrica)
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(codRubrica)
  }
}

function toggleSelectAll() {
  if (selectedIds.value.length === rubricas.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = rubricas.value.map((r) => r.cod_rubrica)
  }
}

function toggleEnvioExpand(id: number) {
  expandedEnvioId.value = expandedEnvioId.value === id ? null : id
}

function toggleRepoExpand(id: number) {
  expandedRepoId.value = expandedRepoId.value === id ? null : id
}

// ── Editar Natureza ──────────────────────────────────────────────

function iniciarEditNatureza(rub: any) {
  editingNatureza.value = rub.cod_rubrica
  editNaturezaValue.value = rub.nat_rubr || ''
  nextTick(() => {
    const input = document.querySelector<HTMLInputElement>(
      'input[ref="naturezaInput"], .esocial-view input[maxlength="6"]',
    )
    input?.focus()
    input?.select()
  })
}

async function salvarNatureza(rub: any) {
  const novoValor = editNaturezaValue.value.trim()
  if (!novoValor || novoValor === rub.nat_rubr) {
    editingNatureza.value = null
    return
  }
  salvandoNatureza.value = true
  try {
    const resp = await axios.patch(`${ESOCIAL_API}/api/esocial/rubrica-natureza`, {
      cod_rubrica: rub.cod_rubrica,
      nova_natureza: novoValor,
    })
    // Atualizar localmente
    rub.nat_rubr = resp.data.nat_rubr
    rub.cod_natureza = resp.data.cod_natureza
    editingNatureza.value = null
    showToast(`Natureza da rubrica ${rub.cod_rubrica} alterada para ${novoValor}`, 'ok')
  } catch (err: any) {
    showToast(err.response?.data?.detail || 'Erro ao alterar natureza', 'err')
  } finally {
    salvandoNatureza.value = false
  }
}

function getEventoStatus(env: any, index: number): string | null {
  const eventos = env.recibo_consulta?.eventos
  if (eventos && eventos[index]) {
    return eventos[index].codigo_resposta
  }
  return null
}

function countRecibos(env: any): number {
  const eventos = env.recibo_consulta?.eventos
  if (!eventos) return 0
  return eventos.filter((e: any) => e.nr_recibo).length
}

function countAlteracoes(env: any): number {
  if (!env.rubrica_detalhes) return 0
  return env.rubrica_detalhes.filter(
    (r: any) =>
      (r.incid_inss && r.incid_inss !== r.inss_correto) ||
      (r.incid_irrf && r.incid_irrf !== r.irrf_correto) ||
      (r.incid_fgts && r.incid_fgts !== r.fgts_correto),
  ).length
}

function exportarEnvioJSON(env: any) {
  const data = {
    envio_id: env.id,
    tipo_evento: env.tipo_evento,
    modo: env.modo,
    ambiente: env.ambiente === '1' ? 'producao' : 'homologacao',
    ambiente_codigo: env.ambiente,
    ini_valid: env.ini_valid,
    status: env.status,
    protocolo_envio: env.protocolo_envio,
    codigo_resposta: env.codigo_resposta,
    descricao_resposta: env.descricao_resposta,
    total_eventos: env.total_eventos,
    data_envio: env.created_at,
    data_consulta: env.updated_at,
    rubricas: (env.rubrica_detalhes || []).map((rub: any, i: number) => ({
      seq: i + 1,
      cod_rubrica: rub.cod_rubrica,
      descricao: rub.descricao,
      cod_natureza: rub.cod_natureza || null,
      nat_rubr: rub.nat_rubr,
      incidencia_antes: {
        inss: rub.incid_inss || null,
        irrf: rub.incid_irrf || null,
        fgts: rub.incid_fgts || null,
      },
      incidencia_correta: {
        inss: rub.inss_correto,
        irrf: rub.irrf_correto,
        fgts: rub.fgts_correto,
      },
      fundamentacao_juridica: {
        inss: rub.base_legal_inss || null,
        irrf: rub.base_legal_irrf || null,
        fgts: rub.base_legal_fgts || null,
      },
      analise: rub.analise || null,
      nr_recibo: getReciboForIndex(env, i) !== '—' ? getReciboForIndex(env, i) : null,
      status_evento: getEventoStatus(env, i),
    })),
    consulta: env.recibo_consulta || null,
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `envio_s1010_${env.id}_${env.ambiente === '1' ? 'prod' : 'hml'}.json`
  a.click()
  URL.revokeObjectURL(url)
  showToast('JSON exportado', 'ok')
}

function getRubricaDescricao(evt: any, index: number): string {
  const detalhes = resultadoConsulta.value?.envio_detalhes?.rubrica_detalhes
  if (detalhes && detalhes[index]) {
    return `Rubrica ${detalhes[index].cod_rubrica} — ${detalhes[index].descricao}`
  }
  return `Evento ${index + 1}`
}

function getRubricaDetalhe(index: number): any {
  const detalhes = resultadoConsulta.value?.envio_detalhes?.rubrica_detalhes
  return detalhes?.[index] || null
}

function getReciboForIndex(env: any, index: number): string {
  const eventos = env.recibo_consulta?.eventos
  if (eventos && eventos[index] && eventos[index].nr_recibo) {
    return eventos[index].nr_recibo
  }
  return '—'
}

// ── API Calls ────────────────────────────────────────────────────

async function uploadCert() {
  if (!certFile.value || (!certSenha.value && !senhaSalva.value?.saved)) return
  certUploading.value = true
  try {
    const form = new FormData()
    form.append('file', certFile.value)
    form.append('senha', certSenha.value || '')
    const resp = await axios.post(`${ESOCIAL_API}/api/certificados/upload`, form)
    certStatus.value = { ...resp.data, ativo: true }
    certFile.value = null
    certSenha.value = ''
    showToast(`Certificado importado — ${resp.data.titular}`, 'ok')
  } catch (err: any) {
    const status = err.response?.status || 'sem resposta'
    const detail = err.response?.data?.detail || err.message || 'Erro desconhecido'
    const msg = `[${status}] ${detail}`
    console.error('Upload certificado falhou:', { status, detail, fullError: err.response?.data })
    showToast(msg, 'err')
  } finally {
    certUploading.value = false
  }
}

async function removeCert() {
  if (!certStatus.value?.id) return
  certRemoving.value = true
  try {
    await axios.delete(`${ESOCIAL_API}/api/certificados/${certStatus.value.id}`)
    certStatus.value = { ativo: false }
    showToast('Certificado removido', 'ok')
  } catch (err: any) {
    showToast(err.response?.data?.detail || 'Erro ao remover certificado', 'err')
  } finally {
    certRemoving.value = false
  }
}

function onSelectCert(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    certFile.value = input.files[0]
  }
}

function onDropCert(e: DragEvent) {
  certDragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  const name = file?.name.toLowerCase() || ''
  if (file && (name.endsWith('.pfx') || name.endsWith('.p12'))) {
    certFile.value = file
  } else {
    showToast('Selecione um arquivo .pfx ou .p12', 'err')
  }
}

function formatCnpj(cnpj: string): string {
  if (!cnpj || cnpj.length !== 14) return cnpj || '—'
  return `${cnpj.slice(0, 2)}.${cnpj.slice(2, 5)}.${cnpj.slice(5, 8)}/${cnpj.slice(8, 12)}-${cnpj.slice(12)}`
}

async function fetchCertStatus() {
  try {
    const resp = await axios.get(`${ESOCIAL_API}/api/certificados/ativo`)
    certStatus.value = resp.data
  } catch {
    certStatus.value = { ativo: false }
  }
}

async function fetchSenhaSalva() {
  try {
    const resp = await axios.get(`${ESOCIAL_API}/api/certificados/senha/status`)
    senhaSalva.value = resp.data
  } catch {
    senhaSalva.value = { saved: false }
  }
}

async function salvarSenha() {
  if (!senhaParaSalvar.value) return
  salvandoSenha.value = true
  try {
    const form = new FormData()
    form.append('senha', senhaParaSalvar.value)
    const resp = await axios.post(`${ESOCIAL_API}/api/certificados/senha/salvar`, form)
    senhaSalva.value = resp.data
    senhaParaSalvar.value = ''
    showToast('Senha salva com sucesso — válida por 24h', 'ok')
  } catch (err: any) {
    showToast(err.response?.data?.detail || 'Erro ao salvar senha', 'err')
  } finally {
    salvandoSenha.value = false
  }
}

async function removerSenhaSalva() {
  removendoSenha.value = true
  try {
    await axios.delete(`${ESOCIAL_API}/api/certificados/senha/remover`)
    senhaSalva.value = { saved: false }
    showToast('Senha removida', 'ok')
  } catch (err: any) {
    showToast(err.response?.data?.detail || 'Erro ao remover senha', 'err')
  } finally {
    removendoSenha.value = false
  }
}

function setFiltro(f: string) {
  filtroRubricas.value = f
  page.value = 1
  fetchRubricas()
}

async function fetchRubricas() {
  loadingRubricas.value = true
  try {
    const resp = await axios.get(`${ESOCIAL_API}/api/esocial/rubricas-pendentes`, {
      params: { filtro: filtroRubricas.value },
    })
    rubricas.value = resp.data.rubricas
    // Atualizar ini_valid_empresa se veio do backend
    if (resp.data.ini_valid_empresa && !iniValidEmpresa.value) {
      iniValidEmpresa.value = resp.data.ini_valid_empresa
    }
  } catch {
    rubricas.value = []
    showToast('Erro ao carregar rubricas', 'err')
  } finally {
    loadingRubricas.value = false
  }
}

async function fetchConfigEmpresa() {
  try {
    const resp = await axios.get(`${ESOCIAL_API}/api/esocial/config-empresa`)
    if (resp.data.ini_valid_padrao) {
      iniValidEmpresa.value = resp.data.ini_valid_padrao
    }
  } catch {
    // silenciar
  }
}

async function salvarIniValidEmpresa() {
  if (!iniValidEmpresa.value) return
  try {
    await axios.post(`${ESOCIAL_API}/api/esocial/config-empresa`, {
      ini_valid_padrao: iniValidEmpresa.value,
    })
    iniValidEmpresaSalvo.value = true
    setTimeout(() => {
      iniValidEmpresaSalvo.value = false
    }, 3000)
    showToast(`Data empresa salva: ${iniValidEmpresa.value}`, 'ok')
    // Recarregar rubricas para atualizar iniValid resolvido
    fetchRubricas()
  } catch (err: any) {
    showToast(err.response?.data?.detail || 'Erro ao salvar', 'err')
  }
}

async function enviar() {
  if (selectedIds.value.length === 0) return
  if (!certStatus.value?.ativo) {
    showToast('Faça upload de um certificado A1 primeiro', 'err')
    return
  }

  // Confirmação de segurança para produção
  if (ambiente.value === '1') {
    const confirmed = confirm(
      `⚠️ ATENÇÃO: Você está prestes a enviar ${selectedIds.value.length} rubrica(s) para PRODUÇÃO.\n\nEsta ação é irreversível. Deseja continuar?`,
    )
    if (!confirmed) return
  }

  enviando.value = true
  resultado.value = null
  try {
    const resp = await axios.post(`${ESOCIAL_API}/api/esocial/s1010/enviar`, {
      rubrica_ids: selectedIds.value,
      ini_valid: iniValidAuto.value ? '' : iniValid.value,
      modo: modoEnvio.value,
      ambiente: ambiente.value,
    })
    resultado.value = resp.data
    if (resp.data.sucesso) {
      showToast(`Lote enviado! Protocolo: ${resp.data.protocolo}`, 'ok')
      // Refresh rubricas para mostrar status 'enviado'
      await fetchRubricas()
      await fetchRepositorio()
      selectedIds.value = []
      // Auto-poll para consultar o resultado
      startPolling(resp.data.protocolo)
    } else {
      showToast(resp.data.erro || resp.data.descricao || 'Erro no envio', 'err')
    }
  } catch (err: any) {
    const msg = err.response?.data?.detail || 'Erro ao enviar ao eSocial'
    showToast(msg, 'err')
    resultado.value = { sucesso: false, descricao: msg }
  } finally {
    enviando.value = false
  }
}

async function consultarProtocolo(protocolo: string) {
  if (!protocolo) return
  protocoloConsulta.value = protocolo
  consultando.value = true
  resultadoConsulta.value = null
  try {
    const resp = await axios.get(
      `${ESOCIAL_API}/api/esocial/s1010/consultar/${protocolo}?ambiente=${ambiente.value}`,
    )
    resultadoConsulta.value = resp.data
    if (resp.data.sucesso) {
      showToast(`Protocolo ${protocolo}: Processado com sucesso`, 'ok')
    } else {
      showToast(`Protocolo ${protocolo}: ${resp.data.descricao || 'Erro no processamento'}`, 'err')
    }
  } catch (err: any) {
    showToast(err.response?.data?.detail || 'Erro na consulta', 'err')
  } finally {
    consultando.value = false
  }
}

async function fetchEnvios() {
  loadingEnvios.value = true
  try {
    const resp = await axios.get(`${ESOCIAL_API}/api/esocial/envios`)
    envios.value = resp.data.envios
  } catch {
    envios.value = []
  } finally {
    loadingEnvios.value = false
  }
}

async function fetchRepositorio() {
  loadingRepositorio.value = true
  try {
    const resp = await axios.get(`${ESOCIAL_API}/api/esocial/envios`)
    repositorioEnvios.value = resp.data.envios
  } catch {
    repositorioEnvios.value = []
  } finally {
    loadingRepositorio.value = false
  }
}

function startPolling(protocolo: string) {
  stopPolling()
  let attempts = 0
  const maxAttempts = 60 // ~5 min (5s interval)
  pollTimer = setInterval(async () => {
    attempts++
    if (attempts > maxAttempts) {
      stopPolling()
      showToast('Tempo limite de polling atingido. Consulte manualmente.', 'err')
      return
    }
    try {
      const resp = await axios.get(
        `${ESOCIAL_API}/api/esocial/s1010/consultar/${protocolo}?ambiente=${ambiente.value}`,
      )
      const data = resp.data
      // Verificar se o lote foi processado (não está mais em fila)
      if (data.codigo_resposta && data.codigo_resposta !== '101') {
        stopPolling()
        // Verificar se todos os eventos tiveram sucesso
        const eventos = data.eventos || []
        const todosSucesso =
          eventos.length > 0 &&
          eventos.every((ev: any) => ['201', '202'].includes(String(ev.codigo_resposta)))
        if (todosSucesso) {
          showToast('✅ Todas as rubricas foram processadas com sucesso!', 'ok')
        } else {
          const erros = eventos.flatMap((ev: any) => ev.ocorrencias || [])
          const primeiro = erros[0]
          const msg = primeiro
            ? `❌ Código ${primeiro.codigo}: ${primeiro.descricao?.split('\n')[0]}`
            : '⚠️ Processamento concluído com erros.'
          showToast(msg, 'err')
        }
        // Atualizar as listas
        await fetchRubricas()
        await fetchEnvios()
        await fetchRepositorio()
        resultadoConsulta.value = data
      }
    } catch {
      // Silenciar erros de polling (eSocial pode demorar)
    }
  }, 5000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// ── Init ─────────────────────────────────────────────────────────

onMounted(() => {
  fetchCertStatus()
  fetchSenhaSalva()
  fetchRubricas()
  fetchEnvios()
  fetchRepositorio()
  fetchConfigEmpresa()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════
   ESocial S-1010 — Neural Glassmorphism Design
   Matching PainelView's brain-navigation aesthetic
   ═══════════════════════════════════════════════════ */

.esocial-view {
  --brain-blue: #5ac8f5;
  --brain-glow: rgba(90, 200, 245, 0.55);
  --brain-dim: rgba(90, 200, 245, 0.25);
  --brain-faint: rgba(90, 200, 245, 0.08);
  --glass-bg: rgba(8, 14, 36, 0.75);
  --glass-border: rgba(90, 200, 245, 0.12);
  --surface-dark: #0a1024;
  max-width: 1200px;
}

/* ── Tab Bar ─────────────────────────────────────── */

.header-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 0.8125rem;
  color: rgba(148, 163, 184, 0.8);
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  background: rgba(8, 14, 36, 0.5);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition:
    color 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease,
    background 0.25s ease;
}

.header-btn:hover {
  color: var(--brain-blue);
  border-color: rgba(90, 200, 245, 0.25);
  box-shadow: 0 0 12px rgba(90, 200, 245, 0.12);
  background: rgba(90, 200, 245, 0.05);
}

.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 1.5rem;
  padding: 4px;
  border-radius: 14px;
  background: rgba(8, 14, 36, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(148, 163, 184, 0.75);
  transition:
    color 0.25s ease,
    background 0.25s ease,
    box-shadow 0.35s ease;
  cursor: pointer;
  border: 1px solid transparent;
  background: transparent;
  position: relative;
  white-space: nowrap;
}

.tab-btn:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.04);
}

.tab-btn.active {
  color: var(--brain-blue);
  background: rgba(90, 200, 245, 0.08);
  border-color: rgba(90, 200, 245, 0.2);
  box-shadow:
    0 0 12px rgba(90, 200, 245, 0.15),
    inset 0 0 8px rgba(90, 200, 245, 0.04);
}

.tab-icon {
  width: 16px;
  height: 16px;
  opacity: 0.6;
  transition: opacity 0.25s ease;
}

.tab-btn.active .tab-icon {
  opacity: 1;
}

/* ── Glass Cards ─────────────────────────────────── */
.card {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid var(--glass-border);
  box-shadow:
    0 0 20px rgba(90, 200, 245, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.3);
  transition:
    border-color 0.3s ease,
    box-shadow 0.3s ease;
}

.card:hover {
  border-color: rgba(90, 200, 245, 0.18);
  box-shadow:
    0 0 24px rgba(90, 200, 245, 0.08),
    0 8px 32px rgba(0, 0, 0, 0.3);
}

/* ── Form Inputs ─────────────────────────────────── */
.input-field {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--surface-dark);
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  color: #fff;
  font-size: 0.875rem;
  outline: none;
  transition:
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.input-field:focus {
  border-color: var(--brain-blue);
  box-shadow: 0 0 12px rgba(90, 200, 245, 0.15);
}

/* ── Tables ──────────────────────────────────────── */
.esocial-view :deep(table) {
  border-collapse: separate;
  border-spacing: 0;
}

.esocial-view :deep(thead tr) {
  border-bottom: 1px solid rgba(90, 200, 245, 0.1);
}

.esocial-view :deep(thead th) {
  color: rgba(90, 200, 245, 0.6);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.esocial-view :deep(tbody tr) {
  transition:
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.esocial-view :deep(tbody tr:hover) {
  background: rgba(90, 200, 245, 0.03);
}

/* ── Status Badges ───────────────────────────────── */
.esocial-view :deep(.rounded) {
  transition: box-shadow 0.2s ease;
}

/* ── Drag & Drop Area ────────────────────────────── */
.esocial-view :deep(.border-dashed) {
  border-radius: 16px;
  transition:
    border-color 0.3s ease,
    background 0.3s ease,
    box-shadow 0.3s ease;
}

.esocial-view :deep(.border-dashed:hover) {
  box-shadow: 0 0 20px rgba(90, 200, 245, 0.06);
}

/* ── Buttons glow on hover ───────────────────────── */
.esocial-view :deep(button) {
  transition: all 0.25s ease;
}

.esocial-view :deep(.bg-emerald-600:hover) {
  box-shadow: 0 0 18px rgba(16, 185, 129, 0.35);
}

.esocial-view :deep(.bg-\[\\#0066FF\]:hover) {
  box-shadow: 0 0 18px rgba(0, 102, 255, 0.35);
}

/* ── Expandable sections ─────────────────────────── */
.esocial-view :deep([style*='background: #0a1024']) {
  background: rgba(8, 14, 36, 0.6) !important;
  backdrop-filter: blur(8px);
  border: 1px solid var(--glass-border) !important;
  border-radius: 12px !important;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.esocial-view :deep([style*='background: #0a1024']:hover) {
  border-color: rgba(90, 200, 245, 0.18) !important;
}

/* ── Header title glow ───────────────────────────── */
.esocial-view h1 {
  background: linear-gradient(135deg, #fff 0%, var(--brain-blue) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.esocial-view h2 {
  color: #e2e8f0;
  letter-spacing: -0.01em;
}

/* ── Scrollbar ───────────────────────────────────── */
.esocial-view :deep(::-webkit-scrollbar) {
  width: 6px;
  height: 6px;
}

.esocial-view :deep(::-webkit-scrollbar-track) {
  background: transparent;
}

.esocial-view :deep(::-webkit-scrollbar-thumb) {
  background: rgba(90, 200, 245, 0.15);
  border-radius: 3px;
}

.esocial-view :deep(::-webkit-scrollbar-thumb:hover) {
  background: rgba(90, 200, 245, 0.3);
}

/* ── Pagination ──────────────────────────────────── */
.esocial-view :deep(.flex.items-center.justify-center.gap-2.mt-4 button) {
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--glass-border);
  transition: all 0.2s ease;
}

.esocial-view :deep(.flex.items-center.justify-center.gap-2.mt-4 button:hover:not(:disabled)) {
  border-color: var(--brain-blue);
  box-shadow: 0 0 10px rgba(90, 200, 245, 0.15);
  color: var(--brain-blue);
}

/* ── Select dropdowns ────────────────────────────── */
.esocial-view :deep(select) {
  background: var(--surface-dark) !important;
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  transition: border-color 0.2s ease;
}

.esocial-view :deep(select:hover) {
  border-color: rgba(90, 200, 245, 0.25);
}

/* ── Toast ────────────────────────────────────────── */
.toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  padding: 0.75rem 1.5rem;
  border-radius: 14px;
  font-size: 0.875rem;
  font-weight: 500;
  z-index: 1000;
  backdrop-filter: blur(16px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.toast.ok {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.25);
  box-shadow:
    0 0 16px rgba(16, 185, 129, 0.15),
    0 8px 32px rgba(0, 0, 0, 0.4);
}

.toast.err {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.25);
  box-shadow:
    0 0 16px rgba(239, 68, 68, 0.15),
    0 8px 32px rgba(0, 0, 0, 0.4);
}

.toast-enter-active {
  animation: toastIn 0.35s cubic-bezier(0.22, 0.61, 0.36, 1);
}
.toast-leave-active {
  animation: toastIn 0.25s cubic-bezier(0.55, 0, 1, 0.45) reverse;
}

@keyframes toastIn {
  from {
    transform: translate3d(0, 1.5rem, 0) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translate3d(0, 0, 0) scale(1);
    opacity: 1;
  }
}

/* ── Code elements ───────────────────────────────── */
.esocial-view :deep(code) {
  border-radius: 6px;
}

/* ── Checkbox accent ─────────────────────────────── */
.esocial-view :deep(input[type='checkbox']) {
  accent-color: var(--brain-blue);
}
</style>
