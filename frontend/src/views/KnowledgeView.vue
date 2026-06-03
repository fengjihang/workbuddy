<template>
  <div class="knowledge-view">
    <div class="page-header">
      <h2>知识库管理</h2>
      <el-button type="primary" @click="showUpload = true">上传知识文档</el-button>
    </div>

    <el-dialog v-model="showUpload" title="上传知识文档" width="420px">
      <el-form label-width="80px">
        <el-form-item label="分类">
          <el-select v-model="uploadCategory" placeholder="选择分类">
            <el-option label="法律法规" value="法规" />
            <el-option label="公司资质" value="资质" />
            <el-option label="标书模板" value="标书模板" />
            <el-option label="常用话术" value="话术" />
            <el-option label="废标案例" value="案例" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件">
          <el-upload :auto-upload="false" :on-change="(f: any) => uploadFile = f.raw" :limit="1">
            <el-button size="small">选择文件</el-button>
          </el-upload>
          <span v-if="uploadFile" class="file-name">{{ uploadFile.name }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :disabled="!uploadFile || !uploadCategory">上传</el-button>
      </template>
    </el-dialog>

    <div class="filter-bar">
      <el-radio-group v-model="filterCategory" @change="handleFilterChange">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="法规">法律法规</el-radio-button>
        <el-radio-button value="资质">公司资质</el-radio-button>
        <el-radio-button value="标书模板">标书模板</el-radio-button>
        <el-radio-button value="话术">常用话术</el-radio-button>
        <el-radio-button value="案例">废标案例</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="docs" stripe v-loading="loading">
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column prop="title" label="文档名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column prop="upload_time" label="上传时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.upload_time).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useKnowledgeStore } from '../stores/knowledge'

const store = useKnowledgeStore()
const docs = ref(store.docs)
const loading = ref(false)
const showUpload = ref(false)
const uploadFile = ref<File | null>(null)
const uploadCategory = ref('')
const filterCategory = ref('')

async function handleUpload() {
  if (!uploadFile.value || !uploadCategory.value) return
  try {
    await store.uploadDoc(uploadFile.value, uploadCategory.value)
    docs.value = store.docs
    showUpload.value = false
    ElMessage.success('上传成功')
  } catch {
    ElMessage.error('上传失败')
  }
}

async function handleDelete(id: number) {
  try {
    await store.deleteDoc(id)
    docs.value = store.docs
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleFilterChange() {
  await store.fetchDocs(filterCategory.value || undefined)
  docs.value = store.docs
}

onMounted(async () => {
  await store.fetchDocs()
  docs.value = store.docs
})
</script>

<style scoped>
.knowledge-view { max-width: 900px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 20px; color: #303133; }
.filter-bar { margin-bottom: 16px; }
.file-name { margin-left: 10px; font-size: 13px; color: #67c23a; }
</style>
