<template>
  <div class="tabelas-view">
    <h1>Tabelas do Banco de Dados</h1>
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
  color: #333;
}

h1 {
  margin-bottom: 16px;
}
</style>
