<template>
  <div class="host-dashboard">
    <div class="header">
      <h2>主持人控制台</h2>
      <div v-if="currentPluginId" class="current-game">
        <p>当前游戏: {{ currentPluginName }}</p>
        <button @click="endCurrentGame" class="btn-danger">结束游戏</button>
      </div>
    </div>

    <div v-if="currentPluginId && gameStats" class="stats-panel">
      <h3>游戏统计</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">在线人数</span>
          <span class="stat-value">{{ gameStats.totalUsers }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">已提交</span>
          <span class="stat-value">{{ gameStats.totalSubmissions }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">正确数</span>
          <span class="stat-value">{{ gameStats.correctCount }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">正确率</span>
          <span class="stat-value">{{ gameStats.accuracy }}%</span>
        </div>
      </div>
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
import { ref, onMounted, onUnmounted, computed } from 'vue';
import axios from 'axios';
import { invoke, on, off } from '@/services/signalr';

const plugins = ref([]);
const currentPluginId = ref(null);
const gameStats = ref(null);

const currentPluginName = computed(() => {
    const plugin = plugins.value.find(p => p.id === currentPluginId.value);
    return plugin ? plugin.name : '';
});

onMounted(async () => {
    try {
        const res = await axios.get('/api/Plugin');
        plugins.value = res.data;
    } catch (e) {
        console.error("Failed to load plugins", e);
        alert("无法加载插件列表");
    }

    // Listen for statistics updates
    on('StatsUpdate', (stats) => {
        gameStats.value = stats;
        console.log('Stats updated:', stats);
    });

    on('SubmissionReceived', (data) => {
        console.log('New submission:', data);
        gameStats.value = data.stats;
    });

    on('GameStarted', (data) => {
        console.log('Game started:', data);
    });

    on('GameEnded', (results) => {
        console.log('Game ended:', results);
        alert(`游戏结束！正确答案：${results.missingNumber}\n正确率：${results.stats.accuracy}%`);
        currentPluginId.value = null;
        gameStats.value = null;
    });
});

onUnmounted(() => {
    off('StatsUpdate');
    off('SubmissionReceived');
    off('GameStarted');
    off('GameEnded');
});

const startPlugin = async (id) => {
    try {
        await invoke("StartInteraction", id);
        currentPluginId.value = id;
        gameStats.value = {
            totalUsers: 0,
            totalSubmissions: 0,
            correctCount: 0,
            accuracy: 0
        };
    } catch (e) {
        console.error("Failed to start plugin", e);
        alert("启动失败: " + e.message);
    }
};

const endCurrentGame = async () => {
    if (!currentPluginId.value) return;
    
    if (confirm('确定要结束当前游戏吗？')) {
        try {
            await invoke("EndGame");
        } catch (e) {
            console.error("Failed to end game", e);
            alert("结束游戏失败");
        }
    }
};
</script>

<style scoped>
.host-dashboard {
    padding: 20px;
    max-width: 800px;
    margin: 0 auto;
}
.header {
    margin-bottom: 30px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}
.current-game {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
    padding: 10px;
    background: #f0f8ff;
    border-radius: 8px;
}
.current-game p {
    margin: 0;
    font-weight: bold;
    color: #0052d9;
}
.btn-danger {
    padding: 8px 16px;
    background: #e34d59;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
}
.stats-panel {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.stats-panel h3 {
    margin-top: 0;
    margin-bottom: 15px;
}
.stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
}
.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 15px;
    background: #f5f5f5;
    border-radius: 8px;
}
.stat-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
}
.stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #0052d9;
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
    cursor: pointer;
}
.start-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}
</style>
