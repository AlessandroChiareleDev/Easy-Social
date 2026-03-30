<template>
  <div class="tabelas-view">
    <TableViewer />
  </div>
</template>

<script setup lang="ts">
import TableViewer from '../components/TableViewer.vue'
</script>

<style scoped>
.tabelas-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  color: #e2e8f0;
}

h1 {
  margin-bottom: 16px;
  color: #ffffff;
}
</style>
