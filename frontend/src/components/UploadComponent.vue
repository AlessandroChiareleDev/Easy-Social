<template>
  <div class="upload-container">
    <div
      :class="['upload-box', { dragover: dragover }]"
      @dragover.prevent="dragover = true"
      @dragleave="dragover = false"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div v-if="!uploading" class="upload-content">
        <h2>📁 Upload DIRF.xlsx</h2>
        <p>Arraste o arquivo aqui ou clique para selecionar</p>
        <input
          type="file"
          ref="fileInput"
          @change="handleFileSelect"
          accept=".xlsx,.xls"
          style="display: none"
        />
        <button @click.stop="triggerFileInput" :disabled="uploading">Selecionar Arquivo</button>
        <p v-if="selectedFile">
          Arquivo selecionado: <strong>{{ selectedFile.name }}</strong>
        </p>
        <button
          v-if="selectedFile && !analysisResult"
          @click.stop="uploadFile"
          :disabled="uploading"
        >
          Enviar Arquivo
        </button>
      </div>
      <div v-else class="uploading-content">
        <p>Processando... {{ uploadProgress }}%</p>
        <div class="progress-bar">
          <div class="progress" :style="{ width: uploadProgress + '%' }"></div>
        </div>
      </div>
    </div>

    <div v-if="analysisResult" class="analysis-result">
      <h3>✅ Análise Concluída</h3>
      <p><strong>Arquivo:</strong> {{ analysisResult.fileName }}</p>
      <p><strong>Tamanho:</strong> {{ formatFileSize(analysisResult.fileSize) }}</p>
      <p><strong>Tabelas Encontradas:</strong> {{ analysisResult.tables.length }}</p>

      <div class="tables-list">
        <div v-for="table in analysisResult.tables" :key="table.name" class="table-card">
          <h4>{{ table.name }}</h4>
          <p>Linhas: {{ table.rowCount }} | Colunas: {{ table.columnCount }}</p>
          <p>Colunas: {{ table.columnLetters.join(', ') }}</p>
        </div>
      </div>

      <button @click="processData" :disabled="processingData">
        {{ processingData ? 'Processando...' : 'Processar e Normalizar Dados' }}
      </button>
      <p v-if="processingData">O processamento pode levar alguns minutos para arquivos grandes.</p>
    </div>

    <div v-if="duplicateDetected" class="duplicate-message">
      <h3>📋 Arquivo já processado</h3>
      <p>Os dados deste arquivo já foram processados e salvos no banco de dados.</p>
      <p>Utilize o <strong>Visualizador de Tabelas</strong> abaixo para consultar os dados.</p>
      <button @click="scrollToViewer">Ir para Visualizador de Tabelas ↓</button>
    </div>

    <div v-if="error" class="error-message">❌ {{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333/api'

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const dragover = ref(false)
const analysisResult = ref<any>(null)
const error = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const processingData = ref(false)
const duplicateDetected = ref(false)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] || null
  analysisResult.value = null
  duplicateDetected.value = false
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  dragover.value = false
  selectedFile.value = event.dataTransfer?.files[0] || null
  analysisResult.value = null
  duplicateDetected.value = false
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  error.value = null

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    console.log(
      '[Upload] Enviando arquivo:',
      selectedFile.value.name,
      `(${(selectedFile.value.size / 1024 / 1024).toFixed(1)} MB)`,
    )
    const response = await axios.post(`${API_URL}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        uploadProgress.value = Math.round((progressEvent.loaded / (progressEvent.total || 1)) * 100)
      },
    })

    if (response.data.duplicate) {
      duplicateDetected.value = true
      analysisResult.value = null
      console.log('[Upload] Arquivo já processado:', response.data.data)
    } else {
      duplicateDetected.value = false
      analysisResult.value = response.data.data
      console.log('[Upload] Análise concluída:', {
        uploadId: response.data.data.uploadId,
        tabelas: response.data.data.tables?.map((t: any) => `${t.name} (${t.rowCount} linhas)`),
      })
    }
  } catch (err: any) {
    console.error('[Upload] ERRO:', err.response?.data || err.message)
    error.value = err.response?.data?.error || 'Erro ao fazer upload'
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

const processData = async () => {
  if (!analysisResult.value || !analysisResult.value.uploadId || !analysisResult.value.filePath) {
    error.value = 'Nenhum arquivo analisado ou uploadId/filePath ausente para processamento.'
    return
  }

  processingData.value = true
  error.value = null

  try {
    console.log('[Process] Iniciando processamento...', { uploadId: analysisResult.value.uploadId })
    const resp = await axios.post(`${API_URL}/process`, {
      uploadId: analysisResult.value.uploadId,
      filePath: analysisResult.value.filePath,
    })
    console.log('[Process] Resposta do backend:', resp.data)
    alert('Processamento de dados iniciado com sucesso! Verifique o status na seção de tabelas.')
  } catch (err: any) {
    console.error('[Process] ERRO:', err.response?.data || err.message)
    error.value = err.response?.data?.error || 'Erro ao processar dados'
  } finally {
    processingData.value = false
  }
}

const scrollToViewer = () => {
  const viewer = document.querySelector('.table-viewer')
  if (viewer) viewer.scrollIntoView({ behavior: 'smooth' })
}

const formatFileSize = (bytes: number) => {
  const mb = (bytes / (1024 * 1024)).toFixed(2)
  return `${mb} MB`
}
</script>

<style scoped>
.upload-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  color: #333;
}

.upload-box {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-box:hover {
  border-color: #007bff;
  background-color: #f8f9fa;
}

.upload-box.dragover {
  border-color: #007bff;
  background-color: #e7f3ff;
}

input[type='file'] {
  display: none;
}

button {
  background-color: #007bff;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
  margin-left: 5px;
  margin-right: 5px;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 10px;
}

.progress {
  height: 100%;
  background-color: #28a745;
  transition: width 0.3s;
}

.analysis-result {
  margin-top: 30px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  color: #333;
}

.tables-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.table-card {
  background-color: white;
  padding: 15px;
  border-radius: 4px;
  border-left: 4px solid #007bff;
  color: #333;
}

.duplicate-message {
  margin-top: 30px;
  padding: 20px;
  background-color: #fff3cd;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
  color: #333;
  text-align: center;
}

.duplicate-message h3 {
  margin-bottom: 10px;
}

.duplicate-message button {
  margin-top: 15px;
  background-color: #007bff;
}

.error-message {
  color: #dc3545;
  padding: 10px;
  background-color: #f8d7da;
  border-radius: 4px;
  margin-top: 10px;
}
</style>
