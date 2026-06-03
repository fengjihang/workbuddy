<template>
  <div class="analysis-detail">
    <div v-if="allDone" class="goto-bid-bar">
      <el-button type="primary" size="large" @click="goToBid">前往标书制作</el-button>
    </div>

    <div class="detail-panels">
      <div class="panel-left">
        <h3>招标文件原件</h3>
        <div class="doc-preview" v-if="fileContent">
          <div v-for="s in fileContent.sections" :key="s.page" class="doc-section">
            <h4>{{ s.title }}</h4>
            <p>{{ s.content }}</p>
          </div>
        </div>
        <el-skeleton v-else :rows="10" animated />
      </div>

      <div class="panel-right">
        <div class="panel-right-header">
          <h3>解读结果</h3>
          <div v-if="needResume && !sseActive" class="resume-bar">
            <span>已完成 {{ doneCount }}/10 模块</span>
            <button class="resume-btn" @click="startSSE">继续解读</button>
          </div>
          <div v-else-if="sseActive" class="resume-bar">
            <span>解读中... {{ doneCount }}/10</span>
          </div>
        </div>
        <div class="modules-grid">
          <div
            v-for="m in modules"
            :key="m.module_index"
            class="module-card"
            :class="{ 'module--done': m.status === '已完成', 'module--active': m.status === '进行中' }"
            @click="toggleModule(m.module_index)"
          >
            <div class="module-header">
              <span class="module-index">{{ m.module_index }}</span>
              <span class="module-name">{{ m.module_name }}</span>
              <el-icon v-if="m.status === '已完成'" class="module-icon done"><CircleCheckFilled /></el-icon>
              <el-icon v-else-if="m.status === '进行中'" class="module-icon loading"><Loading /></el-icon>
              <el-icon v-else class="module-icon wait"><Clock /></el-icon>
            </div>
            <div v-if="expandedModule === m.module_index && m.content" class="module-content">
              <div class="module-text">{{ m.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CircleCheckFilled, Loading, Clock } from '@element-plus/icons-vue'
import { useTenderStore } from '../stores/tender'
import api from '../api'

const route = useRoute()
const router = useRouter()
const store = useTenderStore()

const tenderId = computed(() => Number(route.params.id))
const modules = ref<any[]>([])
const fileContent = ref<any>(null)
const expandedModule = ref<number | null>(null)
const allDone = ref(false)
const sseActive = ref(false)
const needResume = ref(false)

let eventSource: EventSource | null = null

const doneCount = computed(() => modules.value.filter((m: any) => m.status === '已完成').length)

function toggleModule(idx: number) {
  expandedModule.value = expandedModule.value === idx ? null : idx
}

function goToBid() {
  router.push(`/bid?tenderId=${tenderId.value}`)
}

function startSSE() {
  console.log('[startSSE] 被调用, tenderId:', tenderId.value, 'url:', `/api/analysis/start/${tenderId.value}`)
  sseActive.value = true
  needResume.value = false

  eventSource = new EventSource(`/api/analysis/start/${tenderId.value}`)
  console.log('[startSSE] EventSource 已创建, readyState:', eventSource.readyState)

  eventSource.addEventListener('module_start', (e: MessageEvent) => {
    const d = JSON.parse(e.data)
    let mod = modules.value.find((m: any) => m.module_index === d.module_index)
    if (!mod) {
      mod = { module_index: d.module_index, module_name: d.module_name, content: '', status: '进行中' }
      modules.value.push(mod)
    } else {
      mod.status = '进行中'
    }
  })

  eventSource.addEventListener('module_chunk', (e: MessageEvent) => {
    const d = JSON.parse(e.data)
    const mod = modules.value.find((m: any) => m.module_index === d.module_index)
    if (mod) {
      mod.content = (mod.content || '') + d.delta
    }
  })

  eventSource.addEventListener('module_done', (e: MessageEvent) => {
    const d = JSON.parse(e.data)
    let mod = modules.value.find((m: any) => m.module_index === d.module_index)
    if (!mod) {
      mod = { module_index: d.module_index, module_name: d.module_name || '', content: d.content, status: '已完成' }
      modules.value.push(mod)
    } else {
      mod.content = d.content
      mod.status = '已完成'
    }
  })

  eventSource.addEventListener('module_error', (e: MessageEvent) => {
    const d = JSON.parse(e.data)
    const mod = modules.value.find((m: any) => m.module_index === d.module_index)
    if (mod) {
      mod.content = (mod.content || '') + '\n\n[错误] ' + d.message
      mod.status = '等待中'
    }
    if (doneCount.value > 0) {
      needResume.value = true
    }
  })

  eventSource.addEventListener('analysis_error', (e: MessageEvent) => {
    try {
      const d = JSON.parse(e.data)
      console.error('解读错误:', d.message)
    } catch {}
    sseActive.value = false
    eventSource?.close()
    if (doneCount.value > 0) {
      needResume.value = true
    }
  })

  eventSource.addEventListener('done', () => {
    allDone.value = true
    sseActive.value = false
    eventSource?.close()
  })

  // EventSource 连接级别的错误
  eventSource.onerror = () => {
    sseActive.value = false
    eventSource?.close()
    if (doneCount.value > 0) {
      needResume.value = true
    }
  }
}

onMounted(async () => {
  // 加载文件预览内容
  try {
    const { data } = await api.get(`/files/${tenderId.value}/content`)
    fileContent.value = data
  } catch {}

  // 从DB加载已有模块
  try {
    const { data } = await api.get(`/analysis/${tenderId.value}/modules`)
    modules.value = data
  } catch {}

  // 检查是否需要恢复
  try {
    const { data } = await api.get(`/analysis/${tenderId.value}/resume`)
    if (data.can_resume) {
      needResume.value = true
    } else if (data.status === '已上传' || data.done_count === 0) {
      // 全新开始，自动启动
      startSSE()
    } else if (data.status === '已解读' || data.done_count === data.total_count) {
      allDone.value = true
      needResume.value = false
    }
  } catch {
    // 如果resume接口失败，尝试直接启动
    if (doneCount.value === 0) {
      startSSE()
    }
  }
})

onUnmounted(() => {
  eventSource?.close()
  sseActive.value = false
  // 不重置 modules/doneCount，下次回来可以从DB恢复
})
</script>

<style scoped>
.analysis-detail { max-width: 1400px; }
.goto-bid-bar { text-align: right; margin-bottom: 16px; }
.detail-panels { display: flex; gap: 20px; height: calc(100vh - 160px); }
.panel-left { flex: 1; overflow-y: auto; background: #fff; border-radius: 8px; padding: 20px; }
.panel-left h3 { margin-bottom: 12px; font-size: 15px; color: #303133; }
.panel-right { flex: 1; overflow-y: auto; }
.panel-right-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.panel-right-header h3 { font-size: 15px; color: #303133; }
.resume-bar { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #909399; }
.resume-btn { padding: 6px 14px; background: #409eff; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.resume-btn:hover { background: #337ecc; }
.doc-section { margin-bottom: 16px; }
.doc-section h4 { font-size: 14px; color: #409eff; margin-bottom: 4px; }
.doc-section p { font-size: 13px; color: #606266; line-height: 1.8; white-space: pre-wrap; }
.modules-grid { display: flex; flex-direction: column; gap: 8px; }
.module-card { background: #fff; border-radius: 8px; padding: 14px 18px; cursor: pointer; transition: all 0.2s; border: 1px solid #ebeef5; }
.module-card:hover { border-color: #409eff; }
.module--done { border-left: 3px solid #67c23a; }
.module--active { border-left: 3px solid #409eff; background: #ecf5ff; }
.module-header { display: flex; align-items: center; gap: 10px; }
.module-index { width: 24px; height: 24px; background: #f0f2f5; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #606266; }
.module-name { font-size: 14px; color: #303133; font-weight: 500; flex: 1; }
.module-icon.done { color: #67c23a; }
.module-icon.loading { color: #409eff; animation: spin 1s linear infinite; }
.module-icon.wait { color: #c0c4cc; }
.module-content { margin-top: 12px; padding-top: 12px; border-top: 1px solid #ebeef5; }
.module-text { font-size: 13px; color: #606266; line-height: 1.8; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
