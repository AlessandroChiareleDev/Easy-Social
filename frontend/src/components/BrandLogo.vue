<template>
  <div class="brand-logo" :style="containerStyle">
    <!-- PNG image base -->
    <img src="/brand-logo.png" alt="Easy e-Social" :style="imgStyle" draggable="false" />
    <!-- Animated glow contour overlay -->
    <svg
      v-if="animate"
      class="brand-logo__glow"
      viewBox="0 0 612 408"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <filter :id="filterId('soft')" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter :id="filterId('strong')" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="10" result="blur1" />
          <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur2" />
          <feMerge>
            <feMergeNode in="blur1" />
            <feMergeNode in="blur2" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <!-- Faint full contour always visible -->
      <path :d="contourPath" stroke="rgba(0,102,255,0.06)" stroke-width="2" fill="none" />
      <!-- Traveling light — wide soft glow -->
      <path
        :d="contourPath"
        stroke="#0066FF"
        stroke-width="8"
        fill="none"
        stroke-linecap="round"
        :filter="`url(#${filterId('strong')})`"
        class="brand-logo__trail"
        :style="animStyle"
      />
      <!-- Traveling light — bright white-blue core -->
      <path
        :d="contourPath"
        stroke="#93c5fd"
        stroke-width="3"
        fill="none"
        stroke-linecap="round"
        :filter="`url(#${filterId('soft')})`"
        class="brand-logo__trail"
        :style="animStyle"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    size?: number | string
    animate?: boolean
    speed?: number
  }>(),
  {
    size: 40,
    animate: true,
    speed: 2,
  },
)

// Unique filter IDs to avoid conflicts when multiple instances exist
const uid = Math.random().toString(36).slice(2, 8)
const filterId = (name: string) => `bl-${name}-${uid}`

const contourPath =
  'M469,82 C462,75 468,76 453,72 C438,68 438,74 425,71 C412,68 423,65 414,62 C405,59 408,68 399,62 C390,56 398,52 387,44 C376,36 378,39 367,39 C356,39 363,35 354,43 C345,51 351,55 341,62 C331,69 332,60 323,63 C314,66 326,68 314,71 C302,74 303,67 287,72 C271,77 279,82 265,86 C251,90 258,83 246,83 C234,83 239,83 229,87 C219,91 225,87 216,95 C207,103 214,104 203,112 C192,120 193,111 182,118 C171,125 175,120 169,133 C163,146 170,145 165,156 C160,167 159,159 153,166 C147,173 149,168 146,178 C143,188 144,186 145,196 C146,206 150,201 149,209 C148,217 145,214 142,221 C139,228 139,219 141,229 C143,239 139,238 147,251 C155,264 158,258 164,268 C170,278 163,273 165,281 C167,289 163,283 170,291 C177,299 176,299 187,304 C198,309 191,299 204,306 C217,313 214,317 225,324 C236,331 224,327 238,328 C252,329 253,322 266,326 C279,330 271,334 278,340 C285,346 229,343 287,344 C345,345 394,346 453,344 C512,342 457,345 464,338 C471,331 471,405 474,323 C477,241 476,172 474,92 C472,12 476,89 469,82 Z'

const ASPECT = 612 / 408

const numSize = computed(() => {
  const s = props.size
  return typeof s === 'string' ? parseFloat(s) : s
})

const containerStyle = computed(() => ({
  width: `${numSize.value * ASPECT}px`,
  height: `${numSize.value}px`,
  position: 'relative' as const,
  flexShrink: 0,
}))

const imgStyle = computed(() => ({
  width: '100%',
  height: '100%',
  display: 'block',
  objectFit: 'contain' as const,
}))

const animStyle = computed(() => ({
  animationDuration: `${props.speed}s`,
}))
</script>

<style scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.brand-logo__glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.brand-logo__trail {
  stroke-dasharray: 120 1080;
  stroke-dashoffset: 0;
  animation: trace-contour 2s linear infinite;
}

@keyframes trace-contour {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: -1200;
  }
}
</style>
