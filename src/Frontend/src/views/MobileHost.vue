<template>
  <div class="host-dashboard">
    <div class="header">
      <h2>主持人控制台</h2>
    </div>
    
    <div class="plugins-list">
      <h3>可用互动</h3>
      <div 
        v-for="plugin in plugins" 
        :key="plugin.id" 
        class="plugin-card"
      >
        <div class="plugin-info">
          <h4>{{ plugin.name }}</h4>
          <p>{{ plugin.description }}</p>
        </div>
        <button 
            @click="startPlugin(plugin.id)" 
            class="start-btn"
            :disabled="currentPluginId === plugin.id"
        >
            {{ currentPluginId === plugin.id ? '进行中' : '开始' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { invoke } from '@/services/signalr';

const plugins = ref([]);
const currentPluginId = ref(null);

onMounted(async () => {
    try {
        const res = await axios.get('/api/plugin');
        plugins.value = res.data;
    } catch (e) {
        console.error("Failed to load plugins", e);
    }
});

const startPlugin = async (id) => {
    try {
        await invoke("StartInteraction", id);
        currentPluginId.value = id;
    } catch (e) {
        console.error("Failed to start plugin", e);
        alert("启动失败");
    }
};
</script>

<style scoped>
.host-dashboard {
    padding: 20px;
}
.header {
    margin-bottom: 30px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}
.plugin-card {
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.plugin-info h4 {
    margin: 0 0 5px 0;
    font-size: 16px;
}
.plugin-info p {
    margin: 0;
    color: #666;
    font-size: 12px;
}
.start-btn {
    padding: 8px 16px;
    background: #0052d9;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 14px;
}
.start-btn:disabled {
    background: #ccc;
}
</style>
