<template>
  <div class="min-h-screen relative overflow-hidden painel-bg">
    <!-- Animated glassmorphism shapes -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
      <div class="glass-shape shape-4"></div>
      <div class="glass-shape shape-5"></div>
      <div class="glass-shape shape-6"></div>
      <div class="glass-shape shape-7"></div>
      <div class="glass-shape shape-8"></div>
    </div>

    <!-- Top bar -->
    <div class="relative z-10 flex items-center justify-between px-8 pt-3">
      <div class="flex items-center gap-3">
        <BrandLogo :size="52" :speed="4" />
        <span class="text-white/80 font-semibold text-lg"
          >Easy <span class="text-[#0066FF]">e-Social</span></span
        >
      </div>

      <div class="flex items-center gap-3">
        <!-- Trocar empresa -->
        <button
          @click="trocarEmpresa"
          class="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 text-white/80 rounded-lg text-sm font-medium backdrop-blur-sm transition-all duration-200"
        >
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M3 21h18M9 8h1M9 12h1M9 16h1M14 8h1M14 12h1M14 16h1M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"
            />
          </svg>
          {{ authStore.empresaSelecionada?.nome }}
        </button>

        <button
          @click="handleLogout"
          class="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/40 border border-red-400/30 text-red-100 rounded-lg text-sm font-medium backdrop-blur-sm transition-all duration-200"
        >
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Sair
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="relative z-10 flex items-center justify-center px-8 mt-2 pb-4">
      <div class="w-full max-w-4xl animate-fade-in">
        <!-- Header -->
        <div class="text-center mb-2">
          <div
            class="inline-flex items-center gap-2 px-4 py-1.5 bg-white/10 backdrop-blur-sm rounded-full border border-white/15 text-white/70 text-xs font-medium mb-2"
          >
            <svg
              class="w-3.5 h-3.5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <rect x="14" y="14" width="7" height="7" rx="1" />
            </svg>
            {{ authStore.empresaSelecionada?.nome }}
          </div>
          <h1 class="text-2xl font-bold text-white mb-1">Painel de Controle</h1>
          <p class="text-white/50 text-sm">Clique em uma região do cérebro para navegar</p>
        </div>

        <!-- Interactive brain navigation -->
        <div class="flex flex-col items-center">
          <BrainNav @select="onBrainSelect" />

          <!-- Neural branch expansion — always in DOM for smooth transitions -->
          <div v-if="displayedGroup" class="dendrite-panel" :class="panelPhase">
            <!-- SVG neural wires + particles -->
            <svg
              class="neural-wires-svg"
              :viewBox="`0 0 ${svgW} ${svgH}`"
              preserveAspectRatio="xMidYMid meet"
            >
              <defs>
                <filter id="glow-particle">
                  <feGaussianBlur stdDeviation="3.5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
                <filter id="glow-wire">
                  <feGaussianBlur stdDeviation="2" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
                <radialGradient id="convergence-glow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stop-color="#5ac8f5" stop-opacity="0.6" />
                  <stop offset="60%" stop-color="#5ac8f5" stop-opacity="0.15" />
                  <stop offset="100%" stop-color="#5ac8f5" stop-opacity="0" />
                </radialGradient>
              </defs>

              <!-- Convergence glow at fork point -->
              <circle
                :cx="cx"
                :cy="forkY"
                r="18"
                fill="url(#convergence-glow)"
                class="convergence-pulse"
              />

              <!-- Wire paths -->
              <path
                v-for="(wire, wi) in wirePaths"
                :key="'w' + wi"
                :d="wire.d"
                fill="none"
                stroke="#5ac8f5"
                :stroke-width="wire.thick ? 2.5 : 1.2"
                :opacity="wire.opacity"
                filter="url(#glow-wire)"
                class="neural-wire"
                :style="{
                  '--wire-len': wire.len,
                  '--wire-delay': `${wi * 30}ms`,
                }"
              />

              <!-- Fork center dot -->
              <circle
                :cx="cx"
                :cy="forkY"
                r="3.5"
                fill="#5ac8f5"
                filter="url(#glow-particle)"
                class="fork-dot"
              />

              <!-- Particles -->
              <circle
                v-for="(p, pi) in particles"
                :key="'p' + pi"
                :r="p.r"
                fill="#5ac8f5"
                filter="url(#glow-particle)"
                :opacity="p.opacity"
                class="neural-particle"
              >
                <animateMotion
                  :dur="p.dur + 's'"
                  repeatCount="indefinite"
                  :begin="p.begin + 's'"
                  :path="p.path"
                  rotate="auto"
                />
              </circle>
            </svg>

            <!-- Cards at the end of branches -->
            <div class="neural-cards-row" :class="`cards-${displayedItems.length}`">
              <div
                v-for="(item, idx) in displayedItems"
                :key="item.to"
                class="neural-card"
                :style="{
                  '--i': idx,
                  '--total': displayedItems.length,
                }"
                @click="navigateTo(item.to)"
              >
                <div class="neural-card-glow"></div>
                <div class="neural-card-body">
                  <span class="neural-card-title">{{ item.label }}</span>
                  <span class="neural-card-desc">{{ item.description }}</span>
                </div>
                <svg
                  class="neural-card-arrow"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <path d="M9 18l6-6-6-6" />
                </svg>
              </div>
            </div>

            <!-- Group label + close -->
            <div class="neural-tag">
              <span>{{ displayedLabel }}</span>
              <button @click="retractAndClose" class="neural-close-btn">
                <svg
                  class="w-3.5 h-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import BrandLogo from '../components/BrandLogo.vue'
import BrainNav from '../components/BrainNav.vue'

const router = useRouter()
const authStore = useAuthStore()

// ── Phase state machine ──
// 'idle' → user clicks → 'expanding' → done
// 'idle' → user clicks close → 'retracting' → remove
// 'idle' → user clicks other region → 'retracting' → swap data → 'expanding' → done
type Phase = 'expanding' | 'idle' | 'retracting'

const displayedGroup = ref<string | null>(null)
const panelPhase = ref<Phase>('idle')
let pendingGroup: string | null = null
let phaseTimer: ReturnType<typeof setTimeout> | null = null

const RETRACT_DURATION = 350
const EXPAND_DELAY = 30 // small gap between retract end and expand start

const painelGroups = [
  {
    id: 'arquivos',
    label: 'Arquivos, Folhas e Tabelas',
    items: [
      {
        to: '/tabelas',
        label: 'Tabelas',
        description: 'Importar e gerenciar tabelas de folha de pagamento',
      },
      {
        to: '/cruzamento',
        label: 'Cruzamento',
        description: 'Cruzar dados entre tabelas e identificar divergências',
      },
      { to: '/depara', label: 'De-Para', description: 'Mapear códigos entre sistemas diferentes' },
    ],
  },
  {
    id: 'rubricas',
    label: 'Rubricas',
    items: [
      {
        to: '/validador',
        label: 'Validador',
        description: 'Validar rubricas contra regras e naturezas do eSocial',
      },
      {
        to: '/confirmar',
        label: 'Confirmar Alterações',
        description: 'Revisar e confirmar correções sugeridas',
      },
      {
        to: '/eb-cruzamento',
        label: 'EB Skills Cruzamentos',
        description: 'Cruzar rubricas com base EB Skills (448 registros)',
      },
    ],
  },
  {
    id: 'automacao',
    label: 'Automação eSocial',
    items: [
      {
        to: '/bot',
        label: 'Robô eSocial',
        description: 'Automação de processos no portal eSocial',
      },
      {
        to: '/esocial',
        label: 'eSocial S-1010',
        description: 'Envio de eventos S-1010 via web service',
      },
    ],
  },
]

const displayedLabel = computed(() => {
  return painelGroups.find((g) => g.id === displayedGroup.value)?.label ?? ''
})

const displayedItems = computed(() => {
  return painelGroups.find((g) => g.id === displayedGroup.value)?.items ?? []
})

// SVG dimensions
const svgW = 800
const svgH = 350
const cx = svgW / 2 // center X
const forkY = 120 // where the trunk forks into branches
const bottomY = svgH // bottom of SVG (where cards are)

// Trunk wires: 6 parallel wires going straight down from brain center
const trunkOffsets = [-5, -2.5, -0.5, 0.5, 2.5, 5]

// Compute card X targets based on item count
function cardTargets(count: number): number[] {
  if (count === 2) return [cx - 160, cx + 160]
  return [cx - 220, cx, cx + 220] // 3 items
}

// Build wire paths as a TREE: trunk → fork → branches
const wirePaths = computed(() => {
  const count = displayedItems.value.length
  const targets = cardTargets(count)
  const paths: { d: string; opacity: number; thick: boolean; len: number }[] = []

  // === TRUNK: vertical bundle from brain center going down ===
  trunkOffsets.forEach((off, i) => {
    const wobble = (i % 2 === 0 ? 1 : -1) * (2 + (i % 3))
    const x = cx + off
    const d = `M${x},0 C${x + wobble},${forkY * 0.3} ${x - wobble * 0.5},${forkY * 0.65} ${cx},${forkY}`
    paths.push({ d, opacity: 0.25 + (i % 3) * 0.1, thick: false, len: forkY + 20 })
  })

  // === BRANCHES: fork out from trunk center to each card ===
  // More wires per branch for visual density
  targets.forEach((tx, ti) => {
    const dx = tx - cx
    const branchLen = bottomY - forkY
    const isCenter = Math.abs(dx) < 10

    // Main thick branch
    const cp1x = cx + dx * 0.15
    const cp1y = forkY + branchLen * 0.3
    const cp2x = cx + dx * 0.6
    const cp2y = forkY + branchLen * 0.65
    const d = `M${cx},${forkY} C${cp1x},${cp1y} ${cp2x},${cp2y} ${tx},${bottomY}`
    paths.push({ d, opacity: 0.5, thick: true, len: 280 })

    // Flanking wires — more for center branch so it doesn't look thin
    const flanks = isCenter
      ? [
          { ox: -6, oy1: -8, oy2: 6 },
          { ox: 6, oy1: 6, oy2: -8 },
          { ox: -3, oy1: -4, oy2: 10 },
          { ox: 3, oy1: 10, oy2: -4 },
        ]
      : [
          { ox: ti % 2 === 0 ? -8 : 8, oy1: -10, oy2: 5 },
          { ox: ti % 2 === 0 ? 8 : -8, oy1: 10, oy2: -5 },
          { ox: ti % 2 === 0 ? -4 : 4, oy1: -5, oy2: 8 },
        ]

    flanks.forEach((f, fi) => {
      const fd = `M${cx},${forkY} C${cp1x + f.ox},${cp1y + f.oy1} ${cp2x + f.ox * 0.5},${cp2y + f.oy2} ${tx},${bottomY}`
      paths.push({ d: fd, opacity: 0.15 + fi * 0.05, thick: false, len: 270 - fi * 5 })
    })
  })

  return paths
})

// Particles: energy traveling from brain → trunk → branch → card
const particles = computed(() => {
  const count = displayedItems.value.length
  const targets = cardTargets(count)
  const pts: { path: string; dur: number; begin: number; r: number; opacity: number }[] = []

  // Full path particles: trunk + branch (equal distribution per target)
  trunkOffsets.forEach((off, i) => {
    const wobble = (i % 2 === 0 ? 1 : -1) * (2 + (i % 3))
    const x = cx + off
    const trunkPath = `M${x},0 C${x + wobble},${forkY * 0.3} ${x - wobble * 0.5},${forkY * 0.65} ${cx},${forkY}`

    // Each trunk wire feeds into a specific branch (equally distributed)
    const ti = i % targets.length
    const tx = targets[ti]!
    const dx = tx - cx
    const cp1x = cx + dx * 0.15
    const cp1y = forkY + (bottomY - forkY) * 0.3
    const cp2x = cx + dx * 0.6
    const cp2y = forkY + (bottomY - forkY) * 0.65
    const branchPath = `C${cp1x},${cp1y} ${cp2x},${cp2y} ${tx},${bottomY}`

    const fullPath = `${trunkPath} ${branchPath}`
    const dur = 2.2 + (i % 4) * 0.4
    const begin = i * 0.4

    pts.push({ path: fullPath, dur, begin, r: 2.5 + (i % 2), opacity: 0.7 + (i % 3) * 0.1 })
  })

  // Extra particles on branches only (2 per branch)
  targets.forEach((tx, i) => {
    const dx = tx - cx
    const cp1x = cx + dx * 0.15
    const cp1y = forkY + (bottomY - forkY) * 0.3
    const cp2x = cx + dx * 0.6
    const cp2y = forkY + (bottomY - forkY) * 0.65
    const path = `M${cx},${forkY} C${cp1x},${cp1y} ${cp2x},${cp2y} ${tx},${bottomY}`
    pts.push({ path, dur: 1.4 + i * 0.25, begin: 0.3 + i * 0.5, r: 2.2, opacity: 0.6 })
    pts.push({ path, dur: 1.7 + i * 0.2, begin: 0.9 + i * 0.35, r: 1.8, opacity: 0.5 })
  })

  return pts
})

function clearTimer() {
  if (phaseTimer) {
    clearTimeout(phaseTimer)
    phaseTimer = null
  }
}

function expandGroup(groupId: string) {
  displayedGroup.value = groupId
  // Force DOM update, then trigger expanding on next frame for CSS transition
  nextTick(() => {
    requestAnimationFrame(() => {
      panelPhase.value = 'expanding'
    })
  })
}

function onBrainSelect(region: string) {
  clearTimer()

  if (displayedGroup.value === region && panelPhase.value !== 'retracting') {
    // Toggle off: retract then remove
    panelPhase.value = 'retracting'
    pendingGroup = null
    phaseTimer = setTimeout(() => {
      displayedGroup.value = null
      panelPhase.value = 'idle'
    }, RETRACT_DURATION)
  } else if (displayedGroup.value && panelPhase.value !== 'retracting') {
    // Switch: retract old → swap data → expand new
    panelPhase.value = 'retracting'
    pendingGroup = region
    phaseTimer = setTimeout(() => {
      // Swap data while retracted (DOM stays, content changes)
      displayedGroup.value = pendingGroup
      pendingGroup = null
      // Tiny gap then expand
      phaseTimer = setTimeout(() => {
        panelPhase.value = 'expanding'
      }, EXPAND_DELAY)
    }, RETRACT_DURATION)
  } else if (!displayedGroup.value) {
    // Fresh open
    expandGroup(region)
  }
}

function retractAndClose() {
  clearTimer()
  panelPhase.value = 'retracting'
  pendingGroup = null
  phaseTimer = setTimeout(() => {
    displayedGroup.value = null
    panelPhase.value = 'idle'
  }, RETRACT_DURATION)
}

function navigateTo(path: string) {
  router.push(path)
}

function trocarEmpresa() {
  router.push('/empresas')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 400ms ease;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-down {
  animation: slideDown 200ms ease;
}
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Neural branch panel ── */
.dendrite-panel {
  --brain-blue: #5ac8f5;
  --brain-glow: rgba(90, 200, 245, 0.55);
  --brain-dim: rgba(90, 200, 245, 0.35);
  --brain-faint: rgba(90, 200, 245, 0.12);
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  margin-top: -100px;
  position: relative;
  z-index: 1;
  pointer-events: none;
}

.dendrite-panel > * {
  pointer-events: auto;
}

/* ── SVG wires container ── */
.neural-wires-svg {
  width: 100%;
  max-width: 800px;
  height: auto;
  overflow: visible;
  will-change: opacity;
  transition: opacity 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

.retracting .neural-wires-svg {
  opacity: 0;
}

/* ── Convergence glow pulse ── */
.convergence-pulse {
  opacity: 0.6;
  transition: opacity 250ms ease;
}

.expanding .convergence-pulse {
  opacity: 0.6;
  animation: convPulse 2s ease-in-out infinite;
}

.retracting .convergence-pulse {
  opacity: 0;
}

@keyframes convPulse {
  0%,
  100% {
    opacity: 0.6;
    r: 18;
  }
  50% {
    opacity: 1;
    r: 24;
  }
}

/* ── Wire draw-in / retract via stroke-dashoffset ── */
.neural-wire {
  stroke-dasharray: var(--wire-len);
  stroke-dashoffset: var(--wire-len);
  will-change: stroke-dashoffset;
  transition: stroke-dashoffset 450ms cubic-bezier(0.22, 0.61, 0.36, 1);
  transition-delay: var(--wire-delay, 0ms);
}

.expanding .neural-wire {
  stroke-dashoffset: 0;
}

.retracting .neural-wire {
  stroke-dashoffset: var(--wire-len);
  transition: stroke-dashoffset 300ms cubic-bezier(0.55, 0, 1, 0.45);
  transition-delay: 0ms;
}

/* Fork dot */
.fork-dot {
  opacity: 0;
  transition: opacity 200ms ease;
}

.expanding .fork-dot {
  opacity: 0.9;
  transition-delay: 200ms;
}

.retracting .fork-dot {
  opacity: 0;
  transition-delay: 0ms;
}

/* Particles hidden during retract */
.neural-particle {
  transition: opacity 200ms ease;
}

.retracting .neural-particle {
  opacity: 0 !important;
}

/* ── Cards row ── */
.neural-cards-row {
  display: flex;
  justify-content: center;
  gap: 16px;
  width: 100%;
  max-width: 800px;
  margin-top: -2px;
}

.cards-2 {
  padding: 0 80px;
}

.cards-3 {
  padding: 0 20px;
}

/* ── Neural card ── */
.neural-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(8, 14, 36, 0.75);
  backdrop-filter: blur(16px);
  border: 2px solid var(--brain-blue);
  border-radius: 14px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
  box-shadow:
    0 0 14px var(--brain-glow),
    0 0 36px var(--brain-faint),
    inset 0 0 12px rgba(90, 200, 245, 0.04);
  overflow: hidden;

  /* Default: retracted state (hidden) */
  opacity: 0;
  transform: translate3d(0, -120px, 0) scale(0.2);
  will-change: transform, opacity;
  transition:
    transform 420ms cubic-bezier(0.22, 0.61, 0.36, 1),
    opacity 350ms cubic-bezier(0.22, 0.61, 0.36, 1),
    border-color 0.3s ease,
    background 0.3s ease,
    box-shadow 0.3s ease;
  transition-delay: calc(var(--i, 0) * 70ms);
}

/* Expand: cards descend into place */
.expanding .neural-card {
  opacity: 1;
  transform: translate3d(0, 0, 0) scale(1);
}

/* Retract: cards fly back up to brain */
.retracting .neural-card {
  opacity: 0;
  transform: translate3d(0, -180px, 0) scale(0.15);
  transition:
    transform 320ms cubic-bezier(0.55, 0, 1, 0.45),
    opacity 280ms cubic-bezier(0.55, 0, 0.68, 0.28);
  transition-delay: calc((var(--total, 3) - 1 - var(--i, 0)) * 45ms);
}

/* Pulsing glow overlay on card border */
.neural-card-glow {
  position: absolute;
  inset: -2px;
  border-radius: 16px;
  border: 2px solid var(--brain-blue);
  opacity: 0;
  pointer-events: none;
}

.expanding .neural-card-glow {
  animation: cardBorderPulse 2.5s ease-in-out 1s infinite;
}

@keyframes cardBorderPulse {
  0%,
  100% {
    opacity: 0;
    box-shadow: 0 0 10px var(--brain-glow);
  }
  50% {
    opacity: 0.7;
    box-shadow:
      0 0 24px var(--brain-glow),
      0 0 48px var(--brain-faint);
  }
}

.neural-card:hover {
  border-color: #7dd8f9;
  background: rgba(14, 24, 56, 0.9);
  box-shadow:
    0 0 28px var(--brain-glow),
    0 0 60px rgba(90, 200, 245, 0.25),
    inset 0 0 20px rgba(90, 200, 245, 0.06);
  transform: translate3d(0, -3px, 0) scale(1) !important;
}

.neural-card:hover .neural-card-glow {
  animation: none;
  opacity: 1;
  box-shadow: 0 0 30px var(--brain-glow);
  border-color: #7dd8f9;
}

.neural-card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.neural-card-title {
  color: var(--brain-blue);
  font-size: 0.88rem;
  font-weight: 700;
  transition: color 0.2s;
  text-shadow: 0 0 12px rgba(90, 200, 245, 0.3);
}

.neural-card:hover .neural-card-title {
  color: #a0e4ff;
  text-shadow: 0 0 16px rgba(90, 200, 245, 0.5);
}

.neural-card-desc {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.72rem;
  line-height: 1.4;
  transition: color 0.2s;
}

.neural-card:hover .neural-card-desc {
  color: rgba(255, 255, 255, 0.65);
}

.neural-card-arrow {
  width: 16px;
  height: 16px;
  min-width: 16px;
  color: var(--brain-dim);
  margin-top: 3px;
  transition: all 0.25s;
}

.neural-card:hover .neural-card-arrow {
  color: var(--brain-blue);
  transform: translateX(3px);
}

/* ── Group label tag ── */
.neural-tag {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  opacity: 0;
  transform: translate3d(0, 8px, 0);
  will-change: transform, opacity;
  transition:
    transform 280ms cubic-bezier(0.22, 0.61, 0.36, 1),
    opacity 250ms ease;
  transition-delay: 300ms;
}

.expanding .neural-tag {
  opacity: 1;
  transform: translate3d(0, 0, 0);
}

.retracting .neural-tag {
  opacity: 0;
  transform: translate3d(0, -14px, 0) scale(0.7);
  transition:
    transform 200ms cubic-bezier(0.55, 0, 1, 0.45),
    opacity 180ms ease;
  transition-delay: 0ms;
}

.neural-tag span {
  color: var(--brain-blue);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.65;
}

.neural-close-btn {
  color: rgba(255, 255, 255, 0.25);
  transition: color 0.2s;
}

.neural-close-btn:hover {
  color: rgba(255, 255, 255, 0.8);
}

/* ── Animated background gradient ── */
.painel-bg {
  background: linear-gradient(135deg, #0a1024, #0d1530, #0066ff, #0d1530, #0a1024);
  background-size: 400% 400%;
  animation: bgShift 12s ease-in-out infinite;
}
@keyframes bgShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

/* ── Glass shape base ── */
.glass-shape {
  position: absolute;
  border: 1.5px solid rgba(0, 102, 255, 0.25);
  background: rgba(0, 102, 255, 0.06);
  box-shadow:
    0 0 15px rgba(0, 102, 255, 0.3),
    0 0 40px rgba(0, 102, 255, 0.18),
    0 0 80px rgba(0, 102, 255, 0.08),
    inset 0 0 20px rgba(0, 102, 255, 0.04);
  will-change: transform;
}

.shape-1 {
  width: 300px;
  height: 300px;
  border-radius: 50%;
  filter: blur(2px);
  animation: drift1 26s ease-in-out infinite;
}
@keyframes drift1 {
  0% {
    transform: translate(-10%, -15%) rotate(0deg);
  }
  50% {
    transform: translate(40%, 60%) rotate(30deg);
  }
  100% {
    transform: translate(-10%, -15%) rotate(0deg);
  }
}

.shape-2 {
  width: 220px;
  height: 220px;
  border-radius: 36px;
  filter: blur(1.5px);
  right: -30px;
  animation: drift2 30s ease-in-out infinite;
}
@keyframes drift2 {
  0% {
    transform: translate(10%, -20%) rotate(45deg);
  }
  50% {
    transform: translate(-50%, 70%) rotate(90deg);
  }
  100% {
    transform: translate(10%, -20%) rotate(45deg);
  }
}

.shape-3 {
  width: 170px;
  height: 170px;
  border-radius: 50%;
  filter: blur(3px);
  left: 60%;
  animation: drift3 22s ease-in-out infinite;
  animation-delay: -8s;
}
@keyframes drift3 {
  0% {
    transform: translate(0, -30%) rotate(0deg);
  }
  50% {
    transform: translate(-30%, 85%) rotate(-20deg);
  }
  100% {
    transform: translate(0, -30%) rotate(0deg);
  }
}

.shape-4 {
  width: 110px;
  height: 110px;
  border-radius: 22px;
  filter: blur(1px);
  left: 35%;
  animation: drift4 18s ease-in-out infinite;
  animation-delay: -4s;
}
@keyframes drift4 {
  0% {
    transform: translate(0, -10%) rotate(12deg);
  }
  50% {
    transform: translate(20%, 95%) rotate(60deg);
  }
  100% {
    transform: translate(0, -10%) rotate(12deg);
  }
}

.shape-5 {
  width: 250px;
  height: 190px;
  border-radius: 44px;
  filter: blur(2.5px);
  left: 12%;
  bottom: 0;
  animation: drift5 34s ease-in-out infinite;
  animation-delay: -12s;
}
@keyframes drift5 {
  0% {
    transform: translate(-5%, 20%) rotate(-8deg);
  }
  50% {
    transform: translate(30%, -75%) rotate(15deg);
  }
  100% {
    transform: translate(-5%, 20%) rotate(-8deg);
  }
}

.shape-6 {
  width: 85px;
  height: 85px;
  border-radius: 50%;
  filter: blur(1px);
  left: 75%;
  top: 55%;
  border-color: rgba(0, 102, 255, 0.4);
  box-shadow:
    0 0 20px rgba(0, 102, 255, 0.4),
    0 0 50px rgba(0, 102, 255, 0.2),
    0 0 80px rgba(0, 102, 255, 0.1);
  animation: drift6 15s ease-in-out infinite;
  animation-delay: -6s;
}
@keyframes drift6 {
  0% {
    transform: translate(0, 0) rotate(0deg);
  }
  50% {
    transform: translate(-40%, -110%) rotate(45deg);
  }
  100% {
    transform: translate(0, 0) rotate(0deg);
  }
}

.shape-7 {
  width: 150px;
  height: 150px;
  border-radius: 30px;
  filter: blur(2px);
  right: 12%;
  top: 18%;
  animation: drift7 24s ease-in-out infinite;
  animation-delay: -10s;
}
@keyframes drift7 {
  0% {
    transform: translate(10%, -5%) rotate(-12deg);
  }
  50% {
    transform: translate(-20%, 70%) rotate(25deg);
  }
  100% {
    transform: translate(10%, -5%) rotate(-12deg);
  }
}

.shape-8 {
  width: 65px;
  height: 65px;
  border-radius: 50%;
  filter: blur(0.5px);
  left: 22%;
  top: 42%;
  border-color: rgba(0, 102, 255, 0.45);
  box-shadow:
    0 0 18px rgba(0, 102, 255, 0.45),
    0 0 45px rgba(0, 102, 255, 0.22),
    0 0 70px rgba(0, 102, 255, 0.1);
  animation: drift8 13s ease-in-out infinite;
  animation-delay: -3s;
}
@keyframes drift8 {
  0% {
    transform: translate(0, 0) rotate(0deg);
  }
  50% {
    transform: translate(50%, 100%) rotate(-30deg);
  }
  100% {
    transform: translate(0, 0) rotate(0deg);
  }
}
</style>
