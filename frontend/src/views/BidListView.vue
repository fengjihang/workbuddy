<template>
  <div class="bid-list-view">
    <div class="page-header">
      <h2>标书制作</h2>
      <el-button type="primary" @click="showCreate = true">新建标书</el-button>
    </div>

    <el-dialog v-model="showCreate" title="新建标书" width="420px">
      <el-form label-width="80px">
        <el-form-item label="标书名称">
          <el-input v-model="newBidName" placeholder="如：XXX项目投标书" />
        </el-form-item>
        <el-form-item label="关联招标文件">
          <el-select v-model="newBidTenderId" placeholder="可选" clearable>
            <el-option v-for="t in tenders" :key="t.id" :label="t.filename" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :disabled="!newBidName">创建</el-button>
      </template>
    </el-dialog>

    <el-table v-if="bids.length > 0" :data="bids" stripe>
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column prop="name" label="标书名称" min-width="200" />
      <el-table-column prop="create_time" label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.create_time).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === '已导出' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="$router.push(`/bid/${row.id}`)">编辑</el-button>
          <el-button size="small" @click="handleExport(row.id)">导出</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-else description="暂无标书，点击上方按钮新建" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useBidStore } from '../stores/bid'
import { useTenderStore } from '../stores/tender'
import type { Tender } from '../types'

const bidStore = useBidStore()
const tenderStore = useTenderStore()

const bids = ref(bidStore.bids)
const tenders = ref<Tender[]>([])
const showCreate = ref(false)
const newBidName = ref('')
const newBidTenderId = ref<number | null>(null)

async function handleCreate() {
  try {
    await bidStore.createBid(newBidName.value, newBidTenderId.value)
    bids.value = bidStore.bids
    showCreate.value = false
    newBidName.value = ''
    ElMessage.success('创建成功')
  } catch {
    ElMessage.error('创建失败')
  }
}

async function handleExport(id: number) {
  try {
    const url = await bidStore.exportBid(id)
    const a = document.createElement('a')
    a.href = url
    a.download = ''
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
}

async function handleDelete(id: number) {
  try {
    await bidStore.deleteBid(id)
    bids.value = bidStore.bids
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(async () => {
  await bidStore.fetchBids()
  bids.value = bidStore.bids
  await tenderStore.fetchTenders()
  tenders.value = tenderStore.tenders
})
</script>

<style scoped>
.bid-list-view { max-width: 900px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 20px; color: #303133; }
</style>
