<template>
  <div class="mobile-lobby">
    <div class="header">
      <h2>欢迎, {{ userName }}</h2>
      <p>等待主持人开启互动...</p>
    </div>
    <div class="content">
      <div v-if="currentPlugin" class="plugin-container">
          <!-- Dynamic Plugin Component -->
          <component :is="pluginComponent" />
      </div>
      <div v-else class="empty-state">
        暂无进行中的互动
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, shallowRef } from 'vue';
import { connection, on } from '@/services/signalr';
import { loadPluginComponent } from '@/utils/pluginLoader';

const userName = ref(localStorage.getItem('userName') || 'Guest');
const currentPlugin = ref(null);
const pluginComponent = shallowRef(null);

onMounted(() => {
    on('SwitchPlugin', async (pluginId) => {
        currentPlugin.value = pluginId;
        // Load remote component
        try {
            const comp = await loadPluginComponent(`/plugins/${pluginId}/mobile.vue`);
            pluginComponent.value = comp;
        } catch (e) {
            console.error("Failed to load plugin", e);
        }
    });
});
</script>

<style scoped>
.mobile-lobby {
    padding: 20px;
}
.header {
    margin-bottom: 30px;
    text-align: center;
}
.empty-state {
    text-align: center;
    color: #999;
    margin-top: 100px;
}
</style>
