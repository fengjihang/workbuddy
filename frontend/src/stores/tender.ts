import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'
import type { Tender, AnalysisModule, FileContent } from '../types'

export const useTenderStore = defineStore('tender', () => {
  const tenders = ref<Tender[]>([])
  const currentTender = ref<Tender | null>(null)
  const modules = ref<AnalysisModule[]>([])
  const fileContent = ref<FileContent | null>(null)
  const loading = ref(false)

  async function fetchTenders() {
    const { data } = await api.get('/tenders')
    tenders.value = data
  }

  async function fetchTender(id: number) {
    const { data } = await api.get(`/tenders/${id}`)
    currentTender.value = data
  }

  async function uploadTender(file: File) {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post('/tenders/upload', form)
    tenders.value.unshift(data)
    return data
  }

  async function deleteTender(id: number) {
    await api.delete(`/tenders/${id}`)
    tenders.value = tenders.value.filter(t => t.id !== id)
  }

  async function fetchModules(tenderId: number) {
    const { data } = await api.get(`/analysis/${tenderId}/modules`)
    modules.value = data
  }

  async function fetchFileContent(tenderId: number) {
    const { data } = await api.get(`/files/${tenderId}/content`)
    fileContent.value = data
  }

  function updateModule(moduleIndex: number, status: string, content?: string) {
    const mod = modules.value.find(m => m.module_index === moduleIndex)
    if (mod) {
      mod.status = status
      if (content !== undefined) mod.content = content
    }
  }

  return {
    tenders, currentTender, modules, fileContent, loading,
    fetchTenders, fetchTender, uploadTender, deleteTender,
    fetchModules, fetchFileContent, updateModule,
  }
})
