<template>
  <div class="app-container">
    <WorkSpace />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import WorkSpace from './WorkSpace.vue'
</script>
