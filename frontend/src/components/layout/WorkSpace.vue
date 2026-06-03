<template>
  <aside class="workspace">
    <div class="workspace-header">
      <h2>ZCM 招投标助手</h2>
    </div>

    <nav class="workspace-nav">
      <router-link to="/analysis" class="nav-item" active-class="nav-item--active">
        <el-icon><Document /></el-icon>
        <span>招标解读</span>
      </router-link>
      <router-link to="/bid" class="nav-item" active-class="nav-item--active">
        <el-icon><Edit /></el-icon>
        <span>标书制作</span>
      </router-link>
      <router-link to="/compliance" class="nav-item" active-class="nav-item--active">
        <el-icon><CircleCheck /></el-icon>
        <span>合规检查</span>
      </router-link>
      <router-link to="/knowledge" class="nav-item" active-class="nav-item--active">
        <el-icon><FolderOpened /></el-icon>
        <span>知识库</span>
      </router-link>
    </nav>

    <div class="workspace-recent">
      <h3>最近文件</h3>
      <div v-if="recentTenders.length === 0" class="recent-empty">暂无文件</div>
      <div v-for="t in recentTenders" :key="t.id" class="recent-item" @click="$router.push(`/analysis/${t.id}`)">
        <el-icon><Document /></el-icon>
        <span class="recent-name">{{ t.filename }}</span>
        <el-tag :type="statusTag(t.status)" size="small">{{ t.status }}</el-tag>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Document, Edit, CircleCheck, FolderOpened } from '@element-plus/icons-vue'
import api from '../../api'
import type { Tender } from '../../types'

const recentTenders = ref<Tender[]>([])

function statusTag(status: string): 'success' | 'warning' | 'info' {
  if (status === '已解读') return 'success'
  if (status === '解读中') return 'warning'
  return 'info'
}

onMounted(async () => {
  try {
    const { data } = await api.get('/tenders')
    recentTenders.value = data.slice(0, 5)
  } catch {}
})
</script>

<style scoped>
.workspace {
  width: 200px;
  min-width: 200px;
  height: 100%;
  background: #1d1e2c;
  color: #ccc;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.workspace-header {
  padding: 20px 16px;
  border-bottom: 1px solid #333;
}
.workspace-header h2 {
  color: #fff;
  font-size: 16px;
  text-align: center;
}
.workspace-nav {
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  color: #aaa;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}
.nav-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}
.nav-item--active {
  color: #409eff;
  background: rgba(64, 158, 255, 0.12);
}
.workspace-recent {
  margin-top: 24px;
  padding: 0 16px;
  flex: 1;
  overflow-y: auto;
}
.workspace-recent h3 {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
  text-transform: uppercase;
}
.recent-empty {
  font-size: 12px;
  color: #666;
}
.recent-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  cursor: pointer;
  font-size: 12px;
}
.recent-item:hover {
  color: #fff;
}
.recent-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
