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
import { ref, onMounted, onUnmounted, shallowRef } from 'vue';
import { connection, on, off, invoke } from '@/services/signalr';
import { loadPluginComponent } from '@/utils/pluginLoader';

const userName = ref(localStorage.getItem('userName') || 'Guest');
const currentPlugin = ref(null);
const pluginComponent = shallowRef(null);

// Expose SignalR to plugins via window object
if (typeof window !== 'undefined') {
    window.signalRConnection = connection;
    window.signalRInvoke = invoke;
}

onMounted(() => {
    on('SwitchPlugin', async (pluginId, config) => {
        console.log("Mobile switching to plugin:", pluginId, config);
        currentPlugin.value = pluginId;
        // Load remote component
        try {
            const comp = await loadPluginComponent(`/plugins/${pluginId}/mobile.vue`);
            pluginComponent.value = comp;
        } catch (e) {
            console.error("Failed to load plugin", e);
            alert("加载插件失败: " + e.message);
        }
    });
});

onUnmounted(() => {
    off('SwitchPlugin');
    
    // Clean up window references
    if (typeof window !== 'undefined') {
        delete window.signalRConnection;
        delete window.signalRInvoke;
    }
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
