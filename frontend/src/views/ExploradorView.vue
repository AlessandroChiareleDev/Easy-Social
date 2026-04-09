<template>
  <div class="explorador-wrapper">
    <div class="tabs-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <svg v-if="tab.key === 'eventos'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        {{ tab.label }}
      </button>
    </div>

    <ExploradorEventosView v-if="activeTab === 'eventos'" />
    <ExploradorDadosFuncionariosTab v-else-if="activeTab === 'funcionarios'" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ExploradorEventosView from './ExploradorEventosView.vue'
import ExploradorDadosFuncionariosTab from '../components/ExploradorDadosFuncionariosTab.vue'

const tabs = [
  { key: 'eventos', label: 'Explorador de Eventos' },
  { key: 'funcionarios', label: 'Dados Funcionários' },
]

const activeTab = ref('eventos')
</script>

<style scoped>
.explorador-wrapper {
  width: 100%;
}

.tabs-bar {
  display: flex;
  gap: 4px;
  padding: 0 4px;
  margin-bottom: 24px;
  border-bottom: 1px solid rgba(90, 200, 245, 0.1);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  color: #94a3b8;
  background: rgba(90, 200, 245, 0.04);
}

.tab-btn.active {
  color: #5ac8f5;
  border-bottom-color: #5ac8f5;
}

.tab-btn.active svg {
  filter: drop-shadow(0 0 4px rgba(90, 200, 245, 0.4));
}
</style>
