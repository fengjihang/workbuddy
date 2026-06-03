<template>
  <div class="analysis-view">
    <div class="page-header">
      <h2>招标文件解读</h2>
    </div>

    <el-upload
      class="upload-area"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :limit="1"
      accept=".docx,.pdf"
    >
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <div class="upload-text">拖拽或点击上传招标文件</div>
      <div class="upload-hint">支持 .docx / .pdf 格式</div>
    </el-upload>

    <div v-if="uploading" class="upload-progress">
      <el-progress :percentage="100" :indeterminate="true" />
      <span>正在上传...</span>
    </div>

    <div class="tender-list" v-if="tenders.length > 0">
      <h3>已上传文件</h3>
      <el-table :data="tenders" stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="upload_time" label="上传时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.upload_time).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button v-if="row.status === '已解读'" size="small" @click="$router.push(`/analysis/${row.id}`)">
              查看
            </el-button>
            <el-button v-if="row.status === '解读中'" size="small" type="warning" @click="$router.push(`/analysis/${row.id}`)">
              继续解读
            </el-button>
            <el-button v-if="row.status === '已上传'" size="small" type="primary" @click="startAnalysis(row.id)">
              开始解读
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useTenderStore } from '../stores/tender'

const store = useTenderStore()
const router = useRouter()
const tenders = ref(store.tenders)
const uploading = ref(false)

function statusTag(status: string): 'success' | 'warning' | 'info' {
  if (status === '已解读') return 'success'
  if (status === '解读中') return 'warning'
  return 'info'
}

async function handleFileChange(file: any) {
  uploading.value = true
  try {
    await store.uploadTender(file.raw)
    ElMessage.success('上传成功')
    tenders.value = store.tenders
  } catch {
    ElMessage.error('上传失败')
  }
  uploading.value = false
}

function startAnalysis(id: number) {
  router.push(`/analysis/${id}`)
}

async function handleDelete(id: number) {
  try {
    await store.deleteTender(id)
    tenders.value = store.tenders
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  store.fetchTenders().then(() => {
    tenders.value = store.tenders
  })
})
</script>

<style scoped>
.analysis-view { max-width: 900px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 20px; color: #303133; }
.upload-area { margin-bottom: 24px; }
.upload-icon { font-size: 48px; color: #c0c4cc; }
.upload-text { font-size: 16px; color: #606266; margin: 8px 0; }
.upload-hint { font-size: 12px; color: #c0c4cc; }
.upload-progress { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.tender-list h3 { font-size: 15px; color: #606266; margin-bottom: 12px; }
</style>
