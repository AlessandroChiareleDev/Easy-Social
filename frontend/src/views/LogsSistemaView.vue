<template>
  <div class="logs-view">
    <!-- Glass shapes -->
    <div class="glass-shapes">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
    </div>

    <!-- Horizontal Tabs -->
    <div class="tabs-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <ComunicacaoEsocialTab v-if="activeTab === 'comunicacao'" />
      <EventosEsocialTab v-if="activeTab === 'eventos'" />
      <PipelineAuditView v-if="activeTab === 'pipeline'" />
      <ProvaCorrecaoView v-if="activeTab === 'prova'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ComunicacaoEsocialTab from '../components/ComunicacaoEsocialTab.vue'
import EventosEsocialTab from '../components/EventosEsocialTab.vue'
import PipelineAuditView from './PipelineAuditView.vue'
import ProvaCorrecaoView from './ProvaCorrecaoView.vue'

const tabs = [
  { key: 'comunicacao', label: 'Comunicação eSocial' },
  { key: 'eventos', label: 'Eventos eSocial' },
  { key: 'pipeline', label: 'Pipeline Audit' },
  { key: 'prova', label: 'Prova de Correção' },
]

const activeTab = ref('comunicacao')
</script>

<style scoped>
.logs-view {
  position: relative;
  min-height: 100vh;
  padding: 24px 32px;
  color: #e0e6ed;
  font-family:
    'Inter',
    system-ui,
    -apple-system,
    sans-serif;
}

/* Glass background shapes */
.glass-shapes {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}
.glass-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.08;
}
.shape-1 {
  width: 600px;
  height: 600px;
  background: #0066ff;
  top: -100px;
  right: -100px;
}
.shape-2 {
  width: 400px;
  height: 400px;
  background: #00d4ff;
  bottom: 100px;
  left: -50px;
}
.shape-3 {
  width: 500px;
  height: 500px;
  background: #7c3aed;
  bottom: -150px;
  right: 200px;
}

/* Tabs bar */
.tabs-bar {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 0;
  border-bottom: 1px solid rgba(0, 102, 255, 0.2);
  margin-bottom: 0;
}

.tab-btn {
  padding: 14px 28px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: rgba(224, 230, 237, 0.5);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab-btn:hover {
  color: rgba(224, 230, 237, 0.8);
  background: rgba(0, 102, 255, 0.05);
}

.tab-btn.active {
  color: #0066ff;
  border-bottom-color: #0066ff;
  background: rgba(0, 102, 255, 0.08);
}

/* Tab content */
.tab-content {
  position: relative;
  z-index: 1;
}

/* Remove padding/glass from embedded views so they don't double up */
.tab-content :deep(.audit-view),
.tab-content :deep(.prova-view) {
  padding: 0 !important;
  min-height: auto !important;
}
.tab-content :deep(.audit-view > .glass-shapes),
.tab-content :deep(.prova-view > .glass-shapes) {
  display: none !important;
}
</style>
