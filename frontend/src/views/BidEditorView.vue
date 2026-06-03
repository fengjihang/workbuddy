<template>
  <div class="bid-editor">
    <div class="editor-header">
      <el-button @click="$router.back()" text>← 返回</el-button>
      <h2>{{ bidDetail?.name }}</h2>
      <el-button type="primary" @click="handleExport">导出 .docx</el-button>
    </div>

    <div class="editor-body" v-if="bidDetail">
      <div class="chapter-list">
        <h3>章节列表</h3>
        <div
          v-for="ch in bidDetail.chapters"
          :key="ch.chapter_index"
          class="chapter-item"
          :class="{ 'chapter--active': activeChapter === ch.chapter_index }"
          @click="activeChapter = ch.chapter_index"
        >
          <span class="chapter-index">{{ ch.chapter_index }}.</span>
          <span>{{ ch.title }}</span>
        </div>
      </div>

      <div class="field-fill-panel" v-if="activeChapter">
        <el-tabs v-model="fillPanelTab">
          <el-tab-pane label="占位符填写" name="placeholder">
            <p class="hint-text">AI 生成的内容中含有双花括号占位符，扫描后导出 Excel 模板填写真实信息。</p>

            <div class="fill-step">
              <el-button type="primary" size="small" @click="handleExtractFields" :loading="extractingFields">
                扫描当前章节占位符
              </el-button>
            </div>

            <div v-if="detectedFields && detectedFields.fields.length > 0" class="fill-step">
              <p>当前章节检测到 <strong>{{ detectedFields.total_count }}</strong> 个待填写字段：</p>
              <div class="field-tags">
                <el-tag v-for="f in detectedFields.fields" :key="f.field_name" size="small" effect="plain" class="field-tag">
                  {{ f.field_name }}
                </el-tag>
              </div>
              <div class="fill-actions">
                <el-button size="small" @click="handleDownloadFieldsExcel" :loading="downloadingExcel">
                  导出本章节模板 (.xlsx)
                </el-button>
                <el-upload :auto-upload="false" :show-file-list="false" accept=".xlsx,.xls" :on-change="handleUploadFilledExcel">
                  <el-button size="small" type="success">导入填写信息</el-button>
                </el-upload>
              </div>
            </div>

            <div v-if="detectedFields && detectedFields.fields.length === 0" class="fill-step">
              <el-empty description="当前章节未检测到占位符" :image-size="60" />
            </div>

            <div v-if="fillResult" class="fill-step">
              <el-alert :type="fillResult.unfilled_fields.length > 0 ? 'warning' : 'success'" :closable="false">
                <template #title>
                  已更新 {{ fillResult.updated_chapters }} 个章节，填写了 {{ fillResult.filled_fields.length }} 个字段
                </template>
                <span v-if="fillResult.unfilled_fields.length > 0">
                  仍有 {{ fillResult.unfilled_fields.length }} 个字段未填写：{{ fillResult.unfilled_fields.join('、') }}
                </span>
              </el-alert>
              <el-button size="small" @click="handleReloadAfterFill" style="margin-top:8px">刷新编辑器</el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="一键检查" name="inspect">
            <p class="hint-text">对比招标文件要求，AI 智能识别标书中缺失的关键信息（全标书扫描）。</p>

            <div class="fill-step">
              <el-button type="primary" size="small" @click="handleInspect" :loading="store.inspecting">
                一键扫描
              </el-button>
            </div>

            <div v-if="inspectResult" class="fill-step">
              <p>发现 <strong>{{ inspectResult.total_count }}</strong> 个缺失项：</p>
              <div class="inspect-priority-summary">
                <span class="priority-tag must">必须: {{ mustCount }}</span>
                <span class="priority-tag important">重要: {{ importantCount }}</span>
                <span class="priority-tag suggest">建议: {{ suggestCount }}</span>
              </div>

              <div v-for="group in inspectGroups" :key="group.chapter_index" class="inspect-group">
                <h4>{{ group.chapter_title }}</h4>
                <div v-for="f in group.fields" :key="f.field_name" class="inspect-item">
                  <el-tooltip :content="f.description" placement="left" :show-after="300">
                    <span :class="'priority-' + f.priority">[{{ f.priority }}] {{ f.field_name }}</span>
                  </el-tooltip>
                </div>
              </div>

              <div class="fill-actions">
                <el-button size="small" @click="handleDownloadInspectExcel" :loading="downloadingInspectExcel">
                  导出缺失信息模板 (.xlsx)
                </el-button>
                <el-upload :auto-upload="false" :show-file-list="false" accept=".xlsx,.xls" :on-change="handleUploadInspectExcel">
                  <el-button size="small" type="success">导入填写信息</el-button>
                </el-upload>
              </div>
            </div>

            <div v-if="inspectResult && inspectResult.total_count === 0" class="fill-step">
              <el-empty description="未发现缺失信息，标书内容完整" :image-size="60" />
            </div>

            <div v-if="inspectMergeProgress.length > 0" class="fill-step">
              <div v-for="p in inspectMergeProgress" :key="p.chapter" class="merge-progress-item">
                <el-icon v-if="p.status === 'done'" color="#67c23a"><CircleCheckFilled /></el-icon>
                <el-icon v-else color="#409eff"><Loading /></el-icon>
                <span>{{ p.chapter }} {{ p.status === 'done' ? '已完成' : '处理中...' }}</span>
              </div>
            </div>

            <div v-if="inspectMergeDone" class="fill-step">
              <el-alert type="success" :closable="false" title="缺失信息已融入标书各章节" />
              <el-button size="small" @click="reloadAfterInspectFill" style="margin-top:8px">刷新编辑器</el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="chapter-editor" v-if="activeChapter">
        <div class="editor-toolbar">
          <h3>{{ currentChapter?.title }}</h3>
          <el-button size="small" type="primary" @click="handleGenerate" :loading="generating">
            AI 生成
          </el-button>
        </div>
        <el-input
          v-model="editingContent"
          type="textarea"
          :rows="20"
          placeholder="在此编辑章节内容，或点击「AI 生成」自动生成..."
        />
        <div v-if="generatingStream" class="generating-stream">{{ generatingStream }}</div>
        <div class="editor-actions">
          <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled, Loading } from '@element-plus/icons-vue'
import { useBidStore } from '../stores/bid'
import type { FieldListResponse, FillResult, InspectResult, MissingField } from '../types'
import type { UploadFile } from 'element-plus'

const route = useRoute()
const store = useBidStore()

const bidDetail = computed(() => store.currentBid)
const activeChapter = ref(1)
const editingContent = ref('')
const generating = ref(false)
const generatingStream = ref('')
const saving = ref(false)

const fillPanelTab = ref('placeholder')
const detectedFields = ref<FieldListResponse | null>(null)
const fillResult = ref<FillResult | null>(null)
const extractingFields = ref(false)
const downloadingExcel = ref(false)

const inspectResult = ref<InspectResult | null>(null)
const downloadingInspectExcel = ref(false)
const inspectMergeProgress = ref<{ chapter: string; status: 'loading' | 'done' }[]>([])
const inspectMergeDone = ref(false)

const currentChapter = computed(() =>
  bidDetail.value?.chapters.find(c => c.chapter_index === activeChapter.value)
)

const mustCount = computed(() => inspectResult.value?.missing_fields.filter(f => f.priority === '必须').length ?? 0)
const importantCount = computed(() => inspectResult.value?.missing_fields.filter(f => f.priority === '重要').length ?? 0)
const suggestCount = computed(() => inspectResult.value?.missing_fields.filter(f => f.priority === '建议').length ?? 0)

const inspectGroups = computed(() => {
  if (!inspectResult.value) return []
  const groups: Record<number, { chapter_index: number; chapter_title: string; fields: MissingField[] }> = {}
  for (const f of inspectResult.value.missing_fields) {
    const key = f.suggested_chapter_index
    if (!groups[key]) {
      groups[key] = { chapter_index: key, chapter_title: f.suggested_chapter_title, fields: [] }
    }
    groups[key].fields.push(f)
  }
  return Object.values(groups)
})

watch(activeChapter, async () => {
  editingContent.value = currentChapter.value?.content || ''
  generatingStream.value = ''
  fillResult.value = null
  if (currentChapter.value?.content) {
    await handleExtractFields()
  } else {
    detectedFields.value = null
  }
})

async function handleGenerate() {
  if (!bidDetail.value) return
  generating.value = true
  generatingStream.value = ''
  try {
    const result = await store.generateChapter(
      bidDetail.value.id, activeChapter.value,
      (token) => { generatingStream.value += token },
    )
    editingContent.value = result
    store.updateChapterContent(activeChapter.value, result)
  } catch {
    ElMessage.error('生成失败')
  }
  generating.value = false
}

async function handleSave() {
  if (!bidDetail.value) return
  saving.value = true
  try {
    await store.updateChapter(bidDetail.value.id, activeChapter.value, editingContent.value)
    store.updateChapterContent(activeChapter.value, editingContent.value)
    ElMessage.success('已保存')
  } catch {
    ElMessage.error('保存失败')
  }
  saving.value = false
}

async function handleExport() {
  if (!bidDetail.value) return
  try {
    const url = await store.exportBid(bidDetail.value.id)
    const a = document.createElement('a')
    a.href = url
    a.download = ''
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

async function handleExtractFields() {
  if (!bidDetail.value) return
  extractingFields.value = true
  fillResult.value = null
  try {
    detectedFields.value = await store.fetchFields(bidDetail.value.id, activeChapter.value)
  } catch {
    ElMessage.error('字段提取失败')
  }
  extractingFields.value = false
}

async function handleDownloadFieldsExcel() {
  if (!bidDetail.value) return
  downloadingExcel.value = true
  try {
    const url = await store.downloadFieldsExcel(bidDetail.value.id, activeChapter.value)
    const a = document.createElement('a')
    a.href = url
    a.download = ''
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('Excel 模板已下载')
  } catch {
    ElMessage.error('Excel 下载失败')
  }
  downloadingExcel.value = false
}

async function handleUploadFilledExcel(uploadFile: UploadFile) {
  if (!bidDetail.value || !uploadFile.raw) return
  try {
    const result = await store.uploadFilledFields(bidDetail.value.id, uploadFile.raw, activeChapter.value)
    fillResult.value = result
    if (currentChapter.value?.content) {
      editingContent.value = currentChapter.value.content
    }
    ElMessage.success(`已填写 ${result.filled_fields.length} 个字段`)
  } catch {
    ElMessage.error('填写失败，请检查Excel格式是否正确')
  }
}

function handleReloadAfterFill() {
  if (!bidDetail.value) return
  store.fetchBid(bidDetail.value.id)
  if (currentChapter.value?.content) {
    editingContent.value = currentChapter.value.content
  }
  fillResult.value = null
  detectedFields.value = null
}

async function handleInspect() {
  if (!bidDetail.value) return
  inspectMergeDone.value = false
  inspectMergeProgress.value = []
  try {
    inspectResult.value = await store.inspectBid(bidDetail.value.id)
    if (inspectResult.value.total_count > 0) {
      ElMessage.success(`发现 ${inspectResult.value.total_count} 个缺失项`)
    }
  } catch {
    ElMessage.error('检查失败，请确保标书已关联招标文件')
  }
}

async function handleDownloadInspectExcel() {
  if (!bidDetail.value) return
  downloadingInspectExcel.value = true
  try {
    const url = await store.downloadInspectExcel(bidDetail.value.id)
    const a = document.createElement('a')
    a.href = url
    a.download = ''
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('缺失信息模板已下载')
  } catch {
    ElMessage.error('Excel 下载失败，请先执行一键扫描')
  }
  downloadingInspectExcel.value = false
}

async function handleUploadInspectExcel(uploadFile: UploadFile) {
  if (!bidDetail.value || !uploadFile.raw) return
  inspectMergeProgress.value = []
  inspectMergeDone.value = false
  try {
    const response = await store.uploadInspectFill(bidDetail.value.id, uploadFile.raw)
    if (!response.ok) throw new Error('Upload failed')

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No stream reader')
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      while (true) {
        const eventMatch = buffer.match(/^event: (\w+)\ndata: (.+?)(?=\n\nevent:|\n\n$|\n$)/s)
        if (!eventMatch) break
        const [fullMatch, event, dataStr] = eventMatch
        buffer = buffer.slice(buffer.indexOf(fullMatch) + fullMatch.length)
        try {
          const data = JSON.parse(dataStr.trim())
          if (event === 'chapter_start') {
            inspectMergeProgress.value.push({ chapter: data.chapter_title, status: 'loading' })
          } else if (event === 'chapter_done') {
            const item = inspectMergeProgress.value.find(p => p.chapter === data.chapter_title)
            if (item) item.status = 'done'
          } else if (event === 'done') {
            inspectMergeDone.value = true
            ElMessage.success('缺失信息已融入标书')
            return
          }
        } catch { /* skip parse errors for partial chunks */ }
      }
    }
  } catch {
    ElMessage.error('填写失败，请检查Excel格式是否正确')
  }
}

function reloadAfterInspectFill() {
  if (!bidDetail.value) return
  store.fetchBid(bidDetail.value.id)
  if (currentChapter.value?.content) {
    editingContent.value = currentChapter.value.content
  }
  inspectMergeDone.value = false
}

onMounted(async () => {
  const id = Number(route.params.id)
  await store.fetchBid(id)
  if (currentChapter.value?.content) {
    editingContent.value = currentChapter.value.content
  }
})
</script>

<style scoped>
.bid-editor { max-width: 1200px; }
.editor-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.editor-header h2 { flex: 1; font-size: 18px; color: #303133; }
.editor-body { display: flex; gap: 20px; height: calc(100vh - 160px); }
.chapter-list { width: 220px; min-width: 220px; background: #fff; border-radius: 8px; padding: 16px; overflow-y: auto; }
.chapter-list h3 { font-size: 14px; color: #909399; margin-bottom: 12px; }
.chapter-item { display: flex; gap: 6px; padding: 8px 10px; font-size: 13px; color: #606266; cursor: pointer; border-radius: 4px; }
.chapter-item:hover { background: #f5f7fa; }
.chapter--active { background: #ecf5ff; color: #409eff; }
.chapter-index { font-weight: 600; }
.chapter-editor { flex: 1; background: #fff; border-radius: 8px; padding: 20px; overflow-y: auto; }
.editor-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.editor-toolbar h3 { font-size: 16px; color: #303133; }
.generating-stream { margin-top: 8px; padding: 12px; background: #f0f9eb; border-radius: 4px; font-size: 13px; color: #67c23a; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }
.editor-actions { margin-top: 12px; text-align: right; }
.field-fill-panel {
  width: 280px;
  min-width: 280px;
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;
}
.field-fill-panel :deep(.el-tabs__header) { margin-bottom: 8px; }
.field-fill-panel :deep(.el-tabs__item) { font-size: 13px; padding: 0 12px; height: 32px; line-height: 32px; }
.hint-text { font-size: 12px; color: #909399; margin: 0 0 8px; line-height: 1.5; }
.fill-step { padding: 10px 0; border-top: 1px solid #ebeef5; }
.fill-step:first-of-type { border-top: none; padding-top: 0; }
.field-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.field-tag { max-width: 220px; overflow: hidden; text-overflow: ellipsis; }
.fill-actions { display: flex; flex-direction: column; gap: 8px; }
.inspect-priority-summary { display: flex; gap: 8px; margin-bottom: 8px; }
.priority-tag { font-size: 12px; padding: 2px 6px; border-radius: 4px; }
.priority-tag.must { background: #fef0f0; color: #f56c6c; }
.priority-tag.important { background: #fdf6ec; color: #e6a23c; }
.priority-tag.suggest { background: #ecf5ff; color: #409eff; }
.inspect-group { margin-bottom: 6px; }
.inspect-group h4 { font-size: 12px; color: #909399; margin: 4px 0; }
.inspect-item { font-size: 12px; padding: 2px 0; cursor: default; }
.inspect-item .priority-必须 { color: #f56c6c; }
.inspect-item .priority-重要 { color: #e6a23c; }
.inspect-item .priority-建议 { color: #409eff; }
.merge-progress-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #606266; }
</style>
