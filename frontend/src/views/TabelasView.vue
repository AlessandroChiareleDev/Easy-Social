<template>
  <div class="tabelas-view">
    <!-- Glass shapes -->
    <div class="glass-shapes">
      <div class="glass-shape shape-1"></div>
      <div class="glass-shape shape-2"></div>
      <div class="glass-shape shape-3"></div>
    </div>

    <TableViewer />
  </div>
</template>

<script setup lang="ts">
import TableViewer from '../components/TableViewer.vue'
</script>

<style scoped>
.tabelas-view {
  position: relative;
  overflow: hidden;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  color: #e2e8f0;
}

h1 {
  margin-bottom: 16px;
  color: #ffffff;
}

/* ── Glass Shapes ── */
.glass-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.glass-shape {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(0, 102, 255, 0.15);
  background: rgba(0, 102, 255, 0.04);
  box-shadow:
    0 0 15px rgba(0, 102, 255, 0.2),
    0 0 40px rgba(0, 102, 255, 0.1);
}
.shape-1 {
  width: 280px;
  height: 280px;
  top: -60px;
  right: -60px;
  filter: blur(2px);
  animation: drift1 26s ease-in-out infinite;
}
.shape-2 {
  width: 200px;
  height: 200px;
  bottom: 10%;
  left: -40px;
  border-radius: 36px;
  filter: blur(1.5px);
  animation: drift2 30s ease-in-out infinite;
}
.shape-3 {
  width: 150px;
  height: 150px;
  top: 40%;
  left: 55%;
  filter: blur(3px);
  animation: drift3 22s ease-in-out infinite;
  animation-delay: -8s;
}
@keyframes drift1 {
  0%,
  100% {
    transform: translate(-10%, -15%) rotate(0deg);
  }
  50% {
    transform: translate(30%, 50%) rotate(25deg);
  }
}
@keyframes drift2 {
  0%,
  100% {
    transform: translate(10%, -20%) rotate(45deg);
  }
  50% {
    transform: translate(-40%, 60%) rotate(90deg);
  }
}
@keyframes drift3 {
  0%,
  100% {
    transform: translate(0, -20%) rotate(0deg);
  }
  50% {
    transform: translate(-25%, 70%) rotate(-20deg);
  }
}
</style>
