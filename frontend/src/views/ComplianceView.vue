<template>
  <div class="compliance-view">
    <div class="page-header">
      <h2>合规检查</h2>
    </div>

    <div class="upload-section">
      <el-upload
        class="upload-box"
        drag
        :auto-upload="false"
        :on-change="(f: any) => tenderFile = f.raw"
        :limit="1"
        accept=".docx,.pdf"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">上传招标文件</div>
        <div v-if="tenderFile" class="upload-selected">{{ tenderFile.name }}</div>
      </el-upload>

      <el-upload
        class="upload-box"
        drag
        :auto-upload="false"
        :on-change="(f: any) => bidFile = f.raw"
        :limit="1"
        accept=".docx,.pdf"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">上传投标书</div>
        <div v-if="bidFile" class="upload-selected">{{ bidFile.name }}</div>
      </el-upload>
    </div>

    <div class="check-actions" v-if="tenderFile && bidFile && !store.checking">
      <el-button type="primary" size="large" @click="startCheck" :disabled="!tenderFile || !bidFile">
        开始检查
      </el-button>
    </div>

    <div v-if="store.checking" class="check-progress">
      <el-progress :percentage="checkProgress" />
      <p>{{ store.message || '正在连接服务器...' }}</p>
    </div>

    <div v-if="store.items.length > 0" class="check-results">
      <div class="risk-summary">
        <div class="risk-card risk-severe">
          <span class="risk-count">{{ store.summary.severe }}</span>
          <span class="risk-label">严重</span>
        </div>
        <div class="risk-card risk-high">
          <span class="risk-count">{{ store.summary.high }}</span>
          <span class="risk-label">高</span>
        </div>
        <div class="risk-card risk-medium">
          <span class="risk-count">{{ store.summary.medium }}</span>
          <span class="risk-label">中</span>
        </div>
        <div class="risk-card risk-low">
          <span class="risk-count">{{ store.summary.low }}</span>
          <span class="risk-label">低</span>
        </div>
      </div>

      <el-table :data="store.items" stripe style="margin-top: 16px;">
        <el-table-column prop="item_index" label="序号" width="60" />
        <el-table-column prop="item_desc" label="检查项描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="category" label="类别" width="80" />
        <el-table-column prop="risk_level" label="风险等级" width="90">
          <template #default="{ row }">
            <el-tag :type="riskTag(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="page_ref" label="页码" width="70" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '已满足' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
      </el-table>

      <div class="export-bar">
        <el-button type="primary" @click="handleExport">导出 Excel</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useComplianceStore } from '../stores/compliance'

const store = useComplianceStore()
const tenderFile = ref<File | null>(null)
const bidFile = ref<File | null>(null)
const checkProgress = ref(0)

function riskTag(level: string): string {
  const map: Record<string, string> = { '严重': 'danger', '高': 'warning', '中': '', '低': 'info' }
  return map[level] || 'info'
}

function startCheck() {
  if (!tenderFile.value || !bidFile.value) return
  store.reset()
  store.checking = true
  checkProgress.value = 0

  const form = new FormData()
  form.append('tender_file', tenderFile.value)
  form.append('bid_file', bidFile.value)

  fetch('/api/compliance/check', {
    method: 'POST',
    body: form,
  }).then(async (response) => {
    if (!response.ok) {
      store.checking = false
      ElMessage.error('检查请求失败，请重试')
      return
    }
    const reader = response.body?.getReader()
    if (!reader) return
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        store.checking = false
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const d = JSON.parse(line.slice(6))
            if (d.type === 'requirements') {
              checkProgress.value = 10
            } else if (d.type === 'checking') {
              checkProgress.value = Math.round(10 + 80 * (d.item_index / d.total))
            } else if (d.type === 'summary' || d.type === 'done') {
              checkProgress.value = 100
            }
            store.handleSSEEvent(d)
          } catch {}
        }
      }
    }
  }).catch(() => {
    store.checking = false
    ElMessage.error('检查失败')
  })
}

async function handleExport() {
  // 使用最后一个 bid_id
  const bidId = store.items[0]?.bid_id
  if (!bidId) return
  try {
    const response = await fetch(`/api/compliance/${bidId}/export`)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '合规检查结果.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
}
</script>

<style scoped>
.compliance-view { max-width: 1000px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 20px; color: #303133; }
.upload-section { display: flex; gap: 20px; margin-bottom: 16px; }
.upload-box { flex: 1; }
.upload-icon { font-size: 40px; color: #c0c4cc; }
.upload-text { font-size: 14px; color: #606266; margin: 4px 0; }
.upload-selected { font-size: 13px; color: #67c23a; margin-top: 4px; }
.check-actions { text-align: center; margin: 16px 0; }
.check-progress { max-width: 500px; margin: 16px auto; text-align: center; }
.check-progress p { margin-top: 8px; font-size: 13px; color: #909399; }
.risk-summary { display: flex; gap: 16px; margin-top: 16px; }
.risk-card { flex: 1; text-align: center; padding: 16px; border-radius: 8px; color: #fff; }
.risk-severe { background: #f56c6c; }
.risk-high { background: #e6a23c; }
.risk-medium { background: #f0c040; color: #303133; }
.risk-low { background: #909399; }
.risk-count { font-size: 28px; font-weight: 700; display: block; }
.risk-label { font-size: 13px; }
.export-bar { text-align: right; margin-top: 16px; }
</style>
