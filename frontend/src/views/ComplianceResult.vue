<template>
  <div class="compliance-result">
    <div class="page-header">
      <el-button @click="$router.back()" text>← 返回</el-button>
      <h2>历史检查结果</h2>
    </div>
    <el-empty v-if="!results.length" description="暂无检查结果" />
    <div v-else>
      <!-- Same as ComplianceView results section -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()
const results = ref<any[]>([])

onMounted(async () => {
  const { data } = await api.get(`/compliance/${route.params.id}/results`)
  results.value = data
})
</script>

<style scoped>
.compliance-result { max-width: 1000px; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.page-header h2 { font-size: 20px; color: #303133; }
</style>
