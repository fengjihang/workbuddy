import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'
import type { ComplianceItem, ComplianceSummary } from '../types'

export const useComplianceStore = defineStore('compliance', () => {
  const summary = ref<ComplianceSummary>({ severe: 0, high: 0, medium: 0, low: 0 })
  const items = ref<ComplianceItem[]>([])
  const checking = ref(false)
  const message = ref('')

  function handleSSEEvent(data: any) {
    switch (data.type) {
      case 'status':
        message.value = data.message
        break
      case 'requirements':
        message.value = `已提取 ${data.count} 项要求，正在逐条检查...`
        break
      case 'checking':
        message.value = `正在检查: ${data.item_desc}`
        break
      case 'item_result':
        items.value.push(data.data)
        break
      case 'summary':
        summary.value = data.data.summary
        items.value = data.data.items
        checking.value = false
        break
      case 'done':
        checking.value = false
        break
    }
  }

  function reset() {
    summary.value = { severe: 0, high: 0, medium: 0, low: 0 }
    items.value = []
    checking.value = false
    message.value = ''
  }

  return { summary, items, checking, message, handleSSEEvent, reset }
})
