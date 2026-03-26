<template>
  <div class="table-viewer">
    <h2>📊 Visualizador de Tabelas</h2>

    <div class="table-selector">
      <select v-model="selectedTable" @change="onTableChange">
        <option value="">Selecione uma tabela...</option>
        <option v-for="table in availableTables" :key="table" :value="table">
          {{ formatTableName(table) }}
        </option>
      </select>
      <button
        v-if="selectedTable && tableData.length > 0"
        class="btn-download"
        @click="downloadXlsx"
        :disabled="downloading"
      >
        {{ downloading ? 'Baixando...' : '⬇ Baixar XLSX' }}
      </button>
    </div>

    <div v-if="loading" class="loading">Carregando...</div>

    <div v-if="tableData.length > 0" class="table-container">
      <table>
        <thead>
          <tr>
            <th v-for="(col, index) in columns" :key="index">
              <span class="col-letter">{{ col.letter }}</span>
              <span class="col-name">{{ col.name }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in tableData" :key="rowIndex">
            <td v-for="(col, colIndex) in columns" :key="colIndex">
              {{ row[`col_${col.letter.toLowerCase()}`] || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
      <div class="pagination">
        <button @click="prevPage" :disabled="currentPage === 1">Anterior</button>
        <span>Página {{ currentPage }} de {{ totalPages }}</span>
        <button @click="nextPage" :disabled="currentPage === totalPages">Próxima</button>
      </div>
    </div>

    <div v-if="error" class="error-message">❌ {{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import * as XLSX from 'xlsx'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333/api'

const selectedTable = ref('')
const tableData = ref<any[]>([])
const columns = ref<{ letter: string; name: string }[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const availableTables = ref<string[]>([])

const currentPage = ref(1)
const itemsPerPage = 100
const totalItems = ref(0)
const totalPages = ref(1)
const downloading = ref(false)

const fetchAvailableTables = async () => {
  try {
    const response = await axios.get(`${API_URL}/tables`)
    availableTables.value = response.data.tables
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao carregar lista de tabelas'
  }
}

const onTableChange = () => {
  currentPage.value = 1
  loadTableData()
}

const loadTableData = async () => {
  if (!selectedTable.value) return

  loading.value = true
  error.value = null

  try {
    // Buscar colunas apenas quando trocar de tabela (page 1)
    if (currentPage.value === 1) {
      const colRes = await axios.get(`${API_URL}/tables/${selectedTable.value}/columns`)
      columns.value = colRes.data.columns
    }

    const offset = (currentPage.value - 1) * itemsPerPage
    const response = await axios.get(
      `${API_URL}/tables/${selectedTable.value}?limit=${itemsPerPage}&offset=${offset}`,
    )
    tableData.value = response.data.data
    totalItems.value = response.data.total
    totalPages.value = Math.ceil(totalItems.value / itemsPerPage)
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao carregar tabela'
  } finally {
    loading.value = false
  }
}

const formatTableName = (name: string) => {
  const mapping: { [key: string]: string } = {
    analise_natureza: 'ANALISE NATUREZA',
    dinamica: 'Dinamica',
    tabela_eventos_gl: 'Tabela Eventos GI',
    tabela_eb: 'Tabela EB',
  }
  return mapping[name] || name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadTableData()
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadTableData()
  }
}

const downloadXlsx = async () => {
  if (!selectedTable.value) return

  downloading.value = true
  try {
    const response = await axios.get(`${API_URL}/tables/${selectedTable.value}/export`)
    const { data, columns: cols } = response.data

    // Montar dados com nomes reais das colunas
    const rows = data.map((row: any) => {
      const obj: any = {}
      for (const col of cols) {
        obj[col.name] = row[`col_${col.letter.toLowerCase()}`] || ''
      }
      return obj
    })

    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, formatTableName(selectedTable.value))
    XLSX.writeFile(wb, `${formatTableName(selectedTable.value)}.xlsx`)
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao exportar tabela'
  } finally {
    downloading.value = false
  }
}

onMounted(() => {
  fetchAvailableTables()
})
</script>

<style scoped>
.table-viewer {
  padding: 20px;
  color: #333;
}

.table-selector {
  margin: 20px 0;
}

.table-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

select {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
  width: 100%;
  max-width: 300px;
}

.btn-download {
  background-color: #28a745;
  color: white;
  padding: 10px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.btn-download:hover {
  background-color: #218838;
}

.btn-download:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.table-container {
  overflow-x: auto;
  margin-top: 20px;
  transform: rotateX(180deg);
}

.table-container > table,
.table-container > .pagination {
  transform: rotateX(180deg);
}

table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

th,
td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: left;
  white-space: nowrap;
}

th {
  background-color: #007bff;
  color: white;
  font-weight: bold;
  text-align: center;
}

.col-letter {
  display: block;
  font-size: 11px;
  opacity: 0.8;
}

.col-name {
  display: block;
  font-size: 13px;
}

tr:nth-child(even) {
  background-color: #f9f9f9;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.error-message {
  color: #dc3545;
  padding: 10px;
  background-color: #f8d7da;
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.pagination button {
  background-color: #007bff;
  color: white;
  padding: 8px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
