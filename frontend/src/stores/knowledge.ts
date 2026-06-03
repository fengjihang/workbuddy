import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'
import type { KnowledgeDoc } from '../types'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const docs = ref<KnowledgeDoc[]>([])
  const filterCategory = ref<string>('')
  const loading = ref(false)

  async function fetchDocs(category?: string) {
    loading.value = true
    const params = category ? { category } : {}
    const { data } = await api.get('/knowledge', { params })
    docs.value = data
    loading.value = false
  }

  async function uploadDoc(file: File, category: string) {
    const form = new FormData()
    form.append('file', file)
    form.append('category', category)
    const { data } = await api.post('/knowledge/upload', form)
    docs.value.unshift(data)
    return data
  }

  async function deleteDoc(id: number) {
    await api.delete(`/knowledge/${id}`)
    docs.value = docs.value.filter(d => d.id !== id)
  }

  return { docs, filterCategory, loading, fetchDocs, uploadDoc, deleteDoc }
})
