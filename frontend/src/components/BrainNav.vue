<template>
  <div class="brain-nav">
    <div class="brain-container">
      <!-- Bottom-left region — Arquivos, Folhas e Tabelas (relative to set container size) -->
      <img
        src="/brain-bottom-left.png"
        alt="Arquivos, Folhas e Tabelas"
        class="brain-region brain-region--base region-bottom-left"
        :class="{ hovered: hovered === 'arquivos' }"
        @mouseenter="hovered = 'arquivos'"
        @mouseleave="hovered = null"
        @click="$emit('select', 'arquivos')"
        draggable="false"
      />
      <!-- Bottom-right region — Rubricas -->
      <img
        src="/brain-bottom-right.png"
        alt="Rubricas"
        class="brain-region brain-region--overlay region-bottom-right"
        :class="{ hovered: hovered === 'rubricas' }"
        @mouseenter="hovered = 'rubricas'"
        @mouseleave="hovered = null"
        @click="$emit('select', 'rubricas')"
        draggable="false"
      />
      <!-- Top region — Automação eSocial -->
      <img
        src="/brain-top.png"
        alt="Automação eSocial"
        class="brain-region brain-region--overlay region-top"
        :class="{ hovered: hovered === 'automacao' }"
        @mouseenter="hovered = 'automacao'"
        @mouseleave="hovered = null"
        @click="$emit('select', 'automacao')"
        draggable="false"
      />

      <!-- Region label tooltip -->
      <transition name="label-fade">
        <div v-if="hovered" class="region-label" :class="labelPosition">
          {{ regionLabels[hovered] }}
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const hovered = ref<string | null>(null)

const regionLabels: Record<string, string> = {
  automacao: 'Automação eSocial',
  arquivos: 'Arquivos, Folhas e Tabelas',
  rubricas: 'Rubricas',
}

const labelPosition = computed(() => {
  if (hovered.value === 'automacao') return 'label-top'
  if (hovered.value === 'arquivos') return 'label-bottom-left'
  if (hovered.value === 'rubricas') return 'label-bottom-right'
  return ''
})

defineEmits<{
  select: [region: string]
}>()
</script>

<style scoped>
.brain-nav {
  display: flex;
  justify-content: center;
  align-items: center;
}

.brain-container {
  position: relative;
  width: 100%;
  max-width: 400px;
}

.brain-region {
  width: 100%;
  height: auto;
  display: block;
  cursor: pointer;
  transition: filter 0.25s ease;
  user-select: none;
}

.brain-region--base {
  position: relative;
}

.brain-region--overlay {
  position: absolute;
  top: 0;
  left: 0;
}

/*
 * CLIP-PATH polygons — match the Python polygon masks exactly.
 * Coordinates are percentages of the image (1536×1024).
 * This ensures pointer events ONLY fire within each region's visible area.
 */

/* Top region: above the horizontal sulcus boundary */
.region-top {
  clip-path: polygon(
    0% 0%,
    100% 0%,
    100% 50.3%,
    91.1% 50.3%,
    87.9% 49.8%,
    80.7% 48.8%,
    74.2% 47.9%,
    67.7% 46.9%,
    61.2% 45.9%,
    55.3% 44.7%,
    50% 44.4%,
    44.3% 44.7%,
    37.8% 45.4%,
    31.3% 46.4%,
    24.7% 47.9%,
    18.2% 49.8%,
    13% 51.3%,
    8.8% 51.8%,
    0% 51.8%
  );
}

/* Bottom-left region: below sulcus, left of longitudinal fissure */
.region-bottom-left {
  clip-path: polygon(
    0% 51.8%,
    8.8% 51.8%,
    13% 51.3%,
    18.2% 49.8%,
    24.7% 47.9%,
    31.3% 46.4%,
    37.8% 45.4%,
    44.3% 44.7%,
    50% 44.4%,
    49.9% 48.8%,
    49.7% 53.7%,
    49.6% 58.6%,
    49.5% 63.5%,
    49.3% 68.4%,
    49.2% 73.2%,
    49.2% 78.1%,
    49.1% 83%,
    49% 87.9%,
    49% 91.8%,
    48.8% 100%,
    0% 100%
  );
}

/* Bottom-right region: below sulcus, right of longitudinal fissure */
.region-bottom-right {
  clip-path: polygon(
    48.8% 100%,
    49% 91.8%,
    49% 87.9%,
    49.1% 83%,
    49.2% 78.1%,
    49.2% 73.2%,
    49.3% 68.4%,
    49.5% 63.5%,
    49.6% 58.6%,
    49.7% 53.7%,
    49.9% 48.8%,
    50% 44.4%,
    55.3% 44.7%,
    61.2% 45.9%,
    67.7% 46.9%,
    74.2% 47.9%,
    80.7% 48.8%,
    87.9% 49.8%,
    91.1% 50.3%,
    100% 50.3%,
    100% 100%
  );
}

.brain-region:hover,
.brain-region.hovered {
  filter: brightness(1.4) drop-shadow(0 0 16px rgba(77, 201, 246, 0.6));
  z-index: 2;
}

/* Region label tooltip */
.region-label {
  position: absolute;
  padding: 6px 14px;
  background: rgba(13, 21, 48, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(77, 201, 246, 0.35);
  border-radius: 8px;
  color: #4dc9f6;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  pointer-events: none;
  z-index: 10;
}

.label-top {
  top: 15%;
  left: 50%;
  transform: translateX(-50%);
}

.label-bottom-left {
  bottom: 15%;
  left: 15%;
}

.label-bottom-right {
  bottom: 15%;
  right: 15%;
}

.label-fade-enter-active,
.label-fade-leave-active {
  transition: opacity 0.2s ease;
}

.label-fade-enter-from,
.label-fade-leave-to {
  opacity: 0;
}
</style>
