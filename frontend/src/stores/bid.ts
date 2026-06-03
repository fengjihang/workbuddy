import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'
import type { Bid, BidDetail, BidChapter, FieldListResponse, FillResult, InspectResult } from '../types'

export const useBidStore = defineStore('bid', () => {
  const bids = ref<Bid[]>([])
  const currentBid = ref<BidDetail | null>(null)
  const loading = ref(false)
  const detectedFields = ref<FieldListResponse | null>(null)
  const inspectResult = ref<InspectResult | null>(null)
  const inspecting = ref(false)

  async function fetchBids() {
    const { data } = await api.get('/bids')
    bids.value = data
  }

  async function fetchBid(id: number) {
    const { data } = await api.get(`/bids/${id}`)
    currentBid.value = data
  }

  async function createBid(name: string, tenderId: number | null) {
    const { data } = await api.post('/bids', { name, tender_id: tenderId })
    bids.value.unshift(data)
    return data
  }

  async function updateChapter(bidId: number, chapterIndex: number, content: string) {
    await api.put(`/bids/${bidId}/chapters/${chapterIndex}`, { content })
  }

  function generateChapter(bidId: number, chapterIndex: number, onToken: (s: string) => void): Promise<string> {
    return new Promise((resolve, reject) => {
      const url = `/api/bids/${bidId}/generate/${chapterIndex}`
      const eventSource = new EventSource(url)
      let full = ''

      eventSource.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'chunk') {
            full += msg.content
            onToken(msg.content)
          } else if (msg.type === 'done') {
            full = msg.content
            eventSource.close()
            resolve(full)
          }
        } catch {
          full += e.data
          onToken(e.data)
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        if (full) {
          resolve(full)
        } else {
          reject(new Error('生成失败'))
        }
      }
    })
  }

  async function deleteBid(id: number) {
    await api.delete(`/bids/${id}`)
    bids.value = bids.value.filter(b => b.id !== id)
  }

  async function exportBid(bidId: number): Promise<string> {
    const { data } = await api.post(`/bids/${bidId}/export`, {}, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    return url
  }

  function updateChapterContent(chapterIndex: number, content: string) {
    if (currentBid.value) {
      const ch = currentBid.value.chapters.find(c => c.chapter_index === chapterIndex)
      if (ch) ch.content = content
    }
  }

  async function fetchFields(bidId: number, chapterIndex?: number): Promise<FieldListResponse> {
    const params: Record<string, any> = {}
    if (chapterIndex !== undefined) params.chapter_index = chapterIndex
    const { data } = await api.get(`/bids/${bidId}/fields`, { params })
    detectedFields.value = data
    return data
  }

  async function downloadFieldsExcel(bidId: number, chapterIndex?: number): Promise<string> {
    const params: Record<string, any> = {}
    if (chapterIndex !== undefined) params.chapter_index = chapterIndex
    const { data } = await api.get(`/bids/${bidId}/fields/excel`, { params, responseType: 'blob' })
    const url = URL.createObjectURL(data)
    return url
  }

  async function uploadFilledFields(bidId: number, file: File, chapterIndex?: number): Promise<FillResult> {
    const formData = new FormData()
    formData.append('file', file)
    if (chapterIndex !== undefined) formData.append('chapter_index', String(chapterIndex))
    const { data } = await api.post(`/bids/${bidId}/fields/fill`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await fetchBid(bidId)
    return data
  }

  async function inspectBid(bidId: number): Promise<InspectResult> {
    inspecting.value = true
    try {
      const { data } = await api.post(`/bids/${bidId}/inspect`)
      inspectResult.value = data
      return data
    } finally {
      inspecting.value = false
    }
  }

  async function downloadInspectExcel(bidId: number): Promise<string> {
    const { data } = await api.get(`/bids/${bidId}/inspect/excel`, { responseType: 'blob' })
    return URL.createObjectURL(data)
  }

  async function uploadInspectFill(bidId: number, file: File): Promise<Response> {
    const formData = new FormData()
    formData.append('file', file)
    return fetch(`/api/bids/${bidId}/inspect/fill`, {
      method: 'POST',
      body: formData,
    })
  }

  return {
    bids, currentBid, loading, detectedFields, inspectResult, inspecting,
    fetchBids, fetchBid, createBid, deleteBid, updateChapter, generateChapter, exportBid, updateChapterContent,
    fetchFields, downloadFieldsExcel, uploadFilledFields,
    inspectBid, downloadInspectExcel, uploadInspectFill,
  }
})
