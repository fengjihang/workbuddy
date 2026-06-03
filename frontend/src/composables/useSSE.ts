import { ref, onUnmounted } from 'vue'

export interface SSEEvent {
  event: string
  data: string
}

export function useSSE() {
  const isConnected = ref(false)
  const error = ref<string | null>(null)
  let eventSource: EventSource | null = null

  function connect(url: string, handlers: Record<string, (data: any) => void>) {
    disconnect()
    isConnected.value = true
    error.value = null

    eventSource = new EventSource(url)

    Object.entries(handlers).forEach(([eventName, handler]) => {
      eventSource!.addEventListener(eventName, (e: MessageEvent) => {
        try {
          const parsed = JSON.parse(e.data)
          handler(parsed)
        } catch {
          handler(e.data)
        }
      })
    })

    eventSource.onerror = () => {
      error.value = 'SSE 连接错误'
      isConnected.value = false
    }

    eventSource.onopen = () => {
      isConnected.value = true
    }
  }

  function disconnect() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isConnected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return { isConnected, error, connect, disconnect }
}
