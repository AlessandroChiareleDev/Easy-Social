<template>
  <div class="dashboard-view">
    <h1>Easy Social Dashboard</h1>
    <UploadComponent />
    <hr class="my-8" />
    <TableViewer />
    <hr class="my-8" />
    <DivergenceViewer />
  </div>
</template>

<script setup lang="ts">
import UploadComponent from '../components/UploadComponent.vue'
import TableViewer from '../components/TableViewer.vue'
import DivergenceViewer from '../components/DivergenceViewer.vue'
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  color: #333;
}
hr {
  border: none;
  border-top: 1px solid #eee;
  margin: 2rem 0;
}
</style>
