import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_URL =
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? import.meta.env.VITE_API_URL || 'http://localhost:3333/api'
    : 'https://breath-conferences-min-firewall.trycloudflare.com/api'

export interface User {
  userId: number
  username: string
  nome: string
  role: string
}

export interface Empresa {
  id: number
  nome: string
  cnpj: string | null
  db_name: string
  role_emp: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('es_token'))
  const user = ref<User | null>(null)
  const empresas = ref<Empresa[]>([])
  const empresaSelecionada = ref<Empresa | null>(null)

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // Configure axios with token
  function setupAxios() {
    if (token.value) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
    if (empresaSelecionada.value) {
      axios.defaults.headers.common['X-Empresa-Id'] = String(empresaSelecionada.value.id)
    }
  }

  async function login(username: string, senha: string): Promise<boolean> {
    try {
      const resp = await axios.post(`${API_URL}/auth/login`, { username, senha })
      token.value = resp.data.token
      user.value = resp.data.user
      localStorage.setItem('es_token', resp.data.token)
      setupAxios()
      await fetchEmpresas()
      return true
    } catch (err: any) {
      if (err.response) {
        // Server respondeu com erro
        throw new Error(err.response.data?.error || 'Credenciais inválidas')
      } else if (err.request) {
        // Sem resposta do servidor
        throw new Error('Servidor indisponível — verifique se o backend está rodando')
      }
      throw new Error('Erro de conexão com o servidor')
    }
  }

  function logout() {
    token.value = null
    user.value = null
    empresas.value = []
    empresaSelecionada.value = null
    localStorage.removeItem('es_token')
    localStorage.removeItem('es_empresa_id')
    delete axios.defaults.headers.common['Authorization']
    delete axios.defaults.headers.common['X-Empresa-Id']
  }

  async function fetchEmpresas() {
    try {
      setupAxios()
      const resp = await axios.get(`${API_URL}/auth/empresas`)
      empresas.value = resp.data.empresas

      // Restore previously selected empresa
      const savedId = localStorage.getItem('es_empresa_id')
      if (savedId) {
        const found = empresas.value.find((e) => e.id === parseInt(savedId))
        if (found) {
          selecionarEmpresa(found)
        }
      }
    } catch {
      empresas.value = []
    }
  }

  function selecionarEmpresa(empresa: Empresa) {
    empresaSelecionada.value = empresa
    localStorage.setItem('es_empresa_id', String(empresa.id))
    axios.defaults.headers.common['X-Empresa-Id'] = String(empresa.id)
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) return false
    try {
      setupAxios()
      const resp = await axios.get(`${API_URL}/auth/me`)
      user.value = resp.data.user
      await fetchEmpresas()
      return true
    } catch {
      logout()
      return false
    }
  }

  return {
    token,
    user,
    empresas,
    empresaSelecionada,
    isLoggedIn,
    isAdmin,
    login,
    logout,
    fetchEmpresas,
    selecionarEmpresa,
    checkAuth,
    setupAxios,
  }
})
